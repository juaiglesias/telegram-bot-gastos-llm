"""Configuración de logging con rotación de archivos."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(config) -> logging.Logger:
    """
    Configura el logger con salida a consola y archivo con rotación.

    Args:
        config: Instancia de Config con la configuración

    Returns:
        Logger configurado
    """
    # Crear logger
    logger = logging.getLogger('telegram-bot-gastos-llm')
    logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))

    # Evitar duplicados si ya está configurado
    if logger.handlers:
        return logger

    # Formato de los mensajes
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo con rotación (10MB, 5 backups)
    try:
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'bot.log'

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        logger.warning("No se pudo crear archivo de log en /var/log/telegram-bot-gastos-llm/, solo se usará consola")

    return logger
