from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class Classified(Base):
    __tablename__ = "classified"
    __table_args__ = {"schema": "api"}

    classified_id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("api.inspection.inspection_id", ondelete="CASCADE"), unique=True)

    level0 = Column(Integer, default=0)
    level1 = Column(Integer, default=0)
    level2 = Column(Integer, default=0)
    level3 = Column(Integer, default=0)
    level4 = Column(Integer, default=0)
    level5 = Column(Integer, default=0)
    total = Column(Integer, default=0)

    inspection = relationship("Inspection", back_populates="classified")
