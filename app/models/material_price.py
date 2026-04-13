from sqlalchemy import Column, Integer, String,  DateTime, ForeignKey
from datetime import datetime

from app.core.database import Base


class MaterialPrice:
    __tablename__ = "material_prices"