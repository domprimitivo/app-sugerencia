# Credenciales / Estado de prueba — Aprendiz Mileforum

App 100% local (SQLite, sin auth de usuario). No hay login.

## Activación (requerida para procesar / no quedar en modo lectura)
- Archivo: `/app/backend/mileforum_activador.json` (firmado HMAC-SHA256).
- cliente_id de esta máquina: `7e7cb50ecdfee392d46e15808afeb3dc`
- Clave secreta (dev): `mileforum-prudential-2026-clave-privada-antonio` (constante `ACTIVACION_CLAVE_SECRETA` en server.py).
- Para regenerar el activador (si cambia el hardware/cliente_id):
  computar `cliente_id` desde `GET /api/activacion/estado`, armar payload
  `{cliente_id, valido_hasta (futuro), plan, emitido_por}`, firmar con la clave
  sobre `json.dumps(campos, sort_keys=True, ensure_ascii=False)` (excluyendo `firma`).

## Dominio configurado actualmente
- `fabrica` (tipo empresa) — journey de verificación de fábrica.
- Dominios empresa: clinica, hotel, restaurante, retail, fabrica, logistica.
- Dominios unipersonales: abogado, arquitecto, contador, consultor_pyme, diseno_producto, operaciones.
