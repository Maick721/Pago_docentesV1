"""
app/modules/documentos/models/documentos.py
Modelos SQLAlchemy para gestión documental transversal:
  FILE_ASSET, DOCUMENT, DOCUMENT_VERSION, DOCUMENT_REVIEW
Estos modelos son utilizados por múltiples módulos del sistema.
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FileAsset(Base):
    """
    docs.file_assets — Registro físico de archivos almacenados (S3, disco, etc.).
    Representa el binario crudo antes de ser asociado a un documento lógico.
    """
    __tablename__ = "file_assets"
    __table_args__ = {"schema": "docs"}

    id_file_asset: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre_original: Mapped[str] = mapped_column(String(500), nullable=False)
    nombre_almacenado: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    ruta: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    tamano_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fecha_subida: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    subido_por: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # FK a core.usuarios
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relaciones
    versiones: Mapped[list["DocumentVersion"]] = relationship(back_populates="file_asset")

    def __repr__(self) -> str:
        return f"<FileAsset(id={self.id_file_asset}, nombre={self.nombre_original})>"


class Document(Base):
    """
    docs.documents — Entidad lógica de documento con metadatos y ciclo de vida.
    Un documento puede tener múltiples versiones y reseñas de revisión.
    """
    __tablename__ = "documents"
    __table_args__ = {"schema": "docs"}

    id_document: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_documento: Mapped[str] = mapped_column(String(100), nullable=False)
    # Módulo propietario del documento (ej. "GRADUACION", "TITULACION", "VINCULACION")
    modulo_origen: Mapped[str] = mapped_column(String(100), nullable=False)
    # ID del registro al que pertenece en el módulo de origen
    id_entidad_origen: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="borrador")
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    creado_por: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # FK a core.usuarios
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relaciones
    versiones: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", order_by="DocumentVersion.numero_version.desc()"
    )
    revisiones: Mapped[list["DocumentReview"]] = relationship(back_populates="document")

    def __repr__(self) -> str:
        return f"<Document(id={self.id_document}, titulo={self.titulo}, estado={self.estado})>"


class DocumentVersion(Base):
    """
    docs.document_versions — Historial de versiones de un documento.
    Cada versión referencia un FileAsset con el binario real.
    """
    __tablename__ = "document_versions"
    __table_args__ = {"schema": "docs"}

    id_version: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_document: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("docs.documents.id_document", ondelete="CASCADE"), nullable=False
    )
    id_file_asset: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("docs.file_assets.id_file_asset", ondelete="RESTRICT"), nullable=False
    )
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_version_actual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_version: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    creado_por: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # FK a core.usuarios

    # Relaciones
    document: Mapped[Document] = relationship(back_populates="versiones")
    file_asset: Mapped[FileAsset] = relationship(back_populates="versiones")

    def __repr__(self) -> str:
        return f"<DocumentVersion(doc={self.id_document}, v={self.numero_version})>"


class DocumentReview(Base):
    """
    docs.document_reviews — Revisiones y aprobaciones de un documento.
    Permite modelar flujos de trabajo de aprobación multi-etapa.
    """
    __tablename__ = "document_reviews"
    __table_args__ = {"schema": "docs"}

    id_review: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_document: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("docs.documents.id_document", ondelete="CASCADE"), nullable=False
    )
    id_revisor: Mapped[int] = mapped_column(BigInteger, nullable=False)  # FK a core.usuarios
    etapa: Mapped[str] = mapped_column(String(100), nullable=False)
    resultado: Mapped[str] = mapped_column(String(50), nullable=False)  # aprobado, rechazado, pendiente
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_revision: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    document: Mapped[Document] = relationship(back_populates="revisiones")

    def __repr__(self) -> str:
        return f"<DocumentReview(doc={self.id_document}, revisor={self.id_revisor}, resultado={self.resultado})>"
