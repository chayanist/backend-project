from pydantic import BaseModel
from typing import Optional

class UnitCreate(BaseModel):
    unit_name: str

class UnitUpdate(BaseModel):
    unit_name: Optional[str] = None
    date:  Optional[str] = None
