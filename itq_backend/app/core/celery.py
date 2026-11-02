"""
app/core/celery.py
Configuración de Celery para tareas asíncronas del core:
envío de correos, notificaciones internas, parsing de PDFs, etc.
Requerido por el stack tecnológico del documento de requerimientos.
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "itq_conecta_core",
    broker=settings.CELERY_BROKER_URL or "redis://localhost:6379/0",
    backend=settings.CELERY_RESULT_BACKEND or "redis://localhost:6379/0",
    include=["app.core.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Guayaquil",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
)

__all__ = ["celery_app"]
