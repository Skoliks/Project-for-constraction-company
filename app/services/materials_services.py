from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.material_repository import material_repository
from app.schemas.material_schema import CreateMaterial, UpdateMaterial


class MaterialServices:
    
    def get_all_materials(self, db: Session):
        return material_repository.get_all(db=db)
    
    def get_material_by_id(self, db: Session, id: int):
        material = material_repository.get_by_id(db=db, id=id)
        
        if material is None:
            raise HTTPException(status_code=404, detail="Material not found")
        
        return material
    
    def create_material(self, db: Session, new_data: CreateMaterial):
        existing_material = material_repository.get_by_name(db=db, name=new_data.name)
        
        if existing_material is not None:
            raise HTTPException(status_code=400, detail="Material with this name already exists")
        
        return material_repository.create(db=db, material_data=new_data)
            
    def update_material(self, db: Session, id: int, update_data: UpdateMaterial):
        material = material_repository.get_by_id(db=db, id=id)
        
        if material is None:
            raise HTTPException(status_code=404, detail="Material not found")
        
        if update_data.name is not None:
            existing_material = material_repository.get_by_name(db=db, name=update_data.name)
            if existing_material is not None:
                raise HTTPException(status_code=400, detail="Material with this name already exists")
            
            material.name = update_data.name    
            
            if update_data.category is not None:
                material.category = update_data.category
            
            if update_data.base_unit is not None:
                material.base_unit = update_data.base_unit
                
            if update_data.description is not None:
                material.description = update_data.description
            
            return material_repository.save(db=db, material=material)
    
    def delete_material(self, db: Session, id: int):
        material = material_repository.get_by_id(db=db, id=id)
        
        if material is None:
            raise HTTPException(status_code=404, detail="Material not found")
        
        return material_repository.delete(db=db, material=material)
            
            
material_services = MaterialServices()
    