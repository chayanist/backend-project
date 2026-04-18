import os
import shutil  # 🚀 1. เพิ่ม import shutil สำหรับลบโฟลเดอร์
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
from sqlalchemy import or_
from models.modelstatus import ModelStatus

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(
            User.username == req.username,
            User.email == req.username
        )
    ).filter(User.status == True).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ==========================================
    # โค้ดเคลียร์สถานะ AI (อัปเดต: สั่งลบทิ้ง ไม่เซฟลง DB)
    # ==========================================
    try:
        status_obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
        
        # เช็คว่าถ้า AI กำลังรันอยู่จริงๆ ถึงจะสั่งล้างบาง
        if status_obj and status_obj.status == True:
            # A. รีเซ็ตสถานะเป็น False
            status_obj.status = False
            db.commit()

            ai_dir = "/home/ricebelly/riceBellyProjectV4/ai_engine"
            
            # B. ส่ง Signal ปิดกล้อง/ปิด Python
            with open(os.path.join(ai_dir, "stop_ai.signal"), "w") as f:
                f.write("stop")
            with open(os.path.join(ai_dir, "stop_eval.signal"), "w") as f:
                f.write("stop")
            
            # C. ลบข้อมูลที่วิเคราะห์ค้างไว้ทิ้งไปเลย! (เพื่อป้องกันไม่ให้ถูกเซฟลง Database)
            results_dir = os.path.join(ai_dir, "results")
            if os.path.exists(results_dir):
                shutil.rmtree(results_dir, ignore_errors=True)
                os.makedirs(results_dir, exist_ok=True) # สร้างโฟลเดอร์เปล่าๆ คืนไว้ ป้องกัน error ตอนรันรอบหน้า
                
            print("[AUTH] User logged in. AI aborted and dirty data discarded.")
            
    except Exception as e:
        print(f"[AUTH Warning] Failed to reset AI status: {e}")
    # ==========================================

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