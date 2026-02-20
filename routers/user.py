from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.deps import get_db, get_current_user
from models.user import User as UserModel
from core.response import success
from core.messages import MessageEnum
from schemas.user import UserCreate, UserUpdate
from services.user_service import (
    create_user, get_user, search_user, update_user, delete_user
)

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(get_current_user)])

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
def update(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    target = get_user(db, user_id)
    if not target:
        raise HTTPException(404, "user not found")

    # Prevent user from deactivating themselves
    if hasattr(data, 'status') and data.status is not None and data.status is False and target.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    # Prevent modifying default users (if field exists) to inactive
    if hasattr(target, 'default') and getattr(target, 'default') and hasattr(data, 'status') and data.status is not None and data.status is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate default user")

    user = update_user(db, user_id, data)
    if not user:
        raise HTTPException(404, "user not found")
    return success(user, MessageEnum.UPDATED)

@router.delete("/delete/{user_id}")
def delete(user_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    target = get_user(db, user_id)
    if not target:
        raise HTTPException(404, "user not found")

    # Prevent deleting self
    if target.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    # Prevent deleting default users if such flag exists
    if hasattr(target, 'default') and getattr(target, 'default'):
        raise HTTPException(status_code=400, detail="Cannot delete default user")

    delete_user(db, user_id)
    return success(None, MessageEnum.DELETED)
