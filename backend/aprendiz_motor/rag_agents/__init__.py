"""
aprendiz_motor/rag_agents/__init__.py
Exporta la API pública que server.py llama:
  from aprendiz_motor.rag_agents import inicializar_rag
  from aprendiz_motor.rag_agents import procesar_expediente as rag_procesar
"""
from .processor import inicializar_rag, procesar_expediente

__all__ = ["inicializar_rag", "procesar_expediente"]
