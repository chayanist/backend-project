from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
class Inspection(Base):
    __tablename__ = "inspection"

    inspection_id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.unit_id"))
    date_time = Column(DateTime)

    unit = relationship("Unit", back_populates="inspections")
    classifieds = relationship("Classified", back_populates="inspection")