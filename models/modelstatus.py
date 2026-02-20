from sqlalchemy import Column, Boolean, Integer, func,DateTime
from sqlalchemy.orm import relationship
from core.database import Base

class ModelStatus(Base):
    __tablename__ = "modelstatus"
    __table_args__ = {"schema": "api"}

    id = Column(Integer, primary_key=True)
    status = Column(Boolean, nullable=False)
    unit_id = Column(Integer, nullable=True)
