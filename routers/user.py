from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.deps import get_db
from core.response import success
from core.messages import MessageEnum
from schemas.user import UserCreate, UserUpdate
from services.user_service import (
    create_user, get_user, search_user, update_user, delete_user
)

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/create")
def create(data: UserCreate, db: Session = Depends(get_db)):
    user = create_user(db, data)
    return success(user, MessageEnum.CREATED)

@router.get("/search")
def search(
    keyword: str = Query("", description="search by username"),
    db: Session = Depends(get_db)
):
    users = search_user(db, keyword)
    return success(users, MessageEnum.SUCCESS)

@router.get("/detail/{user_id}")
def detail(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    return success(user, MessageEnum.SUCCESS)

@router.put("/update/{user_id}")
def update(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = update_user(db, user_id, data)
    if not user:
        raise HTTPException(404, "user not found")
    return success(user, MessageEnum.UPDATED)

@router.delete("/delete/{user_id}")
def delete(user_id: int, db: Session = Depends(get_db)):
    delete_user(db, user_id)
    return success(None, MessageEnum.DELETED)
