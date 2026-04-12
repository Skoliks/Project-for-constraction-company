from pydantic import BaseModel
from datetime import datetime


class BaseSupplier(BaseModel):
    name: str 
    city: str 
    website_url: str
    description: str | None = None


class CreateSupplier(BaseSupplier):
    pass


class UpdateSupplier(BaseModel):
    name: str | None = None
    city: str | None = None
    website_url: str | None = None
    description: str | None = None


class Supplier(BaseModel):
    id: int
    name: str 
    city: str 
    website_url: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
