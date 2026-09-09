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
        "gamma_0": {"nombre": "Mantener la operación en régimen nominal", "condicion": "Todos los indicadores en verde"},
        "gamma_1": {"nombre": "Flexibilizar: ajustar el flujo insuficiente", "condicion": "Indicador de flujo por debajo del umbral"},
        "gamma_2": {"nombre": "Amortiguar: reducir la sobrecarga", "condicion": "Indicador de carga por encima del umbral"},
        "gamma_3": {"nombre": "Sincronizar: estabilizar el proceso", "condicion": "Proceso inestable (indicador de estabilidad fuera de rango)"},
        "gamma_4": {"nombre": "Desacoplar: revisar las políticas", "condicion": "Patrón de autoengaño"},
    }
)


# ──────────────────────────────────────────────────────────────
# 1b. TRAYECTORIAS (GEODESICAS) POR DOMINIO
# El semáforo (KPIs y umbrales) es IGUAL para todos; sólo cambia el
# lenguaje natural de las trayectorias para que sean claras en cada dominio.
# ──────────────────────────────────────────────────────────────
_CONDICIONES = {
    "gamma_0": "Todos los indicadores en verde",
    "gamma_1": "Indicador de flujo por debajo del umbral",
    "gamma_2": "Indicador de carga por encima del umbral",
    "gamma_3": "Proceso inestable (indicador de estabilidad fuera de rango)",
    "gamma_4": "Patrón de autoengaño (indicadores estructurales en rojo con señal de control en verde)",
}

TRAYECTORIAS_POR_DOMINIO = {
    "fabrica": {
        "gamma_0": "Mantener la línea en régimen nominal",
        "gamma_1": "Flexibilizar: reajustar el ritmo de producción",
        "gamma_2": "Amortiguar: aliviar carga en el cuello de botella",
        "gamma_3": "Sincronizar: estabilizar turno y mantenimiento",
        "gamma_4": "Desacoplar: revisar políticas de planta",
    },
    "logistica": {
        "gamma_0": "Mantener rutas y flota en operación nominal",
        "gamma_1": "Flexibilizar: reasignar rutas y capacidad",
        "gamma_2": "Amortiguar: reducir carga en el tramo saturado",
        "gamma_3": "Sincronizar: reprogramar entregas y relevos",
        "gamma_4": "Desacoplar: revisar SLA y prioridades",
    },
    "retail": {
        "gamma_0": "Mantener inventario y piso de venta estables",
        "gamma_1": "Flexibilizar: reponer y ajustar surtido",
        "gamma_2": "Amortiguar: descongestionar caja y atención",
        "gamma_3": "Sincronizar: alinear stock con demanda",
        "gamma_4": "Desacoplar: revisar promociones y precios",
    },
    "hotel": {
        "gamma_0": "Mantener ocupación y servicio en nivel nominal",
        "gamma_1": "Flexibilizar: reasignar habitaciones y personal",
        "gamma_2": "Amortiguar: reforzar recepción en hora pico",
        "gamma_3": "Sincronizar: coordinar limpieza y check-in",
        "gamma_4": "Desacoplar: revisar overbooking y tarifas",
    },
    "restaurante": {
        "gamma_0": "Mantener cocina y salón en ritmo nominal",
        "gamma_1": "Flexibilizar: ajustar mise en place y turnos",
        "gamma_2": "Amortiguar: aliviar la cocina en hora pico",
        "gamma_3": "Sincronizar: acompasar sala y pases de cocina",
        "gamma_4": "Desacoplar: revisar carta y mermas",
    },
    "clinica": {
        "gamma_0": "Mantener flujo de pacientes estable",
        "gamma_1": "Flexibilizar: reprogramar agenda y salas",
        "gamma_2": "Amortiguar: reforzar triaje en saturación",
        "gamma_3": "Sincronizar: coordinar turnos y camas",
        "gamma_4": "Desacoplar: revisar protocolos de derivación",
    },
    "medicina": {
        "gamma_0": "Mantener el plan de tratamiento vigente",
        "gamma_1": "Flexibilizar: ajustar dosis o seguimiento",
        "gamma_2": "Amortiguar: contener el signo de alarma",
        "gamma_3": "Sincronizar: reordenar estudios y control",
        "gamma_4": "Desacoplar: revisar diagnóstico diferencial",
    },
    "ciberseguridad": {
        "gamma_0": "Mantener la postura de seguridad nominal",
        "gamma_1": "Flexibilizar: reforzar el control debilitado",
        "gamma_2": "Amortiguar: contener el incidente activo",
        "gamma_3": "Sincronizar: aislar y estabilizar el segmento",
        "gamma_4": "Desacoplar: revisar políticas y accesos",
    },
}

_TRAYECTORIAS_GENERICAS = {
    "gamma_0": "Mantener la operación en régimen nominal",
    "gamma_1": "Flexibilizar: ajustar el flujo insuficiente",
    "gamma_2": "Amortiguar: reducir la sobrecarga",
    "gamma_3": "Sincronizar: estabilizar el proceso",
    "gamma_4": "Desacoplar: revisar las políticas",
}


def construir_dominio(dominio_id: str, dominio_nombre: str = None) -> "DominioConfig":
    """
    Devuelve un DominioConfig con el MISMO semáforo (KPIs/umbrales) que la base,
    pero con las trayectorias (geodésicas) en el lenguaje del dominio activo.
    """
    nombres = TRAYECTORIAS_POR_DOMINIO.get(dominio_id, _TRAYECTORIAS_GENERICAS)
    geodesicas = {
        k: {"nombre": nombres.get(k, _TRAYECTORIAS_GENERICAS[k]), "condicion": _CONDICIONES[k]}
        for k in _CONDICIONES
    }
    return DominioConfig(
        nombre=dominio_nombre or DOMINIO_CVD.nombre,
        kpis_nombres=DOMINIO_CVD.kpis_nombres,
        kpis_umbrales=DOMINIO_CVD.kpis_umbrales,
        variables_controlables=DOMINIO_CVD.variables_controlables,
        variables_opacas=DOMINIO_CVD.variables_opacas,
        geodesicas=geodesicas,
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

# Enmascaramiento de PI: los nombres reales de los KPIs y de las variables del
# modelo viven SOLO como clave interna del backend. La API expone códigos
# neutrales (K1..K7 para KPIs, C1..Cn / O1..On para variables de control/opacas).
CODIGO_POR_KPI = {n: f"K{i + 1}" for i, n in enumerate(DOMINIO_CVD.kpis_nombres)}
KPI_POR_CODIGO = {v: k for k, v in CODIGO_POR_KPI.items()}


def desenmascarar_kpis(kpis_codificados: Dict[str, float]) -> Dict[str, float]:
    """Traduce códigos (K1..K7) → nombres internos para el cálculo del lazo."""
    return {KPI_POR_CODIGO.get(k, k): v for k, v in kpis_codificados.items()}


def enmascarar_nombres(nombres: List[str]) -> List[str]:
    """Lista de nombres reales de KPI → lista de códigos neutrales."""
    return [CODIGO_POR_KPI.get(n, n) for n in nombres]


def enmascarar_dict_por_kpi(d: Dict) -> Dict:
    """Reemplaza las claves (nombres reales de KPI) por códigos neutrales."""
    return {CODIGO_POR_KPI.get(k, k): v for k, v in (d or {}).items()}


def enmascarar_resultado(resultado: Dict) -> Dict:
    """Enmascara los nombres internos de KPI por códigos neutrales en la salida del lazo."""
    r = dict(resultado)
    if isinstance(r.get("kpis"), dict):
        r["kpis"] = enmascarar_dict_por_kpi(r["kpis"])
    return r


def dominio_serializable(dominio: DominioConfig) -> Dict:
    """Config del dominio lista para JSON, con los nombres de PI enmascarados."""
    umbrales = {}
    for nombre, u in dominio.kpis_umbrales.items():
        verde = u.get("verde", (0.0, 1.0))
        umbrales[CODIGO_POR_KPI.get(nombre, nombre)] = {"verde": [verde[0], verde[1]], "rojo": u.get("rojo", 0.5)}
    return {
        "nombre": dominio.nombre,
        "kpis_nombres": enmascarar_nombres(dominio.kpis_nombres),
        "kpis_umbrales": umbrales,
        "variables_controlables": [f"C{i + 1}" for i in range(len(dominio.variables_controlables))],
        "variables_opacas": [f"O{i + 1}" for i in range(len(dominio.variables_opacas))],
        "geodesicas": dominio.geodesicas,
    }
