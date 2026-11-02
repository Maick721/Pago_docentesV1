# ITQ Conecta — Backend API

Backend del sistema institucional **ITQ Conecta**, desarrollado con **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL** y **Pydantic v2**.

Para consultar la descripción detallada de cada carpeta, archivo y flujo de trabajo del proyecto, revisa el documento dedicado:
📖 **[ESTRUCTURA_BACKEND.md](./ESTRUCTURA_BACKEND.md)**

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos
* Python 3.13 (mínimo; validado localmente con 3.13.14)
* PostgreSQL 16+

### 2. Instalación de Dependencias
```bash
uv python install 3.13
uv venv --python 3.13
.venv\Scripts\activate
uv pip install -r requirements.txt
```

### 3. Configuración de Base de Datos
Configura `DATABASE_URL` en `.env` para que apunte a la misma instancia y base
que contiene el esquema institucional:
```bash
# DATABASE_URL=postgresql+asyncpg://usuario:contraseña@host:puerto/base
```
El servicio PostgreSQL de `compose.yaml` publica el puerto `5433` y usa por
defecto la base `itqconecta`; verifica que `DATABASE_URL` corresponda a esa
instancia si decides usar Compose.

Aplica primero el DDL institucional oficial que define el esquema
`pagos_docentes` y sus dependencias en `core`. Después, ejecuta esta migración
aditiva para conservar los campos Carrera/Validación que captura la interfaz:
```bash
psql -U postgres -d <base> -f scripts/pagos_docentes.sql
```

Verifica la conexión y esquemas:
```bash
python -m scripts.check_db
```

Siembra el usuario administrador inicial:
```bash
python -m scripts.seed_admin
```

### 4. Ejecutar el Servidor
```bash
uvicorn app.main:app --reload
```
* **Swagger UI:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
* **ReDoc:** [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

Las rutas de pagos docentes están bajo `/api/v1/finance/payments` y requieren
un token Bearer válido del endpoint de autenticación.
