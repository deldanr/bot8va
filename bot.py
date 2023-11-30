from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import main
import pandas as pd
import re
import os
from dotenv import load_dotenv

# Inicializar el bot
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
df = main.crear_dataset()


def crear_dataset(directorio_raiz='./Repositorio'):
    dataset = []
    # Iterar sobre las carpetas de año
    for carpeta_ano in os.listdir(directorio_raiz):
        if carpeta_ano.startswith("ODD"):
            path_carpeta_ano = os.path.join(directorio_raiz, carpeta_ano)
            # Iterar sobre los archivos en la subcarpeta
            for archivo in os.listdir(path_carpeta_ano):
                if archivo.endswith('.pdf'):
                    partes_nombre = archivo.split(' ')
                    if re.match(r'\d{4}-\d{3}', partes_nombre[0]):
                        ano, numero = partes_nombre[0].split('-')
                        asunto = ' '.join(partes_nombre[1:]).replace('.pdf', '')
                    else:
                        ano, numero = '0000', '000'
                        asunto = 'Sin Asunto'
                    asunto = asunto if asunto.strip() else 'Sin Asunto'
                    ruta = os.path.join(path_carpeta_ano, archivo)
                    # Agregar la información al dataset
                    dataset.append({'Año': ano, 'Número': numero, 'Asunto': asunto, 'Ruta': ruta})
    return pd.DataFrame(dataset)


# Funciones para obtener años y números
def obtener_anios_disponibles(df):
    return df['Año'].drop_duplicates().sort_values().tolist()

def obtener_numeros_por_anio(df, anio):
    return df[df['Año'] == anio]['Número'].tolist()


# Comando /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    start_message = (
        "¡Bienvenide!\n"
        "Puedo ayudarte a navegar por las Ordenes del Día organizadas por año y número.\n\n"
        "Comandos disponibles:\n"
        "/start - Muestra este mensaje\n"
        "/ver - Muestra los años disponibles para explorar"
    )
    await message.reply(start_message)
    
# Comando /ver para mostrar años
@dp.message_handler(commands=['ver'])
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=6)  # Ajusta el row_width según sea necesario
    anios = obtener_anios_disponibles(df)
    for anio in anios:
        keyboard.insert(InlineKeyboardButton(text=anio, callback_data=anio))
    await message.reply("Selecciona un año:", reply_markup=keyboard)

# Callback para cuando se selecciona un año
@dp.callback_query_handler(lambda c: c.data in obtener_anios_disponibles(df))
async def process_callback_anio(callback_query: types.CallbackQuery):
    anio = callback_query.data
    numeros = obtener_numeros_por_anio(df, anio)

    keyboard = InlineKeyboardMarkup(row_width=8)  # Ajusta el row_width según sea necesario
    for numero in numeros:
        callback_data = f"{anio}-{numero}"  # Formato para identificar año y número
        keyboard.insert(InlineKeyboardButton(text=numero, callback_data=callback_data))
    
    await bot.send_message(callback_query.message.chat.id, f"Selecciona un número para el año {anio}:", reply_markup=keyboard)

# Callback para cuando se selecciona un número
@dp.callback_query_handler(lambda c: '-' in c.data)  # Supone que el callback_data es "año-número"
async def enviar_pdf(callback_query: types.CallbackQuery):
    anio, numero = callback_query.data.split('-')

    # Encuentra la ruta del PDF en el DataFrame
    ruta_pdf = df[(df['Año'] == anio) & (df['Número'] == numero)]['Ruta'].iloc[0]

    try:
        with open(ruta_pdf, 'rb') as pdf_file:
            await bot.send_document(callback_query.message.chat.id, pdf_file)
    except Exception as e:
        await bot.send_message(callback_query.message.chat.id, f"Error al enviar documento: {str(e)}")

# Función para configurar los comandos del bot
async def setup_bot_commands(dp):
    commands = [
        BotCommand(command="/start", description="Iniciar el bot"),
        BotCommand(command="/ver", description="Ver años disponibles")
    ]
    await bot.set_my_commands(commands)
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=setup_bot_commands)
