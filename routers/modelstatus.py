from fastapi import APIRouter, Depends , Body
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.deps import get_db
from core.messages import MessageEnum
from core.response import success
from models.modelstatus import ModelStatus

router = APIRouter(prefix="/model", tags=["model"])

@router.get("/status")
def status(db: Session = Depends(get_db)):
    obj = db.query(ModelStatus).first()
    return success(obj.status if obj else None, MessageEnum.SUCCESS)

@router.put("/start")
def start(db: Session = Depends(get_db)):
    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()

    if not obj:
        obj = ModelStatus(id=1, status=True)
        db.add(obj)
    else:
        obj.status = True

    db.commit()
    ### ใช้ตัวนี้ call function model
    ###Thread(target=run_model_loop, daemon=True).start()

    return success(True, MessageEnum.SUCCESS)

@router.put("/stop")
def stop(data: dict = Body(...), db: Session = Depends(get_db)):
    print("STOP BODY =", data) 
    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()

    if not obj:
        return success(False, "Model not initialized")

    # ⭐ reset ทุกอย่าง
    obj.status = False

    # ถ้ามี column unit_id
    if hasattr(obj, "unit_id"):
        obj.unit_id = None

    db.commit()
    db.refresh(obj)   # <<< สำคัญมาก

    return success(True, MessageEnum.SUCCESS)
