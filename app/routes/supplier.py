from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.schemas.supplier_schema import CreateSupplier, UpdateSupplier, Supplier
from app.core.database import get_db
from app.services.supplier_services import supplier_services


router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("/", response_model=list[Supplier])
def get_all_suppliers_route(db: Session = Depends(get_db)):
    return supplier_services.get_all_suppliers(db=db)


@router.get("/{id}", response_model=Supplier)
def get_supplier_by_id_route(id: int, db: Session = Depends(get_db)):
    return supplier_services.get_supplier_by_id(db=db, id=id)


@router.post("/", response_model=Supplier, status_code=201)
def create_supplier_route(new_data: CreateSupplier, db: Session = Depends(get_db)):
    return supplier_services.create_supplier(db=db, new_supplier=new_data)


@router.patch("/{id}", response_model=Supplier)
def update_supplier_route(id: int, new_data: UpdateSupplier, db: Session = Depends(get_db)):
    return supplier_services.update_supplier(db=db, update_data=new_data, id=id)


@router.delete("/{id}", response_model=Supplier)
def delete_supplier_route(id: int, db: Session = Depends(get_db)):
    return supplier_services.delete_supplier(db=db, id=id)