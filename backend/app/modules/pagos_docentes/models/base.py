from datetime import datetime, timezone

from app.core.database import Base


SCHEMA = "pagos_docentes"


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
