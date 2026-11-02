"""
app/modules/documentos/schemas/documentos.py
DTOs Pydantic v2 para gestión documental transversal (RF-CORE-07):
FileAsset, Document, DocumentVersion, DocumentReview.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── FileAsset ─────────────────────────────────────────────────────────────────

class FileAssetBase(BaseModel):
    nombre_original: str = Field(..., min_length=1, max_length=500)
    nombre_almacenado: str = Field(..., min_length=1, max_length=500)
    ruta: str = Field(..., min_length=1)
    mime_type: Optional[str] = Field(None, max_length=150)
    tamano_bytes: Optional[int] = Field(None, ge=0)
    checksum_sha256: Optional[str] = Field(None, max_length=64)
    subido_por: Optional[int] = None
    activo: bool = Field(default=True)


class FileAssetCreate(FileAssetBase):
    """DTO para registrar un archivo físico."""
    pass


class FileAssetOut(FileAssetBase):
    """DTO de respuesta de un archivo."""
    id_file_asset: int
    fecha_subida: datetime

    model_config = {"from_attributes": True}


# ─── Document ──────────────────────────────────────────────────────────────────

class DocumentBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=500)
    descripcion: Optional[str] = None
    tipo_documento: str = Field(..., min_length=1, max_length=100)
    modulo_origen: str = Field(..., min_length=1, max_length=100)
    id_entidad_origen: Optional[int] = None
    estado: str = Field(default="borrador", max_length=50)
    creado_por: Optional[int] = None


class DocumentCreate(DocumentBase):
    """DTO para crear un documento lógico."""
    pass


class DocumentUpdate(BaseModel):
    """DTO para actualizar metadatos de un documento."""
    titulo: Optional[str] = Field(None, min_length=1, max_length=500)
    descripcion: Optional[str] = None
    tipo_documento: Optional[str] = Field(None, min_length=1, max_length=100)
    modulo_origen: Optional[str] = Field(None, min_length=1, max_length=100)
    id_entidad_origen: Optional[int] = None
    estado: Optional[str] = Field(None, max_length=50)


class DocumentOut(DocumentBase):
    """DTO de respuesta de un documento."""
    id_document: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── DocumentVersion ───────────────────────────────────────────────────────────

class DocumentVersionBase(BaseModel):
    id_file_asset: int
    numero_version: int = Field(default=1, ge=1)
    comentario: Optional[str] = None
    es_version_actual: bool = Field(default=True)
    creado_por: Optional[int] = None


class DocumentVersionCreate(DocumentVersionBase):
    """DTO para crear una nueva versión de documento."""
    pass


class DocumentVersionOut(DocumentVersionBase):
    """DTO de respuesta de una versión."""
    id_version: int
    id_document: int
    fecha_version: datetime

    model_config = {"from_attributes": True}


# ─── DocumentReview ────────────────────────────────────────────────────────────

class DocumentReviewBase(BaseModel):
    id_document: int
    id_revisor: int
    etapa: str = Field(..., min_length=1, max_length=100)
    resultado: str = Field(..., min_length=1, max_length=50)  # aprobado, rechazado, pendiente
    comentario: Optional[str] = None


class DocumentReviewCreate(DocumentReviewBase):
    """DTO para registrar una revisión/aprobación."""
    pass


class DocumentReviewOut(DocumentReviewBase):
    """DTO de respuesta de una revisión."""
    id_review: int
    fecha_revision: datetime

    model_config = {"from_attributes": True}
