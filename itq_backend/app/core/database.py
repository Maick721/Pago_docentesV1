"""
app/core/database.py
Motor asíncrono de base de datos con SQLAlchemy 2.0 y asyncpg.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ─── Motor asíncrono ──────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,          # Cambiar a True para ver SQL en desarrollo
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ─── Fábrica de sesiones asíncronas ──────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ─── Clase base declarativa ──────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy."""
    pass


# ─── Dependencia inyectable para FastAPI ─────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador asíncrono que provee una sesión de base de datos por request.
    Se garantiza el cierre correcto de la sesión al finalizar.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
