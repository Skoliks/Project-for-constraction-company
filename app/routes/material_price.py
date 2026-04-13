from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.material_price_schema import (
    MaterialPrice,
    CreateMaterialPrice,
)
from app.services.material_price_services import material_price_service

router = APIRouter(prefix="/material-prices", tags=["Material Prices"])


@router.get("/", response_model=list[MaterialPrice])
def get_all_material_prices_route(db: Session = Depends(get_db)):
    return material_price_service.get_all_material_prices(db=db)


@router.get("/{id}", response_model=MaterialPrice)
def get_material_price_by_id_route(id: int, db: Session = Depends(get_db)):
    return material_price_service.get_material_price_by_id(db=db, id=id)


@router.post("/", response_model=MaterialPrice, status_code=201)
def create_material_price_route(new_data: CreateMaterialPrice, db: Session = Depends(get_db)):
    return material_price_service.create_material_price(db=db, new_data=new_data)
