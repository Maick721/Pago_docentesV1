# Frontend de ITQ Conecta — Pagos a Docentes

Aplicación Angular standalone que presenta el módulo de Pagos a Docentes y
consume la API FastAPI. El frontend no se conecta directamente a PostgreSQL.

## Requisitos

- Node.js 24 LTS y npm.
- Backend disponible en `http://127.0.0.1:8000`.

## Instalación y ejecución

Desde la raíz del repositorio se puede preparar el entorno completo con:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

O, para instalar solo las dependencias del frontend, desde esta carpeta:

```powershell
npm.cmd ci
```

Inicia Angular desde la raíz:

```powershell
.\start-frontend.cmd
```

O desde `frontend/`:

```powershell
npm.cmd start
```

La aplicación de desarrollo queda normalmente en
<http://localhost:4200>. Para compilar y ejecutar las pruebas configuradas:

```powershell
npm.cmd run build
npm.cmd test
```

## Estructura

```text
frontend/
├── public/                 Recursos estáticos
└── src/
    ├── main.ts             Inicio de Angular
    └── app/
        ├── core/           Servicios compartidos
        ├── app.routes.ts   Ruta principal
        └── modules/
            └── pago_docentes/
                ├── components/
                ├── models/
                ├── services/
                └── pago-docentes.page.*
```

- `pago-docentes.page.ts`: coordina filtros, consultas, resumen, configuración y acciones.
- `components/`: bandeja de pagos, resumen/alertas, formulario, filtro de carreras y acciones.
- `models/`: contratos TypeScript y formularios reactivos.
- `services/payments.service.ts`: llamadas HTTP del módulo.
- `app.routes.ts`: muestra Pagos a Docentes en la ruta raíz.

## Integración con el backend

[proxy.conf.json](proxy.conf.json) reenvía las solicitudes `/api` a
`http://127.0.0.1:8000`. Los endpoints del módulo usan el prefijo
`/api/v1/finance/payments`:

| Método | Ruta | Uso |
|---|---|---|
| GET | `/` | Listado, filtros y paginación |
| GET | `/summary` | Resumen de pagos |
| GET | `/alerts` | Consulta de alertas |
| GET / PUT | `/settings` | Consultar o actualizar el umbral |
| GET | `/lookups` | Docentes, carreras y períodos |
| POST | `/` | Crear registro de módulo |
| POST | `/{id}/ready` | Marcar listo para pago |
| POST | `/{id}/approval` | Registrar aprobación |
| POST | `/{id}/paid` | Confirmar pago |
| GET | `/{id}/history` | Consultar historial |

El formulario registra los modelos Carrera y Validación. La página también
incluye filtros, historial y vistas de resumen.

## Autenticación y datos

Actualmente el módulo de Pagos a Docentes no tiene pantalla de login y sus
endpoints de backend no exigen JWT. No expongas esta aplicación ni la API a una
red pública sin implementar autenticación y autorización. Los catálogos
mostrados en el formulario (docentes, carreras y períodos) deben existir y
estar activos en la base de datos configurada por el backend.

El frontend no incluye pruebas `*.spec.ts` en el estado actual. La
configuración del comando `npm test` existe, pero no sustituye pruebas de
componentes o flujos automatizados.
