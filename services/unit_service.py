# services/unit_service.py
from sqlalchemy.orm import Session
from models.classified import Classified
from models.unit import Unit
from models.inspection import Inspection
from models.ricegrain import RiceGrain
from sqlalchemy import func, case
from datetime import datetime, time
import shutil
import os
from pathlib import Path

# กำหนด Path หลักของโปรเจกต์ (ปรับให้ตรงกับเครื่องของคุณ)
BASE_DIR = Path(__file__).resolve().parents[1] 
STORE_DIR = BASE_DIR / "ai_engine" / "store"

def create_unit(db: Session, unit_name: str):
    unit = Unit(unit_name=unit_name)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def get_unit(db: Session, unit_id: int):
    return db.query(Unit).filter(Unit.unit_id == unit_id).first()

from sqlalchemy import func, case
from datetime import datetime

def get_unit_report(
    db: Session,
    unit_id: int,
    min_date: datetime | None = None,
    max_date: datetime | None = None,
):
    query = (
        db.query(
            Inspection.inspection_id,
            Inspection.date_time,

            func.sum(Classified.level5).label("lv5"),
            func.sum(Classified.level4).label("lv4"),
            func.sum(Classified.level3).label("lv3"),
            func.sum(Classified.level2).label("lv2"),
            func.sum(Classified.level1).label("lv1"),
            func.sum(Classified.level0).label("lv0"),
            func.sum(Classified.total).label("total"),
        )
        .join(Classified, Classified.inspection_id == Inspection.inspection_id)
        .filter(Inspection.unit_id == unit_id)
        .group_by(Inspection.inspection_id, Inspection.date_time)
    )

    # ✅ filter date
    if min_date:
        query = query.filter(Inspection.date_time >= min_date)

    if max_date:
        query = query.filter(Inspection.date_time <= max_date)

    rows = (
        query.group_by(Inspection.inspection_id, Inspection.date_time)
        .order_by(Inspection.inspection_id.desc())
        .all()
    )

    # ===== list per inspection =====
    data = [
        {
            "id": r.inspection_id,
            "date": r.date_time.strftime("%d/%m/%Y"),
            "lv5": int(r.lv5 or 0),
            "lv4": int(r.lv4 or 0),
            "lv3": int(r.lv3 or 0),
            "lv2": int(r.lv2 or 0),
            "lv1": int(r.lv1 or 0),
            "lv0": int(r.lv0 or 0),
            "total": int(r.total or 0),
        }
        for r in rows
    ]

    # ===== summary รวมทั้งหมด =====
    summary = {
        "lv5": sum(d["lv5"] for d in data),
        "lv4": sum(d["lv4"] for d in data),
        "lv3": sum(d["lv3"] for d in data),
        "lv2": sum(d["lv2"] for d in data),
        "lv1": sum(d["lv1"] for d in data),
        "lv0": sum(d["lv0"] for d in data),
        "total": sum(d["total"] for d in data),
    }

    return {
        "summary": summary,
        "items": data
    }

def get_inspection_summary(db: Session, inspection_id: int):
    """
    Summarize inspection data grouped by belly_white_ratio into 6 categories:
    - 0: ratio = 0
    - 1-10%: 0 < ratio <= 10
    - 11-24%: 10 < ratio <= 24
    - 25-50%: 24 < ratio <= 50
    - 51-75%: 50 < ratio <= 75
    - 75%+: ratio > 75
    
    Each category (except 0) is further divided into 5 sub-ranges for detailed visualization.
    Note: belly_white_ratio is stored as percentage (0-100), not decimal (0-1)
    """
    
    row = (
        db.query(
            func.count(RiceGrain.rice_grain_id).label("total"),
            
            # Group 0: ratio = 0
            func.sum(case((RiceGrain.belly_white_ratio == 0, 1), else_=0)).label("group_0"),
            
            # Group 1-10% divided into 5 sub-bars
            func.sum(case((
                (RiceGrain.belly_white_ratio > 0) & 
                (RiceGrain.belly_white_ratio <= 2), 1
            ), else_=0)).label("group_1_1"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 2) & 
                (RiceGrain.belly_white_ratio <= 4), 1
            ), else_=0)).label("group_1_2"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 4) & 
                (RiceGrain.belly_white_ratio <= 6), 1
            ), else_=0)).label("group_1_3"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 6) & 
                (RiceGrain.belly_white_ratio <= 8), 1
            ), else_=0)).label("group_1_4"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 8) & 
                (RiceGrain.belly_white_ratio <= 10), 1
            ), else_=0)).label("group_1_5"),
            
            # Group 11-24% divided into 5 sub-bars
            func.sum(case((
                (RiceGrain.belly_white_ratio > 10) & 
                (RiceGrain.belly_white_ratio <= 13.3), 1
            ), else_=0)).label("group_2_1"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 13.3) & 
                (RiceGrain.belly_white_ratio <= 16.6), 1
            ), else_=0)).label("group_2_2"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 16.6) & 
                (RiceGrain.belly_white_ratio <= 19.9), 1
            ), else_=0)).label("group_2_3"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 19.9) & 
                (RiceGrain.belly_white_ratio <= 21.7), 1
            ), else_=0)).label("group_2_4"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 21.7) & 
                (RiceGrain.belly_white_ratio <= 24), 1
            ), else_=0)).label("group_2_5"),
            
            # Group 25-50% divided into 5 sub-bars
            func.sum(case((
                (RiceGrain.belly_white_ratio > 24) & 
                (RiceGrain.belly_white_ratio <= 30), 1
            ), else_=0)).label("group_3_1"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 30) & 
                (RiceGrain.belly_white_ratio <= 35), 1
            ), else_=0)).label("group_3_2"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 35) & 
                (RiceGrain.belly_white_ratio <= 40), 1
            ), else_=0)).label("group_3_3"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 40) & 
                (RiceGrain.belly_white_ratio <= 45), 1
            ), else_=0)).label("group_3_4"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 45) & 
                (RiceGrain.belly_white_ratio <= 50), 1
            ), else_=0)).label("group_3_5"),
            
            # Group 51-75% divided into 5 sub-bars
            func.sum(case((
                (RiceGrain.belly_white_ratio > 50) & 
                (RiceGrain.belly_white_ratio <= 59), 1
            ), else_=0)).label("group_4_1"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 59) & 
                (RiceGrain.belly_white_ratio <= 63), 1
            ), else_=0)).label("group_4_2"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 63) & 
                (RiceGrain.belly_white_ratio <= 67), 1
            ), else_=0)).label("group_4_3"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 67) & 
                (RiceGrain.belly_white_ratio <= 71), 1
            ), else_=0)).label("group_4_4"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 71) & 
                (RiceGrain.belly_white_ratio <= 75), 1
            ), else_=0)).label("group_4_5"),
            
            # Group 75%+ divided into 5 sub-bars
            func.sum(case((
                (RiceGrain.belly_white_ratio > 75) & 
                (RiceGrain.belly_white_ratio <= 82), 1
            ), else_=0)).label("group_5_1"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 82) & 
                (RiceGrain.belly_white_ratio <= 87), 1
            ), else_=0)).label("group_5_2"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 87) & 
                (RiceGrain.belly_white_ratio <= 91), 1
            ), else_=0)).label("group_5_3"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 91) & 
                (RiceGrain.belly_white_ratio <= 96), 1
            ), else_=0)).label("group_5_4"),
            func.sum(case((
                (RiceGrain.belly_white_ratio > 96), 1
            ), else_=0)).label("group_5_5"),
        )
        .join(Classified, RiceGrain.classified_id == Classified.classified_id)
        .filter(Classified.inspection_id == inspection_id)
        .one()
    )

    # Calculate group totals
    group_0 = int(row.group_0 or 0)
    
    group_1_bars = [
        int(row.group_1_1 or 0),
        int(row.group_1_2 or 0),
        int(row.group_1_3 or 0),
        int(row.group_1_4 or 0),
        int(row.group_1_5 or 0),
    ]
    group_1_total = sum(group_1_bars)
    
    group_2_bars = [
        int(row.group_2_1 or 0),
        int(row.group_2_2 or 0),
        int(row.group_2_3 or 0),
        int(row.group_2_4 or 0),
        int(row.group_2_5 or 0),
    ]
    group_2_total = sum(group_2_bars)
    
    group_3_bars = [
        int(row.group_3_1 or 0),
        int(row.group_3_2 or 0),
        int(row.group_3_3 or 0),
        int(row.group_3_4 or 0),
        int(row.group_3_5 or 0),
    ]
    group_3_total = sum(group_3_bars)
    
    group_4_bars = [
        int(row.group_4_1 or 0),
        int(row.group_4_2 or 0),
        int(row.group_4_3 or 0),
        int(row.group_4_4 or 0),
        int(row.group_4_5 or 0),
    ]
    group_4_total = sum(group_4_bars)
    
    group_5_bars = [
        int(row.group_5_1 or 0),
        int(row.group_5_2 or 0),
        int(row.group_5_3 or 0),
        int(row.group_5_4 or 0),
        int(row.group_5_5 or 0),
    ]
    group_5_total = sum(group_5_bars)

    return {
        "summary": {
            "0": {
                "label": "0%",
                "count": group_0,
                "percentage": round((group_0 / int(row.total or 1)) * 100, 2)
            },
            "1": {
                "label": "1-10%",
                "count": group_1_total,
                "percentage": round((group_1_total / int(row.total or 1)) * 100, 2),
                "bars": group_1_bars,
                "labels": ["0-2%", "2-4%", "4-6%", "6-8%", "8-10%"]
            },
            "2": {
                "label": "11-24%",
                "count": group_2_total,
                "percentage": round((group_2_total / int(row.total or 1)) * 100, 2),
                "bars": group_2_bars,
                "labels": ["11-13.3%", "13.3-16.6%", "16.6-19.9%", "19.9-21.7%", "21.7-24%"]
            },
            "3": {
                "label": "25-50%",
                "count": group_3_total,
                "percentage": round((group_3_total / int(row.total or 1)) * 100, 2),
                "bars": group_3_bars,
                "labels": ["25-30%", "30-35%", "35-40%", "40-45%", "45-50%"]
            },
            "4": {
                "label": "51-75%",
                "count": group_4_total,
                "percentage": round((group_4_total / int(row.total or 1)) * 100, 2),
                "bars": group_4_bars,
                "labels": ["50-59%", "59-63%", "63-67%", "67-71%", "71-75%"]
            },
            "5": {
                "label": "75%+",
                "count": group_5_total,
                "percentage": round((group_5_total / int(row.total or 1)) * 100, 2),
                "bars": group_5_bars,
                "labels": ["75-82%", "82-87%", "87-91%", "91-96%", "96-100%"]
            }
        },
        "total": int(row.total or 0),
    }


def convert_path_to_url(file_path: str):
    base_path = "/home/ricebelly/riceBellyProjectV4/ai_engine/store/"
    return file_path.replace(base_path, "/images/")

def get_unit_summary_all(db: Session, unit_id: int):
    # ดึง belly_white_ratio ทั้งหมดของ unit
    rows = (
        db.query(RiceGrain.belly_white_ratio)
        .join(Classified, RiceGrain.classified_id == Classified.classified_id)
        .join(Inspection, Classified.inspection_id == Inspection.inspection_id)
        .filter(Inspection.unit_id == unit_id)
        .all()
    )

    ratios = [r[0] for r in rows if r[0] is not None]

    summary = build_summary(ratios)
    print("UNIT:", unit_id)
    print("ROWS:", len(rows))
    return {
        "summary": summary,
        "total": len(ratios),
    }

def build_summary(ratios: list[float]):
    ranges = {
        "0": {"label": "0%", "min": 0, "max": 0},
        "1": {"label": "1-10%", "min": 0.01, "max": 10},
        "2": {"label": "11-24%", "min": 11, "max": 24},
        "3": {"label": "25-50%", "min": 25, "max": 50},
        "4": {"label": "51-75%", "min": 51, "max": 75},
        "5": {"label": "75%+", "min": 75.01, "max": 100},
    }

    summary = {}

    total = len(ratios)

    for key, r in ranges.items():
        count = sum(1 for v in ratios if r["min"] <= v <= r["max"])

        percentage = round((count / total) * 100, 2) if total else 0

        summary[key] = {
            "label": r["label"],
            "count": count,
            "percentage": percentage,
        }

    return summary
def list_ricegrains_by_inspection(db: Session, inspection_id: int, level: int = None):
    """Return rice grains for an inspection with id, belly_white_ratio and image path.

    Args:
        db: SQLAlchemy Session
        inspection_id: inspection id to filter rice grains

    Returns:
        List of dicts with keys: rice_grain_id, belly_white_ratio, image
    """
    query = (
        db.query(
            RiceGrain.rice_grain_id,
            RiceGrain.belly_white_ratio,
            RiceGrain.image,
        )
        .join(Classified, RiceGrain.classified_id == Classified.classified_id)
        .filter(Classified.inspection_id == inspection_id)
    )

    # Apply level filtering based on belly_white_ratio ranges
    # Levels mapping:
    # 0: ratio == 0
    # 1: 0 < ratio <= 10
    # 2: 10 < ratio <= 24
    # 3: 24 < ratio <= 50
    # 4: 50 < ratio <= 75
    # 5: ratio > 75
    if level is not None:
        if level == 0:
            query = query.filter(RiceGrain.belly_white_ratio == 0)
        elif level == 1:
            query = query.filter(RiceGrain.belly_white_ratio > 0, RiceGrain.belly_white_ratio <= 10)
        elif level == 2:
            query = query.filter(RiceGrain.belly_white_ratio > 10, RiceGrain.belly_white_ratio <= 24)
        elif level == 3:
            query = query.filter(RiceGrain.belly_white_ratio > 24, RiceGrain.belly_white_ratio <= 50)
        elif level == 4:
            query = query.filter(RiceGrain.belly_white_ratio > 50, RiceGrain.belly_white_ratio <= 75)
        elif level == 5:
            query = query.filter(RiceGrain.belly_white_ratio > 75)

    rows = query.order_by(RiceGrain.rice_grain_id.asc()).all()

    return [
        {
            "rice_grain_id": r.rice_grain_id,
            "belly_white_ratio": float(r.belly_white_ratio) if r.belly_white_ratio is not None else None,
            "image": f"http://localhost:8000{convert_path_to_url(r.image)}",
        }
        for r in rows
    ]


def update_unit(db: Session, unit_id: int, unit_name: str):
    unit = get_unit(db, unit_id)
    if unit:
        unit.unit_name = unit_name
        db.commit()
    return unit


def delete_unit(db: Session, unit_id: int):
    # 1. ค้นหา Unit
    unit = get_unit(db, unit_id)
    if not unit:
        return

    try:
        # 2. หาโฟลเดอร์ทั้งหมดที่เกี่ยวข้องกับ Unit นี้
        # โดยเชื่อมจาก Unit -> Inspection -> RiceGrain เพื่อเอา path รูปภาพ
        inspections = db.query(RiceGrain)\
                        .join(Classified, RiceGrain.classified_id == Classified.classified_id)\
                        .filter(Classified.inspection_id == insp.inspection_id)
        folders_to_delete = set()
        for insp in inspections:
            # หาเมล็ดข้าวเมล็ดแรกในแต่ละ inspection เพื่อระบุโฟลเดอร์
            first_grain = db.query(RiceGrain).filter(RiceGrain.inspection_id == insp.inspection_id).first()
            if first_grain and first_grain.image:
                # แปลง path จาก string เป็น Path object และหา parent folder (session folder)
                folder_path = Path(first_grain.image).parent
                if folder_path.exists():
                    folders_to_delete.add(folder_path)

        # 3. ลบโฟลเดอร์ออกจาก Disk
        for folder in folders_to_delete:
            try:
                shutil.rmtree(folder)
                print(f"[System] Deleted folder: {folder}")
            except Exception as e:
                print(f"[Error] Could not delete folder {folder}: {e}")

        # 4. ลบข้อมูลออกจาก Database
        # หมายเหตุ: SQL ของคุณตั้ง ON DELETE CASCADE ไว้แล้ว 
        # การลบ unit จะลบ inspection และ ricegrain อัตโนมัติ
        db.delete(unit)
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"[Error] Process failed: {e}")
        raise e

def search_units(
    db: Session,
    keyword: str = "",
    date_min: str = "",
    date_max: str = "",
):
    # -------------------------
    # MAIN QUERY
    # -------------------------
    # subquery: latest inspection datetime per unit (used to show latest inspection date)
    insp_max = (
        db.query(
            Inspection.unit_id.label("unit_id"),
            func.max(Inspection.date_time).label("max_dt")
        )
        .group_by(Inspection.unit_id)
        .subquery()
    )

    data_query = (
        db.query(
            Unit.unit_id,
            Unit.unit_name,
            func.count(RiceGrain.rice_grain_id).label("ricegrain_count"),
            insp_max.c.max_dt.label("datetimeInspection")
        )
        .outerjoin(insp_max, insp_max.c.unit_id == Unit.unit_id)
        .outerjoin(Inspection, Inspection.unit_id == Unit.unit_id)
        .outerjoin(Classified, Classified.inspection_id == Inspection.inspection_id)
        .outerjoin(RiceGrain, RiceGrain.classified_id == Classified.classified_id)
        .group_by(Unit.unit_id, Unit.unit_name, insp_max.c.max_dt)
    )

    # -------------------------
    # COUNT QUERY
    # -------------------------
    count_query = db.query(Unit)

    # -------------------------
    # FILTER: keyword
    # -------------------------
    if keyword:
        data_query = data_query.filter(Unit.unit_name.ilike(f"%{keyword}%"))
        count_query = count_query.filter(Unit.unit_name.ilike(f"%{keyword}%"))

    # -------------------------
    # FILTER: date range -> use latest inspection per unit within range
    # -------------------------
    if date_min or date_max:
        start_dt = None
        end_dt = None
        if date_min:
            dmin = datetime.strptime(date_min, "%Y-%m-%d").date()
            start_dt = datetime.combine(dmin, time.min)
        if date_max:
            dmax = datetime.strptime(date_max, "%Y-%m-%d").date()
            end_dt = datetime.combine(dmax, time.max)

        insp_q = db.query(
            Inspection.unit_id.label("unit_id"),
            func.max(Inspection.date_time).label("max_dt")
        )
        if start_dt:
            insp_q = insp_q.filter(Inspection.date_time >= start_dt)
        if end_dt:
            insp_q = insp_q.filter(Inspection.date_time <= end_dt)
        insp_q = insp_q.group_by(Inspection.unit_id).subquery()

        # join units to their latest inspection in range, then ricegrains for that inspection
        data_query = (
            db.query(
                Unit.unit_id,
                Unit.unit_name,
                func.count(RiceGrain.rice_grain_id).label("ricegrain_count"),
                Inspection.date_time.label("datetimeInspection")
            )
            .join(insp_q, insp_q.c.unit_id == Unit.unit_id)
            .join(Inspection, (Inspection.unit_id == insp_q.c.unit_id) & (Inspection.date_time == insp_q.c.max_dt))
            .outerjoin(Classified, Classified.inspection_id == Inspection.inspection_id)
            .outerjoin(RiceGrain, RiceGrain.classified_id == Classified.classified_id)
            .group_by(Unit.unit_id, Unit.unit_name, Inspection.date_time)
        )

        count_query = (
            db.query(Unit)
            .join(insp_q, insp_q.c.unit_id == Unit.unit_id)
            .distinct()
        )

    total = count_query.count()

    # -------------------------
    # EXECUTE
    # -------------------------
    items = (
        data_query
        .order_by(Unit.unit_id.desc())
        .all()
    )

    result = [
        {
            "unit_id": item.unit_id,
            "unit_name": item.unit_name,
            "ricegrain_count": int(item.ricegrain_count or 0),
            "datetimeInspection": item.datetimeInspection.strftime("%d/%m/%Y") if hasattr(item, "datetimeInspection") and item.datetimeInspection else None
        }
        for item in items
    ]

    return {
        "items": result,
        "total": total
    }


def dropdown_units(db: Session):
    units = db.query(Unit.unit_id, Unit.unit_name)\
        .order_by(Unit.unit_name.asc())\
        .all()

    return [
        {
            "value": u.unit_id,
            "label": u.unit_name
        }
        for u in units
    ]


def create_next_inspection(db: Session, unit_id: int):
    """
    สร้าง inspection ใหม่ของ unit
    inspection_id จะ auto +1 จากของเดิม
    """


    new_inspection = Inspection(
        unit_id=unit_id,
        date_time=datetime.utcnow()
    )

    db.add(new_inspection)
    db.commit()
    db.refresh(new_inspection)

    return {
        "inspection_id": new_inspection.inspection_id
    }


def get_dropdown_inspections(db: Session, unit_id: int):
    """
    คืน inspection_id ที่ยังตรวจได้ไม่ครบ 3 รอบ
    """

    rows = (
        db.query(
            Inspection.inspection_id,
            func.count(func.distinct(Classified.classified_id)).label("round_count")
        )
        .outerjoin(
            Classified,
            Classified.inspection_id == Inspection.inspection_id
        )
        .filter(Inspection.unit_id == unit_id)
        .group_by(Inspection.inspection_id)
        .having(func.count(func.distinct(Classified.classified_id)) < 3)
        .order_by(Inspection.inspection_id.asc())
        .all()
    )

    return [
        {
            "value": r.inspection_id,
            "label": f"ครั้งที่ {r.inspection_id} (เหลือ {3 - r.round_count} รอบ)",
            "remaining": 3 - r.round_count,
            "next_round": r.round_count + 1
        }
        for r in rows
    ]