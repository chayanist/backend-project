from sqlalchemy import Column, Integer, String
from core.database import Base

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "api"}

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String)
