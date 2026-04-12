from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.schemas.supplier_schema import CreateSupplier, UpdateSupplier
from app.repositories.supplier_repository import supplier_repository


class SupplierServices:
    
    def get_all_suppliers(self, db: Session):
        return supplier_repository.get_all(db=db)
    
    def get_supplier_by_id(self, db: Session, id: int):
        supplier = supplier_repository.get_by_id(db=db, id=id)
        
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return supplier
    
    def create_supplier(self, db: Session, new_supplier: CreateSupplier):
        existing_supplier_by_name = supplier_repository.get_by_name(db=db, name=new_supplier.name)
        existing_supplier_by_url = supplier_repository.get_by_url(db=db, url=new_supplier.website_url)
        
        if existing_supplier_by_url is not None:
            raise HTTPException(status_code=400, detail="Supplier with this url already exists")
        
        if existing_supplier_by_name is not None:
            raise HTTPException(status_code=400, detail="Supplier with this name already exists")
            
        return supplier_repository.create(db=db, new_data=new_supplier)
    
    def update_supplier(self, db: Session, update_data: UpdateSupplier, id: int):
        supplier = supplier_repository.get_by_id(db=db, id=id)
        
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        if update_data.name is not None:
            existing_supplier = supplier_repository.get_by_name(db=db, name=update_data.name)
            
            if existing_supplier is not None and existing_supplier.id != id:
                raise HTTPException(status_code=400, detail="Supplier with this name already exists")
            
            supplier.name = update_data.name
            
        if update_data.city is not None:
            supplier.city = update_data.city
        
        if update_data.website_url is not None:
            existing_supplier = supplier_repository.get_by_url(db=db, url=update_data.website_url)
            
            if existing_supplier is not None and existing_supplier.id != id:
                raise HTTPException(status_code=400, detail="Supplier with this url already exists")
            
            supplier.website_url = update_data.website_url
        
        if update_data.description is not None:
            supplier.description = update_data.description
        
        return supplier_repository.save(db=db, supplier=supplier)
                
    def delete_supplier(self, db: Session, id: int):
        supplier = supplier_repository.get_by_id(db=db, id=id)
        
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return supplier_repository.delete(db=db, supplier=supplier)
        

supplier_services = SupplierServices()