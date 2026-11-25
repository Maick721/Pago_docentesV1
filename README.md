# ITQ Conecta — Backend

Este repositorio reúne el backend que he ido desarrollando e integrando para
ITQ Conecta. Está hecho con FastAPI, SQLAlchemy asíncrono y PostgreSQL. Incluye
autenticación y los módulos institucionales de Core, Documentos, Graduación,
Admisiones (CRM), Pagos a Docentes y Vacaciones.

## Módulos y estado actual

| Módulo | Qué incluye | Qué falta o debo mejorar |
|---|---|---|
| Autenticación y Core | Usuarios, roles, permisos, catálogos y acceso con JWT. | Verificar credenciales y asignaciones de roles válidas en cada entorno. |
| Documentos | Rutas y modelos para documentos, archivos, versiones y revisiones. | Crear/verificar sus cuatro tablas en la base de desarrollo y probar el flujo completo de archivos y revisiones. |
| Graduación | Eventos, pases y validación por QR o cédula. | Alinear cuatro columnas que faltan en las tablas `graduacion.pases` y `graduacion.qr`, y volver a probar sus rutas con la base. |
| Admisiones (CRM) | Prospectos, responsables, seguimientos, cambios de estado y conversión a aspirantes. | Añadir permisos por rol y comprobar que el responsable de cada acción corresponda al usuario autenticado. |
| Pagos a Docentes | Registro, filtros, estados de pago, historial, resumen y alertas visibles en la API. | El módulo está temporalmente sin login ni roles; los importes siguen siendo manuales. |
| Vacaciones | Solicitudes, saldos, aprobaciones, permisos, feriados e históricos. | Añadir permisos por rol y comprobar la relación entre el usuario autenticado, los empleados y las solicitudes. |
| Celery y correo | La aplicación Celery está preparada para ampliarse. | Implementar las tareas de alertas/correo y configurar y probar Redis; por ahora las tareas de negocio no están terminadas. |

Estos pendientes son parte del trabajo por completar; no significa que todas las
rutas estén listas para exponerse a usuarios finales.

## Preparar un clon en Windows

Requisitos: Git, Python 3.13, Node.js 24 LTS con npm y Docker Desktop. Desde la
raíz del repositorio, ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

El script crea los archivos `.env` locales sin sobrescribir los existentes,
genera una `SECRET_KEY` aleatoria para el backend, crea `.venv`, instala las
dependencias Python y Angular desde sus manifiestos y levanta PostgreSQL y
Redis mediante Docker Compose. También registra la carpeta del repositorio en
el `PATH` del usuario, para habilitar los comandos de desarrollo en una
terminal nueva. Los archivos `.env` y entornos instalados no se versionan.

Para omitir Docker:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -SkipDocker
```

Después, inicia backend y frontend en terminales separadas:

```powershell
start-backend
```

```powershell
start-frontend
```

Para ejecutar las pruebas del módulo Pagos a Docentes:

```powershell
start-pago
```

La API queda en <http://localhost:8000/api/docs> y Angular en
<http://localhost:4200>. Docker Compose inicia PostgreSQL en el puerto 5433 y
Redis en 6379. **La base de datos aún no queda lista para todos los módulos**:
el SQL montado por Compose corresponde a una versión antigua de Pagos a
Docentes; hay que alinear los esquemas/migraciones actuales antes de usar la
API con PostgreSQL. Revisa la sección de base de datos antes de aplicar SQL.

## Base de datos

Docker Compose usa `backend/database/pagos_docentes/init.sql` al crear un
volumen vacío. Ese archivo conserva una inicialización antigua del esquema
`financiera`; no prepara por sí solo todos los esquemas que necesita el backend.
Los SQL de Vacaciones son versiones específicas y no se deben ejecutar en
bloque sobre una base existente. Revisa las instrucciones de cada módulo y
compara primero la estructura de la base.

En la base de desarrollo que usé para revisar el backend, faltan las cuatro
tablas del esquema `docs` y cinco catálogos académicos de `core`. También faltan
dos columnas en `graduacion.pases` y dos en `graduacion.qr`. La tabla de
seguimientos de Admisiones sí se creó en esa base. Este estado describe esa
instalación local; revisa cualquier otra base por separado antes de aplicar
cambios.

## Pruebas

Desde `backend/`, ejecuta:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

La suite pasó 135 pruebas en la revisión local. También comprobé la carga de la
aplicación y el registro de 92 rutas en OpenAPI. Esto no sustituye pruebas de
escritura y de flujos completos contra una base de datos de prueba.

Para más detalle sobre la estructura y los pendientes, consulta
[backend/README.md](backend/README.md).
