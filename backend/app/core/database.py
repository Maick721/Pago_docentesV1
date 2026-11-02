from collections.abc import AsyncGenerator, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base común de SQLAlchemy para declarar los modelos de la aplicación."""

    pass


# El motor administra un conjunto reutilizable de conexiones a PostgreSQL.
# pool_pre_ping comprueba una conexión antes de reutilizarla, reduciendo fallos
# por conexiones que el servidor ya cerró.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
# El fabricante de sesiones crea una sesión independiente para cada operación.
# expire_on_commit=False permite leer los valores del objeto tras confirmar
# una transacción sin que SQLAlchemy intente recargarlos automáticamente.
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
SessionLocal = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Entrega una sesión y confirma o revierte la transacción de la petición."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Entrega una sesión sin confirmar automáticamente la transacción.

    FastAPI usa esta función como dependencia de los endpoints. El bloque
    asíncrono libera la sesión incluso si la petición termina con un error.
    """
    async with AsyncSessionLocal() as session:
        yield session
