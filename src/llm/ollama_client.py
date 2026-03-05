"""Cliente para interactuar con Ollama usando la librería oficial."""
import json
import re
import logging
import ollama
from src.llm.base import LLMConnector
from src.utils.exceptions import OllamaConnectionError, OllamaInvalidJSONError


logger = logging.getLogger('telegram-bot-gastos-llm')


class OllamaClient(LLMConnector):
    """Cliente para generar respuestas usando Ollama."""

    def __init__(self, model: str, timeout: int = 45):
        """
        Inicializa el cliente de Ollama.

        Args:
            model: Nombre del modelo (ej: "qwen3:1.7b")
            timeout: Timeout en segundos para la generación
        """
        self.model = model
        self.timeout = timeout
        logger.info(f"Cliente Ollama inicializado con modelo: {model}")

    def generate(self, prompt: str) -> dict:
        """
        Genera una respuesta usando Ollama y extrae el JSON.

        Args:
            prompt: Prompt completo para el modelo

        Returns:
            Diccionario con los datos del gasto (monto, categoria, fecha)

        Raises:
            OllamaConnectionError: Si no se puede conectar con Ollama
            OllamaInvalidJSONError: Si no se puede parsear el JSON
        """
        try:
            logger.debug(f"Enviando prompt a Ollama (modelo: {self.model})")

            # Llamar a Ollama usando la librería oficial
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={'timeout': self.timeout}
            )

            # response['response'] contiene el texto generado
            response_text = response['response']
            logger.debug(f"Respuesta de Ollama: {response_text}")

            # Extraer y parsear JSON
            return self._extract_json_from_text(response_text)

        except Exception as e:
            logger.error(f"Error al conectar con Ollama: {e}")
            raise OllamaConnectionError(f"No se pudo conectar con Ollama: {e}")

    def _extract_json_from_text(self, text: str) -> dict:
        """
        Extrae JSON de un texto, incluso si viene rodeado de texto adicional.

        El modelo puede devolver:
        - Solo JSON: {"monto": 100, ...}
        - JSON con texto: "Aquí está: {"monto": 100, ...}"
        - JSON con saltos de línea

        Args:
            text: Texto que contiene JSON

        Returns:
            Diccionario parseado del JSON

        Raises:
            OllamaInvalidJSONError: Si no se encuentra o no se puede parsear el JSON
        """
        # Buscar patrón de JSON en el texto
        json_match = re.search(r'\{.*\}', text, re.DOTALL)

        if not json_match:
            logger.error(f"No se encontró JSON en la respuesta: {text}")
            raise OllamaInvalidJSONError("No se encontró JSON en la respuesta del modelo")

        json_str = json_match.group()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON: {e}")
            raise OllamaInvalidJSONError(f"JSON inválido: {e}")
