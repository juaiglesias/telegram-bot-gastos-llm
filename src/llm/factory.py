"""Factory para instanciar el conector LLM según configuración."""
import logging
from src.llm.base import LLMConnector
from src.llm.ollama_client import OllamaClient
from src.llm.gemini_client import GeminiClient


logger = logging.getLogger('telegram-bot-gastos-llm')

SUPPORTED_CONNECTORS = ('ollama', 'gemini')


def create_llm_connector(config) -> LLMConnector:
    """
    Crea e instancia el conector LLM según LLM_CONNECTOR en config.

    Args:
        config: Instancia de Config con las variables de entorno cargadas

    Returns:
        Instancia de LLMConnector (OllamaClient o GeminiClient)

    Raises:
        ValueError: Si LLM_CONNECTOR tiene un valor no soportado
    """
    connector = config.llm_connector

    if connector == 'ollama':
        logger.info(f"Usando conector LLM: Ollama (modelo: {config.ollama_model})")
        return OllamaClient(model=config.ollama_model, timeout=config.ollama_timeout)

    if connector == 'gemini':
        logger.info(f"Usando conector LLM: Gemini (modelo: {config.gemini_model})")
        return GeminiClient(api_key=config.gemini_api_key, model=config.gemini_model)

    raise ValueError(
        f"LLM_CONNECTOR '{connector}' no soportado. Valores válidos: {', '.join(SUPPORTED_CONNECTORS)}"
    )
