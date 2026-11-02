# Frontend ITQ Conecta

Guía de operación y handoff del frontend Angular para el módulo **Pagos a Docentes**.

## Requisitos

- Node.js LTS y npm.
- Backend FastAPI ejecutándose en `http://127.0.0.1:8000`.
- Base PostgreSQL configurada por el backend en `backend/.env`.

En esta máquina Node está instalado por WinGet. Si PowerShell no reconoce `node`/`npm`, abre una terminal nueva o añade temporalmente el directorio de Node a PATH. Para evitar el alias bloqueado por la política de PowerShell, usa `npm.cmd`.

Desde la raíz del repositorio:

```powershell
cd frontend
npm.cmd install
npm.cmd start
```

La aplicación queda en `http://localhost:4200`. El proxy de `frontend/proxy.conf.json` reenvía `/api` al backend en el puerto `8000`. Si ejecutas `ng serve` manualmente, conserva `--proxy-config proxy.conf.json`.

Compilar para producción:

```powershell
npm.cmd run build
```

Compilar en desarrollo directamente con los archivos locales instalados:

```powershell
node node_modules/@angular/cli/bin/ng.js build --configuration development
```

## Estructura principal

- `src/app/app.routes.ts`: ruta principal que muestra el dashboard.
- `src/app/modules/dashboard/dashboard.page.ts`: estado, formularios, filtros y acciones.
- `src/app/modules/dashboard/dashboard.page.html`: interfaz y tablas.
- `src/app/modules/dashboard/dashboard.page.scss`: layout responsive y estilos del módulo.
- `src/app/core/payments.service.ts`: tipos y llamadas HTTP a pagos.
- `src/styles.scss`: tema global Angular Material y variables de color.
- `public/itq-logo.svg`: logo servido como recurso y favicon.
- `proxy.conf.json`: proxy de API para desarrollo.

## Funcionalidades disponibles

1. Resumen: registros totales, listos, por pagar, pagados, montos y mora.
2. Alertas activas de pagos atrasados, con docente, módulo, carrera, periodo, días y umbral.
3. Configuración de umbral por valor y unidad (`DIAS` o `MESES`).
4. Bandeja paginada con filtros por texto, periodo, mes de aprobación, carrera y estado.
5. Formulario de alta de módulo con referencias a docente, periodo y carrera, y selector de modelo Carrera/Validación.
6. Campos detallados de ambos modelos en `datos_modelo` JSONB.
7. Transiciones `EN_CURSO → LISTO_PAGO → APROBADO → PAGADO`; en la interfaz se muestran como Borrador, Listo, Por pagar y Pagado.
8. Registro de monto, observaciones, factura y comprobante.
9. Expansión de detalles por modelo e historial de cambios por registro.
10. Indicadores de carga, error, éxito y catálogos vacíos.

## Integración backend

El cliente HTTP usa `/api/v1/finance/payments`, con estas rutas:

- `GET /`: listado, filtros y paginación.
- `GET /summary`: resumen.
- `GET /alerts`: alertas de pago.
- `GET /settings` y `PUT /settings`: lectura/actualización de umbral.
- `GET /lookups`: docentes, periodos y carreras activas.
- `POST /`: creación de módulo.
- `POST /{id}/ready`: marcar listo y registrar monto.
- `POST /{id}/approval`: registrar aprobación.
- `POST /{id}/paid`: confirmar pago.
- `GET /{id}/history`: historial.

El backend aún tiene una dependencia temporal que recibe `id_usuario` por query para las operaciones que escriben. La interfaz incluye un campo **ID de operador** y lo envía en esas llamadas. Debe ser un ID real de `core.usuarios`; no es un mecanismo de autenticación ni reemplaza el login.

## Datos requeridos

La base actual tiene un periodo de prueba `2026-PRUEBA-ITQ` en `pagos_docentes.periodos`. Para habilitar altas y pruebas end-to-end también se necesitan, mediante el procedimiento autorizado del proyecto:

- Un usuario válido en `core.usuarios` para el actor.
- Una persona y empleado relacionados en `core.personas`/`core.empleados`.
- Una fila de docente en `pagos_docentes.docentes` que apunte al empleado.
- Una carrera activa en `core.catalogos_academicos` con `tipo = 'CARRERA'`.

El frontend solo consulta esas referencias; no las crea. Mientras falten docentes o carreras, el formulario muestra un aviso y no permite completar el alta. No insertes manualmente datos de `core` sin autorización.

## Identidad visual

La interfaz utiliza rojo `#E31E36`, blanco `#FFFFFF` y negro `#050505`, con grises para bordes y fondos de lectura. El archivo `public/itq-logo.svg` es una recreación vectorial simple basada en la imagen compartida (fondo rojo, emblema negro y texto blanco); no es el archivo maestro original. Si se proporciona el logo oficial en SVG/PNG, sustituye ese recurso conservando el nombre o actualiza el `src` del `<img>` y el favicon de `src/index.html`.

## Estado conocido

- El build de Angular terminó correctamente.
- Se probaron `http://127.0.0.1:4200/` y las rutas proxied de resumen/lookups; respondieron `200`.
- La base actualmente devuelve arrays vacíos de docentes/carreras porque las referencias de `core` están vacías.
- Redis/Celery y lectura de correo no forman parte del frontend terminado; el backend todavía no ofrece esas tareas.
- Los cambios de estado y configuración requieren un usuario actor real en `core.usuarios`.
