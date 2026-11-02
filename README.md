en # ITQ Conecta

Scaffold inicial para la plataforma modular ITQ Conecta:

- Frontend Angular 22 standalone, Angular Material y Signals.
- Backend FastAPI con Pydantic v2 y SQLAlchemy 2.0 async.
- PostgreSQL 16 con `uuid-ossp` y Redis para Celery, iniciables con Docker Compose.
- Módulos institucionales de autenticación, Core, documentos, graduación y pagos
  a docentes, reunidos en `backend/`.

La carpeta `itq_backend/` se conserva como respaldo de origen; usa únicamente
`backend/` para ejecutar la aplicación. Su archivo de entorno no se copió.

## Requisitos

- Node.js 22.12 o superior y npm.
- Python 3.12 o superior.
- Docker Desktop con Docker Compose (para PostgreSQL y Redis).

Compose publica PostgreSQL en el puerto `5433` para no interferir con una
instalación local de PostgreSQL que ya utilice el puerto `5432`.

## Inicio local en Windows

Desde la raíz del repositorio, prepara los servicios y el entorno de Python:

```powershell
docker compose up -d
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
if (!(Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
# Configura DATABASE_URL y reemplaza SECRET_KEY por una clave segura en backend\.env.
```

En una terminal, inicia FastAPI:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

El servicio PostgreSQL de Compose publica el puerto `5433`. Ten en cuenta que
`backend/database/init.sql` es un DDL legado del esquema `financiera`, no el
esquema que consume el backend unificado. `backend/scripts/create_schemas.sql`
crea Core, documentos y graduación, pero no crea las tablas actuales de
`pagos_docentes`. Por eso, un volumen nuevo no queda listo para atender todas
las rutas: usa una base ya preparada o completa y valida un script de
inicialización para los cuatro esquemas antes de ejecutarlo. Compose solo
ejecuta los SQL de inicialización al crear un volumen vacío; los existentes no
se modifican automáticamente.

En otra terminal, inicia Angular:

```powershell
Set-Location frontend
npm start
```

Abre <http://localhost:4200>. Angular reenvía `/api` a FastAPI en el puerto
8000. La documentación interactiva del backend está en
<http://localhost:8000/api/docs> y el endpoint de salud en
<http://localhost:8000/api/health>.

Redis y Celery están preparados en la infraestructura, pero el módulo de pagos
actual no requiere ni ejecuta un worker. Las credenciales de desarrollo de
Compose están en `compose.yaml`; cámbialas antes de cualquier despliegue real.

## Módulo financiero: pagos a docentes

La pantalla principal y la API cubren por ahora el registro de pagos por
docente/módulo, filtros por periodo, mes y carrera, flujo borrador → listo →
aprobado → pagado, historial de cambios, resumen financiero y umbral configurable
para alertas de atraso.

El formulario permite elegir el modelo Carrera o Validación y registrar sus
campos académicos, requisitos, seguimiento, factura y datos económicos. Los
importes se capturan manualmente: las fórmulas de los Excel no se ejecutan porque
algunas reglas aún deben confirmarse con Financiero. Las hojas financieras de
los Excel son reportes agregados y no se importan como pagos individuales.

El resumen muestra pagos aprobados sin pagar y pagos listos sin aprobar que
superan el umbral configurado. Los días y contadores se calculan en SQL; por
ahora son indicadores en pantalla y no se envían notificaciones automáticas.
Las aprobaciones son manuales hasta que se confirme el proveedor de correo
institucional. El backend incluye autenticación JWT para los módulos institucionales. El
módulo de pagos todavía conserva un identificador de usuario temporal por
query string y no aplica RBAC; no lo expongas en producción hasta conectarlo
con la autenticación central y sus permisos.

La documentación detallada del alcance, modelos Excel, base de datos, API,
estado actual y próximos pasos está en
[docs/modulo-pagos-docentes.md](docs/modulo-pagos-docentes.md).

Rutas API principales:

- `GET/POST /api/v1/finance/payments`
- `GET /api/v1/finance/payments/summary`
- `POST /api/v1/finance/payments/{id}/ready`
- `POST /api/v1/finance/payments/{id}/approval`
- `POST /api/v1/finance/payments/{id}/paid`
- `GET /api/v1/finance/payments/{id}/history`
- `GET/PUT /api/v1/finance/payments/settings`

## Estructura

```text
backend/
  app/
    core/       configuración, seguridad, base de datos, health check y Celery
    middleware/ excepciones y auditoría
    modules/    core, documentos y pagos_docentes
    models/     modelos de graduación
    routers/    autenticación y graduación
    schemas/    contratos API
  database/     SQL para el esquema de pagos
  scripts/      utilidades de base de datos
frontend/
  src/app/
    core/       servicios compartidos
    modules/    pantalla de pagos docentes
    shared/
```
