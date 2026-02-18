# services/unit_service.py
from sqlalchemy.orm import Session
from models.unit import Unit
from models.inspection import Inspection
from models.ricegrain import RiceGrain
from sqlalchemy import func, case
from datetime import datetime


def create_unit(db: Session, unit_name: str):
    unit = Unit(unit_name=unit_name)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def get_unit(db: Session, unit_id: int):
    return db.query(Unit).filter(Unit.unit_id == unit_id).first()

def get_unit_report(db: Session, unit_id: int):

    rows = (
        db.query(
            Inspection.inspection_id,
            Inspection.date_time,

            func.count(RiceGrain.rice_grain_id).label("total"),

            func.sum(case((RiceGrain.belly_white_level == 5, 1), else_=0)).label("lv5"),
            func.sum(case((RiceGrain.belly_white_level == 4, 1), else_=0)).label("lv4"),
            func.sum(case((RiceGrain.belly_white_level == 3, 1), else_=0)).label("lv3"),
            func.sum(case((RiceGrain.belly_white_level == 2, 1), else_=0)).label("lv2"),
            func.sum(case((RiceGrain.belly_white_level == 1, 1), else_=0)).label("lv1"),
            func.sum(case((RiceGrain.belly_white_level == 0, 1), else_=0)).label("lv0"),
        )
        .outerjoin(
            RiceGrain,
            RiceGrain.inspection_id == Inspection.inspection_id
        )
        .filter(Inspection.unit_id == unit_id)
        .group_by(Inspection.inspection_id, Inspection.date_time)
        .order_by(Inspection.inspection_id.desc())
        .all()
    )

    return [
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


def get_inspection_summary(db: Session, inspection_id: int):

    row = (
        db.query(
            func.count(RiceGrain.rice_grain_id).label("total"),

            func.count(RiceGrain.rice_grain_id).filter(RiceGrain.belly_white_level == 5).label("lv5"),
            func.count(RiceGrain.rice_grain_id).filter(RiceGrain.belly_white_level == 4).label("lv4"),
            func.count(RiceGrain.rice_grain_id).filter(RiceGrain.belly_white_level == 3).label("lv3"),
            func.count(RiceGrain.rice_grain_id).filter(RiceGrain.belly_white_level == 2).label("lv2"),
            func.count(RiceGrain.rice_grain_id).filter(RiceGrain.belly_white_level == 1).label("lv1"),
            func.count(RiceGrain.rice_grain_id).filter(RiceGrain.belly_white_level == 0).label("lv0"),
        )
        .filter(RiceGrain.inspection_id == inspection_id)
        .one()
    )

    return {
        "lv5": int(row.lv5 or 0),
        "lv4": int(row.lv4 or 0),
        "lv3": int(row.lv3 or 0),
        "lv2": int(row.lv2 or 0),
        "lv1": int(row.lv1 or 0),
        "lv0": int(row.lv0 or 0),
        "total": int(row.total or 0),
    }

def update_unit(db: Session, unit_id: int, unit_name: str):
    unit = get_unit(db, unit_id)
    if unit:
        unit.unit_name = unit_name
        db.commit()
    return unit


def delete_unit(db: Session, unit_id: int):
    unit = get_unit(db, unit_id)
    if unit:
        db.delete(unit)
        db.commit()

def search_units(
    db: Session,
    keyword: str = "",
    date: str = ""
):
    # -------------------------
    # MAIN QUERY
    # -------------------------
    data_query = (
        db.query(
            Unit.unit_id,
            Unit.unit_name,
            func.count(RiceGrain.rice_grain_id).label("ricegrain_count")
        )
        .outerjoin(Inspection, Inspection.unit_id == Unit.unit_id)
        .outerjoin(RiceGrain, RiceGrain.inspection_id == Inspection.inspection_id)
        .group_by(Unit.unit_id, Unit.unit_name)
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
    # FILTER: date
    # -------------------------
    if date:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        data_query = data_query.filter(
            func.date(Inspection.date_time) == date_obj
        )

        count_query = (
            count_query.join(Inspection, Inspection.unit_id == Unit.unit_id)
            .filter(func.date(Inspection.date_time) == date_obj)
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
            "ricegrain_count": int(item.ricegrain_count or 0)
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