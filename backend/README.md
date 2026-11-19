# Backend de ITQ Conecta

Este es el backend que he ido armando para reunir varios módulos de ITQ Conecta
en una sola API. Uso FastAPI, SQLAlchemy asíncrono y PostgreSQL. La entrada de
la aplicación es `app/main.py`; desde ahí se registran los routers de cada
módulo.

## Estructura

```text
backend/
├── app/
│   ├── core/                 Configuración, base de datos, JWT y Celery
│   ├── middleware/           Auditoría y manejo de errores
│   ├── models/               Modelos usados por Graduación
│   ├── modules/
│   │   ├── core/             Personas, usuarios, roles y catálogos
│   │   ├── documentos/       Documentos, archivos, versiones y revisiones
│   │   ├── admisiones/       CRM, prospectos y aspirantes
│   │   ├── pagos_docentes/   Pagos, aprobaciones, reportes e historial
│   │   └── vacaciones/       Solicitudes, saldos, permisos e históricos
│   ├── routers/              Autenticación y Graduación
│   └── tasks.py              Punto inicial para tareas Celery
├── database/                 SQL separado por módulo
├── scripts/                  Utilidades de administración y base de datos
└── tests/                    Pruebas automatizadas
```

## Módulos

### Autenticación y Core

Core concentra los modelos compartidos de personas, usuarios, roles, permisos,
empleados y catálogos. La autenticación genera y valida JWT, y las rutas de Core
requieren un usuario autenticado.

El script `scripts/setup.ps1` crea `backend/.env` con una `SECRET_KEY` aleatoria
local. El archivo no debe compartirse ni subirse al repositorio. La autenticación
JWT está integrada en Pagos a Docentes; los demás módulos todavía requieren
revisar sus permisos específicos por rol.

### Documentos

Incluye rutas y modelos para registrar archivos, asociarlos con documentos,
guardar versiones y llevar revisiones.

**Pendiente:** en la base de desarrollo revisada no existen las tablas
`docs.file_assets`, `docs.documents`, `docs.document_versions` y
`docs.document_reviews`. Hay que definir y revisar el SQL de ese esquema antes
de probar estas rutas contra PostgreSQL. También falta validar de punta a punta
el almacenamiento y consulta de archivos.

### Graduación

Incluye eventos, pases y operaciones para validar pases mediante QR o cédula.
Las rutas protegidas usan la autenticación central.

**Pendiente:** en la base revisada faltan `nombre_invitado` y `cedula_invitado`
en `graduacion.pases`, y `id_usuario_valida` y `dispositivo_info` en
`graduacion.qr`. Las consultas de los modelos afectados fallan hasta alinear la
base. Antes de cambiarla, compara el esquema y prepara una migración revisable.

### Admisiones (CRM)

El CRM permite registrar prospectos, asignar responsables, guardar seguimientos,
cambiar estados y convertir prospectos en aspirantes. Reutiliza los modelos
compartidos de Core, la sesión de base de datos y la auditoría.

Las rutas requieren JWT, pero todavía no tienen permisos por rol. En algunas
operaciones el cliente envía el identificador del responsable; falta comprobar
que ese empleado corresponda al usuario autenticado.

El SQL original para `admision.crm_seguimiento` está en
`database/admisiones/001_crm_seguimiento.sql`. Se aplicó a la base de desarrollo
local; no lo ejecutes de nuevo sin verificar si la tabla ya existe. Para más
detalles, revisa `database/admisiones/README.md`.

### Pagos a Docentes

Incluye registro de pagos, filtros, estados, historial, aprobaciones manuales,
resumen y avisos de atraso en la API. El importe se ingresa manualmente; los
cálculos de hojas externas todavía no se aplican.

Las rutas requieren JWT; el actor de las escrituras se obtiene del usuario
autenticado y no de un `id_usuario` enviado por el cliente. Las operaciones de
escritura verifican roles institucionales (`administrador`, `coordinador`,
`financiero` y `tesorero`, según la acción). Falta validar las asignaciones con
usuarios de prueba y ejecutar los flujos de escritura en una base PostgreSQL
desechable. Las aprobaciones por correo y alertas automáticas aún no están
implementadas.

La migración `database/pagos_docentes/pagos_docentes_runtime_compat_v2.sql`
corresponde a una actualización ya aplicada en la base de desarrollo revisada.
El SQL `database/pagos_docentes/init.sql` es una inicialización antigua del
esquema `financiera`; no crea por sí solo las tablas operativas actuales.

Las pruebas están organizadas por módulo en `tests/pagos_docentes/`,
`tests/admisiones/` y `tests/vacaciones/`. Pagos a Docentes tiene validaciones
de esquemas y una colección Postman; las instrucciones están en
`tests/pagos_docentes/README.md`. La colección no incluye transiciones exitosas
porque escriben en la base de datos.

Las pruebas enfocadas verifican el paso del actor JWT al servicio y el rechazo
de roles no financieros. La colección Postman debe actualizarse/ejecutarse para
validar 401 y 403 contra una instancia local.

### Vacaciones

Incluye solicitudes, aprobaciones, saldos, cálculos, permisos, feriados,
reservas por período e históricos. Sus rutas requieren un JWT válido y las
pruebas automatizadas cubren reglas de negocio usando SQLite temporal.

**Pendiente:** faltan permisos por rol y verificaciones de propiedad. Algunas
operaciones reciben identificadores de empleado o aprobador desde la solicitud;
el backend debe comprobarlos contra el usuario autenticado. Las pruebas SQLite
no reemplazan una prueba de escritura controlada en PostgreSQL.

Los scripts de `database/vacaciones/` tienen instrucciones en
`database/vacaciones/README.md`. Son específicos de distintas versiones; no
ejecutes toda la carpeta en bloque sobre una instalación existente.

### Celery, Redis y correo

Celery está configurado como base para trabajo futuro. Por ahora,
`app/tasks.py` solo contiene una tarea de prueba; no hay un proceso terminado de
envío de correos ni de alertas automáticas. Falta iniciar y configurar Redis,
definir el flujo de correo y probar worker y scheduler.

## Base de datos y configuración

La aplicación comparte un solo `Base` y una configuración de conexión
asíncrona. Cada módulo usa los esquemas PostgreSQL que le corresponden. La base
de desarrollo revisada no está completa para todas las rutas: faltan cuatro
tablas `docs`, cinco tablas de catálogos académicos `core` y cuatro columnas de
Graduación, detalladas arriba.

Docker Compose monta `database/pagos_docentes/init.sql` al crear un volumen
vacío. Ese archivo solo prepara el esquema antiguo `financiera`; por eso una
base nueva de Docker todavía necesita una inicialización completa, ordenada y
validada para los esquemas actuales. No hay un script único que prepare todo.

Usa `backend/.env` para `DATABASE_URL`, `SECRET_KEY` y otros ajustes locales.
No subas `.env`, contraseñas, tokens ni respaldos de base de datos.

## Ejecutar y probar

Desde la raíz del repositorio, prepara backend, frontend, variables locales y
servicios con:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Para los comandos completos de inicio y los límites actuales de la base,
consulta la sección de preparación en el `README.md` raíz. El entorno Docker
inicializa actualmente un esquema antiguo de pagos y no reemplaza la preparación
de los esquemas operativos actuales.

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La documentación de rutas está en `/api/docs`. Para correr las pruebas:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

En la revisión local pasaron 135 pruebas y la aplicación registró 92 rutas en
OpenAPI. Aún faltan pruebas integrales de autenticación y operaciones de
escritura contra una base PostgreSQL preparada para pruebas.
