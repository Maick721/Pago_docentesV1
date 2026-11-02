from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger, CheckConstraint, Date, ForeignKey, Numeric, String, Text,
    UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA
from .modulos import TeacherModule


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
