from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.supplier_product_repository import supplier_product_repository
from app.repositories.supplier_repository import supplier_repository
from app.repositories.material_repository import material_repository
from app.schemas.supplier_product_schema import (
    SupplierProduct,
    UpdateSupplierProduct,
    CreateSupplierProduct
)


class SupplierProductService:
    
    def get_all_supplier_product(self, db: Session):
        return supplier_product_repository.get_all(db=db)
    
    def get_supplier_product_by_id(self, db: Session, id: int):
        product = supplier_product_repository.get_by_id(db=db, id=id)
        
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
    
    def create_supplier_product(self, db: Session, new_data: CreateSupplierProduct):
        supplier = supplier_repository.get_by_id(db=db, id=new_data.supplier_id)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        material = material_repository.get_by_id(db=db, id=new_data.material_id)
        if material is None:
            raise HTTPException(status_code=404, detail="Material not found")
        
        product_url = supplier_product_repository.get_by_product_url(db=db, product_url=new_data.product_url)
        if product_url is not None:
            raise HTTPException(status_code=400, detail="Supplier product with this url alredy exist")
        
        return supplier_product_repository.create(db=db, new_data=new_data)
        
    def update_supplier_product(self, db: Session, update_data: UpdateSupplierProduct, id: int):
        product = supplier_product_repository.get_by_id(db=db, id=id)
        
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if update_data.material_id is not None:
            material = material_repository.get_by_id(db=db, id=update_data.material_id)
            if material is None:
                raise HTTPException(status_code=404, detail="Material not found")
            product.material_id = update_data.material_id
            
        if update_data.supplier_id is not None:
            supplier = supplier_repository.get_by_id(db=db, id=update_data.supplier_id)
            if supplier is None:
                raise HTTPException(status_code=404, detail="Supplier not found")
            product.supplier_id = update_data.supplier_id
            
        if update_data.external_name is not None:
            product.external_name = update_data.external_name
        
        if update_data.product_url is not None:
            existing_product = supplier_product_repository.get_by_product_url(db=db, product_url=update_data.product_url)
            if existing_product is not None and existing_product.id != id:
                raise HTTPException(status_code=400, detail="Supplier product with this url alredy exist")
            product.product_url = update_data.product_url
        
        if update_data.sku is not None:
            product.sku = update_data.sku

        if update_data.unit is not None:
            product.unit = update_data.unit

        if update_data.attributes_json is not None:
            product.attributes_json = update_data.attributes_json
        
        return supplier_product_repository.save(db=db, product=product)
    
    def delete_supplier_product(self, db: Session, id: int):
        product = supplier_product_repository.get_by_id(db=db, id=id)
        
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return supplier_product_repository.delete(db=db, product=product)
        

supplier_product_service = SupplierProductService()