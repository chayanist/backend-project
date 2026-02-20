from core.database import SessionLocal
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from core.config import SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from models.user import User
from models.role import Role


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # attach role name if available
        if getattr(user, "role_id", None) is not None:
            role = db.query(Role).filter(Role.role_id == user.role_id).first()
            user.role_name = role.role_name if role else None

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
