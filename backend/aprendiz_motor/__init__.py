"""
aprendiz_motor/__init__.py
Exporta la API pública que server.py llama directamente.
Compatible 100% con el server.py existente.
"""
from .notebook_engine import (
    inicializar_motor,
    ejecutar_episodio,
    obtener_estado_motor,
)

__all__ = ["inicializar_motor", "ejecutar_episodio", "obtener_estado_motor"]
