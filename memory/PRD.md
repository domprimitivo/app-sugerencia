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
  - Modelo explícito de los **tres niveles** de registro: técnico (habitabilidad),
    dominio (cadena de valor / soporte) y personal.
