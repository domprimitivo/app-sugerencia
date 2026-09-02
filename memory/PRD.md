# Mileforum — App Local Soberana (PRD)

## Regla soberana (invariante)
App 100% local: FastAPI + SQLite, sin MongoDB, sin dependencias/referencias a terceros,
sin preparación para build/deploy en ninguna plataforma. Cambios puntuales; no agregar
nada que no esté explícitamente solicitado.

## Problema / Cambio (2026-09-02)
Unificar el "reporte de claridad" en el **lazo genérico**. El reporte deja de ser un
paso separado: su información es ahora el resultado natural del lazo, mostrado en la
**Pantalla de Claridad** (interfaz nativa del lazo), con dos modos:
- **ASESORÍA** (sin hermanos): 7 KPIs → Cénit humano. El humano autoriza.
- **AGENCIA** (con hermanos): lazo completo (Corto, Mediano, Largo). El sistema ejecuta;
  solo llama al Cénit en casos críticos.

## Implementado (2026-09-02)
- Backend `/app/backend/lazo_generico.py`: port fiel del notebook (DominioConfig,
  DOMINIO_CVD, evaluar_kpis, detectar_autoengano, sugerir_geodesica, lazo_asesoria,
  lazo_agencia, dominio_serializable). Python puro, sin numpy/pandas (varianza manual).
- Backend endpoints en `server.py`:
  - `GET /api/lazo/dominio` → config del dominio (KPIs, umbrales, geodésicas).
  - `POST /api/lazo/evaluar` {modo, kpis} → resultado del lazo (lo que muestra la pantalla).
- Frontend `/app/frontend/src/components/PantallaClaridad.jsx` (ruta `/claridad`):
  sliders de 7 KPIs, presets Nominal/Autoengaño, toggle ASESORÍA/AGENCIA, panel de
  resultado (estado general, KPIs con color, Barra de Tres Hermanos en AGENCIA,
  diagnóstico autoengaño/fallo de pegado, geodésica sugerida, acciones).
- Routing en `App.js` (BrowserRouter): `/` landing intacta, `/claridad` nueva pantalla.
- `frontend/.env` creado con REACT_APP_BACKEND_URL (gitignored; para preview/local).

## Estado de pruebas
- Testing agent: backend 100%, frontend 100%. POSTs reales desde navegador y render OK
  en ambos modos. Tests en `/app/backend/tests/test_lazo.py`.

## Notas
- El preset "Autoengaño" (valores del notebook) produce estado `TENSION` (fallo_pegado,
  requiere_cenit=True) — fiel a la lógica del notebook; el panel Cénit se muestra correcto.
  El estado `AUTOENGAÑO` requiere los 6 KPIs estructurales en ROJO.
- Warnings de `ephemeral-upload-storage` en server.py son pre-existentes e intencionales
  (soberanía local; no usar object storage).

## Backlog / Next
- P2: Cargar la config de dominio desde el cuestionario/archivos cucurucho en lugar de
  DOMINIO_CVD fijo (multi-dominio en la Pantalla de Claridad).
- P2: Persistir/registrar cada ejecución del lazo (histórico) en SQLite.
- P2: Enlazar las acciones (Autorizar / Validar) a un flujo real de registro de decisión.
