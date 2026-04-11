from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db


app = FastAPI()


@app.get("/", tags=["main page"])
def get_main_page():
    return {"message": "hello!"}
