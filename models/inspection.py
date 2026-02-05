from sqlalchemy import Column, Integer, ForeignKey, DateTime
from core.database import Base

class Inspection(Base):
    __tablename__ = "inspection"

    inspection_id = Column(Integer, primary_key=True)
    classified_id = Column(Integer, ForeignKey("classified.classified_id"))
    date_time = Column(DateTime)
