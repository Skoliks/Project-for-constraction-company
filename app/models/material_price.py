from sqlalchemy import Column, Integer, String,  DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class MaterialPrice(Base):
    __tablename__ = "material_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    
    supplier_product_id = Column(Integer, ForeignKey("supplier_products.id"), nullable=False)
    
    price_rub = Column(Numeric(10, 2), nullable=False)
    old_price_rub = Column(Numeric(10, 2), nullable=True)
    price_per_base_unit_rub = Column(Numeric(10, 2), nullable=True)
    stock_status = Column(String, nullable=True)
    
    observed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    supplier_product = relationship("SupplierProduct", back_populates="prices")