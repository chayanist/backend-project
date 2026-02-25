# routers/unit.py
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.deps import get_db, get_current_user
from core.response import success
from core.messages import MessageEnum
from services.unit_service import (
    create_next_inspection, create_unit, get_dropdown_inspections, get_inspection_summary, get_unit, get_unit_report, get_unit_summary_all, update_unit, delete_unit,search_units,dropdown_units
)
from schemas.unit import UnitCreate, UnitUpdate

router = APIRouter(prefix="/units", tags=["Units"], dependencies=[Depends(get_current_user)])

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
def unit_report(
    unit_id: int,
    min_date: datetime | None = None,
    max_date: datetime | None = None,
    db: Session = Depends(get_db)
):
    data =  get_unit_report(db, unit_id, min_date, max_date)
    return success(data, MessageEnum.SUCCESS)


@router.get("/inspection-summary/{inspection_id}")
def inspection_summary(inspection_id: int, db: Session = Depends(get_db)):
    data =  get_inspection_summary(db, inspection_id)
    return success(data, MessageEnum.SUCCESS)

@router.get("/{unit_id}/inspection-summary-all")
def get_unit_summary_alls(unit_id: int, db: Session = Depends(get_db)):
    summary = get_unit_summary_all(db, unit_id)
    return success(summary, MessageEnum.SUCCESS)


@router.get("/inspection-summary/ricegrains/{inspection_id}")
def list_ricegrains(
    inspection_id: int,
    level: int = Query(None, description="optional level filter (0-5)", ge=0, le=5),
    db: Session = Depends(get_db)
):
    from services.unit_service import list_ricegrains_by_inspection
    data = list_ricegrains_by_inspection(db, inspection_id, level)
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
    date_min: str = Query("", description="start date YYYY-MM-DD"),
    date_max: str = Query("", description="end date YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    result = search_units(
        db=db,
        keyword=keyword,
        date_min=date_min,
        date_max=date_max
    )

    return success(
        data=result,
        message=MessageEnum.SUCCESS
    )

@router.get("/dropdown")
def dropdown(db: Session = Depends(get_db)):
    items = dropdown_units(db)
    return success(items, MessageEnum.SUCCESS)

@router.post("/create-next")
def create_inspection(
    unit_id: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    data = create_next_inspection(db, unit_id)
    return success(data, MessageEnum.SUCCESS)


@router.get("/dropdown/inspection")
def dropdown_inspection(
    unit_id: int = Query(..., description="Unit ID"),
    db: Session = Depends(get_db)
):
    data =  get_dropdown_inspections(db, unit_id)
    return success(data, MessageEnum.SUCCESS)