# ITQ Conecta — Backend API

Backend del sistema institucional **ITQ Conecta**, desarrollado con **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL** y **Pydantic v2**.

Para consultar la descripción detallada de cada carpeta, archivo y flujo de trabajo del proyecto, revisa el documento dedicado:
📖 **[ESTRUCTURA_BACKEND.md](./ESTRUCTURA_BACKEND.md)**

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos
* Python 3.12+
* PostgreSQL 16+

### 2. Instalación de Dependencias
```bash
python -m venv venv
venv\Scripts\activate   # En Windows
pip install -r requirements.txt
```

### 3. Configuración de Base de Datos
Copia el archivo de variables de entorno y ajusta las credenciales:
```bash
# Editar archivo .env con la URL de tu base de datos:
# DATABASE_URL=postgresql+asyncpg://usuario:contraseña@localhost:5432/itq_db
```

Inicializa los esquemas y tablas ejecutando el script DDL:
```bash
psql -U postgres -d itq_db -f scripts/create_schemas.sql
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
