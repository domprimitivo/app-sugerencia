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
- P1: Inferencia usando el `policy_adapter.pt` promovido para refinar la
  sugerencia del asistente (hoy la sugerencia base viene del RAG).
- P2: Vista de historial de decisiones / estado del ajuste dentro de `/archivos`.
- P2: Refactor de ArchivosEmbudo.jsx en subcomponentes (~540 líneas).
- P2: Alinear naming de respuestas del feature aprendiz.
