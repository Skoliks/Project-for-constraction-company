from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.material_schema import Material, CreateMaterial, UpdateMaterial
from app.services.materials_services import material_services
from app.core.database import get_db


router = APIRouter(prefix="/materials", tags=["Materials"])


@router.get("/", response_model=list[Material])
def get_all_materials_route(db: Session = Depends(get_db)):
    return material_services.get_all_materials(db=db)
    

@router.get("/{id}", response_model=Material)
def get_material_by_id_route(id: int, db: Session = Depends(get_db)):
    return material_services.get_material_by_id(db=db, id=id)


@router.post("/", response_model=Material, status_code=201)
def create_material_route(new_material: CreateMaterial, db: Session = Depends(get_db)):
    return material_services.create_material(db=db, new_data=new_material)


@router.patch("/{id}", response_model=Material)
def update_material_route(id: int, update_data: UpdateMaterial, db: Session = Depends(get_db)):
    return material_services.update_material(db=db, id=id, update_data=update_data)


@router.delete("/{id}", response_model=Material)
def delete_material_route(id: int, db: Session = Depends(get_db)):
    return material_services.delete_material(db=db, id=id)