
# Importo uuid para generar identificadores únicos si se necesitan.
# Importo tipos de fecha y hora para registrar fechas en el sistema.
from datetime import date, datetime, timezone

# Decimal sirve para manejar cantidades de dinero con precisión.
from decimal import Decimal

# Importo las herramientas de SQLAlchemy que necesito para crear
# las columnas, las restricciones y los índices de las tablas.
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
    UniqueConstraint,
)

# JSONB permite guardar información estructurada en PostgreSQL.
from sqlalchemy.dialects.postgresql import JSONB

# Mapped y mapped_column sirven para definir las columnas
# utilizando el sistema de tipos de Python.
# relationship permite relacionar unas tablas con otras.
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Importo Base, que es la clase base de los modelos de mi proyecto.
from app.core.database import Base

# Importo las enumeraciones que definen los modelos y estados de pago.
from app.modules.pagos_docentes.enums import PaymentStatus


# Defino el esquema de PostgreSQL donde estarán estas tablas.
SCHEMA = "pagos_docentes"


def utc_now_naive() -> datetime:
    # Obtengo la hora actual en UTC y le quito la zona horaria.
    # Esto se utiliza porque las columnas de este modelo
    # están configuradas como DateTime(timezone=False).
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Teacher(Base):
    __tablename__ = "docentes"
    __table_args__ = (
        UniqueConstraint("id_empleado", name="docentes_id_empleado_key"),
        {"schema": SCHEMA},
    )

    id_docente: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_empleado: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("core.empleados.id_empleado"), nullable=False
    )
    correo_notificacion: Mapped[str | None] = mapped_column(String(150))
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )
    estado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class AcademicPeriod(Base):
    __tablename__ = "periodos"
    __table_args__ = (
        UniqueConstraint("nombre", name="periodos_nombre_key"),
        {"schema": SCHEMA},
    )

    id_periodo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_inicio: Mapped[date | None] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class TeacherModule(Base):
    # Esta clase representa la tabla de módulos de los docentes.
    __tablename__ = "modulos"

    # Aquí defino reglas e índices adicionales para la tabla.
    __table_args__ = (
        CheckConstraint(
            "estado IN ('EN_CURSO', 'LISTO_PAGO', 'APROBADO', 'PAGADO', 'ANULADO')",
            name="modulos_estado_check",
        ),
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_modulo_fechas"),
        {"schema": SCHEMA},
    )

    # Identificador principal del módulo, generado automáticamente.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Identificador del docente relacionado con el módulo.
    # La relación con core.empleados existe en la base de datos,
    # pero no se declara aquí como ForeignKey.
    id_docente: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.docentes.id_docente"), nullable=False
    )
    id_periodo: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.periodos.id_periodo"), nullable=False
    )
    id_carrera: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("core.catalogos_academicos.id_catalogo"), nullable=False
    )
    codigo_eva: Mapped[str | None] = mapped_column(String(50))
    nombre_modulo: Mapped[str] = mapped_column(String(200), nullable=False)
    paralelo: Mapped[str | None] = mapped_column(String(50))
    numero_modulo: Mapped[int | None] = mapped_column(SmallInteger)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    listo_para_pago: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    fecha_listo_pago: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    modelo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CARRERA", server_default=text("'CARRERA'")
    )
    contrato: Mapped[str | None] = mapped_column(String(80))
    datos_modelo: Mapped[dict | None] = mapped_column(JSONB)
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, default=PaymentStatus.EN_CURSO.value,
        server_default=text("'EN_CURSO'"),
    )
    id_usuario_registro: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )

    # Relaciones para consultar aprobaciones, pagos, alertas
    # e historial asociados con este módulo.
    aprobaciones: Mapped[list["Approval"]] = relationship(
        back_populates="modulo"
    )
    pagos: Mapped[list["Payment"]] = relationship(
        back_populates="modulo"
    )
    alertas: Mapped[list["Alert"]] = relationship(
        back_populates="modulo"
    )
    historial: Mapped[list["HistoryEntry"]] = relationship(
        back_populates="modulo"
    )


class Approval(Base):
    # Esta clase representa la tabla de aprobaciones.
    __tablename__ = "aprobaciones"

    __table_args__ = (
        Index("ix_aprobaciones_fecha", "fecha_aprobacion"),
        UniqueConstraint("id_modulo", name="aprobaciones_id_modulo_key"),
        CheckConstraint(
            "estado IN ('VIGENTE', 'ANULADA')", name="aprobaciones_estado_check"
        ),
        CheckConstraint(
            "origen IN ('CORREO', 'MANUAL')", name="aprobaciones_origen_check"
        ),
        {"schema": SCHEMA},
    )

    # Identificador único de cada aprobación.
    id_aprobacion: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Relaciono la aprobación con el módulo correspondiente.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )

    # Registro cuándo se realizó la aprobación.
    fecha_aprobacion: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

    # Indico de dónde provino la aprobación.
    origen: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MANUAL", server_default=text("'MANUAL'")
    )
    id_correo: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.correos_procesados.id_correo")
    )

    # Estado de la aprobación.
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="VIGENTE", server_default=text("'VIGENTE'")
    )
    observacion: Mapped[str | None] = mapped_column(Text)

    # Usuario que realizó la aprobación.
    # La relación con core.usuarios existe en la base de datos,
    # pero no se declara como ForeignKey en este modelo.
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )

    # Permito acceder al módulo desde una aprobación.
    modulo: Mapped[TeacherModule | None] = relationship(
        back_populates="aprobaciones"
    )


class Payment(Base):
    # Esta clase representa los pagos registrados.
    __tablename__ = "pagos"

    __table_args__ = (
        UniqueConstraint("id_modulo", name="pagos_id_modulo_key"),
        CheckConstraint(
            "estado IN ('POR_PAGAR', 'PAGADO')", name="pagos_estado_check"
        ),
        CheckConstraint(
            "estado <> 'PAGADO' OR fecha_pago IS NOT NULL",
            name="ck_pagado_con_fecha",
        ),
        {"schema": SCHEMA},
    )

    # Identificador único del pago.
    id_pago: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Módulo al que corresponde el pago.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )

    # Monto del pago con 12 dígitos en total y 2 decimales.
    # Decimal ayuda a evitar problemas de precisión con el dinero.
    monto: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    # Fecha en la que se realizó el pago.
    fecha_pago: Mapped[date | None] = mapped_column(Date)

    # Estado del pago, por ejemplo, pendiente o pagado,
    # según los valores que utilice el sistema.
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="POR_PAGAR", server_default=text("'POR_PAGAR'")
    )

    # Observaciones adicionales y número de factura.
    observacion: Mapped[str | None] = mapped_column(Text)
    numero_factura: Mapped[str | None] = mapped_column(String(50))
    numero_comprobante: Mapped[str | None] = mapped_column(String(100))
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )

    # Permito acceder al módulo relacionado con el pago.
    modulo: Mapped[TeacherModule | None] = relationship(
        back_populates="pagos"
    )


class Alert(Base):
    # Esta clase representa las alertas del módulo de pagos.
    __tablename__ = "alertas"

    __table_args__ = (
        Index(
            "uq_alerta_activa", "id_modulo", unique=True,
            postgresql_where=text("estado = 'ACTIVA'"),
        ),
        CheckConstraint("tipo = 'PAGO_ATRASADO'", name="alertas_tipo_check"),
        CheckConstraint(
            "estado IN ('ACTIVA', 'RESUELTA')", name="alertas_estado_check"
        ),
        {"schema": SCHEMA},
    )

    # Identificador único de la alerta.
    id_alerta: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Módulo que generó la alerta.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )
    id_configuracion: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.configuracion_umbral.id_configuracion")
    )

    # Fecha y hora en la que se registró la alerta.
    fecha_alerta: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )

    # Tipo de alerta, por ejemplo, pago atrasado.
    tipo: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PAGO_ATRASADO", server_default=text("'PAGO_ATRASADO'")
    )

    # Mensaje que explica el motivo de la alerta.
    mensaje: Mapped[str | None] = mapped_column(Text)

    # Estado actual de la alerta.
    dias_atraso: Mapped[int | None] = mapped_column(Integer)
    correo_enviado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    fecha_envio_correo: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVA", server_default=text("'ACTIVA'")
    )
    fecha_resolucion: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    # Relación que permite consultar el módulo de la alerta.
    modulo: Mapped[TeacherModule | None] = relationship(
        back_populates="alertas"
    )


class HistoryEntry(Base):
    # Esta clase representa el historial de cambios de estado.
    __tablename__ = "historial"

    __table_args__ = (
        # Facilito las consultas del historial por módulo y fecha.
        Index("ix_historial_modulo", "id_modulo", "fecha"),
        {"schema": SCHEMA},
    )

    # Identificador único del registro histórico.
    id_historial: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Módulo al que corresponde el cambio.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )

    # Guardo el estado anterior y el nuevo estado del módulo.
    estado_anterior: Mapped[str | None] = mapped_column(String(50))
    estado_nuevo: Mapped[str] = mapped_column(String(50), nullable=False)

    # Fecha y hora en la que ocurrió el cambio.
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )

    # Explicación del cambio y usuario que lo realizó.
    observacion: Mapped[str | None] = mapped_column(Text)

    # La relación con core.usuarios existe en la BD,
    # pero no se declara como ForeignKey en este modelo.
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )

    # Permito consultar el módulo desde el historial.
    modulo: Mapped[TeacherModule | None] = relationship(
        back_populates="historial"
    )


class PaymentConfig(Base):
    # Esta clase representa la configuración general de los pagos.
    __tablename__ = "configuracion_umbral"
    __table_args__ = (
        Index(
            "uq_umbral_activo", "activo", unique=True,
            postgresql_where=text("activo"),
        ),
        CheckConstraint("valor > 0", name="configuracion_umbral_valor_check"),
        CheckConstraint(
            "unidad IN ('DIAS', 'MESES')",
            name="configuracion_umbral_unidad_check",
        ),
        {"schema": SCHEMA},
    )

    id_configuracion: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    valor: Mapped[int] = mapped_column(Integer, nullable=False)
    unidad: Mapped[str] = mapped_column(String(10), nullable=False)
    correo_notificacion: Mapped[str | None] = mapped_column(String(150))
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )


class ProcessedEmail(Base):
    __tablename__ = "correos_procesados"

    __table_args__ = (
        Index("ix_correos_estado", "estado"),
        UniqueConstraint(
            "message_id", name="correos_procesados_message_id_key"
        ),
        CheckConstraint(
            "estado IN ('PENDIENTE', 'PROCESADO', 'FALLIDO', 'REVISADO_MANUAL')",
            name="correos_procesados_estado_check",
        ),
        {"schema": SCHEMA},
    )

    id_correo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    remitente: Mapped[str | None] = mapped_column(String(150))
    asunto: Mapped[str | None] = mapped_column(String(300))
    fecha_recepcion: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    fecha_procesamiento: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDIENTE", server_default=text("'PENDIENTE'")
    )
    detalle_error: Mapped[str | None] = mapped_column(Text)
    id_modulo: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.modulos.id_modulo")
    )
    id_usuario_revision: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )
    fecha_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
