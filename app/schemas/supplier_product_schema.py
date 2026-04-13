from datetime import datetime
from pydantic import BaseModel


class CreateSupplierProduct(BaseModel):
    supplier_id: int
    material_id: int
    external_name: str
    product_url: str
    sku: str | None = None
    unit: str | None = None
    attributes_json: str | None = None


class UpdateSupplierProduct(BaseModel):
    supplier_id: int | None = None
    material_id: int | None = None
    external_name: str | None = None
    product_url: str | None = None
    sku: str | None = None
    unit: str | None = None
    attributes_json: str | None = None


class SupplierProduct(BaseModel):
    id: int
    supplier_id: int
    material_id: int
    external_name: str
    product_url: str
    sku: str | None = None
    unit: str | None = None
    attributes_json: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True