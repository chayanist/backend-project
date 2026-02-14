from sqlalchemy import Column, Integer, String, func,DateTime
from sqlalchemy.orm import relationship
from core.database import Base

class Unit(Base):
    __tablename__ = "units"
    __table_args__ = {"schema": "api"}

    unit_id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String, nullable=False)
    create_date = Column(DateTime(timezone=True), server_default=func.now())
    inspections = relationship("Inspection", back_populates="unit", cascade="all, delete")
