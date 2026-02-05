# services/unit_service.py
from sqlalchemy.orm import Session
from models.unit import Unit

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
    keyword: str = ""
):
    query = db.query(Unit)

    if keyword:
        query = query.filter(Unit.unit_name.ilike(f"%{keyword}%"))

    total = query.count()

    items = (
        query
        .order_by(Unit.unit_id.desc())
        .all()
    )

    return {
        "items": items,
        "total": total
    }