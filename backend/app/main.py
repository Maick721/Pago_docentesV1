from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.health import router as health_router
from app.modules.pagos_docentes.router import router as payments_router

# Este archivo es el punto de entrada que Uvicorn carga para iniciar el backend.
# Aquí se crea la aplicación FastAPI y se conectan los routers disponibles;
# la lógica concreta de pagos se mantiene en su propio módulo.
app = FastAPI(title=settings.app_name, version="0.1.0")

# CORS controla desde qué origen del navegador se permite llamar a esta API.
# El origen del frontend se configura por entorno para no dejarlo fijo aquí.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health conserva /api; los pagos siguen el prefijo /api/v1 que consume Angular.
app.include_router(health_router, prefix="/api")
app.include_router(payments_router, prefix="/api/v1")
