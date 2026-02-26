from sqlalchemy import Column, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class Accuracy(Base):
    __tablename__ = "accuracy"

    accuracy_id = Column(Integer, primary_key=True, index=True)
    classified_id = Column(Integer, ForeignKey("classified.classified_id"))

    level0 = Column(Float)
    level1 = Column(Float)
    level2 = Column(Float)
    level3 = Column(Float)
    level4 = Column(Float)
    level5 = Column(Float)

    overall = Column(Float)

    classified = relationship("Classified", back_populates="accuracy")