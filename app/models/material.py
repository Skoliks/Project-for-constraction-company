from app.core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    base_unit = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, 
                        nullable=True, 
                        default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    
    
    