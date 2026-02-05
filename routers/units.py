# routers/unit.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.deps import get_db
from core.response import success
from core.messages import MessageEnum
from services.unit_service import (
    create_unit, get_unit, update_unit, delete_unit,search_units
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
    db: Session = Depends(get_db)
):
    result = search_units(
        db=db,
        keyword=keyword
    )

    return success(
        data=result,
        message=MessageEnum.SUCCESS
    )