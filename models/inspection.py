from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Inspection(Base):
    __tablename__ = "inspection"
    __table_args__ = {"schema": "api"}

    inspection_id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("api.units.unit_id", ondelete="CASCADE"))
    date_time = Column(TIMESTAMP, server_default=func.now())

    unit = relationship("Unit", back_populates="inspections")
    classified = relationship("Classified", back_populates="inspection", uselist=False, cascade="all, delete")
    ricegrains = relationship("RiceGrain", back_populates="inspection", cascade="all, delete")
