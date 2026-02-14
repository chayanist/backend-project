# services/unit_service.py
from sqlalchemy.orm import Session
from models.unit import Unit
from models.inspection import Inspection
from models.classified import Classified
from sqlalchemy import func
from datetime import datetime


def create_unit(db: Session, unit_name: str):
    unit = Unit(unit_name=unit_name)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def get_unit(db: Session, unit_id: int):
    return db.query(Unit).filter(Unit.unit_id == unit_id).first()


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
            func.coalesce(func.sum(Classified.total), 0).label("ricegrain_count")
        )
        .outerjoin(Inspection, Inspection.unit_id == Unit.unit_id)
        .outerjoin(Classified, Classified.inspection_id == Inspection.inspection_id)
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
    # FILTER: date (inspection date)
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
