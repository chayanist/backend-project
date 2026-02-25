from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class RiceGrain(Base):
    __tablename__ = "ricegrain"

    rice_grain_id = Column(Integer, primary_key=True, index=True)
    classified_id = Column(Integer, ForeignKey("classified.classified_id"))

    image = Column(String)
    belly_white_level = Column(Integer)
    belly_white_ratio = Column(Float)

    classified = relationship("Classified", back_populates="ricegrains")