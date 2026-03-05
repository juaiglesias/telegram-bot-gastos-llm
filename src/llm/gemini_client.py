"""Cliente para interactuar con Gemini usando la librería oficial de Google."""
import json
import re
import logging
import google.generativeai as genai
from src.llm.base import LLMConnector
from src.utils.exceptions import GeminiConnectionError, GeminiInvalidJSONError


logger = logging.getLogger('telegram-bot-gastos-llm')


class GeminiClient(LLMConnector):
    """Cliente para generar respuestas usando Gemini."""

    def __init__(self, api_key: str, model: str = 'gemini-2.0-flash'):
        """
        Inicializa el cliente de Gemini.

        Args:
            api_key: API key de Google Gemini
            model: Nombre del modelo (ej: "gemini-2.0-flash")
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        logger.info(f"Cliente Gemini inicializado con modelo: {model}")

    def generate(self, prompt: str) -> dict:
        """
        Genera una respuesta usando Gemini y extrae el JSON.

        Args:
            prompt: Prompt completo para el modelo

        Returns:
            Diccionario con los datos del gasto (monto, categoria, fecha)

        Raises:
            GeminiConnectionError: Si no se puede conectar con Gemini
            GeminiInvalidJSONError: Si no se puede parsear el JSON
        """
        try:
            logger.debug(f"Enviando prompt a Gemini (modelo: {self.model_name})")
            response = self.model.generate_content(prompt)
            response_text = response.text
            logger.debug(f"Respuesta de Gemini: {response_text}")
            return self._extract_json_from_text(response_text)

        except Exception as e:
            logger.error(f"Error al conectar con Gemini: {e}")
            raise GeminiConnectionError(f"No se pudo conectar con Gemini: {e}")

    def _extract_json_from_text(self, text: str) -> dict:
        """
        Extrae JSON de un texto, incluso si viene rodeado de texto adicional.

        Args:
            text: Texto que contiene JSON

        Returns:
            Diccionario parseado del JSON

        Raises:
            GeminiInvalidJSONError: Si no se encuentra o no se puede parsear el JSON
        """
        json_match = re.search(r'\{.*\}', text, re.DOTALL)

        if not json_match:
            logger.error(f"No se encontró JSON en la respuesta: {text}")
            raise GeminiInvalidJSONError("No se encontró JSON en la respuesta del modelo")

        json_str = json_match.group()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON: {e}")
            raise GeminiInvalidJSONError(f"JSON inválido: {e}")
