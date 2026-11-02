# Estructura del backend unificado

`backend/` es la raíz del código Python. Desde esa carpeta se ejecuta
`uvicorn app.main:app --reload`; la aplicación configura los módulos y rutas
del sistema ITQ Conecta.

```text
backend/
├── app/
│   ├── core/                 Configuración, base de datos, seguridad y Celery
│   ├── middleware/           Auditoría y manejo de errores
│   ├── models/               Modelos ORM del módulo de graduación
│   ├── modules/
│   │   ├── core/             Modelos, schemas y rutas institucionales
│   │   ├── documentos/       Modelos, schemas y rutas de documentos
│   │   └── pagos_docentes/
│   │       ├── models/       Modelos separados por entidad
│   │       └── services/     Reglas de negocio y consultas
│   ├── routers/              Autenticación y graduación
│   ├── schemas/              Contratos de autenticación y graduación
│   └── tasks.py              Tareas Celery
├── database/                 SQL de inicialización y compatibilidad de pagos
├── scripts/                  Utilidades de base de datos y administración
├── .env.example              Plantilla de configuración
└── requirements.txt          Dependencias Python
```

## Componentes compartidos

- `app/main.py` registra autenticación, Core, documentos, graduación y pagos
  bajo `/api/v1`; salud está disponible bajo `/api`.
- `app/core/config.py` carga la configuración del entorno y de `.env`.
  La clave `SECRET_KEY` debe configurarse antes de usar autenticación.
- `app/core/database.py` comparte una sola clase `Base` y un motor SQLAlchemy
  asíncrono para todos los modelos. `get_db` confirma o revierte la sesión de
  la petición; `get_db_session` deja las transacciones explícitas.
- `app/core/security.py` contiene hashing de contraseñas y validación JWT.
- `app/core/celery_app.py` configura Celery; `app/core/celery.py` conserva el
  import de compatibilidad.
- `app/middleware/` contiene la auditoría y los manejadores de excepciones.

## Módulos y rutas

| Módulo | Código | Prefijo |
|---|---|---|
| Autenticación | `app/routers/auth.py` | `/api/v1/auth` |
| Core institucional | `app/modules/core/` | `/api/v1/core` |
| Documentos | `app/modules/documentos/` | `/api/v1/documentos` |
| Graduación | `app/routers/graduacion.py` | `/api/v1/graduacion` |
| Pagos docentes | `app/modules/pagos_docentes/` | `/api/v1/finance/payments` |

El módulo de pagos mantiene sus modelos y servicios propios. Sus referencias a
tablas del esquema `core` reutilizan las tablas ORM canónicas y se protegen
contra escrituras desde esas referencias. La API de pagos aún debe cambiar su
stub de `id_usuario` por la dependencia JWT central y aplicar permisos antes
de exponerse en producción.

## Configuración y ejecución

Usa `backend/.env` para la configuración local y no lo subas al repositorio.
Parte de `.env.example` solo si aún no existe `.env`, y configura al menos
`DATABASE_URL` y una `SECRET_KEY` segura.

```powershell
cd backend
uvicorn app.main:app --reload
```

La documentación OpenAPI está en `/api/docs`; el health check es `/api/health`.
Los scripts de mantenimiento están en `scripts/`, y el SQL inicial del
módulo financiero en `database/`.
