# ITQ Conecta — frontend

Guía de desarrollo, estructura, cambios recientes y pendientes del frontend de **Pagos a Docentes**.

## Tecnologías y comandos

- Angular 22 con componentes standalone y TypeScript 6.
- Angular Material/CDK para controles; Reactive Forms para formularios.
- RxJS para llamadas y flujos de actualización; SCSS para estilos.
- Backend FastAPI en `http://127.0.0.1:8000`; base PostgreSQL configurada por el backend.

Desde PowerShell, en la carpeta `frontend`:

```powershell
npm.cmd install
npm.cmd start
npm.cmd run build
```

La aplicación de desarrollo queda en `http://localhost:4200`. `proxy.conf.json` reenvía `/api` al backend. El comando de build usa la configuración de producción por defecto.

El presupuesto de Angular advierte por encima de 650 kB para el bundle inicial y 6.6 kB por estilo de componente. El formulario de registro y las acciones se cargan bajo demanda con `@defer`.

## Estructura completa

```text
frontend/
├── .editorconfig
├── .gitignore
├── .prettierrc
├── .vscode/
│   ├── extensions.json
│   ├── launch.json
│   ├── mcp.json
│   └── tasks.json
├── README.md
├── README_FRONTEND.md
├── angular.json
├── package.json
├── package-lock.json
├── proxy.conf.json
├── public/
│   ├── favicon.ico
│   └── itq-logo.svg
├── src/
│   ├── index.html
│   ├── main.ts
│   ├── styles.scss
│   └── app/
│       ├── app.config.ts
│       ├── app.html
│       ├── app.routes.ts
│       ├── app.scss
│       ├── app.ts
│       ├── core/
│       │   └── api.service.ts
│       └── modules/
│           └── pago_docentes/
│               ├── pago-docentes.page.html
│               ├── pago-docentes.page.scss
│               ├── pago-docentes.page.ts
│               ├── components/
│               │   ├── career-filter/
│               │   │   ├── career-filter.component.html
│               │   │   └── career-filter.component.ts
│               │   ├── payment-action/
│               │   │   ├── payment-action.component.html
│               │   │   ├── payment-action.component.scss
│               │   │   └── payment-action.component.ts
│               │   ├── payment-create-form/
│               │   │   ├── academic-validation.component.html
│               │   │   ├── academic-validation.component.ts
│               │   │   ├── payment-create-form.component.html
│               │   │   ├── payment-create-form.component.scss
│               │   │   ├── payment-create-form.component.ts
│               │   │   ├── payment-create-sections.scss
│               │   │   ├── payment-followup.component.html
│               │   │   ├── payment-followup.component.ts
│               │   │   ├── payment-values.component.html
│               │   │   └── payment-values.component.ts
│               │   ├── payment-list/
│               │   │   ├── payment-list.component.html
│               │   │   ├── payment-list.component.scss
│               │   │   └── payment-list.component.ts
│               │   └── payment-overview/
│               │       ├── payment-overview.component.html
│               │       ├── payment-overview.component.scss
│               │       └── payment-overview.component.ts
│               ├── models/
│               │   ├── payment-action.ts
│               │   ├── payment-form.ts
│               │   └── payment.models.ts
│               └── services/
│                   └── payments.service.ts
├── tsconfig.app.json
├── tsconfig.json
└── tsconfig.spec.json
```

`node_modules/`, `dist/` y `.angular/` son directorios generados localmente y no forman parte del código fuente versionado.

## Descripción de la estructura

### Inicio y aplicación Angular

- `src/main.ts`: arranca Angular con la configuración de `app.config.ts`.
- `src/index.html`: documento HTML base, idioma, título y favicon.
- `src/app/app.ts`, `app.html`, `app.scss`: componente raíz. Su `router-outlet` muestra la página activa.
- `src/app/app.config.ts`: registra el router, HttpClient y listeners globales de errores.
- `src/app/app.routes.ts`: muestra `PagoDocentesPage` en la ruta principal y redirige rutas desconocidas.
- `src/app/core/api.service.ts`: servicio general para consultar `/api/health`; no contiene los endpoints de pagos.

### Módulo `src/app/modules/pago_docentes/`

La página raíz reúne el estado de pantalla y coordina componentes con responsabilidades acotadas:

- `pago-docentes.page.ts`: consulta y refresca datos, procesa filtros, configura el umbral, coordina historial, expansión y paginación, y recibe los eventos de los componentes.
- `pago-docentes.page.html`: estructura del dashboard, encabezado, mensajes, configuración, filtros, formularios diferidos y nota informativa.
- `pago-docentes.page.scss`: layout, estilos generales del dashboard y ajustes responsive.

#### Componentes (`components/`)

- `career-filter/`: filtro de carrera con sugerencias agrupadas por área. Permite buscar sin distinguir tildes y navegar con flechas, Enter y Escape. Su presentación desplegable tiene estilos globales en `src/styles.scss`.
- `payment-overview/`: tarjetas de resumen y tabla de alertas. Recibe los datos y presenta moneda y fechas.
- `payment-list/`: bandeja de pagos, estados de carga/vacío, tabla, acciones disponibles por estado, detalles, historial y paginación. Emite eventos; la página coordina las actualizaciones.
- `payment-action/`: formularios de transición para marcar listo, registrar aprobación manual y confirmar pago. Al terminar comunica éxito o error a la página.
- `payment-create-form/`: alta de módulos. El componente principal valida y normaliza campos, arma el payload de Carrera o Validación y envía la solicitud.
  - `academic-validation.*`: controles de validación académica.
  - `payment-values.*`: horas, montos, descuentos, retención y datos de factura.
  - `payment-followup.*`: fechas y datos de seguimiento/aprobación.
  - `payment-create-sections.scss`: estilos compartidos por esas secciones.
  - Las subsecciones usan el mismo formulario reactivo; no son formularios separados.

En los nombres anteriores, `.*` representa los archivos `.ts` y/o `.html` enumerados en el árbol.

#### Modelos y servicios

- `models/payment.models.ts`: contratos TypeScript para pagos, modelos Carrera/Validación, catálogos, alertas, resumen, configuración e historial.
- `models/payment-form.ts`: definición del formulario reactivo de alta y validación del rango de fechas.
- `models/payment-action.ts`: conjunto de transiciones de pago que admite la interfaz.
- `services/payments.service.ts`: peticiones HTTP de listado, resumen, alertas, configuración, lookups, creación, cambios de estado e historial.

### Estilos, recursos y configuración

- `src/styles.scss`: tema global de Angular Material, colores institucionales y sugerencias de carrera.
- `public/`: logo y favicon servidos como recursos estáticos. El SVG actual es provisional, no el archivo maestro oficial.
- `proxy.conf.json`: configuración de proxy local para las peticiones `/api`.
- `angular.json`: build, recursos, estilos y presupuestos de bundle.
- `package.json` / `package-lock.json`: scripts y versiones fijadas de dependencias.
- `tsconfig*.json`: opciones de TypeScript de la aplicación y pruebas.
- `.editorconfig`, `.prettierrc`, `.gitignore`: formato, convenciones del editor y archivos ignorados.
- `.vscode/`: extensiones sugeridas, depuración, configuración MCP y tareas del workspace.
- `README.md`: instrucciones breves; `README_FRONTEND.md`: referencia detallada del frontend.

## Trabajo realizado hoy — 2 de noviembre de 2026

1. Se movió la pantalla financiera desde el dashboard genérico a `modules/pago_docentes/` y se actualizó la ruta principal.
2. Se trasladó el servicio HTTP al módulo y se separaron los tipos de dominio en `models/`.
3. Se dividió la lógica y la interfaz por tareas: resumen/alertas, bandeja, filtro de carreras, alta y acciones de pago.
4. Se subdividió el alta en validación académica, valores del pago y seguimiento, conservando el formulario reactivo compartido, validaciones y payload.
5. Se mejoraron los campos de fecha con el calendario nativo del navegador, botones visibles para abrirlo, validación que impide una fecha final anterior a la inicial y limpieza de textos de ayuda que ocupaban espacio.
6. Se ajustó la presentación responsive del dashboard y el formulario, incluyendo separación entre acciones y mejor distribución de campos.
7. Se incorporaron al catálogo las carreras indicadas: 15 opciones regulares y 6 opciones de Validación. El registro de prueba conserva una carrera desactivada para que no aparezca en nuevas selecciones.
8. Se prepararon datos ficticios locales para probar el flujo y se creó desde la pantalla el registro `Módulo de prueba visual`. Se verificó que apareciera en la API y en la bandeja; queda como registro de prueba, sin pago ni aprobación.
9. Se agregó la agrupación de carreras por área: el lookup devuelve el grupo/descripción desde el catálogo académico.
10. El filtro de carrera ofrece sugerencias seleccionables, búsqueda que ignora tildes y control por teclado.
11. Se usó `@defer` para diferir el alta y las acciones y reducir el peso del bundle inicial.
12. Se actualizó esta guía para incluir estructura, responsabilidades, funcionamiento, problemas y pendientes.

## Errores y hallazgos

### Encontrados y corregidos

- **Bundle sobre el presupuesto:** al añadir las vistas sin carga diferida, el bundle inicial llegó a 655.55 kB y Angular advirtió que superaba el límite de 650 kB. Se difirió la carga del alta y las acciones; el build final midió 637.43 kB y no mostró advertencias.
- **Autocomplete de Angular Material demasiado pesado:** una primera alternativa para las sugerencias elevó el tamaño del bundle. Se reemplazó por una lista de sugerencias propia y liviana, manteniendo agrupación y accesibilidad por teclado.
- **Selector de fecha de Angular Material demasiado pesado:** para evitar elevar el bundle se mantuvo el control nativo `type="date"` y se añadieron botones explícitos para abrir el calendario del navegador.
- **Listado de pagos devolvía HTTP 500:** la base local no tenía algunas columnas que el servicio de pagos esperaba. Se respaldó la base, se aplicó `backend/database/pagos_docentes_runtime_compat_v2.sql` y el endpoint del listado volvió a responder HTTP 200.
- **Código concentrado en archivos grandes:** la página/controlador y las plantillas reunían responsabilidades distintas. Se separaron por secciones y componentes para facilitar su mantenimiento sin reescribir los flujos funcionales.

### Pendientes funcionales o de entorno

- La interfaz aún no cuenta con inicio de sesión integrado: para operaciones de escritura pide un `id_usuario` existente y lo envía por query al backend. Es una dependencia temporal, no autenticación.
- La variable `SECRET_KEY` del backend sigue pendiente de configuración en `backend/.env`; el inicio de sesión real no se ha verificado. Configurarla localmente sin compartirla ni subirla al repositorio.
- El lookup del formulario usa carreras de tipo `CARRERA`. El catálogo puede incluir opciones de Validación, pero todavía no hay un selector independiente para escoger entre el catálogo regular y el de validación.
- La aprobación automática por correo no está conectada; la aprobación disponible es manual. Redis/Celery y lectura de correo tampoco son funciones completadas del frontend/backend actual.
- El alta depende de docentes, carreras y periodos reales devueltos por el backend. El frontend no crea esos datos de referencia.
- Hay un registro de prueba vinculado a “Carrera de prueba UI”. La carrera de prueba se desactivó para ocultarla en nuevos formularios, no se borró porque el registro existente la referencia.
- Los datos ficticios y `Módulo de prueba visual` pertenecen al entorno local de pruebas; antes de una salida a producción deben retirarse o reemplazarse siguiendo el procedimiento de datos del proyecto.
- No se encontraron archivos `*.spec.ts` dentro de `src`; faltan pruebas unitarias automatizadas para componentes y flujos.
- El recurso `public/itq-logo.svg` es provisional; se debe sustituir por el logo oficial cuando esté disponible.

## Mejoras recomendadas

Prioridad sugerida para siguientes tareas:

1. Integrar autenticación/autorización real y dejar de pedir manualmente el ID del operador.
2. Acordar con el área académica cómo elegir carreras regulares frente a opciones de Validación; implementar el lookup y selector correspondiente.
3. Agregar pruebas para creación de ambos modelos, fechas, filtro de carreras, transiciones de estado y errores de API.
4. Probar los flujos completos con catálogos y usuarios reales de prueba autorizados, incluidos permisos y errores del backend.
5. Revisar manejo y presentación de errores de carga independientes para resumen, alertas, settings y lookups; confirmar comportamiento de reintento.
6. Reemplazar el logo provisional por el recurso oficial.
7. Mantener el presupuesto del bundle y los estilos al incorporar funcionalidades nuevas; revisar oportunidades de reducir más los estilos globales y archivos extensos sin dividir componentes artificialmente.

## Funcionalidades disponibles

- Resumen de registros, pagos pendientes, montos pagados y atrasos.
- Alertas según un umbral configurable en días o meses.
- Bandeja paginada y filtros por texto, periodo, mes de inicio, carrera y estado.
- Sugerencias de carrera agrupadas por área, sensibles a búsqueda sin tildes y navegación por teclado.
- Alta de módulos de Carrera o Validación, con datos académicos, de pago y seguimiento.
- Acciones para marcar listo, registrar aprobación manual y confirmar pago.
- Expansión de detalles e historial de cambios.
- Estados de carga, vacío, éxito, error y ausencia de referencias requeridas.

## Integración con backend

El servicio utiliza `/api/v1/finance/payments`:

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/` | Listado filtrado y paginado |
| `GET` | `/summary` | Resumen |
| `GET` | `/alerts` | Alertas |
| `GET`, `PUT` | `/settings` | Consultar/guardar umbral |
| `GET` | `/lookups` | Docentes, periodos y carreras |
| `POST` | `/` | Crear módulo |
| `POST` | `/{id}/ready` | Marcar listo y registrar monto |
| `POST` | `/{id}/approval` | Registrar aprobación |
| `POST` | `/{id}/paid` | Confirmar pago |
| `GET` | `/{id}/history` | Consultar historial |

El proxy de desarrollo usa `http://127.0.0.1:8000`. Actualmente las operaciones de escritura requieren el `id_usuario` indicado por el backend.

## Verificación actual

- `npm run build`: verificado correctamente tras los cambios; bundle inicial de 637.43 kB, debajo del presupuesto de 650 kB y sin advertencias.
- Se verificó en el navegador la pantalla principal y la apertura/renderizado de las secciones del formulario.
- `git diff --check`: sin errores de whitespace al publicar el commit de organización/documentación.
- No hay pruebas unitarias frontend automatizadas actualmente.
