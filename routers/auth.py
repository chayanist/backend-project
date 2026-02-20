from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.messages import MessageEnum
from core.response import success
from schemas.auth import LoginRequest
from core.security import create_access_token, verify_password
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from core.deps import get_db
from models.user import User
from models.role import Role


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).filter(User.status == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": user.username},
        expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    user_data = {
        "user_id": user.user_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role_id": user.role_id,
        "status": user.status,
        "role_name": None,
    }

    if user.role_id is not None:
        role = db.query(Role).filter(Role.role_id == user.role_id).first()
        user_data["role_name"] = role.role_name if role else None

    return success(
        data={
            "access_token": token,
            "user": user_data,
        },
        message=MessageEnum.LOGIN_SUCCESS,
    )
