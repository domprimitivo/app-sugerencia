"""
Flujo de KPIs — Cucurucho → 7 KPIs holográficos → Lazo de control.

Piezas del flujo (100% local, soberano):
  cliente (client_id) ── indica ──► dominio (domain_ref)
        │                              │
        │                              └── define las 7 variables/polos + umbrales
        ▼
  cucurucho / embudo  ── recibe archivos de operación (cosecha, pagos, ...) ──►
        AG3 (limpiador) + AG5 (ingeniero de features) SEPARAN los 7 KPIs
        holográficos + features de control ──► ENTRADA LIMPIA para el lazo.

Dominios empresariales (6) = únicos válidos. El palenque de mezcal
(dom_fermentacion_lotes_v1) es SOLO demostración del flujo.
"""

import json
import csv
import io
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from lazo_generico import DOMINIO_CVD, lazo_asesoria, lazo_agencia

BASE = Path(__file__).resolve().parent
FLUJO_DIR = BASE / "flujo"

# Los 6 dominios empresariales válidos (únicos productivos)
DOMINIOS_EMPRESARIALES = [
    {"domain_id": "dom_restaurante_v1", "descriptor": "Restaurante / Food Service"},
    {"domain_id": "dom_retail_v1",      "descriptor": "Retail / Punto de venta"},
    {"domain_id": "dom_hotel_v1",       "descriptor": "Hotelería"},
    {"domain_id": "dom_fabrica_v1",     "descriptor": "Manufactura / Fábrica"},
    {"domain_id": "dom_logistica_v1",   "descriptor": "Logística / Distribución"},
    {"domain_id": "dom_clinica_v1",     "descriptor": "Clínica / Salud"},
]

CUCURUCHO_REF = "cucurucho_base_v1"


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_cliente(client_id: str) -> dict:
    p = FLUJO_DIR / "clientes" / f"{client_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"Cliente no encontrado: {client_id}")
    return _load_json(p)


def cargar_dominio(domain_id: str) -> dict:
    p = FLUJO_DIR / "dominios" / f"{domain_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"Dominio no encontrado: {domain_id}")
    return _load_json(p)


def cargar_params(params_ref: str) -> dict:
    p = FLUJO_DIR / "params" / f"{params_ref}.json"
    if not p.exists():
        raise FileNotFoundError(f"Parametrización no encontrada: {params_ref}")
    return _load_json(p)


def cargar_cucurucho() -> dict:
    return _load_json(FLUJO_DIR / "cucurucho" / f"{CUCURUCHO_REF}.json")


def listar_clientes() -> List[dict]:
    d = FLUJO_DIR / "clientes"
    return [_load_json(f) for f in sorted(d.glob("*.json"))]


def listar_dominios() -> dict:
    """6 empresariales (válidos) + demo (palenque) si existe."""
    demo = []
    dd = FLUJO_DIR / "dominios"
    for f in sorted(dd.glob("*.json")):
        cfg = _load_json(f)
        if cfg.get("es_demo"):
            demo.append({"domain_id": cfg["domain_id"], "descriptor": cfg["descriptor"], "es_demo": True})
    return {"empresariales": DOMINIOS_EMPRESARIALES, "demostracion": demo}


# ─── AG3 limpiador + AG5 ingeniero de features: separar señales de operación ──
def _categoria_de(nombre: str, categorias: dict) -> Optional[str]:
    n = nombre.lower()
    for cat, cfg in categorias.items():
        if any(k in n for k in cfg.get("keywords", [])):
            return cat
    return None


def _agg_numericos(datos: bytes) -> Dict[str, float]:
    """Promedia columnas numéricas de un CSV/JSON (limpieza AG3)."""
    try:
        texto = datos.decode("utf-8")
    except Exception:
        return {}
    # JSON objeto
    try:
        obj = json.loads(texto)
        if isinstance(obj, dict):
            return {k: float(v) for k, v in obj.items()
                    if isinstance(v, (int, float)) and not isinstance(v, bool)}
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            acc: Dict[str, list] = {}
            for row in obj:
                for k, v in row.items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        acc.setdefault(k, []).append(float(v))
            return {k: float(np.mean(v)) for k, v in acc.items()}
    except Exception:
        pass
    # CSV
    try:
        reader = csv.DictReader(io.StringIO(texto))
        acc: Dict[str, list] = {}
        for row in reader:
            for k, v in row.items():
                try:
                    acc.setdefault(k, []).append(float(v))
                except (TypeError, ValueError):
                    continue
        return {k: float(np.mean(v)) for k, v in acc.items() if v}
    except Exception:
        return {}


def extraer_senales(archivos: List[dict], params: dict) -> Dict[str, Dict[str, float]]:
    """
    Parte del baseline demo y superpone lo que traigan los archivos reales
    (categoría detectada por nombre). Devuelve señales por categoría.
    """
    categorias = params.get("categorias_operacion", {})
    senales = json.loads(json.dumps(params.get("demo_operacion", {})))  # baseline demo
    for a in archivos or []:
        cat = _categoria_de(a["nombre"], categorias)
        if not cat:
            continue
        senales.setdefault(cat, {}).update(_agg_numericos(a["datos"]))
    return senales


def _norm(v: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (v - lo) / (hi - lo)))


def preparar_kpis(senales: Dict[str, Dict[str, float]], params: dict) -> Dict[str, float]:
    """AG5: separa los 7 KPIs holográficos (0-1) desde las señales de operación."""
    kpis: Dict[str, float] = {}
    for kpi, terminos in params.get("kpi_map", {}).items():
        total = 0.0
        peso_total = 0.0
        for t in terminos:
            cat, col = t["signal"].split(".", 1)
            val = senales.get(cat, {}).get(col)
            if val is None:
                continue
            lo, hi = t.get("norm", [0.0, 1.0])
            x = _norm(float(val), lo, hi)
            if t.get("invertir"):
                x = 1.0 - x
            total += t.get("peso", 1.0) * x
            peso_total += t.get("peso", 1.0)
        kpis[kpi] = round(total / peso_total, 4) if peso_total else 0.5
    return kpis


def detalle_discreto(senales: Dict[str, Dict[str, float]], params: dict) -> Dict[str, list]:
    """
    Para cada métrica geométrica, sus datos tradicionales (discretos) que la
    componen. Hace explícita la armonía dato discreto ↔ contraparte geométrica.
    """
    out: Dict[str, list] = {}
    for kpi, terminos in params.get("kpi_map", {}).items():
        discretos = []
        for t in terminos:
            cat, col = t["signal"].split(".", 1)
            val = senales.get(cat, {}).get(col)
            lo, hi = t.get("norm", [0.0, 1.0])
            norm = None if val is None else round(_norm(float(val), lo, hi), 3)
            discretos.append({"signal": t["signal"], "categoria": cat, "campo": col,
                              "valor": val, "norm": norm, "peso": t.get("peso", 1.0)})
        out[kpi] = discretos
    return out


def control_features(kpis: Dict[str, float], dominio: dict, overrides: dict) -> dict:
    """Features de control adicionales para el lazo (viabilidad, firmeza, coherencia)."""
    umb = dominio.get("umbrales_operativos", {})
    c_crit = overrides.get("c_viabilidad_critico", umb.get("c_viabilidad_critico", 1.07))
    firmeza_min = umb.get("firmeza_suelo_minima_R", 0.60)
    delta_max = umb.get("delta_max_coherencia", 0.12)

    firmeza_R = kpis.get("Retorno al Suelo", 0.5)
    c_viab = round(1.0 + 0.1 * (0.6 * kpis.get("Tensión TR", 0.5) + 0.4 * kpis.get("Ruptura de Fase", 0.5)), 3)
    delta_coh = round(float(np.std(list(kpis.values()))), 3)
    return {
        "c_viabilidad": c_viab, "c_viabilidad_critico": c_crit, "viable": c_viab < c_crit,
        "firmeza_suelo_R": round(firmeza_R, 3), "firmeza_minima_R": firmeza_min, "suelo_firme": firmeza_R >= firmeza_min,
        "delta_coherencia": delta_coh, "delta_max_coherencia": delta_max, "coherente": delta_coh <= delta_max,
    }


def agentes_activos(cucurucho: dict) -> List[dict]:
    core = cucurucho.get("agentes_core", {})
    prep = {"AG3_limpiador", "AG5_ingeniero_features"}
    return [{"id": k, "prepara_kpis": k in prep}
            for k, v in core.items() if v.get("activo")]


def ejecutar_flujo(client_id: str, archivos: List[dict], modo: str = "ASESORIA") -> dict:
    """Flujo completo: cliente → dominio → cucurucho (KPIs limpios) → lazo."""
    cliente = cargar_cliente(client_id)
    if not cliente.get("active_subscription"):
        raise PermissionError("La suscripción del cliente no está activa.")

    dominio = cargar_dominio(cliente["domain_ref"])
    params = cargar_params(dominio.get("params_ref", "palenque_fermentacion_params"))
    cucurucho = cargar_cucurucho()

    senales = extraer_senales(archivos, params)
    kpis = preparar_kpis(senales, params)                    # entrada LIMPIA para el lazo
    discretos = detalle_discreto(senales, params)            # armonía discreto ↔ geométrico
    control = control_features(kpis, dominio, cliente.get("overrides", {}))

    resultado_lazo = lazo_asesoria(kpis, DOMINIO_CVD) if modo == "ASESORIA" \
        else lazo_agencia(kpis, DOMINIO_CVD)

    return {
        "cliente": {"client_id": cliente["client_id"], "client_name": cliente["client_name"],
                    "active_subscription": cliente["active_subscription"],
                    "overrides": cliente.get("overrides", {})},
        "dominio": {"domain_id": dominio["domain_id"], "descriptor": dominio["descriptor"],
                    "es_demo": dominio.get("es_demo", False),
                    "polos": dominio["grafo_meso"]["nombres_polos"]},
        "cucurucho": {"id": cucurucho["id_config"], "agentes": agentes_activos(cucurucho)},
        "senales_operacion": senales,
        "kpis_holograficos": kpis,          # <-- lo que recibe la observación (métricas)
        "metricas_discretas": discretos,    # <-- datos tradicionales por métrica
        "features_control": control,
        "lazo": resultado_lazo,
    }
