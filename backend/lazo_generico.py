"""
Lazo Generico — Navegacion Prudencial (App Local).

Reemplaza el antiguo "reporte de claridad" como paso separado. La informacion
que vivia en ese reporte ahora es el resultado natural del lazo generico, en
sus dos modos:

  - ASESORIA: lazo sin hermanos + Cenit humano (el humano autoriza la accion).
  - AGENCIA:  lazo completo (Corto, Mediano, Largo) + Cenit critico
              (el sistema ejecuta; solo llama al Cenit en casos criticos).

100% soberano: Python puro, sin dependencias de terceros. La pantalla de
claridad (frontend) solo muestra lo que este lazo produce.
"""

from dataclasses import dataclass
from typing import Dict, List


# ──────────────────────────────────────────────────────────────
# 1. CONFIGURACION DEL DOMINIO (desde el cuestionario)
# ──────────────────────────────────────────────────────────────
@dataclass
class DominioConfig:
    nombre: str
    kpis_nombres: List[str]
    kpis_umbrales: Dict[str, Dict[str, object]]
    variables_controlables: List[str]
    variables_opacas: List[str]
    geodesicas: Dict[str, Dict[str, str]]


# ── Dominio CVD (ejemplo) ──────────────────────────────────────
DOMINIO_CVD = DominioConfig(
    nombre="CVD Grafeno",
    kpis_nombres=["Permeabilidad", "Tensión TR", "Sutura", "Retorno al Suelo",
                  "Estancamiento", "Ruptura de Fase", "Resonancia"],
    kpis_umbrales={
        "Permeabilidad": {"verde": (0.30, 0.70), "rojo": 0.55},
        "Tensión TR": {"verde": (0.00, 0.40), "rojo": 0.55},
        "Sutura": {"verde": (0.00, 0.50), "rojo": 0.65},
        "Retorno al Suelo": {"verde": (0.50, 1.00), "rojo": 0.35},
        "Estancamiento": {"verde": (0.00, 0.40), "rojo": 0.60},
        "Ruptura de Fase": {"verde": (0.00, 0.40), "rojo": 0.60},
        "Resonancia": {"verde": (0.20, 0.60), "rojo": 0.70},
    },
    variables_controlables=["T_sub", "F_CH4", "F_H2", "P_tot"],
    variables_opacas=["nucleacion_propensity", "etch_strength"],
    geodesicas={
        "gamma_0": {"nombre": "Mantener vector de estado nominal", "condicion": "Todos los KPIs en verde"},
        "gamma_1": {"nombre": "Flexibilización: Ajustar flujo CH4/H2", "condicion": "Permeabilidad < 0.30"},
        "gamma_2": {"nombre": "Amortiguación: Reducir carga operativa", "condicion": "Tensión TR > 0.55"},
        "gamma_3": {"nombre": "Sincronización: Estabilizar T_sub", "condicion": "Ruptura de Fase > 0.40"},
        "gamma_4": {"nombre": "Desacoplamiento: Revisar políticas", "condicion": "Autoengaño detectado"},
    }
)


def _varianza(valores: List[float]) -> float:
    """Varianza poblacional (soberana, sin numpy)."""
    n = len(valores)
    if n == 0:
        return 0.0
    media = sum(valores) / n
    return sum((v - media) ** 2 for v in valores) / n


# ──────────────────────────────────────────────────────────────
# 2. FUNCIONES DE EVALUACION DE KPIs
# ──────────────────────────────────────────────────────────────
def evaluar_kpis(kpis: Dict[str, float], dominio: DominioConfig) -> Dict[str, Dict]:
    """
    Evalua los KPIs contra los umbrales del dominio.
    Retorna: {nombre_kpi: {"valor": float, "estado": "VERDE/AMARILLO/ROJO", "color": "🟢/🟡/🔴"}}
    """
    resultado = {}
    for nombre, valor in kpis.items():
        umbrales = dominio.kpis_umbrales.get(nombre, {})
        verde_min, verde_max = umbrales.get("verde", (0.0, 1.0))
        rojo = umbrales.get("rojo", 0.5)

        if verde_min <= valor <= verde_max:
            estado = "VERDE"
            color = "🟢"
        elif valor > rojo or valor < verde_min:
            estado = "ROJO"
            color = "🔴"
        else:
            estado = "AMARILLO"
            color = "🟡"

        resultado[nombre] = {"valor": valor, "estado": estado, "color": color}

    return resultado


def detectar_autoengano(kpis_evaluados: Dict[str, Dict]) -> bool:
    """
    Detecta autoengaño: KPIs estructurales en rojo, KPI 7 (Resonancia) en verde.
    """
    estructurales = ["Permeabilidad", "Tensión TR", "Sutura", "Retorno al Suelo",
                     "Estancamiento", "Ruptura de Fase"]
    resonancia = kpis_evaluados.get("Resonancia", {})

    estructurales_rojos = all(kpis_evaluados.get(k, {}).get("estado") == "ROJO" for k in estructurales)
    resonancia_verde = resonancia.get("estado") == "VERDE"

    return estructurales_rojos and resonancia_verde


def sugerir_geodesica(kpis_evaluados: Dict[str, Dict], autoengano: bool, dominio: DominioConfig) -> Dict:
    """
    Sugiere una geodésica basada en los KPIs y autoengaño.
    """
    if autoengano:
        return dominio.geodesicas["gamma_4"]

    # Buscar el primer KPI en rojo
    for nombre, ev in kpis_evaluados.items():
        if ev["estado"] == "ROJO":
            # Mapeo simple: Permeabilidad → γ₁, Tensión TR → γ₂, Ruptura → γ₃
            mapeo = {
                "Permeabilidad": "gamma_1",
                "Tensión TR": "gamma_2",
                "Ruptura de Fase": "gamma_3",
                "Sutura": "gamma_1",
                "Estancamiento": "gamma_2",
                "Retorno al Suelo": "gamma_0",
            }
            key = mapeo.get(nombre, "gamma_0")
            return dominio.geodesicas.get(key, dominio.geodesicas["gamma_0"])

    return dominio.geodesicas["gamma_0"]


# ──────────────────────────────────────────────────────────────
# 3. LAZO GENERICO (ASESORIA) — Sin Hermanos
# ──────────────────────────────────────────────────────────────
def lazo_asesoria(kpis: Dict[str, float], dominio: DominioConfig) -> Dict:
    """
    Lazo de asesoría: evaluar KPIs, detectar autoengaño, sugerir geodésica.
    El humano autoriza la acción.
    """
    kpis_evaluados = evaluar_kpis(kpis, dominio)
    autoengano = detectar_autoengano(kpis_evaluados)
    geodesica = sugerir_geodesica(kpis_evaluados, autoengano, dominio)

    # Calcular estado general
    estados = [e["estado"] for e in kpis_evaluados.values()]
    if autoengano:
        estado_general = "AUTOENGAÑO"
    elif any(e == "ROJO" for e in estados):
        estado_general = "TENSION"
    elif all(e == "VERDE" for e in estados):
        estado_general = "NOMINAL"
    else:
        estado_general = "MONITOREO"

    return {
        "modo": "ASESORIA",
        "kpis": kpis_evaluados,
        "autoengano": autoengano,
        "estado_general": estado_general,
        "geodesica_sugerida": geodesica,
        "requiere_autorizacion": True,
    }


# ──────────────────────────────────────────────────────────────
# 4. LAZO COMPLETO (AGENCIA) — Con Hermanos
# ──────────────────────────────────────────────────────────────
def lazo_agencia(kpis: Dict[str, float], dominio: DominioConfig) -> Dict:
    """
    Lazo de agencia: Corto + Mediano + Largo.
    El sistema ejecuta la acción; solo llama al Cénit en casos críticos.
    """
    # ── Hermano Corto: Firmeza del suelo ─────────────────────
    valores = list(kpis.values())
    varianza = _varianza(valores)
    firmeza = max(0.0, min(1.0, 1.0 - varianza * 2))

    if firmeza >= 0.75:
        corto = {"estado": "FIRME", "color": "🟢"}
    elif firmeza >= 0.50:
        corto = {"estado": "TRANSICION", "color": "🟡"}
    else:
        corto = {"estado": "INESTABLE", "color": "🔴"}

    # ── Hermano Mediano: Condición de pegado ─────────────────
    kpis_evaluados = evaluar_kpis(kpis, dominio)
    tension = kpis_evaluados.get("Tensión TR", {}).get("valor", 0.5)
    sutura = kpis_evaluados.get("Sutura", {}).get("valor", 0.5)
    ruptura = kpis_evaluados.get("Ruptura de Fase", {}).get("valor", 0.5)

    fallo_pegado = (tension > 0.55) and (sutura > 0.45) and (ruptura > 0.40)
    mediano = {"estado": "FALLO" if fallo_pegado else "OK", "color": "🔴" if fallo_pegado else "🟢"}

    # ── Hermano Largo: Re-planificación ──────────────────────
    autoengano = detectar_autoengano(kpis_evaluados)
    requiere_cenit = autoengano or fallo_pegado

    if requiere_cenit:
        largo = {"estado": "ACTIVO", "color": "🟣"}
        geodesica = sugerir_geodesica(kpis_evaluados, autoengano, dominio)
    else:
        largo = {"estado": "INACTIVO", "color": "⚪"}
        geodesica = dominio.geodesicas["gamma_0"]

    # ── Estado general ──────────────────────────────────────
    if autoengano:
        estado_general = "AUTOENGAÑO"
    elif fallo_pegado:
        estado_general = "TENSION"
    elif corto["estado"] == "INESTABLE":
        estado_general = "FRACTURA"
    else:
        estado_general = "NOMINAL"

    return {
        "modo": "AGENCIA",
        "kpis": kpis_evaluados,
        "hermano_corto": corto,
        "hermano_mediano": mediano,
        "hermano_largo": largo,
        "firmeza": firmeza,
        "autoengano": autoengano,
        "fallo_pegado": fallo_pegado,
        "estado_general": estado_general,
        "geodesica_sugerida": geodesica,
        "requiere_cenit": requiere_cenit,
        "ejecutar_autonomamente": not requiere_cenit,
    }


# ──────────────────────────────────────────────────────────────
# 5. SERIALIZACION DEL DOMINIO PARA LA PANTALLA DE CLARIDAD
# ──────────────────────────────────────────────────────────────
def dominio_serializable(dominio: DominioConfig) -> Dict:
    """Config del dominio lista para JSON (tuplas verde → listas)."""
    umbrales = {}
    for nombre, u in dominio.kpis_umbrales.items():
        verde = u.get("verde", (0.0, 1.0))
        umbrales[nombre] = {"verde": [verde[0], verde[1]], "rojo": u.get("rojo", 0.5)}
    return {
        "nombre": dominio.nombre,
        "kpis_nombres": dominio.kpis_nombres,
        "kpis_umbrales": umbrales,
        "variables_controlables": dominio.variables_controlables,
        "variables_opacas": dominio.variables_opacas,
        "geodesicas": dominio.geodesicas,
    }
