from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import engine


router = APIRouter(prefix="/health", tags=["BD test"])


@router.get("/")
def health_check():
    return {"status": "ok"}


@router.get("/health/db")
def db_check():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()

        return {
            "status": "ok",
            "database": "connected",
            "result": value
        }

    except Exception as e:
        return {
            "status": "error",
            "database": "not connected",
            "error": str(e)
        }