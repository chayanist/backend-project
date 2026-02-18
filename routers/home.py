from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.deps import get_db
from core.response import success
from core.messages import MessageEnum
from models.ricegrain import RiceGrain

router = APIRouter(prefix="/home", tags=["home"])

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

    rows = (
        db.query(
            RiceGrain.belly_white_level,
            func.count(RiceGrain.rice_grain_id)
        )
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
