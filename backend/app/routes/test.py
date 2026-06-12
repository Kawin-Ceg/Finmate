from fastapi import APIRouter
from sqlalchemy import text

from app.database.database import engine

router = APIRouter()

@router.get("/db-test")
def test_db():

    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT version();")
        )

        version = result.scalar()

    return {
        "database": "connected",
        "version": version
    }