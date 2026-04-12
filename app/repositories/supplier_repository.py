from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.schemas.supplier_schema import CreateSupplier


class SupplierRepository:
    
    def get_all(self, db: Session):
        return db.query(Supplier).all()
    
    def get_by_id(self, db: Session, id: int):
        return db.query(Supplier).filter(Supplier.id == id).first()
    
    def get_by_name(self, db: Session, name: str):
        return db.query(Supplier).filter(Supplier.name == name).first()
    
    def get_by_url(self, db: Session, url: str):
        return db.query(Supplier).filter(Supplier.website_url == url).first()
    
    def create(self, db: Session, new_data: CreateSupplier):
        new_suppliers = Supplier(**new_data.model_dump())
        
        db.add(new_suppliers)
        db.commit()
        db.refresh(new_suppliers)
        
        return new_suppliers
    
    def save(self, db: Session, supplier: Supplier):
        db.commit()
        db.refresh(supplier)
        
        return supplier
    
    def delete(self, db: Session, supplier: Supplier):
        db.delete(supplier)
        db.commit()
        
        return supplier


supplier_repository = SupplierRepository()