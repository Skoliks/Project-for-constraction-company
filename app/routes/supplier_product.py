from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.services.supplier_product_services import supplier_product_service
from app.core.database import get_db
from app.schemas.supplier_product_schema import (
    SupplierProduct,
    CreateSupplierProduct,
    UpdateSupplierProduct
)


router = APIRouter(prefix="supplier_products", tags=["Supplier products"])


@router.get("/", response_model=list[SupplierProduct])
def get_all_supplier_products_route(db: Session = Depends(get_db)):
    return supplier_product_service.get_all_supplier_product(db=db)


@router.get("/{id}", response_model=SupplierProduct)
def get_supplier_product_by_id_route(id: int, db: Session = Depends(get_db)):
    return supplier_product_service.get_supplier_product_by_id(db=db, id=id)


@router.post("/", response_model=SupplierProduct, status_code=201)
def create_supplier_product_route(new_data: CreateSupplierProduct, db: Session = Depends(get_db)):
    return supplier_product_service.create_supplier_product(db=db, new_data=new_data)


@router.patch("/{id}", response_model=SupplierProduct)
def update_supplier_product_route(new_data: UpdateSupplierProduct, id: int, db: Session = Depends(get_db)):
    return supplier_product_service.update_supplier_product(db=db, update_data=new_data)


@router.delete("/{id}", response_model=SupplierProduct)
def delete_supplier_product_route(id: int, db: Session = Depends(get_db)):
    return supplier_product_service.delete_supplier_product(db=db, id=id)