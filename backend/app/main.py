"""Punto de entrada unificado para la API de ITQ Conecta."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.health import router as health_router
from app.middleware.exceptions import register_exception_handlers
from app.modules.core.routers import core as core_router
from app.modules.documentos.routers import documentos as documentos_router
from app.modules.pagos_docentes.router import router as payments_router
from app.routers import auth, graduacion


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    print(f"{settings.app_name} v{settings.app_version} iniciando...")
    yield
    print(f"{settings.app_name} cerrándose...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

API_V1_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(core_router.router, prefix=API_V1_PREFIX)
app.include_router(documentos_router.router, prefix=API_V1_PREFIX)
app.include_router(graduacion.router, prefix=API_V1_PREFIX)
app.include_router(payments_router, prefix=API_V1_PREFIX)
app.include_router(health_router, prefix="/api")
register_exception_handlers(app)


@app.get("/", tags=["Health"], summary="Health check")
async def root() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/api/docs",
    }


@app.get("/api/v1/health", tags=["Health"], summary="API Health check")
async def health() -> dict[str, str]:
    return {"status": "healthy", "api_version": "v1"}
