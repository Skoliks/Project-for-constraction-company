from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.material_price_repository import material_price_repository
from app.repositories.supplier_product_repository import supplier_product_repository
from app.schemas.material_price_schema import CreateMaterialPrice, UpdateMaterialPrice


class MaterialPriceService:
    def get_all_material_prices(self, db: Session):
        return material_price_repository.get_all(db=db)

    def get_material_price_by_id(self, db: Session, id: int):
        material_price = material_price_repository.get_by_id(db=db, id=id)

        if material_price is None:
            raise HTTPException(status_code=404, detail="Material price not found")

        return material_price

    def create_material_price(self, db: Session, new_data: CreateMaterialPrice):
        supplier_product = supplier_product_repository.get_by_id(
            db=db,
            id=new_data.supplier_product_id
        )

        if supplier_product is None:
            raise HTTPException(status_code=404, detail="Supplier product not found")

        return material_price_repository.create(db=db, new_data=new_data)


material_price_service = MaterialPriceService()