"""
scripts/check_db.py
Diagnóstico rápido de red y PostgreSQL.
Verifica la conectividad y la presencia de los esquemas requeridos del core.
Lee DATABASE_URL desde el archivo .env.
"""
import asyncio
import os
import sys

import asyncpg

# Ruta al archivo .env (raíz del proyecto)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

# Leer DATABASE_URL desde .env
dsn = None
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                val = line.split("=", 1)[1]
                dsn = val.replace("postgresql+asyncpg://", "postgresql://")
                break

if not dsn:
    print("[ERROR] No se encontró DATABASE_URL en .env")
    sys.exit(1)

# Esquemas requeridos del core institucional
REQUIRED_SCHEMAS = ["core", "docs", "graduacion"]

REQUIRED_CORE_TABLES = [
    "personas", "usuarios", "roles", "usuario_rol", "auditoria",
    "permisos", "modulos", "unidades", "estudiantes", "empleados",
    "catalogos_academicos",
]


async def test_conn():
    try:
        conn = await asyncpg.connect(dsn, timeout=5)
        print("[OK]  Conexión a PostgreSQL establecida.")

        # Verificar esquemas
        for schema in REQUIRED_SCHEMAS:
            exists = await conn.fetchval(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = $1",
                schema,
            )
            if exists:
                print(f"[OK]  Esquema '{schema}' presente.")
            else:
                print(f"[FALTA] Esquema '{schema}' NO encontrado. Ejecuta scripts/create_schemas.sql")

        # Verificar tablas del esquema core
        for table in REQUIRED_CORE_TABLES:
            exists = await conn.fetchval(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'core' AND table_name = $1
                """,
                table,
            )
            if exists:
                print(f"[OK]  Tabla 'core.{table}' presente.")
            else:
                print(f"[FALTA] Tabla 'core.{table}' NO encontrada.")

        await conn.close()
        print("\n[RESUMEN] Diagnóstico completado.")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_conn())
