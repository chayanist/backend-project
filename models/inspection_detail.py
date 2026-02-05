from sqlalchemy import Column, Integer, ForeignKey
from core.database import Base

class InspectionDetail(Base):
    __tablename__ = "inspection_detail"

    inspection_id = Column(
        Integer,
        ForeignKey("inspection.inspection_id"),
        primary_key=True
    )
    rice_grain_id = Column(
        Integer,
        ForeignKey("ricegrain.rice_grain_id"),
        primary_key=True
    )
