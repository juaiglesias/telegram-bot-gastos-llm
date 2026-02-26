"""Excepciones customizadas del proyecto."""


class OllamaConnectionError(Exception):
    """Error de conexión con Ollama."""
    pass


class OllamaInvalidJSONError(Exception):
    """El JSON devuelto por Ollama es inválido o no se encontró."""
    pass


class InvalidCategoryError(Exception):
    """La categoría no está en la lista de categorías válidas."""
    pass


class InvalidExpenseDataError(Exception):
    """Los datos del gasto son inválidos o incompletos."""
    pass


class GoogleSheetsError(Exception):
    """Error al interactuar con la API de Google Sheets."""
    pass
