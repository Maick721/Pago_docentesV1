"""
app/modules/documentos/routers/documentos.py
Endpoints de gestión documental transversal (RF-CORE-07).
Exponen FileAsset, Document, DocumentVersion y DocumentReview por la API REST.
Todos los endpoints requieren autenticación JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.documentos.models.documentos import (
    FileAsset,
    Document,
    DocumentVersion,
    DocumentReview,
)
from app.modules.documentos.schemas.documentos import (
    FileAssetOut,
    FileAssetCreate,
    DocumentOut,
    DocumentCreate,
    DocumentUpdate,
    DocumentVersionOut,
    DocumentVersionCreate,
    DocumentReviewOut,
    DocumentReviewCreate,
)
from app.modules.core.models.core import Usuario

router = APIRouter(prefix="/documentos", tags=["Gestión Documental"])


# ─── Helper genérico ───────────────────────────────────────────────────────────

async def _get_or_404(db: AsyncSession, model, entity_id: int, pk_column: str):
    result = await db.execute(select(model).where(getattr(model, pk_column) == entity_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} con id {entity_id} no encontrado.",
        )
    return obj


# ─── FileAsset ─────────────────────────────────────────────────────────────────

@router.get(
    "/file-assets",
    response_model=list[FileAssetOut],
    summary="Listar archivos físicos",
)
async def listar_file_assets(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(FileAsset).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/file-assets",
    response_model=FileAssetOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar archivo físico",
)
async def crear_file_asset(
    body: FileAssetCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = FileAsset(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/file-assets/{asset_id}",
    response_model=FileAssetOut,
    summary="Obtener archivo por ID",
)
async def obtener_file_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, FileAsset, asset_id, "id_file_asset")


@router.delete(
    "/file-assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar archivo",
)
async def desactivar_file_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, FileAsset, asset_id, "id_file_asset")
    obj.activo = False
    await db.commit()


# ─── Document ──────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[DocumentOut],
    summary="Listar documentos lógicos",
)
async def listar_documentos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    modulo_origen: str | None = Query(default=None, description="Filtrar por módulo de origen."),
    estado: str | None = Query(default=None, description="Filtrar por estado del documento."),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    query = select(Document)
    if modulo_origen:
        query = query.where(Document.modulo_origen == modulo_origen)
    if estado:
        query = query.where(Document.estado == estado)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear documento lógico",
)
async def crear_documento(
    body: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = Document(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/{document_id}",
    response_model=DocumentOut,
    summary="Obtener documento por ID",
)
async def obtener_documento(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, Document, document_id, "id_document")


@router.put(
    "/{document_id}",
    response_model=DocumentOut,
    summary="Actualizar documento",
)
async def actualizar_documento(
    document_id: int,
    body: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Document, document_id, "id_document")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar documento",
)
async def eliminar_documento(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Document, document_id, "id_document")
    await db.delete(obj)
    await db.commit()


# ─── DocumentVersion ───────────────────────────────────────────────────────────

@router.get(
    "/{document_id}/versiones",
    response_model=list[DocumentVersionOut],
    summary="Listar versiones de un documento",
)
async def listar_versiones_documento(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    await _get_or_404(db, Document, document_id, "id_document")
    result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.id_document == document_id)
        .order_by(DocumentVersion.numero_version.desc())
    )
    return result.scalars().all()


@router.post(
    "/{document_id}/versiones",
    response_model=DocumentVersionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva versión de documento",
)
async def crear_version_documento(
    document_id: int,
    body: DocumentVersionCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    await _get_or_404(db, Document, document_id, "id_document")
    # Si se marca como actual, desmarcar las demás versiones del documento
    if body.es_version_actual:
        await db.execute(
            __import__("sqlalchemy", fromlist=["update"]).update(DocumentVersion)
            .where(DocumentVersion.id_document == document_id)
            .values(es_version_actual=False)
        )
    obj = DocumentVersion(**body.model_dump(), id_document=document_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


# ─── DocumentReview ────────────────────────────────────────────────────────────

@router.get(
    "/{document_id}/revisiones",
    response_model=list[DocumentReviewOut],
    summary="Listar revisiones de un documento",
)
async def listar_revisiones_documento(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    await _get_or_404(db, Document, document_id, "id_document")
    result = await db.execute(
        select(DocumentReview)
        .where(DocumentReview.id_document == document_id)
        .order_by(DocumentReview.fecha_revision.desc())
    )
    return result.scalars().all()


@router.post(
    "/{document_id}/revisiones",
    response_model=DocumentReviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar revisión/aprobación de documento",
)
async def crear_revision_documento(
    document_id: int,
    body: DocumentReviewCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    await _get_or_404(db, Document, document_id, "id_document")
    obj = DocumentReview(**body.model_dump(), id_document=document_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
