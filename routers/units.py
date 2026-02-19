# routers/unit.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.deps import get_db
from core.response import success
from core.messages import MessageEnum
from services.unit_service import (
    create_unit, get_inspection_summary, get_unit, get_unit_report, update_unit, delete_unit,search_units,dropdown_units
)
from schemas.unit import UnitCreate, UnitUpdate

router = APIRouter(prefix="/units", tags=["Units"])

@router.post("/create")
def create(data: UnitCreate, db: Session = Depends(get_db)):
    unit = create_unit(db, data.unit_name)
    return success(unit, MessageEnum.CREATED)

@router.get("/detail/{unit_id}")
def detail(unit_id: int, db: Session = Depends(get_db)):
    unit = get_unit(db, unit_id)
    if not unit:
        raise HTTPException(404, "not found")
    return success(unit, MessageEnum.SUCCESS)

@router.get("/{unit_id}/inspections")
def get_unit_inspections(unit_id: int, db: Session = Depends(get_db)):
    data = get_unit_report(db, unit_id)
    return success(data, MessageEnum.SUCCESS)

@router.get("/inspection-summary/{inspection_id}")
def inspection_summary(inspection_id: int, db: Session = Depends(get_db)):
    data =  get_inspection_summary(db, inspection_id)
    return success(data, MessageEnum.SUCCESS)


@router.get("/inspection-summary/ricegrains/{inspection_id}")
def list_ricegrains(inspection_id: int, db: Session = Depends(get_db)):
    from services.unit_service import list_ricegrains_by_inspection
    data = list_ricegrains_by_inspection(db, inspection_id)
    return success(data, MessageEnum.SUCCESS)

@router.put("/update/{unit_id}")
def update(unit_id: int, data: UnitUpdate, db: Session = Depends(get_db)):
    unit = update_unit(db, unit_id, data.unit_name)
    return success(unit, MessageEnum.UPDATED)

@router.delete("/delete/{unit_id}")
def delete(unit_id: int, db: Session = Depends(get_db)):
    delete_unit(db, unit_id)
    return success(None, MessageEnum.DELETED)

@router.get("/search")
def search(
    keyword: str = Query("", description="search by unit name"),
    date: str = Query("", description="search by date"),
    db: Session = Depends(get_db)
):
    result = search_units(
        db=db,
        keyword=keyword,
        date=date
    )

    return success(
        data=result,
        message=MessageEnum.SUCCESS
    )

@router.get("/dropdown")
def dropdown(db: Session = Depends(get_db)):
    items = dropdown_units(db)
    return success(items, MessageEnum.SUCCESS)