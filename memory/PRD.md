# Aprendiz Mileforum — PRD

## Problema / Origen
Refinamiento del repo `domprimitivo/app-sugerencia` (copiado íntegro a /app).
App 100% LOCAL y OFFLINE: React + FastAPI + **SQLite** (sin MongoDB, sin
dependencia de internet ni terceros). Objetivo del cliente: distribuible como
.exe local.

## Arquitectura / Flujos (identificados)
- **Embudo (ingesta):** entradas manuales (`/api/expedientes/{id}/procesar`) y
  webhook tiempo real (`/api/ingesta/webhook/{dominio}`). Se bifurca por
  `tipo_dominio` en config.json:
  - **unipersonal** → motor APRENDIZ (`aprendiz_motor/notebook_engine.py`,
    BundleLoader GRU/geométrico) → heads(trigo/cobre/petroleo), estados,
    sugerencia_tcl.
  - **empresa** → agentes RAG (`aprendiz_motor/rag_agents/processor.py` + cucurucho JSON).
- Frontend app: landing + `/claridad` (lazo) + `/archivos` (embudo empresa:
  archivos + escritura libre + compresión geométrica).

## Implementado (sesión 2026-06)
### Fusión aprendiz ↔ empresas (asistente silencioso de etiquetado)
- El aprendiz queda **IDÉNTICO para unipersonales**.
- Para **empresas**, al final del embudo RAG el aprendiz sugiere una acción/etiqueta
  para lo ingestado (archivos + **campo de escritura libre nuevo** en `/archivos`).
  No es explícito: el frontend NO muestra nombres (aprendiz/modelo/cabezas); solo
  un chip "Sugerencia para etiquetar". Usuario **confirma** o **corrige** (texto libre).
- **Registro separado con timestamp**: tabla SQLite `aprendiz_decisiones` +
  `aprendiz_data/{dominio}_learning_log.jsonl` con el **schema EXACTO** de los
  notebooks (backbone_inference, action_execution.{user_accepted_suggestion,
  action_id, action_label, action_known}, soft_context, learning_event en
  correcciones). Actualiza `{dominio}_action_dictionary_state.json`.
- **Ajuste automático cada 50 días** tras la activación: `ajuste_bimestral.py`
  ejecuta el notebook real `Mileforum_Aprendiz_Ajuste_Bimestral_v0_1.ipynb` vía
  nbclient (offline), entrena el PolicyAdapter y **reemplaza el modelo**
  promoviendo `{dominio}_policy_adapter.pt` + vocabularios/allowlist. Scheduler
  daemon (cada 6h) + endpoint manual.
- Endpoints nuevos: `POST /api/aprendiz/{dominio}/decision-asistente`,
  `GET /api/aprendiz/{dominio}/decisiones`, `POST /api/aprendiz/{dominio}/ajuste/ejecutar`,
  `GET /api/aprendiz/{dominio}/ajuste/estado`.
- Deps añadidas: torch, nbclient, nbformat, ipykernel.

### Estado de pruebas
- Testing agent: backend 100% (9/9), frontend 100%. Sin issues críticos.

## Backlog / Próximos
- **EN CURSO / PRÓXIMO: Fase 2 "Habitabilidad"** (elemento de observación en
  `/archivos`: semáforo + trayectoria). Es el siguiente elemento a construir.
- P2: Vista de historial de decisiones / estado del ajuste dentro de `/archivos`.
- P2: Refactor de ArchivosEmbudo.jsx en subcomponentes (~540 líneas).
- P2: Alinear naming de respuestas del feature aprendiz.

## Añadido (sesión 2 · 2026-06)
- **Sugerencia entrenada (empresas):** nuevo `aprendiz_inferencia.py` carga el
  `{dominio}_policy_adapter.pt` promovido y refina la sugerencia del asistente
  (replica la vectorización de la celda 9 del notebook). En la rama empresa de
  `procesar_expediente`, si hay modelo → `asistente.origen="modelo"`, si no
  `="rag"` (fallback). Cache por mtime; si el vector no cuadra, cae al RAG.
- **Ajuste unipersonal:** `registrar_decision` (`/sincronizaciones/{id}/decision`)
  ahora, para dominios unipersonales y decisión ≠ abstener, deriva el evento del
  último `procesamientos` y lo registra en `aprendiz_decisiones` + learning_log
  (schema notebook), sin cambiar la UX. El scheduler de 50 días y
  `/aprendiz/{dominio}/ajuste/ejecutar` ya funcionan para unipersonal (usa el
  bundle real del repo). Validado con `abogado`: 5 decisiones → ajuste ejecutó el
  notebook y reemplazó el modelo.
- Nota: `DecisionCreate` exige `expediente_id` también en el body.

## Añadido (sesión 3 · 2026-06) — Sistema de navegación geométrica
- **Modelo mental del repo:** dos elementos de navegación geométrica —
  **claridad** (ya fusionado para empresas) y **habitabilidad** (medicina /
  ciberseguridad, pendiente). Cada uno opera en **modo sugerencia (ASESORIA)** o
  **modo agencia (AGENCIA)** según el cliente. Frontend: semáforo de KPIs (dots),
  **barra de tres hermanos = "piloto automático"** (sólo AGENCIA), y geodésicas
  = **"trayectorias"**. `/claridad` = PantallaClaridad; motor: `lazo_generico.py`
  (lazo_asesoria / lazo_agencia).
- **Primera adición (hecha):** botón **"Procesar con el embudo"** en `/claridad`
  para AMBOS modos → `POST /api/embudo/registrar-resultado` crea expediente +
  documento `navegacion.txt` y lo pasa por el embudo (procesar_expediente), para
  que quede registrado en el mismo lugar que el resto de la operación
  (expedientes/procesamientos + sugerencia del asistente). Validado 100%.
## Añadido (sesión 4 · 2026-06) — Ingesta real + etiqueta (buyer journey fábrica)
- **BUG FIX — extracción PDF/DOCX:** el embudo abría todo como UTF-8, así que
  PDF/DOCX caían a `[Archivo binario]` y se perdían. Nueva
  `extraer_texto_documento()` en server.py: PDF (pdfplumber), DOCX (python-docx),
  fallback texto plano. Deps: pdfplumber, python-docx. Validado 100%.
- **Etiqueta en escritura libre:** input `escritura-libre-etiqueta-input` en
  `/archivos`; se antepone `Etiqueta: {etiqueta}` al texto y se registra aunque
  el cucurucho no lo reconozca como evento (nivel personal).
- **Pendiente (fuera de alcance del fix, notado):**
  - Trayectorias en lenguaje del dominio activo (hoy `lazo_generico.py` usa un
    dominio fijo CVD Grafeno, no fábrica/medicina/ciberseguridad).
## Añadido (sesión 5 · 2026-06) — Trayectorias por dominio + ingesta ampliada
- **Trayectorias siguen el dominio activo** (`lazo_generico.py`:
  `TRAYECTORIAS_POR_DOMINIO` + `construir_dominio()`): las geodésicas se muestran
  en el lenguaje del dominio (fábrica, logística, retail, hotel, restaurante,
  clínica, medicina, ciberseguridad + genérico). **El semáforo (7 KPIs y
  umbrales) es IGUAL para todos.** `/api/lazo/dominio` y `/api/lazo/evaluar` usan
  el dominio activo (`_dominio_activo_lazo`).
- **Ingesta CSV + Excel** en `extraer_texto_documento` (openpyxl para .xlsx/.xlsm,
  csv stdlib para .csv), además de PDF/DOCX/txt.
- **Ingesta tiempo real (webhook/API) OPCIONAL:** `_ingesta_tiempo_real()`; si no
  hay eventos → `disponible:false` sin error; el embudo procesa lo que haya.
- **Modo AGENCIA vinculado al lazo de control:** `/api/lazo/evaluar` en AGENCIA
  añade `ingesta_tiempo_real{disponible,total,items}`; frontend muestra
  `vinculo-lazo-control` (solo AGENCIA). Deps: openpyxl.
- Validado 100% (iteración 10).
## Añadido (sesión 6 · 2026-06) — Enmascaramiento de PI (P0)
- **Objetivo:** los nombres reales de KPIs, variables del modelo y condiciones de
  trayectoria son PI crítica; viven SOLO como clave interna en el backend. La API
  expone códigos neutrales.
- **lazo_generico.py:** mapa `CODIGO_POR_KPI` (K1..K7) + helpers
  `desenmascarar_kpis`, `enmascarar_resultado`, `enmascarar_nombres`,
  `enmascarar_dict_por_kpi`. `dominio_serializable` devuelve KPIs como K1..K7,
  umbrales por código, `variables_controlables`→C1..Cn, `variables_opacas`→O1..On.
  `_CONDICIONES` y `DOMINIO_CVD.geodesicas` reescritas sin nombres reales (adiós
  "Permeabilidad", "Tensión TR", CH4/H2/T_sub, etc.).
- **server.py `/api/lazo/evaluar`:** desenmascara entrada (K→real) para el cálculo,
  enmascara la salida.
- **flujo_kpis.py (`ejecutar_flujo` y `ejecutar_flujo_dominio`):** `polos`,
  `kpis_holograficos`, `metricas_discretas` y `lazo` enmascarados (mismos códigos).
- **PantallaClaridad.jsx:** presets nominal/autoengaño con claves K1..K7 (el UI ya
  era 100% gráfico; sin texto de KPI). `ArchivosEmbudo.jsx` ahora muestra K1..K7.
- Validado por curl (lazo/dominio, lazo/evaluar, flujo/ejecutar-dominio) + screenshot
  de /claridad: sin fugas de nombres reales en el DOM ni en los payloads.
## Añadido (sesión 7 · 2026-06) — Navegación + empaquetado .exe local
- **Navegación fácil (React preview):** Navbar de la landing ahora tiene enlaces
  "Claridad" (`/claridad`) y "Embudo" (`/archivos`) en desktop y menú móvil.
  Cabeceras de ambas pantallas con enlaces cruzados directos (Claridad↔Embudo) +
  "Inicio". testids: nav-claridad, nav-embudo, claridad-nav-embudo,
  claridad-nav-inicio, archivos-nav-claridad, archivos-nav-inicio.
- **Empaquetado local (Flutter es la UI del .exe; landing = web online):**
  - `backend/build_backend.bat`: PyInstaller `--onefile --name aprendiz_backend`
    con `--collect-all` de deps pesadas (torch, uvicorn, pdfplumber, openpyxl,
    docx, nbclient/nbformat/ipykernel, papermill) + hidden-imports de los módulos
    locales. NO usa --add-data: COPIA los assets read-only (flujo/, bundles/,
    aprendiz_data/, modelos/, config.json) junto al .exe en dist\ (coherente con
    `_resolver_root_dir()`; la BD mileforum.db y uploads/ se crean junto al exe).
  - `Iniciar_App.bat` (raíz): lanza backend\dist\aprendiz_backend.exe minimizado,
    espera, abre app\flutter_app.exe y al cerrarlo mata el backend.
  - **Rutas frozen-aware unificadas:** además de server.py (ya lo tenía),
    `flujo_kpis.py` (FLUJO_DIR/MEMORIA_DIR) y `aprendiz_motor/notebook_engine.py`
    (MODELOS_DIR) ahora usan `Path(sys.executable).parent` cuando `sys.frozen`,
    para que catálogos/memoria/modelos vivan junto al .exe (no en _MEIPASS).
  - Nota: los .bat son para el build en Windows (no ejecutables en este contenedor).
## Auditoría (sesión 7 · 2026-06) — Semáforo / Lazo / Aprendiz (4 etapas)
- Verificación tipo "contratos+regresión+persistencia+arranque" adaptada a este
  stack (sqlite3, `/api`, `.pt`). Resultado: backend sano, sin regresiones.
- 56 rutas registradas; smoke tests OK: `/api/lazo/evaluar` (ASESORIA/AGENCIA,
  K1..K7 enmascarados), `/api/aprendiz/{dom}/decision-asistente`
  (confirmar+corregir → learning_event), `/decisiones`, `/ajuste/estado`,
  `/motor/estado`, `/embudo/registrar-resultado`.
- Contrato clave: `decision-asistente` requiere el objeto `sugerencia` COMPLETO
  (dominio, node_id, phase, phase_probs, clarity, R_score, suggested_action_id/
  label, soft_tags) — el frontend debe reenviar la sugerencia tal cual la recibió
  de `/procesar`; si faltan campos → 500 (KeyError en construir_evento). No es bug.
