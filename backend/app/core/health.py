from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Devuelve un indicador simple de que FastAPI está atendiendo peticiones.

    Esta ruta sirve para comprobar disponibilidad del proceso API. No realiza
    una consulta a PostgreSQL, por lo que un resultado correcto no demuestra
    que la base de datos también esté disponible.
    """
    return {"status": "ok", "service": "itq-conecta-api"}
