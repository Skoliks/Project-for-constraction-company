from sqlalchemy.orm import Session

from app.models.material_price import MaterialPrice
from app.schemas.material_price_schema import CreateMaterialPrice


class MaterialPriceRepository:
    def get_all(self, db: Session):
        return db.query(MaterialPrice).all()

    def get_by_id(self, db: Session, id: int):
        return db.query(MaterialPrice).filter(MaterialPrice.id == id).first()

    def create(self, db: Session, new_data: CreateMaterialPrice):
        new_price = MaterialPrice(**new_data.model_dump())

        db.add(new_price)
        db.commit()
        db.refresh(new_price)

        return new_price


material_price_repository = MaterialPriceRepository()