# ITQ Conecta Backend: Estado de trabajo

Última actualización: 2026-11-02

## Estado de Core y autenticación (2 de noviembre de 2026)

### Cambios realizados

Se adaptaron los modelos de `core.personas`, `usuarios`, `roles`,
`usuario_rol`, `auditoria`, `permisos`, `modulos`, `unidades`, `estudiantes`,
`empleados` y `catalogos_academicos` a los tipos y nulabilidad observados en la
base PostgreSQL existente. Entre los ajustes están:

- Estados como booleanos (incluidos los estados de usuario, rol y asignación
  usuario-rol), en lugar de cadenas como `"activo"`.
- Columnas opcionales reflejadas como nullable en los modelos y en los DTO de
  respuesta de persona, usuario y asignaciones de roles.
- `Empleado.fecha_ingreso` tratado como `date`.
- Longitudes de campos y fechas sin zona horaria alineadas con el esquema
  inspeccionado.
- Login y dependencia JWT consideran activa una cuenta solo si `estado` es
  `True`; los roles del login también deben estar activos. El login rechaza
  usuarios sin hash de contraseña sin intentar verificar un valor nulo.
- El filtro `GET /api/v1/core/usuarios?estado=activo|inactivo` traduce esos
  valores de API a booleanos y devuelve 422 para otros valores.

### Verificaciones realizadas

- Python importó `app.main`, SQLAlchemy configuró los mappers y OpenAPI generó
  51 rutas.
- Se ejecutaron consultas de solo lectura (`SELECT ... LIMIT 0`) sobre los 11
  modelos Core indicados y filtros booleanos de usuario contra PostgreSQL.
- Se validó que los DTO aceptan los valores nulos comprobados.
- `compileall` y la comprobación de sintaxis de los seis archivos Python
  modificados terminaron sin errores.
- No se ejecutaron `INSERT`, `UPDATE`, `DELETE`, migraciones ni pruebas de
  escritura contra la base.

Estas pruebas verifican carga, mapeo y compatibilidad de las consultas
probadas; **no equivalen a una prueba completa de API ni de autenticación**.
No se ejecutó un login real ni una suite de pruebas automatizadas de Core.

### Entorno y versiones observadas

Versiones obtenidas del entorno virtual del repositorio en esta máquina
(versiones instaladas, no todas son pins exactos de `requirements.txt`):

| Componente | Versión observada |
|---|---:|
| Python | 3.12.13 |
| FastAPI | 0.156.4 |
| SQLAlchemy | 2.0.55 |
| Pydantic | 2.14.1 |
| asyncpg | 0.32.0 |
| python-jose | 3.5.0 |
| Passlib | 1.7.4 |
| bcrypt | 4.0.1 |
| PostgreSQL local | 18.6 |
| Git for Windows | 2.54.0.windows.1 |

Herramientas empleadas: entorno virtual `.venv` de la raíz, PowerShell,
SQLAlchemy/asyncpg para las consultas de solo lectura, compilación Python,
validación de sintaxis Pylance y generación OpenAPI de FastAPI. Pylance reportó
imports no resueltos en el intérprete seleccionado por VS Code; la ejecución
y las pruebas anteriores se hicieron explícitamente con
`..\\.venv\\Scripts\\python.exe` desde `backend/`. Selecciona ese intérprete en
VS Code para que el análisis del editor use las mismas dependencias.

### Pendiente antes de considerar terminado Core/auth

1. Configurar una `SECRET_KEY` segura en `backend/.env` (no compartirla ni
   subirla a Git) y probar login, respuesta `/auth/me`, expiración y rechazo de
   cuentas inactivas con un usuario de prueba autorizado.
2. Probar las respuestas y filtros de la API con registros representativos,
   incluyendo campos nulos y estados `true`/`false`; hasta ahora las consultas
   se limitaron a verificar SQL y mapeo sin leer ni modificar filas.
3. Revisar la compatibilidad de las demás tablas y módulos (documentos,
   graduación y modelos académicos adicionales) por separado. La prueba de
   esta etapa cubre solo los 11 modelos Core enumerados arriba.
4. Antes de cualquier DDL, comparar el esquema real y el respaldo, preparar un
   plan aditivo revisable y obtener autorización. Esta etapa preservó la base
   y no aplicó cambios de esquema.
5. Corregir el intérprete Python seleccionado en VS Code y repetir los
   diagnósticos Pylance en ese entorno.

## Backend unificado

Este directorio reúne los módulos de ITQ Conecta y Pagos a Docentes. Los
routers institucionales se sirven bajo `/api/v1`; salud permanece disponible
en `/api` y `/api/v1/health`. La documentación OpenAPI está en `/api/docs`.

Desde la raíz del repositorio, inicia el backend así:

```powershell
cd backend
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Configura DATABASE_URL y SECRET_KEY en .env antes de iniciar.
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La aplicación registra autenticación, Core, documentos, graduación y pagos a
docentes. No copies credenciales entre archivos `.env`; usa `backend/.env` y
manténlo fuera del control de versiones.

La descripción de carpetas y componentes está en
[ESTRUCTURA_BACKEND.md](./ESTRUCTURA_BACKEND.md).

Este documento registra el estado actual del backend y del módulo **Pagos a Docentes** para continuar el trabajo en otra sesión. No contiene credenciales; la URL de PostgreSQL se lee de `backend/.env`.

## Tecnologías y ejecución

- FastAPI, SQLAlchemy 2 async, asyncpg y Pydantic v2.
- Celery con broker/backend Redis configurables mediante `REDIS_URL`,
  `CELERY_BROKER_URL` y `CELERY_RESULT_BACKEND`.
- Usa el entorno Python 3.12 del repositorio en `..\.venv\`; el antiguo
  `backend\.venv\` apunta a una instalación que no existe en esta máquina.

Desde la raíz del repositorio, activa el entorno e inicia la API:

```powershell
.\.venv\Scripts\Activate.ps1
Set-Location backend
uvicorn app.main:app --reload
```

Documentación interactiva: `http://127.0.0.1:8000/api/docs`.

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

- `models/`: separa los modelos de pagos por responsabilidad y los reexporta desde `models/__init__.py`.
- `referencias_docentes.py`: conserva referencias de solo lectura a tablas `core` usando las tablas ORM canónicas del módulo Core.
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
2. **Autenticación de pagos:** `router.py` conserva `get_current_user` como stub que recibe `id_usuario` por query. La autenticación JWT ya existe para otros módulos, pero pagos todavía no la utiliza ni aplica RBAC; cualquier actor enviado debe existir en `core.usuarios` para satisfacer las FKs.
3. **Celery/Redis/correo:** `app/tasks.py` solo contiene `ping`. No hay tareas programadas de alertas ni lector IMAP/SMTP implementado. Redis no respondía en `localhost:6379` durante la revisión. Faltan servicio Redis activo y configuración/secretos de correo antes de abordar esas funciones.
4. **Pruebas de escritura y flujo:** no se ejecutaron POST/PUT que escriban datos. Deben probarse después de disponer de referencias válidas y actor autorizado.
5. **Datos del frontend:** los GET ya funcionan, pero lookups devuelve docentes/carreras vacíos mientras `core` siga vacío.

## Para continuar

1. Confirmar cómo se crearán o identificarán referencias existentes en `core`, sin alterar otros esquemas.
2. Sustituir el stub de usuario en pagos por la dependencia JWT autorizada y probar POST/transiciones con un usuario real.
3. Activar Redis y definir el alcance/configuración de alertas y correo antes de implementar tareas Celery.
4. Decidir si se conserva SQL manual versionado o se adopta Alembic tras establecer una línea base.
