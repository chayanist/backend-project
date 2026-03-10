from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.deps import get_db, get_current_user
from core.response import success
from core.messages import MessageEnum
from models.ricegrain import RiceGrain
from models.classified import Classified
from models.inspection import Inspection
from models.unit import Unit

router = APIRouter(prefix="/home", tags=["home"], dependencies=[Depends(get_current_user)])

COLORS = {
    0: "#f70808ff",
    1: "#6a2de2ff",
    2: "#2de42dff",
    3: "#f7f72cff",
    4: "#049ed1ff",
    5: "#e25069ff",
}

@router.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db)):

    # แก้ไขการนับ: บังคับ JOIN ไปหา Unit เพื่อเช็คว่าหน่วยงานยังมีตัวตนอยู่
    rows = (
        db.query(
            RiceGrain.belly_white_level,
            func.count(RiceGrain.rice_grain_id)
        )
        .join(Classified, RiceGrain.classified_id == Classified.classified_id)
        .join(Inspection, Classified.inspection_id == Inspection.inspection_id)
        .join(Unit, Inspection.unit_id == Unit.unit_id) 
        .group_by(RiceGrain.belly_white_level)
        .all()
    )

    result = []

    # ทำให้ level 0-5 ครบเสมอ
    counts = {lvl: 0 for lvl in range(6)}
    for lvl, cnt in rows:
        counts[lvl] = cnt

    for lvl in range(6):
        result.append({
            "name": f"ท้องข้าวระดับ {lvl}",
            "value": counts[lvl],
            "color": COLORS[lvl]
        })

    total = sum(counts.values())

    return success(
        {
            "chart": result,
            "total": total
        },
        MessageEnum.SUCCESS
    )