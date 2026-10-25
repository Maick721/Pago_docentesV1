import asyncio
import os
import asyncpg

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
dsn = "postgresql://postgres:itqconecta2026@localhost:5432/itq_conecta"

if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                val = line.strip().split("=", 1)[1]
                dsn = val.replace("postgresql+asyncpg://", "postgresql://")
                break


async def test_conn():
    try:
        conn = await asyncpg.connect(dsn, timeout=5)
        await conn.close()
        print("[OK]  Conexion establecida.")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")


if __name__ == "__main__":
    asyncio.run(test_conn())


