"""
app/middleware/exceptions.py
Manejador de excepciones global para el backend ITQ Conecta.
Proporciona respuestas JSON estandarizadas para errores de aplicación y base de datos.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger("itq_conecta.core")


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores de excepción globales en la aplicación FastAPI."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
            },
            headers=exc.headers,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error(f"IntegrityError: {exc}")
        return JSONResponse(
            status_code=409,
            content={
                "error": True,
                "message": "Conflicto de integridad en la base de datos.",
                "detail": str(exc.orig) if hasattr(exc, "orig") else str(exc),
                "status_code": 409,
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"SQLAlchemyError: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "Error interno de base de datos.",
                "detail": str(exc),
                "status_code": 500,
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "Error interno del servidor.",
                "detail": str(exc),
                "status_code": 500,
                "path": str(request.url.path),
            },
        )
