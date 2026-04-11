from sqlalchemy.orm import Session

from app.models.material import Material
from app.schemas.material_schema import CreateMaterial


class MaterialRepository:
    
    def get_all(self, db: Session):
        return db.query(Material).all()
    
    def get_by_id(self, db: Session, id: int):
        return db.query(Material).filter(Material.id == id).first()
    
    def get_by_name(self, db: Session, name: str):
        return db.query(Material).filter(Material.name == name).first()
    
    def create(self, db: Session, material_data: CreateMaterial):
        new_data = Material(**material_data.model_dump())
        
        db.add(new_data)
        db.commit()
        db.refresh(new_data)
        
        return new_data
    
    def save(self, db: Session, material: Material):
        db.commit()
        db.refresh(material)
        return material
    
    def delete(self, db: Session, material: Material):
        db.delete(material)
        db.commit()
        return material


material_repository = MaterialRepository()
