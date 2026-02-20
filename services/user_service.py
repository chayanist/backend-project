from sqlalchemy.orm import Session
from models.user import User
from core.security import hash_password
from datetime import datetime

def create_user(db: Session, data):
    print(len(data.password.encode("utf-8")))
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

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()

def search_user(db: Session, keyword: str = ""):
    q = db.query(User)
    if keyword:
        q = q.filter(User.username.ilike(f"%{keyword}%"))
    return q.order_by(User.user_id.desc()).all()

def update_user(db: Session, user_id: int, data):
    user = get_user(db, user_id)
    if not user:
        return None

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

def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user:
        db.delete(user)
        db.commit()
