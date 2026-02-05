from sqlalchemy import Column, Integer, String
from core.database import Base

class Unit(Base):
    __tablename__ = "units"

    unit_id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String)
