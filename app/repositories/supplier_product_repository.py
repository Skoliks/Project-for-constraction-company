from sqlalchemy.orm import Session

from app.models.supplier_product import SupplierProduct
from app.schemas.supplier_product_schema import CreateSupplierProduct


class SupplierProductRepository:
    def get_all(self, db: Session):
        return db.query(SupplierProduct).all()

    def get_by_id(self, db: Session, id: int):
        return db.query(SupplierProduct).filter(SupplierProduct.id == id).first()

    def get_by_product_url(self, db: Session, product_url: str):
        return db.query(SupplierProduct).filter(SupplierProduct.product_url == product_url).first()

    def create(self, db: Session, new_data: CreateSupplierProduct):
        new_product = SupplierProduct(**new_data.model_dump())

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return new_product

    def save(self, db: Session, product: SupplierProduct):
        db.commit()
        db.refresh(product)
        return product

    def delete(self, db: Session, product: SupplierProduct):
        db.delete(product)
        db.commit()
        return product


supplier_product_repository = SupplierProductRepository()