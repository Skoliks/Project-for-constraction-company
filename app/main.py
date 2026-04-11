from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routes.health import router as health_router


app = FastAPI()
app.include_router(health_router)


@app.get("/", tags=["main page"])
def get_main_page():
    return {"message": "hello!"}
