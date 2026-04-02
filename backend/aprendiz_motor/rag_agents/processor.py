"""
aprendiz_motor/rag_agents/processor.py
Motor RAG para dominios empresariales.
Compatible con las llamadas de server.py:
  - inicializar_rag(dominio_id)
  - procesar_expediente(expediente_id, documentos)
"""

import re
import math
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cucuruchos JSON — configuración por dominio empresarial
CUCURUCHOS_DIR = Path(__file__).parent.parent.parent  # raíz del repo

CUCURUCHO_FILES = {
    "hotel":       "cucurucho_hotel_v1.json",
    "clinica":     "cucurucho_clinica_v1.json",
    "restaurante": "cucurucho_restaurante_v1.json",
    "retail":      "cucurucho_retail_v1.json",
    "fabrica":     "cucurucho_fabrica_v1.json",
    "logistica":   "cucurucho_logistica_v1.json",
}


def _cargar_cucurucho(dominio_id: str) -> Optional[dict]:
    """Carga el cucurucho JSON del dominio si existe."""
    nombre = CUCURUCHO_FILES.get(dominio_id)
    if not nombre:
        return None
    for base in [CUCURUCHOS_DIR, Path(".")]:
        path = base / nombre
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
    return None


class RAGProcessor:
    """
    Pipeline de agentes RAG para dominios empresariales.
    Lee el cucurucho JSON del dominio para configurar umbrales y agentes.
    """

    def __init__(self, dominio_id: str):
        self.dominio_id = dominio_id
        self.cucurucho  = _cargar_cucurucho(dominio_id)
        if self.cucurucho:
            logger.info(
                f"[RAG] Cucurucho cargado: {dominio_id} · "
                f"agentes: {len(self.cucurucho.get('agentes_core', {}))}")
        else:
            logger.warning(f"[RAG] Cucurucho no encontrado: {dominio_id} · defaults")

        # Umbrales desde cucurucho o defaults
        umbrales = (self.cucurucho or {}).get("umbrales_campos", {})
        self.umbral_T  = umbrales.get("T", {}).get("alerta_suave", 0.66)
        self.umbral_R  = umbrales.get("R", {}).get("alerta_suave", 0.45)
        self.umbral_K  = umbrales.get("K", {}).get("alerta_suave", 0.40)

    def procesar_expediente(self, expediente_id: str,
                            documentos: List[Dict[str, Any]]) -> dict:
        """
        Procesa los documentos de un expediente empresarial.
        Retorna el formato que espera server.py:
          resumen, documentos_procesados, total_documentos
        Y también los campos de la Doble Hélice para el panel.
        """
        texto_total = " ".join(
            d.get("contenido", "") for d in documentos
        )
        palabras = re.findall(r"\b\w+\b", texto_total.lower())
        total    = max(len(palabras), 1)

        # Extraer features
        t, c, p = self._extraer_features(palabras, total)

        # Calcular campos prudenciales
        tension    = round(math.sqrt((t**2 + p**2) / 2), 4)
        resilencia = round(max(0.0, c - max(0.0, tension-0.65)*0.5), 4)
        mm         = (t + c + p) / 3
        coherencia = round(1.0 - math.sqrt(
            ((t-mm)**2+(c-mm)**2+(p-mm)**2)/3), 4)
        indice_telos = round(coherencia * resilencia, 4)

        # Determinar fase según umbrales del cucurucho
        if tension >= self.umbral_T and resilencia < self.umbral_R:
            fase_nombre = "Tensión Operativa"
            fase_num    = 3
        elif tension >= self.umbral_T:
            fase_nombre = "Resolución en Curso"
            fase_num    = 4
        elif coherencia >= 0.75 and tension < 0.45:
            fase_nombre = "Estabilidad"
            fase_num    = 1
        else:
            fase_nombre = "Equilibrio"
            fase_num    = 2

        # Acción recomendada desde geodésicas del cucurucho
        accion = self._recomendar_accion(tension, resilencia, coherencia)

        # Resumen narrativo
        resumen = self._generar_resumen(
            tension, resilencia, coherencia, indice_telos,
            fase_nombre, accion, len(documentos))

        docs_procesados = [
            {
                "id":      d.get("id", f"doc_{i}"),
                "nombre":  d.get("nombre", f"documento_{i}"),
                "status":  "procesado",
                "palabras": len(re.findall(r"\b\w+\b",
                                           d.get("contenido", ""))),
            }
            for i, d in enumerate(documentos)
        ]

        return {
            "expediente_id":        expediente_id,
            "resumen":              resumen,
            "documentos_procesados": docs_procesados,
            "total_documentos":     len(documentos),
            # Campos extendidos para el panel Doble Hélice
            "heads": {"trigo": t, "cobre": c, "petroleo": p},
            "estados": {
                "campos":       round(mm, 4),
                "tension":      tension,
                "coherencia":   coherencia,
                "resiliencia":  resilencia,
                "indice_telos": indice_telos,
            },
            "fase":            {"numero": fase_num, "nombre": fase_nombre},
            "accion_sugerida": accion,
            "dominio":         self.dominio_id,
        }

    def _extraer_features(self, palabras, total):
        """Keywords específicos por dominio desde el cucurucho o defaults."""
        DEFAULTS = {
            "trigo":    ["urgente","queja","falla","critico","alerta",
                         "cancelacion","incidente","reclamo","emergencia"],
            "cobre":    ["disponible","capacidad","personal","inventario",
                         "recurso","equipo","servicio","proveedor","reserva"],
            "petroleo": ["proceso","protocolo","estandar","flujo","operacion",
                         "servicio","seguimiento","cronograma","rutina"],
        }

        def sigmoid(n):
            freq = n / total * 100
            return round(max(0.05, min(0.95,
                1/(1+math.exp(-(freq-2)*0.8)))), 4)

        conteos = {k: sum(1 for p in palabras if p in v)
                   for k, v in DEFAULTS.items()}
        return (sigmoid(conteos["trigo"]),
                sigmoid(conteos["cobre"]),
                sigmoid(conteos["petroleo"]))

    def _recomendar_accion(self, tension, resilencia, coherencia) -> str:
        """Usa geodésicas del cucurucho para recomendar acción."""
        if not self.cucurucho:
            return "revisar_operacion"

        geodesicas = (self.cucurucho.get("geodesicas", {})
                                    .get("catalogo", []))
        habilitadas = set(
            self.cucurucho.get("geodesicas", {})
                          .get("habilitadas_por_defecto", []))

        # Seleccionar geodésica más adecuada según estado
        if tension >= self.umbral_T and resilencia < self.umbral_R:
            candidata = "GM2_refuerzo_resiliencia"
        elif coherencia < self.umbral_K:
            candidata = "GM3_reduccion_incoherencias"
        elif tension >= self.umbral_T:
            candidata = "GM1_estabilizacion_basica"
        else:
            candidata = "GM4_reenfoque_telos"

        if candidata in habilitadas:
            for g in geodesicas:
                if g["id"] == candidata:
                    return g["id"].replace("_", " ").lower()

        return "monitorear_operacion"

    def _generar_resumen(self, tension, resilencia, coherencia,
                         telos, fase_nombre, accion,
                         n_docs) -> str:
        cucurucho_id = (self.cucurucho or {}).get("id_config", self.dominio_id)
        return (
            f"[{cucurucho_id}] {n_docs} documento(s) procesado(s). "
            f"Fase: {fase_nombre}. "
            f"Tensión: {tension:.2f} · Resilencia: {resilencia:.2f} · "
            f"Coherencia: {coherencia:.2f} · Índice Telos: {telos:.2f}. "
            f"Acción recomendada: {accion.replace('_',' ')}."
        )


# ─────────────────────────────────────────────────────────────────
# API PÚBLICA — compatible con server.py
# ─────────────────────────────────────────────────────────────────

_procesador_instancia: Optional[RAGProcessor] = None


def inicializar_rag(dominio_id: str) -> bool:
    global _procesador_instancia
    try:
        _procesador_instancia = RAGProcessor(dominio_id)
        return True
    except Exception as e:
        logger.error(f"[RAG] Error inicializando: {e}")
        return False


def procesar_expediente(expediente_id: str,
                        documentos: List[Dict[str, Any]]) -> dict:
    global _procesador_instancia
    if _procesador_instancia is None:
        raise RuntimeError(
            "RAG no inicializado. Llamar inicializar_rag() primero.")
    return _procesador_instancia.procesar_expediente(expediente_id, documentos)
