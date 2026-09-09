"""
Asistente Aprendiz (empresas) — etiquetado silencioso al final del embudo RAG.

El aprendiz NO es explícito: no muestra nombres, cabezas ni modelo en el
frontend. Sólo *sugiere* una acción para lo ingestado al cucurucho (archivos
o escritura libre) y espera que el humano confirme o corrija.

Cada decisión se registra por separado, con timestamp, en dos lugares que
DEBEN COINCIDIR con lo que consumen los notebooks:

  1. Tabla SQLite `aprendiz_decisiones`  (consulta rápida desde la app)
  2. Archivo `aprendiz_data/{dominio}_learning_log.jsonl`  (formato EXACTO
     del Aprendiz Episódico / notebook de ajuste bimestral)

Schema del evento del learning_log (idéntico a los notebooks):
  {
    "timestamp": "YYYY-MM-DDTHH:MM:SS+00:00",
    "domain": "<dominio>",
    "node_id": "<expediente_id>",
    "backbone_inference": {
        "phase": "<fase>",
        "phase_probs": {...},
        "clarity": {"ok": bool, "pmax": f, "gap": f, "entropy": f},
        "R_score": f
    },
    "soft_context": {"soft_tags": [...]},
    "action_execution": {
        "user_accepted_suggestion": bool,   # confirmar=True / corregir=False
        "action_id": "<final>",
        "action_label": "<final>",
        "action_known": bool                # corregir a algo nuevo => False
    },
    "learning_event": {...}                  # presente sólo en corrección
  }
"""

import re
import math
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


FASES_EMPRESA = ["Estabilidad", "Equilibrio", "Tensión Operativa", "Resolución en Curso"]
FASES_UNIPERSONAL = ["Estabilidad", "Tensión", "Ruptura", "Invariante"]


def slugify(texto: Optional[str]) -> str:
    """Convierte una etiqueta libre en un action_id estable."""
    if not texto:
        return "sin_accion"
    t = texto.strip().lower()
    t = re.sub(r"[áàä]", "a", t)
    t = re.sub(r"[éèë]", "e", t)
    t = re.sub(r"[íìï]", "i", t)
    t = re.sub(r"[óòö]", "o", t)
    t = re.sub(r"[úùü]", "u", t)
    t = re.sub(r"ñ", "n", t)
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t or "sin_accion"


def _phase_probs(fase_nombre: str, confianza: float, fases: List[str] = None) -> Dict[str, float]:
    """Reparte la masa de probabilidad con un pico en la fase detectada."""
    fases = fases or FASES_EMPRESA
    pico = max(0.4, min(0.95, confianza))
    resto = (1.0 - pico) / max(1, len(fases) - 1)
    probs = {f: round(resto, 4) for f in fases}
    if fase_nombre not in probs:
        probs[fase_nombre] = 0.0
    probs[fase_nombre] = round(pico, 4)
    return probs


def _clarity(probs: Dict[str, float]) -> Dict[str, Any]:
    vals = sorted(probs.values(), reverse=True)
    pmax = vals[0] if vals else 0.0
    gap = (vals[0] - vals[1]) if len(vals) > 1 else pmax
    entropy = -sum(p * math.log(p + 1e-9) for p in probs.values() if p > 0)
    return {
        "ok": bool(pmax >= 0.5 and gap >= 0.15),
        "pmax": round(pmax, 4),
        "gap": round(gap, 4),
        "entropy": round(entropy, 4),
    }


def _soft_tags(estados: Dict[str, Any]) -> List[str]:
    tags = []
    if estados.get("tension", 0) >= 0.66:
        tags.append("tension_alta")
    if estados.get("resiliencia", 1) < 0.45:
        tags.append("resiliencia_baja")
    if estados.get("coherencia", 1) < 0.5:
        tags.append("coherencia_baja")
    if estados.get("indice_telos", 0) >= 0.6:
        tags.append("telos_firme")
    return tags or ["nominal"]


def construir_sugerencia(dominio: str, node_id: str, rag_resultado: Dict[str, Any]) -> Dict[str, Any]:
    """
    A partir de la salida de los agentes RAG construye la sugerencia silenciosa
    del asistente. Devuelve el contexto que el frontend guarda y devuelve luego
    al confirmar/corregir (para que el evento registrado sea consistente).
    """
    fase = rag_resultado.get("fase", {}) or {}
    estados = rag_resultado.get("estados", {}) or {}
    fase_nombre = fase.get("nombre", "Equilibrio")

    telos = estados.get("indice_telos", 0.5)
    coher = estados.get("coherencia", 0.5)
    confianza = round(max(0.4, min(0.95, (telos + coher) / 2 + 0.15)), 3)

    accion_label = rag_resultado.get("accion_sugerida") or "revisar operacion"
    probs = _phase_probs(fase_nombre, confianza)

    return {
        "node_id": node_id,
        "dominio": dominio,
        "suggested_action_id": slugify(accion_label),
        "suggested_action_label": accion_label,
        "phase": fase_nombre,
        "phase_probs": probs,
        "clarity": _clarity(probs),
        "R_score": round(float(estados.get("indice_telos", 0.5)), 4),
        "soft_tags": _soft_tags(estados),
        "confianza": confianza,
    }


def construir_sugerencia_unipersonal(dominio: str, node_id: str,
                                     resultado: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construye la sugerencia (mismo formato que empresas) a partir del resultado
    del episodio del aprendiz unipersonal. Permite alimentar el mismo registro
    de decisiones y el ajuste automático, sin cambiar la UX unipersonal.
    """
    estados = resultado.get("estados", {}) or {}
    fase = resultado.get("fase_backbone", {}) or {}
    fase_nombre = fase.get("label", "Estabilidad")
    confianza = round(float(resultado.get("confianza", 0.6)), 3)
    accion_label = resultado.get("accion_sugerida") or "revisar caso"
    probs = _phase_probs(fase_nombre, confianza, FASES_UNIPERSONAL)

    return {
        "node_id": node_id,
        "dominio": dominio,
        "suggested_action_id": slugify(accion_label),
        "suggested_action_label": accion_label,
        "phase": fase_nombre,
        "phase_probs": probs,
        "clarity": _clarity(probs),
        "R_score": round(float(estados.get("indice_telos", 0.5)), 4),
        "soft_tags": _soft_tags(estados),
        "confianza": confianza,
    }


def construir_evento(sugerencia: Dict[str, Any], user_accepted: bool,
                     final_action_label: str) -> Dict[str, Any]:
    """Arma el evento del learning_log con el schema exacto de los notebooks."""
    final_label = final_action_label or sugerencia["suggested_action_label"]
    final_id = slugify(final_label)
    # action_known: True si aceptó la sugerencia; False si corrigió a algo distinto
    action_known = bool(user_accepted and final_id == sugerencia["suggested_action_id"])

    evento = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "domain": sugerencia["dominio"],
        "node_id": sugerencia["node_id"],
        "backbone_inference": {
            "phase": sugerencia["phase"],
            "phase_probs": sugerencia["phase_probs"],
            "clarity": sugerencia["clarity"],
            "R_score": sugerencia["R_score"],
        },
        "soft_context": {"soft_tags": sugerencia.get("soft_tags", [])},
        "action_execution": {
            "user_accepted_suggestion": bool(user_accepted),
            "action_id": final_id,
            "action_label": final_label,
            "action_known": action_known,
        },
    }
    if not user_accepted:
        evento["learning_event"] = {
            "type": "correction",
            "from_action_id": sugerencia["suggested_action_id"],
            "from_action_label": sugerencia["suggested_action_label"],
            "to_action_id": final_id,
            "to_action_label": final_label,
        }
    return evento


def escribir_learning_log(aprendiz_dir: Path, dominio: str, evento: Dict[str, Any]):
    """Añade el evento (una línea JSON) al learning_log.jsonl del dominio."""
    ruta = aprendiz_dir / f"{dominio}_learning_log.jsonl"
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return ruta


def actualizar_action_dictionary(aprendiz_dir: Path, dominio: str,
                                 phase: str, action_id: str, action_label: str):
    """Mantiene {dominio}_action_dictionary_state.json con las acciones vistas por fase."""
    ruta = aprendiz_dir / f"{dominio}_action_dictionary_state.json"
    if ruta.exists():
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    else:
        data = {}
    abp = data.setdefault("actions_by_phase", {})
    lst = abp.setdefault(phase, [])
    if not any(isinstance(a, dict) and a.get("action_id") == action_id for a in lst):
        lst.append({"action_id": action_id, "label": action_label})
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
