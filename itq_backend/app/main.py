"""
app/main.py
Punto de entrada principal de la API ITQ Conecta.
Inicializa FastAPI, configura CORS, y registra todos los routers.

Ejecutar con:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.pagos_docentes.router import router as pagos_docentes_router
from app.routers import auth, core, graduacion


# ─── Lifespan (startup/shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    En el startup se pueden inicializar recursos (caches, conexiones, etc.).
    En el shutdown se liberan los recursos.
    """
    # ── Startup ──
    print(f"🚀  {settings.APP_NAME} v{settings.APP_VERSION} iniciando...")
    yield
    # ── Shutdown ──
    print(f"🛑  {settings.APP_NAME} cerrándose...")


# ─── Aplicación FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# ─── CORS ─────────────────────────────────────────────────────────────────────
# En producción, reemplaza ["*"] con los orígenes permitidos específicos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # ← Ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)


# ─── Routers ──────────────────────────────────────────────────────────────────
API_V1_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(core.router, prefix=API_V1_PREFIX)
app.include_router(graduacion.router, prefix=API_V1_PREFIX)
app.include_router(pagos_docentes_router, prefix=API_V1_PREFIX)


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"], summary="Health check")
async def root():
    """Endpoint de verificación de estado del servicio."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }


@app.get("/api/v1/health", tags=["Health"], summary="API Health check")
async def health():
    """Verificación de salud de la API v1."""
    return {"status": "healthy", "api_version": "v1"}
