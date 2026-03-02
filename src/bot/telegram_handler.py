"""Handlers del bot de Telegram."""
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from src.llm.prompt_builder import build_prompt
from src.llm.ollama_client import OllamaClient
from src.storage.sheets_client import SheetsClient
from src.utils.validators import validate_expense_data
from src.utils.exceptions import (
    OllamaConnectionError,
    OllamaInvalidJSONError,
    InvalidExpenseDataError,
    GoogleSheetsError
)


logger = logging.getLogger('telegram-bot-gastos-llm')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para el comando /start.

    Args:
        update: Update de Telegram
        context: Contexto del bot
    """
    welcome_message = """¡Hola! 👋

Soy tu asistente de gastos personal. Envíame tus gastos en lenguaje natural y los registraré automáticamente en tu planilla.

📝 Ejemplos:
• "Compré pan por $500 ayer"
• "Gasté 1200 en suplementos"
• "Salida con amigos, 3500 pesos"
• "Super hoy 2500"

Usa /help para ver más información."""

    await update.message.reply_text(welcome_message)
    logger.info(f"Comando /start recibido de usuario {update.effective_user.id}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para el comando /help.

    Args:
        update: Update de Telegram
        context: Contexto del bot
    """
    # Obtener categorías de la configuración almacenada en context
    categories = context.bot_data.get('categories', [])
    categories_str = '\n• '.join(categories)

    help_message = f"""ℹ️ Ayuda - Bot de Gastos

📂 Categorías disponibles:
• {categories_str}

📝 Cómo usar:
Simplemente envíame un mensaje describiendo tu gasto. Por ejemplo:
• "Compré X por $Y"
• "Gasté Z en [categoría]"
• "Salida ayer, 1500 pesos"

El bot entenderá automáticamente:
✅ El monto del gasto
✅ La categoría
✅ La fecha (si no la especificas, asume hoy)

Los gastos se registran automáticamente en tu planilla de Google Sheets."""

    await update.message.reply_text(help_message)
    logger.info(f"Comando /help recibido de usuario {update.effective_user.id}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler unificado de mensaje, en caso de ser texto realiza validaciones, y en caso de ser un audio intenta primero transcribirlo utilizando
    whisper de OpenAI (https://openai.com/index/whisper/)
    """
    message = update.message
    user_id = update.effective_user.id

    logger.info(f"Mensaje recibido del usuario {user_id}")


    # 1. ¿Es un audio o nota de voz?
    if message.voice or message.audio:
        # Obtener el archivo de mayor calidad
        audio_file = await (message.voice or message.audio).get_file()

        # Descarga temporal
        file_path = f"temp_audio_{user_id}.ogg"
        await audio_file.download_to_drive(file_path)

        whisper_model = context.bot_data['whisper_model']

        try:
            # 2· Transcribir con whisper
            result = whisper_model.transcribe(file_path, language="es", fp16=False)
            user_message = result["text"]
            logger.info(f"Audio transcrito: {user_message}")
        finally:
            # Limpiar archivo temporal
            if os.path.exists(file_path):
                os.remove(file_path)
    elif message.text:
            user_message = message.text
    else:
        logger.warning("Formato del mensaje del usuario {user_id} no soportado")
        return

    await handle_text_message(user_message, update, context)


async def handle_text_message(user_message, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para mensajes de texto con gastos.

    Este es el flujo completo:
    1. Construir prompt con fecha actual
    2. Generar respuesta con Ollama
    3. Validar datos extraídos
    4. Guardar en Google Sheets
    5. Confirmar al usuario

    Args:
        user_message: String mensaje del usuario
        update: Update de Telegram
        context: Contexto del bot
    """
    user_id = update.effective_user.id

    logger.info(f"Mensaje del usuario {user_id}: {user_message}")

    # Obtener clientes del contexto
    ollama_client: OllamaClient = context.bot_data['ollama_client']
    sheets_client: SheetsClient = context.bot_data['sheets_client']
    categories = context.bot_data['categories']

    try:
        # Enviar indicador de "escribiendo..."
        await update.message.chat.send_action(action="typing")

        # 1. Construir prompt con fecha actual
        prompt = build_prompt(user_message, categories)

        # 2. Generar respuesta con Ollama
        expense_data = ollama_client.generate(prompt)
        logger.debug(f"Datos extraídos: {expense_data}")

        # 3. Validar datos
        is_valid, error_message = validate_expense_data(expense_data, categories)
        if not is_valid:
            logger.warning(f"Datos inválidos: {error_message}")
            await update.message.reply_text(
                f"❌ {error_message}\n\n"
                f"💡 Intenta reformular tu mensaje con monto y categoría claros."
            )
            return

        # 4. Guardar en Google Sheets
        sheets_client.append_expense(
            fecha=expense_data['fecha'],
            descripcion=expense_data['descripcion'],
            categoria=expense_data['categoria'],
            monto=expense_data['monto']
        )

        # 5. Confirmar al usuario
        confirmation_message = format_confirmation_message(expense_data, user_message)
        await update.message.reply_text(confirmation_message)

        logger.info(f"Gasto registrado exitosamente para usuario {user_id}")

    except OllamaConnectionError:
        error_msg = "❌ Error de conexión con el LLM.\n🔧 El servicio no está disponible. Intenta más tarde."
        await update.message.reply_text(error_msg)
        logger.error("Error de conexión con Ollama")

    except OllamaInvalidJSONError:
        error_msg = (
            "❌ No pude entender tu mensaje.\n\n"
            "💡 Intenta ser más específico:\n"
            "• 'Compré [cosa] por $[monto]'\n"
            "• 'Gasté [monto] en [categoría]'"
        )
        await update.message.reply_text(error_msg)
        logger.error("JSON inválido desde Ollama")

    except GoogleSheetsError as e:
        error_msg = f"❌ Error al guardar en Google Sheets.\n🔧 {str(e)}"
        await update.message.reply_text(error_msg)
        logger.error(f"Error de Google Sheets: {e}")

    except Exception as e:
        error_msg = "❌ Ocurrió un error inesperado.\n🔧 Intenta nuevamente más tarde."
        await update.message.reply_text(error_msg)
        logger.exception(f"Error inesperado: {e}")


def format_confirmation_message(expense_data: dict, original_message: str) -> str:
    """
    Formatea el mensaje de confirmación con emojis.

    Args:
        expense_data: Datos del gasto (monto, categoria, fecha)
        original_message: Mensaje original del usuario

    Returns:
        Mensaje de confirmación formateado
    """
    return f"""✅ Gasto registrado correctamente

💰 Monto: ${expense_data['monto']:.2f}
📂 Categoría: {expense_data['categoria']}
📅 Fecha: {expense_data['fecha']}
📝 Descripción: {expense_data['descripcion']}

Registro completado en Google Sheets ✨"""
