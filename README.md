en # ITQ Conecta

Scaffold inicial para la plataforma modular ITQ Conecta:

- Frontend Angular 22 standalone, Angular Material y Signals.
- Backend FastAPI con Pydantic v2 y SQLAlchemy 2.0 async.
- PostgreSQL 16 con `uuid-ossp` y Redis para Celery, iniciables con Docker Compose.
- Módulo financiero de pagos a docentes en desarrollo.

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
Copy-Item backend\.env.example backend\.env
```

En una terminal, inicia FastAPI:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La estructura inicial de PostgreSQL está en `backend/database/init.sql`.
Docker la ejecuta al inicializar un volumen de base de datos vacío. Si ya
existe un volumen con datos, el script no se vuelve a ejecutar ni modifica esa
base de datos automáticamente.

En otra terminal, inicia Angular:

```powershell
Set-Location frontend
npm start
```

Abre <http://localhost:4200>. Angular reenvía `/api` a FastAPI en el puerto
8000. La documentación interactiva del backend está en
<http://localhost:8000/docs> y el endpoint de salud en
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
institucional. La autenticación/RBAC central aún no está implementada; estos
endpoints son solo para desarrollo local y no deben exponerse en producción.

La documentación detallada del alcance, modelos Excel, base de datos, API,
estado actual y próximos pasos está en
[docs/modulo-pagos-docentes.md](docs/modulo-pagos-docentes.md).

Rutas API principales:

- `GET/POST /api/finance/payments`
- `GET /api/finance/payments/summary`
- `POST /api/finance/payments/{id}/ready`
- `POST /api/finance/payments/{id}/approval`
- `POST /api/finance/payments/{id}/paid`
- `GET /api/finance/payments/{id}/history`
- `GET/PUT /api/finance/payments/settings`

## Estructura

```text
backend/
  app/
    core/       configuración, base de datos, health check y Celery
    middleware/
    modules/    pagos_docentes
    shared/
  database/     script SQL para la estructura inicial de pagos
frontend/
  src/app/
    core/       servicios compartidos
    modules/    pantalla de pagos docentes
    shared/
```
