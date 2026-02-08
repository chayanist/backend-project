from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    role_id: int
    status: bool


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    password: Optional[str] = None
    status:Optional[bool] = None

class UserResponse(BaseModel):
    user_id: int
    username: str
    full_name: str
    email: str
    role_id: int
