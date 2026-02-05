from fastapi import APIRouter, HTTPException
from core.messages import MessageEnum
from core.response import success
from schemas.auth import LoginRequest, TokenResponse
from core.security import create_access_token, verify_password
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])

# mock user
fake_user = {
    "username": "admin",
    "password": "1234"  # bcrypt hash
}

user = {
    "id":1,
    "username": "admin",
    "role": "admin"  # bcrypt hash
}


@router.post("/login")
def login(req: LoginRequest):
    if req.username != fake_user["username"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # if not verify_password(req.password, fake_user["password"]):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": req.username},
        expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    
    return success(
        data={
                "access_token": token,
                "user":user
              },
        message=MessageEnum.LOGIN_SUCCESS
    )
