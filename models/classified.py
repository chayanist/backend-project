from sqlalchemy import Column, Integer, ForeignKey, DateTime
from core.database import Base

class Classified(Base):
    __tablename__ = "classified"

    classified_id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.unit_id"))
    level0 = Column(Integer)
    level1 = Column(Integer)
    level2 = Column(Integer)
    level3 = Column(Integer)
    level4 = Column(Integer)
    level5 = Column(Integer)
    total = Column(Integer)
    date_time = Column(DateTime)
