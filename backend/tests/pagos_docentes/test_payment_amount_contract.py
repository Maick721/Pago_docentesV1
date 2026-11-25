from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.database import get_db_session
from app.main import app
from app.modules.pagos_docentes.schemas import PaymentRead, PaymentReady


def test_payment_ready_preserves_exact_decimal_amount() -> None:
    payment = PaymentReady.model_validate({"monto": "0.10"})

    assert payment.monto == Decimal("0.10")
    assert str(payment.monto) == "0.10"


@pytest.mark.parametrize("amount", ["0", "-0.01", "1.001", "10000000000.00"])
def test_payment_ready_rejects_invalid_decimal_boundaries(amount: str) -> None:
    with pytest.raises(ValidationError):
        PaymentReady.model_validate({"monto": amount})


def test_ready_endpoint_allows_unauthenticated_write_and_preserves_decimal() -> None:
    previous_overrides = app.dependency_overrides.copy()

    async def override_db_session():
        yield None

    app.dependency_overrides[get_db_session] = override_db_session
    try:
        payment_response = PaymentRead(
            id=1,
            docente="Ana Docente",
            correo_docente=None,
            modulo="Matemática",
            carrera="Sistemas",
            periodo_academico="2026-1",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 1, 31),
            estado="listo",
            codigo_eva=None,
            modelo="carrera",
            monto=Decimal("1250.10"),
        )
        with patch(
            "app.modules.pagos_docentes.router.servicios.marcar_listo",
            new_callable=AsyncMock,
            return_value=payment_response,
        ) as mark_ready:
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/finance/payments/1/ready",
                    json={"monto": "1250.10"},
                )

        assert response.status_code == 200
        assert response.json()["monto"] == "1250.10"
        mark_ready.assert_awaited_once()
        _, body, _, actor_id = mark_ready.await_args.args
        assert body.monto == Decimal("1250.10")
        assert actor_id is None
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
