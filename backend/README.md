# ITQ Conecta Backend: Estado de trabajo

Última actualización: 2026-10-27

Este documento registra el estado actual del backend y del módulo **Pagos a Docentes** para continuar el trabajo en otra sesión. No contiene credenciales; la URL de PostgreSQL se lee de `backend/.env`.

## Tecnologías y ejecución

- FastAPI, SQLAlchemy 2 async, asyncpg y Pydantic v2.
- Celery con broker/backend Redis configurables mediante `REDIS_URL`.
- Python 3.13 instalado en Windows; el entorno local de este backend está en `backend/.venv/` y queda ignorado por Git.

Desde la raíz del repositorio, activar el entorno e iniciar la API:

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Documentación interactiva: `http://127.0.0.1:8000/docs`.

La aplicación lee `.env` relativo al directorio de ejecución. Al iniciar desde `backend/`, usa `backend/.env`. No publiques ese archivo ni incluyas sus valores secretos en documentación.

## Base de datos

La conexión configurada apunta a PostgreSQL 18.6, base `itq_conecta`, en `localhost:5432`. La conexión fue probada desde Python usando asyncpg. El esquema operativo del módulo es `pagos_docentes`; las referencias en `core` se consultan, pero no se deben alterar desde este módulo.

Tablas actuales de `pagos_docentes`:

- `docentes`, `periodos`, `modulos`
- `correos_procesados`, `aprobaciones`, `pagos`
- `configuracion_umbral`, `alertas`, `historial`
- Vista: `v_estado_pagos`

Restricciones relevantes observadas: una fila de docente por empleado, periodo con nombre único, mensaje de correo único, una aprobación y un pago por módulo; alerta activa única por módulo y solo un umbral activo. Los estados de módulos son `EN_CURSO`, `LISTO_PAGO`, `APROBADO`, `PAGADO`, `ANULADO`; los pagos usan `POR_PAGAR`/`PAGADO`; las aprobaciones `VIGENTE`/`ANULADA`; las alertas `ACTIVA`/`RESUELTA` y el tipo permitido es `PAGO_ATRASADO`.

### Compatibilidad aplicada

`database/pagos_docentes_runtime_compat_v2.sql` agrega, de forma idempotente y solo en `pagos_docentes.modulos`, las columnas `modelo`, `contrato` y `datos_modelo`, y el CHECK de modelo `CARRERA`/`VALIDACION`. Esta migración ya se aplicó a `itq_conecta` y se verificó en el catálogo PostgreSQL.

`database/pagos_docentes_cambios_v1.sql` contiene cambios históricos que no corresponden al esquema conectado: crea tablas paralelas, agrega CHECK incompatibles y repite índices únicos. Se dejó un guard que aborta transaccionalmente y apunta a v2. **No ejecutes v1.**

`database/init.sql` pertenece a otra inicialización/esquema (`financiera`); no se ejecutó ni se modificó como parte de este trabajo.

No hay revisiones en `database/migrations/versions/` ni Alembic configurado en los requisitos actuales. Por ahora, la compatibilidad usa SQL manual versionado. Si se adopta Alembic, primero debe establecerse una línea base de esta base real y evitar autogenerar contra la divergencia histórica.

## Módulo Pagos a Docentes

Directorio: `app/modules/pagos_docentes/`.

- `models.py`: mapea las nueve tablas de pagos y sus relaciones de `core`; los tipos, nulabilidad, columnas y FKs se compararon contra PostgreSQL. La comparación final no reportó diferencias. Los modelos `core` son referencias locales protegidas como solo lectura.
- `enums.py`: estados, origen de aprobación, estado de pago, unidad de umbral; acepta minúsculas/alias de API y produce valores válidos para DB.
- `schemas.py`: contratos de creación, pago, configuración, alertas, historial, resumen y lookups alineados con el cliente Angular.
- `services/`: consultas relacionales a través de `pagos_docentes.docentes`, `periodos` y `core.catalogos_academicos`; flujo de pago usa estados y restricciones reales.
- `router.py`: rutas con prefijo `finance/payments`. `main.py` registra pagos bajo `/api/v1`; health continúa bajo `/api`.

Rutas actuales:

- `GET /api/v1/finance/payments`
- `GET /api/v1/finance/payments/summary`
- `GET /api/v1/finance/payments/alerts`
- `GET /api/v1/finance/payments/settings`
- `PUT /api/v1/finance/payments/settings`
- `GET /api/v1/finance/payments/lookups`
- `POST /api/v1/finance/payments`
- `POST /api/v1/finance/payments/{payment_id}/ready`
- `POST /api/v1/finance/payments/{payment_id}/approval`
- `POST /api/v1/finance/payments/{payment_id}/paid`
- `GET /api/v1/finance/payments/{payment_id}/history`

El flujo de módulos es `EN_CURSO → LISTO_PAGO → APROBADO → PAGADO`; el registro de pago pasa de `POR_PAGAR` a `PAGADO`. El umbral consulta `configuracion_umbral.valor` y `.unidad`.

## Cambios hechos

1. Alineé modelos, FKs, tipos, nulabilidad, checks y unicidad con el esquema PostgreSQL existente; añadí los modelos ORM faltantes de docentes y periodos.
2. Adapté schemas y servicios a IDs de periodo/carrera, docente normalizado, estados reales, configuración de umbral y columnas reales de pago/aprobación/alertas.
3. Añadí `/lookups` (docentes, periodos y carreras activas) y adapté historial al response que espera Angular.
4. Alineé el prefijo del router de pagos con `/api/v1`.
5. Añadí y ejecuté la migración de compatibilidad v2, y deshabilité el SQL v1 incompatible.
6. Inserté solamente un periodo de prueba en `pagos_docentes.periodos`: `2026-PRUEBA-ITQ`, activo, ID actual 1. La inserción fue idempotente.

No se insertaron ni actualizaron filas en `core` u otros esquemas. En el momento de la revisión, `core.personas`, `core.empleados`, `core.usuarios` y `core.catalogos_academicos` estaban vacías; las tablas operativas del módulo también estaban vacías, salvo `configuracion_umbral`, que ya tenía un registro activo de 30 días.

## Verificaciones realizadas

- Compilación completa de `app/modules/pagos_docentes` y `app/main.py` con Python 3.13.
- Import de la aplicación y generación de OpenAPI; se verificaron rutas de pagos y health.
- Comparación automatizada de las nueve tablas ORM contra el catálogo DB: cero tablas/columnas adicionales o faltantes, cero diferencias de tipos/nulabilidad, cero FKs adicionales o faltantes.
- Smoke tests GET contra la DB real: settings, summary, alerts, lookups y listado respondieron HTTP 200. El filtro por mes también respondió 200.
- Se comprobó que las tablas `core` siguen sin filas y que el periodo de prueba existe.

## Pendientes y límites

1. **Datos para escritura:** no se puede crear un módulo válido sin docente, carrera y periodo existentes. El periodo de prueba está; docentes requieren `core.empleados` y `core.personas`, carreras requieren `core.catalogos_academicos` con `tipo='CARRERA'`. El historial/operaciones también referencian `core.usuarios`. No insertar esos datos sin autorización explícita, porque implicaría modificar `core`.
2. **Autenticación:** `router.py` conserva `get_current_user` como stub que recibe `id_usuario` por query. Aún no es autenticación real; además, cualquier actor enviado debe existir en `core.usuarios` para satisfacer las FKs.
3. **Celery/Redis/correo:** `app/tasks.py` solo contiene `ping`. No hay tareas programadas de alertas ni lector IMAP/SMTP implementado. Redis no respondía en `localhost:6379` durante la revisión. Faltan servicio Redis activo y configuración/secretos de correo antes de abordar esas funciones.
4. **Pruebas de escritura y flujo:** no se ejecutaron POST/PUT que escriban datos. Deben probarse después de disponer de referencias válidas y actor autorizado.
5. **Datos del frontend:** los GET ya funcionan, pero lookups devuelve docentes/carreras vacíos mientras `core` siga vacío.

## Para continuar

1. Confirmar cómo se crearán o identificarán referencias existentes en `core`, sin alterar otros esquemas.
2. Sustituir el stub de usuario por la dependencia de autenticación autorizada y probar POST/transiciones con un usuario real.
3. Activar Redis y definir el alcance/configuración de alertas y correo antes de implementar tareas Celery.
4. Decidir si se conserva SQL manual versionado o se adopta Alembic tras establecer una línea base.
