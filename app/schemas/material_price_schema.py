from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CreateMaterialPrice(BaseModel):
    supplier_product_id: int
    price_rub: Decimal
    old_price_rub: Decimal | None = None
    price_per_base_unit_rub: Decimal | None = None
    stock_status: str | None = None


class MaterialPrice(BaseModel):
    id: int
    supplier_product_id: int
    price_rub: Decimal
    old_price_rub: Decimal | None = None
    price_per_base_unit_rub: Decimal | None = None
    stock_status: str | None = None
    observed_at: datetime

    class Config:
        from_attributes = True