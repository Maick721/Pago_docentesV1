# ITQ Conecta — frontend

Guía de desarrollo y referencia de la aplicación Angular para la gestión de pagos a docentes. Este documento describe la organización vigente del código, las responsabilidades de cada parte y los cambios recientes de estructura.

## Tecnologías

- Angular 22 con componentes standalone.
- TypeScript 6.
- Angular Material y Angular CDK para controles de interfaz.
- Reactive Forms para formularios y validaciones.
- RxJS para peticiones HTTP y actualización de resultados.
- SCSS para estilos globales y estilos encapsulados por componente.

## Cómo iniciar y compilar

Se requiere Node.js LTS, npm y el backend FastAPI ejecutándose en `http://127.0.0.1:8000`.

Desde PowerShell, en la carpeta `frontend`:

```powershell
npm.cmd install
npm.cmd start
```

La aplicación de desarrollo queda en `http://localhost:4200`. El proxy definido en `proxy.conf.json` envía las llamadas `/api` al backend.

Compilación de producción:

```powershell
npm.cmd run build
```

El proyecto tiene un límite de advertencia de 650 kB para el bundle inicial y de 6.6 kB por estilo de componente. El formulario de creación y el formulario de acciones se cargan bajo demanda con `@defer` para reducir el código descargado al abrir el dashboard.

## Estructura del proyecto

```text
frontend/
├── public/
│   ├── favicon.ico
│   └── itq-logo.svg
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   └── api.service.ts
│   │   ├── modules/
│   │   │   └── pago_docentes/
│   │   │       ├── components/
│   │   │       │   ├── career-filter/
│   │   │       │   ├── payment-action/
│   │   │       │   ├── payment-create-form/
│   │   │       │   ├── payment-list/
│   │   │       │   └── payment-overview/
│   │   │       ├── models/
│   │   │       ├── services/
│   │   │       ├── pago-docentes.page.html
│   │   │       ├── pago-docentes.page.scss
│   │   │       └── pago-docentes.page.ts
│   │   ├── app.config.ts
│   │   ├── app.html
│   │   ├── app.routes.ts
│   │   ├── app.scss
│   │   └── app.ts
│   ├── index.html
│   ├── main.ts
│   └── styles.scss
├── angular.json
├── package.json
├── proxy.conf.json
├── tsconfig.app.json
├── tsconfig.json
└── tsconfig.spec.json
```

### Punto de entrada y armazón Angular

- `src/main.ts`: inicia Angular y registra la configuración de la aplicación.
- `src/app/app.ts`, `app.html` y `app.scss`: componente raíz. Su plantilla contiene el `router-outlet`; el contenido de cada ruta se presenta allí.
- `src/app/app.config.ts`: configura el router, el cliente HTTP y los listeners globales de errores.
- `src/app/app.routes.ts`: muestra `PagoDocentesPage` en la ruta principal y redirige rutas desconocidas.
- `src/index.html`: documento base, idioma, título y favicon.
- `src/app/core/api.service.ts`: servicio general para consultar el estado de salud (`/api/health`) del backend. Los endpoints de pagos están en el servicio propio del módulo.

### Módulo `pago_docentes`

La página coordina el dashboard y sus componentes; cada bloque de interfaz tiene una responsabilidad concreta.

- `pago-docentes.page.ts`: estado del dashboard, consultas y recarga de datos, filtros, selección de operador, configuración del umbral, historial, paginación y coordinación de eventos de los componentes.
- `pago-docentes.page.html`: estructura general, encabezado, avisos, configuración de alertas, filtros, ubicación de los formularios y nota de integración.
- `pago-docentes.page.scss`: estilos propios de la página y de su layout principal.

#### Componentes

- `components/payment-overview/`
  - `payment-overview.component.ts`: recibe resumen, alertas y umbral; formatea moneda y fechas para su presentación.
  - `payment-overview.component.html`: muestra las tarjetas del resumen y la tabla de alertas.
  - `payment-overview.component.scss`: estilos y adaptación responsive de ese bloque.

- `components/payment-list/`
  - `payment-list.component.ts`: presenta la lista, traduce estados, calcula las páginas y emite eventos para acciones, expansión de detalles/historial y navegación.
  - `payment-list.component.html`: filtros no incluidos aquí; contiene estados de carga/vacío, tabla, detalles del modelo, historial y paginación.
  - `payment-list.component.scss`: estilos de tabla, estados de pago, detalles y presentación responsive.

- `components/payment-create-form/`
  - `payment-create-form.component.ts`: administra el envío del alta, normaliza valores opcionales, construye el detalle para Carrera o Validación y reporta éxito o error.
  - `payment-create-form.component.html` y `.scss`: formulario principal, referencias académicas, campos compartidos y botones.
  - `academic-validation.component.ts` y `.html`: controles para la validación académica de cada modelo.
  - `payment-values.component.ts` y `.html`: horas, montos, descuentos, retención y datos de factura.
  - `payment-followup.component.ts` y `.html`: fechas de seguimiento, aprobaciones y observaciones.
  - `payment-create-sections.scss`: estilos compartidos por esas tres secciones.
  - Todas las secciones usan el mismo formulario reactivo; separarlas no crea formularios independientes ni cambia el payload.

- `components/career-filter/`
  - `career-filter.component.ts` y `.html`: campo de búsqueda de carrera con sugerencias agrupadas, búsqueda que no distingue tildes y navegación mediante teclado.
  - La selección escribe el nombre en el filtro; cerrar con Escape y seleccionar con flechas/Enter son compatibles con el patrón accesible del control.
  - Sus estilos compartidos están en `src/styles.scss`, porque el panel de sugerencias se despliega junto al campo dentro del dashboard.

- `components/payment-action/`
  - `payment-action.component.ts`, `.html` y `.scss`: captura los datos necesarios para marcar un módulo listo, registrar aprobación manual o confirmar un pago.
  - El componente solicita al padre actualizar la bandeja y el resumen cuando la operación termina.

#### Modelos y servicio

- `models/payment.models.ts`: tipos de pagos, detalles de los modelos Carrera/Validación, catálogos, alertas, resumen, configuración e historial.
- `models/payment-form.ts`: definición tipada de controles y validaciones del alta, incluido el rango de fechas.
- `models/payment-action.ts`: tipo de acción permitido para la transición de un pago.
- `services/payments.service.ts`: acceso HTTP a pagos, resumen, alertas, configuración, catálogos, creación, cambios de estado e historial.

### Estilos, recursos y configuración

- `src/styles.scss`: tema global de Angular Material, colores institucionales y estilos compartidos del selector de carreras.
- `public/itq-logo.svg` y `public/favicon.ico`: recursos estáticos de marca.
- `proxy.conf.json`: proxy de desarrollo para `/api`.
- `angular.json`: configuración de compilación, recursos, estilos y presupuestos de bundle.
- `package.json` y `package-lock.json`: dependencias y scripts de npm.
- `tsconfig.json`, `tsconfig.app.json` y `tsconfig.spec.json`: configuración de TypeScript para la aplicación y pruebas.
- `README.md`: guía breve del frontend; `README_FRONTEND.md`: guía detallada de esta estructura y funcionamiento.

## Cambios realizados en la organización del frontend

1. Se movió la pantalla de pagos desde el dashboard genérico a `src/app/modules/pago_docentes/`, incluyendo plantilla, estilos y acceso a la API. La ruta principal ahora apunta a este módulo.
2. Se agruparon los contratos TypeScript en `models/` y las llamadas a pagos en `services/`, evitando que el archivo de servicio mezcle transporte HTTP con todos los tipos de dominio.
3. La lógica de creación se trasladó al componente de alta; la página principal ya no arma manualmente el payload completo.
4. El formulario largo se dividió por propósito en validación académica, valores del pago y seguimiento. Las secciones reciben el mismo formulario reactivo y conservan sus nombres de control.
5. Se separó el resumen y las alertas (`payment-overview`) de la bandeja con tabla, historial y paginación (`payment-list`).
6. El filtro de carrera y las transiciones de estado tienen componentes dedicados; la página recibe sus eventos y conserva la coordinación de datos.
7. El formulario de alta y el de acciones usan carga diferida, manteniendo las tareas menos frecuentes fuera de la carga inicial.
8. El lookup de carreras incluye el grupo/área del catálogo académico para ordenar las opciones por su área formativa.
9. Se mantiene la validación del rango de fechas, la apertura del calendario en los campos de fecha y la búsqueda de carreras compatible con tildes y teclado.
10. Se conserva la apariencia responsive y se actualizaron los estilos globales del selector de carreras y la documentación de la estructura.

## Funcionalidades

- Resumen de registros, pagos pendientes, montos pagados y atrasos.
- Alertas según el umbral configurado en días o meses.
- Filtros de bandeja por texto, periodo, mes de inicio, carrera y estado; el filtro de carrera ofrece sugerencias agrupadas.
- Las carreras se presentan agrupadas por área, usando la descripción del catálogo devuelta por el backend.
- Registro de módulos en los modelos Carrera o Validación, con sus datos académicos, de pago y seguimiento.
- Estados de pago con acciones para marcar listo, registrar aprobación manual y confirmar pago.
- Vista expandible de detalles del modelo e historial de eventos.
- Mensajes de carga, error, éxito y disponibilidad de referencias académicas.

## Integración con el backend

El servicio utiliza `/api/v1/finance/payments`:

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/` | Listado filtrado y paginado |
| `GET` | `/summary` | Resumen del dashboard |
| `GET` | `/alerts` | Alertas activas |
| `GET`, `PUT` | `/settings` | Consultar y guardar el umbral |
| `GET` | `/lookups` | Docentes, periodos y carreras activas |
| `POST` | `/` | Crear módulo |
| `POST` | `/{id}/ready` | Marcar listo y registrar monto |
| `POST` | `/{id}/approval` | Registrar aprobación |
| `POST` | `/{id}/paid` | Confirmar pago |
| `GET` | `/{id}/history` | Consultar historial |

Temporalmente las operaciones de escritura envían `id_usuario` como parámetro de consulta, de acuerdo con el backend actual. La interfaz pide un ID de operador existente en `core.usuarios`; este dato no sustituye un mecanismo de autenticación.

Los lookups se consultan desde el backend. El frontend no crea personas, docentes, periodos ni carreras. El alta requiere referencias válidas que el API devuelva en esos catálogos.

## Verificación y límites

- `npm run build` compila la aplicación y verifica las plantillas y tipos de Angular.
- No hay archivos `*.spec.ts` de pruebas unitarias dentro de `src` actualmente.
- La aprobación automática por correo no está conectada; el flujo disponible registra la aprobación manualmente.
- Los servicios de correo, Redis y Celery no son responsabilidades del frontend.
- El logo SVG incluido es un recurso provisional, no el archivo maestro oficial del ITQ.
