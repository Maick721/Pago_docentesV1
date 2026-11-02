from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.pagos_docentes.enums import PaymentModel, PaymentStatus

SCHEMA = "pagos_docentes"


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Teacher(Base):
    __tablename__ = "docentes"
    __table_args__ = {"schema": SCHEMA}

    id_docente: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    # La FK a core.empleados(id_empleado) existe en PostgreSQL.
    id_empleado: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    correo_notificacion: Mapped[str | None] = mapped_column(String(150))
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("NOW()")
    )
    estado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("TRUE")
    )

    modulos: Mapped[list["TeacherModule"]] = relationship(back_populates="docente")


class AcademicPeriod(Base):
    __tablename__ = "periodos"
    __table_args__ = {"schema": SCHEMA}

    id_periodo: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    fecha_inicio: Mapped[date | None] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("TRUE")
    )

    modulos: Mapped[list["TeacherModule"]] = relationship(back_populates="periodo")


class TeacherModule(Base):
    __tablename__ = "modulos"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('EN_CURSO', 'LISTO_PAGO', 'APROBADO', 'PAGADO', 'ANULADO')",
            name="ck_modulos_estado",
        ),
        CheckConstraint(
            "fecha_fin >= fecha_inicio",
            name="ck_modulo_fechas",
        ),
        CheckConstraint(
            "modelo IN ('CARRERA', 'VALIDACION')",
            name="ck_modulos_modelo",
        ),
        Index("ix_modulos_docente", "id_docente"),
        Index("ix_modulos_periodo", "id_periodo"),
        Index("ix_modulos_carrera", "id_carrera"),
        {"schema": SCHEMA},
    )

    id_modulo: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    id_docente: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.docentes.id_docente"),
        nullable=False,
    )
    id_periodo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.periodos.id_periodo"),
        nullable=False,
    )
    # La FK a core.catalogos_academicos(id_catalogo) existe en PostgreSQL.
    id_carrera: Mapped[int] = mapped_column(BigInteger, nullable=False)
    codigo_eva: Mapped[str | None] = mapped_column(String(50))
    nombre_modulo: Mapped[str] = mapped_column(String(200), nullable=False)
    paralelo: Mapped[str | None] = mapped_column(String(50))
    numero_modulo: Mapped[int | None] = mapped_column(SmallInteger)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    listo_para_pago: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE")
    )
    fecha_listo_pago: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False)
    )
    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PaymentStatus.EN_CURSO.value,
        server_default=text("'EN_CURSO'"),
    )
    # La FK a core.usuarios(id_usuario) existe en PostgreSQL.
    id_usuario_registro: Mapped[int | None] = mapped_column(BigInteger)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("NOW()")
    )
    # Columnas aditivas para conservar los detalles del formulario vigente.
    modelo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PaymentModel.CARRERA.value,
        server_default=text("'CARRERA'"),
    )
    contrato: Mapped[str | None] = mapped_column(String(80))
    datos_modelo: Mapped[dict | None] = mapped_column(JSONB)

    docente: Mapped[Teacher] = relationship(back_populates="modulos")
    periodo: Mapped[AcademicPeriod] = relationship(back_populates="modulos")
    aprobacion: Mapped["Approval | None"] = relationship(
        back_populates="modulo", uselist=False
    )
    pago: Mapped["Payment | None"] = relationship(
        back_populates="modulo", uselist=False
    )
    alertas: Mapped[list["Alert"]] = relationship(back_populates="modulo")
    historial: Mapped[list["HistoryEntry"]] = relationship(back_populates="modulo")


class ProcessedEmail(Base):
    __tablename__ = "correos_procesados"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('PENDIENTE', 'PROCESADO', 'FALLIDO', 'REVISADO_MANUAL')"
        ),
        Index("ix_correos_estado", "estado"),
        {"schema": SCHEMA},
    )

    id_correo: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    message_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    remitente: Mapped[str | None] = mapped_column(String(150))
    asunto: Mapped[str | None] = mapped_column(String(300))
    fecha_recepcion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False)
    )
    fecha_procesamiento: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("NOW()")
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDIENTE", server_default=text("'PENDIENTE'")
    )
    detalle_error: Mapped[str | None] = mapped_column(Text)
    id_modulo: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.modulos.id_modulo")
    )
    # La FK a core.usuarios(id_usuario) existe en PostgreSQL.
    id_usuario_revision: Mapped[int | None] = mapped_column(BigInteger)
    fecha_revision: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False)
    )


class Approval(Base):
    __tablename__ = "aprobaciones"
    __table_args__ = (
        CheckConstraint("origen IN ('CORREO', 'MANUAL')"),
        CheckConstraint("estado IN ('VIGENTE', 'ANULADA')"),
        Index("ix_aprobaciones_fecha", "fecha_aprobacion"),
        {"schema": SCHEMA},
    )

    id_aprobacion: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
        unique=True,
    )
    fecha_aprobacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    origen: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MANUAL", server_default=text("'MANUAL'")
    )
    id_correo: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.correos_procesados.id_correo")
    )
    # La FK a core.usuarios(id_usuario) existe en PostgreSQL.
    id_usuario: Mapped[int | None] = mapped_column(BigInteger)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="VIGENTE", server_default=text("'VIGENTE'")
    )
    observacion: Mapped[str | None] = mapped_column(Text)

    modulo: Mapped[TeacherModule] = relationship(back_populates="aprobacion")


class Payment(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('POR_PAGAR', 'PAGADO')",
            name="ck_pagos_estado",
        ),
        CheckConstraint(
            "estado <> 'PAGADO' OR fecha_pago IS NOT NULL",
            name="ck_pagado_con_fecha",
        ),
        Index("ix_pagos_estado", "estado"),
        {"schema": SCHEMA},
    )

    id_pago: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
        unique=True,
    )
    monto: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    fecha_pago: Mapped[date | None] = mapped_column(Date)
    numero_factura: Mapped[str | None] = mapped_column(String(50))
    numero_comprobante: Mapped[str | None] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="POR_PAGAR", server_default=text("'POR_PAGAR'")
    )
    # La FK a core.usuarios(id_usuario) existe en PostgreSQL.
    id_usuario: Mapped[int | None] = mapped_column(BigInteger)
    observacion: Mapped[str | None] = mapped_column(Text)

    modulo: Mapped[TeacherModule] = relationship(back_populates="pago")


class PaymentConfig(Base):
    __tablename__ = "configuracion_umbral"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_umbral_valor"),
        CheckConstraint("unidad IN ('DIAS', 'MESES')", name="ck_umbral_unidad"),
        Index(
            "uq_umbral_activo",
            "activo",
            unique=True,
            postgresql_where=text("activo"),
        ),
        {"schema": SCHEMA},
    )

    id_configuracion: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    valor: Mapped[int] = mapped_column(Integer, nullable=False)
    unidad: Mapped[str] = mapped_column(String(10), nullable=False)
    correo_notificacion: Mapped[str | None] = mapped_column(String(150))
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("TRUE")
    )
    # La FK a core.usuarios(id_usuario) existe en PostgreSQL.
    id_usuario: Mapped[int | None] = mapped_column(BigInteger)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("NOW()")
    )


class Alert(Base):
    __tablename__ = "alertas"
    __table_args__ = (
        CheckConstraint("tipo IN ('PAGO_ATRASADO')", name="ck_alertas_tipo"),
        CheckConstraint(
            "estado IN ('ACTIVA', 'RESUELTA')",
            name="ck_alertas_estado",
        ),
        Index(
            "uq_alerta_activa",
            "id_modulo",
            unique=True,
            postgresql_where=text("estado = 'ACTIVA'"),
        ),
        {"schema": SCHEMA},
    )

    id_alerta: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )
    id_configuracion: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.configuracion_umbral.id_configuracion")
    )
    fecha_alerta: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("NOW()")
    )
    tipo: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PAGO_ATRASADO", server_default=text("'PAGO_ATRASADO'")
    )
    dias_atraso: Mapped[int | None] = mapped_column(Integer)
    mensaje: Mapped[str | None] = mapped_column(Text)
    correo_enviado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE")
    )
    fecha_envio_correo: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False)
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVA", server_default=text("'ACTIVA'")
    )
    fecha_resolucion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False)
    )

    modulo: Mapped[TeacherModule] = relationship(back_populates="alertas")


class HistoryEntry(Base):
    __tablename__ = "historial"
    __table_args__ = (
        Index("ix_historial_modulo", "id_modulo"),
        {"schema": SCHEMA},
    )

    id_historial: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )
    estado_anterior: Mapped[str | None] = mapped_column(String(50))
    estado_nuevo: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("NOW()")
    )
    # La FK a core.usuarios(id_usuario) existe en PostgreSQL.
    id_usuario: Mapped[int | None] = mapped_column(BigInteger)
    observacion: Mapped[str | None] = mapped_column(Text)

    modulo: Mapped[TeacherModule] = relationship(back_populates="historial")
