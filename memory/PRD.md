# Mileforum — App Local Soberana (PRD)

## Regla soberana (invariante)
App 100% local: FastAPI + SQLite, sin MongoDB, sin dependencias/referencias a terceros,
sin build/deploy en ninguna plataforma. Cambios puntuales; no reconstruir; mantener
intacto el resto de funciones. Almacenamiento de archivos en disco local (nunca nube).

## Implementado

### 1) Pantalla de Claridad — Lazo genérico (2026-09-02)
- `backend/lazo_generico.py`: puerto fiel del notebook (evaluar_kpis, detectar_autoengano,
  sugerir_geodesica, lazo_asesoria, lazo_agencia). Endpoints `GET /api/lazo/dominio`,
  `POST /api/lazo/evaluar`. Frontend `/claridad`. Testeado 100%.
- REDISEÑO (2026-09-02): paleta arquitectónica (ladrillo/cielo/césped/arena). KPIs 100%
  gráficos = SEMÁFORO (verde/amarillo/rojo), sin nombres ni números. "Geodésicas" →
  "Trayectorias": único texto; oculto hasta que el usuario lo CONVOCA (indicador que
  pulsa), o automático cuando el backend marca CÉNIT (requiere_cenit) con estilo de alta
  atención (ladrillo). Distinción gráfica/baja-atención vs texto/alta-atención. Testeado 100%.

### 2) Activador / Validador (verificado, sin cambios de código)
- La verificación en `server.py` (`verificar_activador`, `_generar_firma`) coincide
  EXACTAMENTE con `generar_activador.py` (referencia externa del operador):
  clave `mileforum-prudential-2026-clave-privada-antonio`, HMAC-SHA256 sobre
  `json.dumps(campos, sort_keys=True, ensure_ascii=False)` sin el campo `firma`.
- Probado: válido→activo; firma alterada / cliente_id ajeno / vencido→rechazado.
- La generación NO está en la app (solo verificación). `mileforum_activador.json` de
  prueba está ligado al cliente_id de esta máquina de preview.

### 3) Compresión Geométrica — Códec MOCG (2026-09-02)
- `backend/compresion_geometrica.py` (Python puro + numpy; sin gradio/plotly/scipy):
  clasifica por contenido, normaliza a eventos, manifold incremental 8D, comprime en
  3 capas (íntegra lossless / inferible PCA2 / geométrica) + reporte de forma con
  anomalías. `comprimir`, `descomprimir` (exacto, sha256), `es_paquete_comprimido`.
- Endpoints: `POST /api/compresion/toggle` (alterna: comprime, o descomprime si se
  sube un paquete MOCG_CODEC_V1) y `POST /api/compresion/sistema/{dominio}` (comprime
  carpetas del sistema: aprendiz_data, bundles, session_files, bimestral_package).
- Frontend `/archivos` (`ArchivosEmbudo.jsx`): subida de archivos, botón
  "Procesar con el embudo" (RAG: expedientes/documentos/procesar) y botón único
  "Comprimir / Descomprimir". Testeado 100% (round-trip lossless).

### Modo del lazo (hardcodeado)
- Constante `MODO_LAZO = 'ASESORIA'` en `frontend/src/components/ArchivosEmbudo.jsx`.
  Para otro repo/build cambiar a `'AGENCIA'` en esa línea (comentada). El activador no
  lleva campo "modo", por eso se hardcodea en esta versión.

## Cambios de infraestructura (sin alterar comportamiento)
- `backend/local_storage.py`: helper de persistencia local (disco), usado por las
  subidas para centralizar la escritura. Comportamiento idéntico (archivos locales).
- `backend/app/db/sqlite_db.py`: reparado docstring corrupto (comilla triple sin cerrar).
  Archivo huérfano (no importado por nadie).

## Pruebas
- iteration_2.json (lazo) OK; iteration_3.json (compresión) OK. Backend/Frontend 100%.
- Tests: `backend/tests/test_lazo.py`, `backend/tests/test_compresion.py`.

## Backlog / Next
- P2: Multi-dominio para el lazo (config desde cuestionario/cucurucho).
- P2: Pantalla de configuración inicial en React (hoy el sistema no está "configurado",
  por eso el embudo RAG pide configuración). El flujo real vive en el exe Flutter.
- P2: Descarga directa del paquete/archivos del sistema comprimido desde /archivos.
