from sqlalchemy import Column, Integer, ForeignKey, String, Float
from sqlalchemy.orm import relationship
from core.database import Base

class RiceGrain(Base):
    __tablename__ = "ricegrain"
    __table_args__ = {"schema": "api"}

    rice_grain_id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("api.inspection.inspection_id", ondelete="CASCADE"))

    image = Column(String)
    belly_white_level = Column(Integer)
    belly_white_ratio = Column(Float)

    inspection = relationship("Inspection", back_populates="ricegrains")
