from sqlalchemy import Integer, String, DateTime, ForeignKey, Column, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class SupplierProduct(Base):
    __tablename__ = "supplier_products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    external_name = Column(String, nullable=False)
    product_url = Column(String, nullable=False, unique=True)
    sku = Column(String, nullable=True, unique=True)
    unit = Column(String, nullable=True)
    attributes_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    
    supplier = relationship("Supplier", back_populates="products")
    material = relationship("Material", back_populates="supplier_products")