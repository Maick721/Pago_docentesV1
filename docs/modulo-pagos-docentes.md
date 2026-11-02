# Pagos docentes — ITQ Conecta

**Documento de referencia y continuidad · Versión 1.2 · 22 de octubre de 2026**

## Propósito y estado

El módulo registra, valida y da seguimiento a pagos por docente y módulo.
Actualmente es una primera versión para desarrollo local; no transfiere dinero,
no envía correos y no debe exponerse públicamente sin autenticación y permisos.

El backend unificado también incluye autenticación, Core, documentos y
graduación. El módulo de pagos permanece en `backend/app/modules/pagos_docentes/`;
su integración con la autenticación JWT central aún está pendiente. El endpoint
técnico `/api/health` permanece en `app/core/health.py`.

## Tecnología y ejecución

- Angular 22 + Angular Material para la interfaz.
- FastAPI + Pydantic v2 para la API.
- SQLAlchemy 2 async + asyncpg y PostgreSQL 16. La estructura inicial está
  definida en SQL; Alembic no se utiliza por ahora.
- Redis/Celery están preparados, pero el flujo de pagos aún no los utiliza.

Desde la raíz, iniciar servicios:

```powershell
docker compose up -d
```

En una terminal, iniciar FastAPI:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

En otra terminal, iniciar Angular:

```powershell
Set-Location frontend
npm start
```

La aplicación queda en `http://localhost:4200`, la documentación automática
de FastAPI en `http://localhost:8000/api/docs` y el diagnóstico de API en
`http://localhost:8000/api/health`. PostgreSQL del proyecto usa el puerto
`5433`, para no interferir con una instalación local en `5432`.

Docker ejecuta `backend/database/init.sql` únicamente al crear la base en un
volumen vacío. No elimina ni actualiza un volumen existente. Por ahora, si
cambia el esquema, el SQL debe revisarse y aplicarse manualmente; no hay
migraciones automáticas.

## Cómo funciona el backend

1. `app/main.py` crea FastAPI, configura CORS y registra los routers institucionales, pagos y health.
2. `app/core/config.py` carga ajustes del entorno y `backend/.env`.
3. `app/core/database.py` crea el motor SQLAlchemy y entrega una sesión por
   petición.
4. `modules/pagos_docentes/schemas.py` valida las solicitudes con Pydantic,
   incluyendo rango de fechas, correo, importes y modelo elegido.
5. `modules/pagos_docentes/enums.py` centraliza estados y tipos del módulo.
6. `modules/pagos_docentes/models/` define los modelos ORM por responsabilidad y los reexporta desde `__init__.py`.
7. `modules/pagos_docentes/router.py` expone la API y delega operaciones.
8. `modules/pagos_docentes/services/` aplica reglas y consulta PostgreSQL.
9. `database/init.sql` define la estructura inicial de una base nueva.

Al crear un pago, la API valida el registro, guarda sus datos en estado
`borrador` y añade el evento de creación al historial. Los detalles que cambian
entre los modelos Carrera y Validación se validan con esquemas distintos y se
guardan en la columna JSONB `datos_modelo`; los datos comunes se almacenan en
columnas relacionales.

## Datos y flujo

El esquema PostgreSQL `financiera` contiene:

- `pagos_docentes`: docente, módulo, carrera, periodo, fechas, importe, modelo,
  detalle JSONB, estado y fechas del proceso.
- `historial_pagos_docentes`: eventos, detalle, actor y fecha por registro.
- `configuracion_pagos`: umbral de mora configurable (30 días por defecto).

Estados permitidos:

| Estado | Significado |
|---|---|
| `borrador` | Registro en preparación |
| `listo` | Información preparada para aprobación |
| `aprobado` | Aprobado manualmente; pendiente de pago |
| `pagado` | Confirmación manual registrada; no es una transferencia bancaria |

El backend permite solo `borrador → listo → aprobado → pagado`. Cada transición
añade historial. Un umbral configurable (30 días por defecto) alimenta dos
indicadores: aprobados sin pagar desde `aprobado_en` y listos sin aprobar desde
`listo_para_pago_en`. Días y contadores se calculan en PostgreSQL; se muestran
en pantalla, pero no envían notificaciones.

## Modelos Excel

Se analizaron `MODELO CARRERA.xlsx` y `MODELO VALIDACIÓN.xlsx`. La aplicación
permite seleccionar cada modelo y registrar sus campos académicos, requisitos,
seguimiento, datos económicos y factura.

- Carrera incluye, entre otros, PAO, días de clase, PEA, informes, descuentos y
  entrega a Financiero.
- Validación incluye aulas, guía/recursos, notas, portafolio SGA y aprobación
  para pago.
- Las hojas `FINAN...` son reportes agregados; no se deben cargar como pagos
  individuales.
- No se importó el histórico de ninguno de los Excel.
- Los importes son manuales. No se automatizaron fórmulas porque faltan reglas
  confirmadas sobre horas, tarifa, descuentos, retención y total, especialmente
  para Validación.

El registro **DOCENTE DEMOSTRACIÓN (ficticio)** es un ejemplo local del Modelo
Validación, por USD 270. No proviene de los Excel ni representa un pago real.
Su estado verificado es `borrador` y su historial conserva solo la creación.

## API disponible

Base: `/api/v1/finance/payments`

| Método | Ruta | Uso |
|---|---|---|
| GET | `/` | Listar, buscar, filtrar y paginar |
| POST | `/` | Crear un pago |
| GET | `/summary` | Totales y mora |
| GET / PUT | `/settings` | Consultar/actualizar días de mora |
| POST | `/{id}/ready` | Marcar como listo |
| POST | `/{id}/approval` | Guardar aprobación manual |
| POST | `/{id}/paid` | Registrar pago manualmente |
| GET | `/{id}/history` | Consultar historial |

La API ya existe dentro del proyecto: es el backend FastAPI que Angular consume
por `/api`. No hace falta contratar ni crear una API externa para las funciones
actuales. Una integración externa solo sería necesaria para conectar, por
ejemplo, el correo institucional, un sistema académico o un proveedor de pagos.

## Límites y siguientes pasos

- Los endpoints de pagos todavía usan un `id_usuario` temporal por query string; no usan la autenticación JWT central ni aplican roles (RBAC). Tampoco hay edición ni eliminación.
- Aprobación y confirmación de pago son manuales.
- Las alertas son indicadores en pantalla, no notificaciones automáticas.
- No hay correo ni transferencias.
- Las fórmulas deben confirmarse con Financiero antes de automatizarse.
- Antes de producción: definir reglas de aprobación, roles, plazos, pruebas e
  integración institucional; no exponer la API sin autenticación.

## Archivos principales

| Archivo | Responsabilidad |
|---|---|
| `backend/app/main.py` | Crear API y registrar routers |
| `backend/app/core/config.py` | Configuración |
| `backend/app/core/database.py` | Conexión y sesiones SQLAlchemy |
| `backend/app/core/health.py` | Diagnóstico de API |
| `backend/app/modules/pagos_docentes/models/` | Modelos ORM separados por responsabilidad |
| `backend/app/modules/pagos_docentes/enums.py` | Estados y tipos centralizados |
| `backend/app/modules/pagos_docentes/schemas.py` | Validación de datos |
| `backend/app/modules/pagos_docentes/services/` | Reglas de negocio y consultas SQL |
| `backend/app/modules/pagos_docentes/router.py` | Rutas de la API |
| `backend/database/init.sql` | Estructura inicial para una base vacía |
| `frontend/src/app/core/payments.service.ts` | Llamadas HTTP desde Angular |
| `frontend/src/app/modules/dashboard/` | Pantalla, formulario y bandeja |

## Texto para retomar el desarrollo

> Continúo ITQ Conecta, módulo de pagos docentes, en el repositorio actual. Lee
> `docs/modulo-pagos-docentes.md` y revisa el repositorio antes de cambiarlo.
> El backend también incluye Core, documentos, graduación y autenticación; los importes de pagos siguen siendo manuales y
> las reglas Excel necesitan confirmación de Financiero. Conserva los datos
> locales, no importes las hojas agregadas `FINAN...` y valida los cambios con
> build y revisa el SQL si cambia la estructura de la base.
