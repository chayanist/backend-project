# services/unit_service.py
from sqlalchemy.orm import Session
from models.Accuracy import Accuracy
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

def get_local_inspection_mapping(db: Session, unit_id: int) -> dict:
    """
    คืนค่า Dict ที่แปลงจาก inspection_id ฐานข้อมูล ให้เป็นลำดับที่ 1, 2, 3... ของหน่วยงานนั้น
    เช่น {4: 1, 5: 2, 6: 3}
    """
    rows = (
        db.query(Inspection.inspection_id)
        .filter(Inspection.unit_id == unit_id)
        .order_by(Inspection.inspection_id.asc())
        .all()
    )
    return {row[0]: idx + 1 for idx, row in enumerate(rows)}

def create_unit(db: Session, unit_name: str):
    unit = Unit(
        unit_name=unit_name, 
        create_date=datetime.now()  
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def get_unit(db: Session, unit_id: int):
    return db.query(Unit).filter(Unit.unit_id == unit_id).first()


def get_unit_report(
    db: Session,
    unit_id: int,
    min_date: datetime | None = None,
    max_date: datetime | None = None,
):
    # 🚀 1. ดึงชื่อหน่วยงานจากตาราง Unit เพิ่มเข้ามา
    unit_obj = db.query(Unit).filter(Unit.unit_id == unit_id).first()
    unit_name = unit_obj.unit_name if unit_obj else f"ไม่ทราบชื่อ ({unit_id})"    
    
    # 🚀 2. เรียกใช้ตัวแปลงลำดับ ID ให้เป็น 1, 2, 3...
    local_insp_map = get_local_inspection_mapping(db, unit_id)

    # =========================
    # 1️⃣ Query inspection summary
    # =========================

    inspection_query = (
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

    if min_date:
        inspection_query = inspection_query.filter(
            Inspection.date_time >= min_date
        )

    if max_date:
        inspection_query = inspection_query.filter(
            Inspection.date_time <= max_date
        )

    inspections = (
        inspection_query
        .order_by(Inspection.inspection_id.desc())
        .all()
    )

    # =========================
    # 2️⃣ Build items + subRounds
    # =========================

    items = []

    for ins in inspections:
        # 🚀 3. แปลงเลข ID อัตโนมัติเป็นลำดับของหน่วยงานนี้
        local_no = local_insp_map.get(ins.inspection_id, ins.inspection_id)

        # 🔹 ดึง classified (sub rounds) ของ inspection นี้
        classified_rows = (
            db.query(
                Classified.classified_id,
                Classified.round_number,
                Classified.date_time,

                Classified.level5,
                Classified.level4,
                Classified.level3,
                Classified.level2,
                Classified.level1,
                Classified.level0,
                Classified.total,
            )
            .filter(Classified.inspection_id == ins.inspection_id)
            .order_by(Classified.round_number.asc())
            .all()
        )

        sub_rounds = [
            {
                "id": c.classified_id,  # ⭐ ใช้ id นี้ยิง graph/classified
                "roundNumber": c.round_number,
                "date": c.date_time.strftime("%d/%m/%Y")
                if c.date_time else None,
                "lv5": int(c.level5 or 0),
                "lv4": int(c.level4 or 0),
                "lv3": int(c.level3 or 0),
                "lv2": int(c.level2 or 0),
                "lv1": int(c.level1 or 0),
                "lv0": int(c.level0 or 0),
                "total": int(c.total or 0),
            }
            for c in classified_rows
        ]

        items.append(
            {
                "id": ins.inspection_id,
                "local_insp_no": local_no,             # 🚀 ส่งลำดับจริง 1,2,3 ไปให้ Frontend
                "display_name": f"ครั้งที่ {local_no}", # 🚀 ส่งคำว่า "ครั้งที่ 1" ไปให้
                "date": ins.date_time.strftime("%d/%m/%Y") if ins.date_time else "-",
                "lv5": int(ins.lv5 or 0),
                "lv4": int(ins.lv4 or 0),
                "lv3": int(ins.lv3 or 0),
                "lv2": int(ins.lv2 or 0),
                "lv1": int(ins.lv1 or 0),
                "lv0": int(ins.lv0 or 0),
                "total": int(ins.total or 0),
                "subRounds": sub_rounds,  # ⭐ เพิ่มตรงนี้
            }
        )

    # =========================
    # 3️⃣ Summary รวมทั้งหมด
    # =========================

    summary = {
        "lv5": sum(d["lv5"] for d in items),
        "lv4": sum(d["lv4"] for d in items),
        "lv3": sum(d["lv3"] for d in items),
        "lv2": sum(d["lv2"] for d in items),
        "lv1": sum(d["lv1"] for d in items),
        "lv0": sum(d["lv0"] for d in items),
        "total": sum(d["total"] for d in items),
    }

    return {
        "unit_name": unit_name,
        "summary": summary,
        "items": items
    }

def get_inspection_report(db: Session, inspection_id: int):

    # 🚀 1. ดึงชื่อหน่วยงานโดยหาจาก inspection_id
    unit_info = (
        db.query(Unit.unit_name)
        .join(Inspection, Inspection.unit_id == Unit.unit_id)
        .filter(Inspection.inspection_id == inspection_id)
        .first()
    )
    unit_name = unit_info.unit_name if unit_info else "-"

    # 🚀 2. ดึงข้อมูลรายงานตามปกติ
    rows = (
        db.query(
            Classified.classified_id,
            Classified.round_number,
            Classified.level0,
            Classified.level1,
            Classified.level2,
            Classified.level3,
            Classified.level4,
            Classified.level5,
            Classified.total,
            Accuracy.level0.label("a0"),
            Accuracy.level1.label("a1"),
            Accuracy.level2.label("a2"),
            Accuracy.level3.label("a3"),
            Accuracy.level4.label("a4"),
            Accuracy.level5.label("a5"),
            Accuracy.overall,
        )
        .outerjoin(Accuracy, Accuracy.classified_id == Classified.classified_id)
        .filter(Classified.inspection_id == inspection_id)
        .order_by(Classified.round_number.asc())
        .all()
    )

    if not rows:
        return None

    # =============================
    # 🔹 summary รวมเมล็ดทั้งหมด
    # =============================
    summary = {
        "lv5": sum(r.level5 or 0 for r in rows),
        "lv4": sum(r.level4 or 0 for r in rows),
        "lv3": sum(r.level3 or 0 for r in rows),
        "lv2": sum(r.level2 or 0 for r in rows),
        "lv1": sum(r.level1 or 0 for r in rows),
        "lv0": sum(r.level0 or 0 for r in rows),
        "total": sum(r.total or 0 for r in rows),
    }

    # =============================
    # 🔹 accuracy ต่อรอบ (ใช้จาก table)
    # =============================
    accuracy = []
    for r in rows:
        if r.overall is None:
            continue

        accuracy.append({
            "classifiedId": r.classified_id,
            "roundNumber": r.round_number,
            "c0": r.a0 or 0,
            "c1": r.a1 or 0,
            "c2": r.a2 or 0,
            "c3": r.a3 or 0,
            "c4": r.a4 or 0,
            "c5": r.a5 or 0,
            "overall": r.overall or 0,
        })

    # 🚀 3. แนบชื่อหน่วยงานส่งกลับไปให้ Frontend ตรงนี้
    return {
        "unit_name": unit_name,
        "summary": summary,
        "accuracy": accuracy
    }

def get_inspection_summary(db: Session, inspection_id: int):
    # 🚀 1. ดึงข้อมูล ครั้งที่ (inspection_id) และ รอบที่ (round_number) 
    classified_info = (
        db.query(Classified.inspection_id, Classified.round_number)
        .filter(Classified.classified_id == inspection_id)
        .first()
    )
    
    real_insp_id = classified_info.inspection_id if classified_info else "-"
    round_no = classified_info.round_number if classified_info else "-"

    row = (
        db.query(
            func.count(RiceGrain.rice_grain_id).label("total"),
            
            # Group 0: ratio = 0
            func.sum(case((RiceGrain.belly_white_ratio == 0, 1), else_=0)).label("group_0"),
            
            # Group 1-10% divided into 5 sub-bars
            func.sum(case(((RiceGrain.belly_white_ratio > 0) & (RiceGrain.belly_white_ratio <= 2), 1), else_=0)).label("group_1_1"),
            func.sum(case(((RiceGrain.belly_white_ratio > 2) & (RiceGrain.belly_white_ratio <= 4), 1), else_=0)).label("group_1_2"),
            func.sum(case(((RiceGrain.belly_white_ratio > 4) & (RiceGrain.belly_white_ratio <= 6), 1), else_=0)).label("group_1_3"),
            func.sum(case(((RiceGrain.belly_white_ratio > 6) & (RiceGrain.belly_white_ratio <= 8), 1), else_=0)).label("group_1_4"),
            func.sum(case(((RiceGrain.belly_white_ratio > 8) & (RiceGrain.belly_white_ratio <= 10), 1), else_=0)).label("group_1_5"),
            
            # Group 11-24% divided into 5 sub-bars
            func.sum(case(((RiceGrain.belly_white_ratio > 10) & (RiceGrain.belly_white_ratio <= 13.3), 1), else_=0)).label("group_2_1"),
            func.sum(case(((RiceGrain.belly_white_ratio > 13.3) & (RiceGrain.belly_white_ratio <= 16.6), 1), else_=0)).label("group_2_2"),
            func.sum(case(((RiceGrain.belly_white_ratio > 16.6) & (RiceGrain.belly_white_ratio <= 19.9), 1), else_=0)).label("group_2_3"),
            func.sum(case(((RiceGrain.belly_white_ratio > 19.9) & (RiceGrain.belly_white_ratio <= 21.7), 1), else_=0)).label("group_2_4"),
            func.sum(case(((RiceGrain.belly_white_ratio > 21.7) & (RiceGrain.belly_white_ratio <= 24), 1), else_=0)).label("group_2_5"),
            
            # Group 25-50% divided into 5 sub-bars
            func.sum(case(((RiceGrain.belly_white_ratio > 24) & (RiceGrain.belly_white_ratio <= 30), 1), else_=0)).label("group_3_1"),
            func.sum(case(((RiceGrain.belly_white_ratio > 30) & (RiceGrain.belly_white_ratio <= 35), 1), else_=0)).label("group_3_2"),
            func.sum(case(((RiceGrain.belly_white_ratio > 35) & (RiceGrain.belly_white_ratio <= 40), 1), else_=0)).label("group_3_3"),
            func.sum(case(((RiceGrain.belly_white_ratio > 40) & (RiceGrain.belly_white_ratio <= 45), 1), else_=0)).label("group_3_4"),
            func.sum(case(((RiceGrain.belly_white_ratio > 45) & (RiceGrain.belly_white_ratio <= 50), 1), else_=0)).label("group_3_5"),
            
            # Group 51-75% divided into 5 sub-bars
            func.sum(case(((RiceGrain.belly_white_ratio > 50) & (RiceGrain.belly_white_ratio <= 59), 1), else_=0)).label("group_4_1"),
            func.sum(case(((RiceGrain.belly_white_ratio > 59) & (RiceGrain.belly_white_ratio <= 63), 1), else_=0)).label("group_4_2"),
            func.sum(case(((RiceGrain.belly_white_ratio > 63) & (RiceGrain.belly_white_ratio <= 67), 1), else_=0)).label("group_4_3"),
            func.sum(case(((RiceGrain.belly_white_ratio > 67) & (RiceGrain.belly_white_ratio <= 71), 1), else_=0)).label("group_4_4"),
            func.sum(case(((RiceGrain.belly_white_ratio > 71) & (RiceGrain.belly_white_ratio <= 75), 1), else_=0)).label("group_4_5"),
            
            # Group 75%+ divided into 5 sub-bars
            func.sum(case(((RiceGrain.belly_white_ratio > 75) & (RiceGrain.belly_white_ratio <= 82), 1), else_=0)).label("group_5_1"),
            func.sum(case(((RiceGrain.belly_white_ratio > 82) & (RiceGrain.belly_white_ratio <= 87), 1), else_=0)).label("group_5_2"),
            func.sum(case(((RiceGrain.belly_white_ratio > 87) & (RiceGrain.belly_white_ratio <= 91), 1), else_=0)).label("group_5_3"),
            func.sum(case(((RiceGrain.belly_white_ratio > 91) & (RiceGrain.belly_white_ratio <= 96), 1), else_=0)).label("group_5_4"),
            func.sum(case((RiceGrain.belly_white_ratio > 96, 1), else_=0)).label("group_5_5"),
        )
        .join(Classified, RiceGrain.classified_id == Classified.classified_id)
        .filter(RiceGrain.classified_id  == inspection_id)
        .first()
    )

    # Calculate group totals
    group_0 = int(row.group_0 or 0)
    
    group_1_bars = [int(row.group_1_1 or 0), int(row.group_1_2 or 0), int(row.group_1_3 or 0), int(row.group_1_4 or 0), int(row.group_1_5 or 0)]
    group_1_total = sum(group_1_bars)
    
    group_2_bars = [int(row.group_2_1 or 0), int(row.group_2_2 or 0), int(row.group_2_3 or 0), int(row.group_2_4 or 0), int(row.group_2_5 or 0)]
    group_2_total = sum(group_2_bars)
    
    group_3_bars = [int(row.group_3_1 or 0), int(row.group_3_2 or 0), int(row.group_3_3 or 0), int(row.group_3_4 or 0), int(row.group_3_5 or 0)]
    group_3_total = sum(group_3_bars)
    
    group_4_bars = [int(row.group_4_1 or 0), int(row.group_4_2 or 0), int(row.group_4_3 or 0), int(row.group_4_4 or 0), int(row.group_4_5 or 0)]
    group_4_total = sum(group_4_bars)
    
    group_5_bars = [int(row.group_5_1 or 0), int(row.group_5_2 or 0), int(row.group_5_3 or 0), int(row.group_5_4 or 0), int(row.group_5_5 or 0)]
    group_5_total = sum(group_5_bars)

    return {
        "inspection_id": real_insp_id,  
        "round_number": round_no,      
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
        "total": int(row.total or 0) if row else 0,
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

def build_summary(ratios: list):  # 🚀 แก้ list[float] เป็น list ธรรมดาให้แล้ว
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

def list_ricegrains_by_inspection(db: Session, classified_id: int, level: int = None):
    """Return rice grains along with inspection_id and round_number."""
    
    # 🚀 1. ดึงข้อมูล inspection_id และ round_number จากตาราง Classified
    classified_info = (
        db.query(Classified.inspection_id, Classified.round_number)
        .filter(Classified.classified_id == classified_id)
        .first()
    )
    
    insp_id = classified_info.inspection_id if classified_info else "-"
    round_no = classified_info.round_number if classified_info else "-"

    # 🚀 2. ดึงข้อมูลเมล็ดข้าวตามปกติ
    query = (
        db.query(
            RiceGrain.rice_grain_id,
            RiceGrain.belly_white_ratio,
            RiceGrain.image,
        )
        .filter(RiceGrain.classified_id == classified_id) 
    )

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

    grains = [
        {
            "rice_grain_id": r.rice_grain_id,
            "belly_white_ratio": float(r.belly_white_ratio) if r.belly_white_ratio is not None else None,
            "image": f"http://localhost:8000{convert_path_to_url(r.image)}" if r.image else None,
        }
        for r in rows
    ]

    # 🚀 3. จัด Format ส่งกลับไปให้ Frontend แบบมี Header บอกข้อมูลรอบ
    return {
        "inspection_id": insp_id,
        "round_number": round_no,
        "grains": grains
    }

def update_unit(db: Session, unit_id: int, unit_name: str):
    unit = get_unit(db, unit_id)
    if unit:
        unit.unit_name = unit_name
        db.commit()
    return unit


def delete_unit(db: Session, unit_id: int):
    unit = get_unit(db, unit_id)
    if not unit:
        return

    try:
        # 1️⃣ ดึง image path ทั้งหมดของ unit นี้
        ricegrain_images = (
            db.query(RiceGrain.image)
            .join(Classified, RiceGrain.classified_id == Classified.classified_id)
            .join(Inspection, Classified.inspection_id == Inspection.inspection_id)
            .filter(Inspection.unit_id == unit_id)
            .all()
        )

        folders_to_delete = set()

        for row in ricegrain_images:
            if row.image:
                folder_path = Path(row.image).parent
                if folder_path.exists():
                    folders_to_delete.add(folder_path)

        # 2️⃣ ลบโฟลเดอร์
        for folder in folders_to_delete:
            try:
                shutil.rmtree(folder)
                print(f"[System] Deleted folder: {folder}")
            except Exception as e:
                print(f"[Error] Could not delete folder {folder}: {e}")

        # 3️⃣ ลบ unit (มี ON DELETE CASCADE แล้ว)
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
    # FILTER: date range
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
    # 🚀 4. ดึงตัวแปลงลำดับ
    local_insp_map = get_local_inspection_mapping(db, unit_id)

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
            # 🚀 5. เปลี่ยนมาใช้ค่าที่แปลงเป็นลำดับแล้ว
            "label": f"ครั้งที่ {local_insp_map.get(r.inspection_id, r.inspection_id)} (เหลือ {3 - r.round_count} รอบ)",
            "remaining": 3 - r.round_count,
            "next_round": r.round_count + 1
        }
        for r in rows
    ]