from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from models.user import User
from core.security import hash_password
from datetime import datetime

def create_user(db: Session, data):
    existing = db.query(User).filter(
        or_(
            User.username == data.username,
            User.email == data.email
        )
    ).first()

    if existing:
        if existing.username == data.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if existing.email == data.email:
            raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        username=data.username,
        password=hash_password(data.password),
        full_name=data.full_name,
        email=data.email,
        role_id=data.role_id,
        status=data.status,
        create_date=datetime.now()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user_id: int, data):
    user = get_user(db, user_id)
    if not user:
        return None
    # ---------------------------
    #    ตรวจสอบ username ซ้ำ
    # ---------------------------
    if data.username is not None and data.username != user.username:
        existing_username = db.query(User).filter(
            User.username == data.username,
            User.user_id != user_id
        ).first()

        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

    # ---------------------------
    #    ตรวจสอบ email ซ้ำ
    # ---------------------------
    if data.email is not None and data.email != user.email:
        existing_email = db.query(User).filter(
            User.email == data.email,
            User.user_id != user_id
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.email is not None:
        user.email = data.email
    if data.role_id is not None:
        user.role_id = data.role_id
    if data.password:
        user.password = hash_password(data.password)
    # status is a boolean; check explicitly for None so False is accepted
    if getattr(data, 'status', None) is not None:
        user.status = data.status

    db.commit()
    return user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()

def search_user(db: Session, keyword: str = ""):
    q = db.query(User)
    if keyword:
        q = q.filter(User.username.ilike(f"%{keyword}%"))
    return q.order_by(User.user_id.desc()).all()


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user:
        db.delete(user)
        db.commit()
