from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from core.database import Base

class Unit(Base):
    __tablename__ = "units"

    unit_id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String)
    create_date = Column(DateTime)

    inspections = relationship("Inspection", back_populates="unit", cascade="all, delete")