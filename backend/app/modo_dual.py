"""
MILEFORUM · Gestor de Modo Dual
Lee config_arranque.json y decide si usar la API externa
o el motor Python local.

Opción A (modo=api):   todo va a api.mileforum.ia
Opción B (modo=local): todo corre en Python local
"""

import json
import httpx
from pathlib import Path
from typing import Optional
from .core.logger import logger

CONFIG_PATH = Path("app/config_arranque.json")

# ── Leer configuración ────────────────────────────────────────────
def leer_config_arranque() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    # Fallback: modo local
    return {"modo": "local", "dominio_activo": "hotel"}


# ─────────────────────────────────────────────────────────────────
# EJECUTOR DUAL
# ─────────────────────────────────────────────────────────────────
async def ejecutar_episodio_dual(
    expediente_id: str,
    dominio: str,
    texto: str,
    tipo_consulta: str = "general",
    features_externos: Optional[dict] = None,
) -> dict:
    """
    Punto de entrada único para el procesamiento.
    Detecta el modo y enruta al motor correcto.
    """
    cfg  = leer_config_arranque()
    modo = cfg.get("modo", "local")

    if modo == "api":
        return await _ejecutar_via_api(
            cfg, expediente_id, dominio, texto,
            tipo_consulta, features_externos)
    else:
        return _ejecutar_local(
            cfg, expediente_id, dominio, texto,
            tipo_consulta, features_externos)


# ─────────────────────────────────────────────────────────────────
# OPCIÓN A — API externa
# ─────────────────────────────────────────────────────────────────
async def _ejecutar_via_api(cfg, expediente_id, dominio, texto,
                            tipo, features_ext) -> dict:
    """Llama a api.mileforum.ia y devuelve el resultado."""
    url     = cfg.get("api_externa", {}).get("url", "https://api.mileforum.ia")
    timeout = cfg.get("api_externa", {}).get("timeout", 30)

    payload = {
        "expediente_id": expediente_id,
        "dominio":       dominio,
        "tipo_consulta": tipo,
        "trigo":    features_ext.get("trigo")    if features_ext else None,
        "cobre":    features_ext.get("cobre")    if features_ext else None,
        "petroleo": features_ext.get("petroleo") if features_ext else None,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{url}/navigator/ejecutar",
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            snapshot = data.get("snapshot", data)
            snapshot["modo_ejecucion"] = "api_externa"
            logger.info(f"[DUAL·API] Respuesta recibida para {expediente_id}")
            return snapshot

    except Exception as e:
        logger.warning(f"[DUAL·API] Error conectando a API: {e} · fallback local")
        # Si la API falla, cae automáticamente al motor local
        return _ejecutar_local(cfg, expediente_id, dominio, texto, tipo, features_ext)


# ─────────────────────────────────────────────────────────────────
# OPCIÓN B — Motor local Python
# ─────────────────────────────────────────────────────────────────
def _ejecutar_local(cfg, expediente_id, dominio, texto,
                    tipo, features_ext) -> dict:
    """Corre el motor Python directamente en la máquina."""
    from datetime import datetime

    # Determinar qué motor usar según el dominio
    motor_mapa = cfg.get("motor_por_dominio", {})
    tipo_motor = motor_mapa.get(dominio, "rag")

    if tipo_motor == "rag":
        from .motor.rag_processor import ejecutar_rag
        resultado = ejecutar_rag(
            dominio=dominio,
            texto=texto,
            features_externos=features_ext,
            tipo=tipo,
        )
    else:
        from .motor.notebook_engine import ejecutar_episodio
        resultado = ejecutar_episodio(
            dominio_id=dominio,
            texto=texto,
            tipo=tipo,
            features_externos=features_ext,
        )

    # Construir snapshot estándar
    run_id = f"run_{expediente_id}_{resultado['fase']['numero']}"
    snapshot = {
        "run_id":          run_id,
        "expediente_id":   expediente_id,
        "dominio":         dominio,
        "timestamp":       datetime.utcnow().isoformat(),
        "inputs":          resultado.get("features", {}),
        "helice":          resultado.get("helice", {}),
        "estados":         resultado.get("estados", {}),
        "fase":            resultado.get("fase", {}),
        "accion_sugerida": resultado.get("accion_sugerida", ""),
        "sugerencia_tcl":  resultado.get("sugerencia_tcl", ""),
        "resumen":         resultado.get("resumen", ""),
        "kpis":            resultado.get("kpis", {}),
        "confianza":       resultado.get("confianza", 0.75),
        "modo_motor":      resultado.get("modo_motor", tipo_motor),
        "modo_ejecucion":  "local",
        "pipeline_log":    resultado.get("pipeline_log", []),
    }

    logger.info(
        f"[DUAL·LOCAL] {dominio} · Φ{snapshot['fase'].get('numero')} · "
        f"motor={tipo_motor} · acción={snapshot['accion_sugerida']}"
    )
    return snapshot


# ─────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────
def obtener_modo_actual() -> str:
    return leer_config_arranque().get("modo", "local")

def cambiar_modo(nuevo_modo: str):
    """Cambia el modo en config_arranque.json."""
    if nuevo_modo not in ("api", "local"):
        raise ValueError("modo debe ser 'api' o 'local'")
    cfg = leer_config_arranque()
    cfg["modo"] = nuevo_modo
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    logger.info(f"[DUAL] Modo cambiado a: {nuevo_modo}")
