from fastapi import FastAPI

from app.core.database import engine, Base
from app.routes.health import router as health_router
from app.routes.material import router as material_router
from app.routes.supplier import router as supplier_router
from app.routes.supplier_product import router as product_router
from app.routes.material_price import router as price_router
from app.routes.parsers import router as parser_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(health_router)
app.include_router(material_router)
app.include_router(supplier_router)
app.include_router(product_router)
app.include_router(price_router)
app.include_router(parser_router)


@app.get("/", tags=["main page"])
def get_main_page():
    return {"message": "hello!"}
