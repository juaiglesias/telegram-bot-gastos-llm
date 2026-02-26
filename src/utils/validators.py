"""Validadores para datos de gastos."""
from datetime import datetime
from typing import Tuple


def validate_expense_data(data: dict, valid_categories: list) -> Tuple[bool, str]:
    """
    Valida los datos de un gasto.

    Args:
        data: Diccionario con monto, categoria y fecha
        valid_categories: Lista de categorías válidas

    Returns:
        Tupla (es_valido, mensaje_error)
        Si es válido: (True, "")
        Si es inválido: (False, "mensaje de error")
    """
    # Verificar campos requeridos
    required_fields = ['monto', 'categoria', 'fecha']
    for field in required_fields:
        if field not in data:
            return False, f"Campo requerido '{field}' no encontrado"

    # Validar monto
    try:
        monto = float(data['monto'])
        if monto <= 0:
            return False, "El monto debe ser mayor que 0"
    except (ValueError, TypeError):
        return False, "El monto debe ser un número válido"

    # Validar categoría
    categoria = data['categoria']
    if categoria not in valid_categories:
        return False, f"Categoría '{categoria}' no válida. Use una de: {', '.join(valid_categories)}"

    # Validar formato de fecha
    try:
        datetime.strptime(data['fecha'], '%Y-%m-%d')
    except ValueError:
        return False, "La fecha debe tener formato YYYY-MM-DD"

    return True, ""
