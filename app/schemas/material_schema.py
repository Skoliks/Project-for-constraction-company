from pydantic import BaseModel
from datetime import datetime

class MaterialBase(BaseModel):
    name: str
    category: str | None = None
    base_unit: str | None = None
    description: str | None = None


class CreateMaterial(MaterialBase):
    pass

    
class UpdateMaterial(BaseModel):
    name: str | None = None
    category: str | None = None
    base_unit: str | None = None
    description: str | None = None
    

class Material(MaterialBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    