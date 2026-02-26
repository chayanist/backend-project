from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class Classified(Base):
    __tablename__ = "classified"

    classified_id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspection.inspection_id"))

    level0 = Column(Integer)
    level1 = Column(Integer)
    level2 = Column(Integer)
    level3 = Column(Integer)
    level4 = Column(Integer)
    level5 = Column(Integer)
    total = Column(Integer)
    round_number = Column(Integer)
    date_time = Column(DateTime)

    inspection = relationship("Inspection", back_populates="classifieds")
    ricegrains = relationship("RiceGrain", back_populates="classified")
    accuracy = relationship(
        "Accuracy",
        back_populates="classified",
        uselist=False,
        cascade="all, delete"
    )