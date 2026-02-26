"""Constructor de prompts para Ollama con contexto temporal."""
from datetime import datetime


def build_prompt(user_message: str, categories: list) -> str:
    """
    Construye el prompt completo con fecha actual y mensaje del usuario.

    IMPORTANTE: Inyecta la fecha actual para que el modelo pueda interpretar
    referencias temporales como "ayer", "anteayer", "la semana pasada", etc.

    Args:
        user_message: Mensaje del usuario sobre el gasto
        categories: Lista de categorías válidas

    Returns:
        Prompt completo listo para enviar a Ollama
    """
    today = datetime.now().strftime("%Y-%m-%d")
    categories_str = '", "'.join(categories)

    system_prompt = f"""Eres un asistente contable.
HOY ES {today}.

Tu única función es recibir frases de gastos y responder EXCLUSIVAMENTE con un objeto JSON.
Formato: {{"monto": <float>, "categoria": <string>, "fecha": <string formato Y-m-d>}}

Si no hay fecha explícita, asume hoy.
Las categorías posibles son: "{categories_str}".

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional."""

    return f"{system_prompt}\n\nUsuario: {user_message}\n\nAsistente:"
