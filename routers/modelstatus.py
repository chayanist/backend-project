import os
import json
import shutil
import subprocess
import threading
from pathlib import Path
from fastapi import APIRouter, Depends, Body
from sqlalchemy import text
from sqlalchemy.orm import Session

# Import ส่วนจัดการ Database และ Model
from core.database import SessionLocal 
from core.deps import get_db
from core.messages import MessageEnum
from core.response import success
from models.modelstatus import ModelStatus

router = APIRouter(prefix="/model", tags=["model"])

# ================= ⚙️ CONFIGURATION =================
BASE_DIR = Path(__file__).resolve().parents[2]
AI_DIR = BASE_DIR / "ai_engine"
RESULTS_DIR = AI_DIR / "results"
STORE_ROOT = AI_DIR / "store"
SIGNAL_FILE = AI_DIR / "stop_ai.signal"

# ================= 🧹 [SWEEPER] ย้ายข้อมูลจาก JSON ลง DB =================
def data_sweeper():
    """ทำหน้าที่กวาดไฟล์ JSON ใน results/ เข้า Database"""
    try:
        if not RESULTS_DIR.exists(): return
        all_sessions = [d for d in RESULTS_DIR.iterdir() if d.is_dir()]
        if not all_sessions: return
        
        db = SessionLocal()
        try:
            # 🚀 1. ดึง unit_id ล่าสุดที่เพิ่งบันทึกไว้ตอน Stop
            status_obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
            current_unit_id = status_obj.unit_id if (status_obj and status_obj.unit_id) else 1
            
            # 🚀 2. รีเซ็ต Sequence ของ Primary Key (กัน Error ID ซ้ำ)
            db.execute(text("""
                SELECT setval(
                    pg_get_serial_sequence('api.ricegrain', 'rice_grain_id'), 
                    COALESCE(MAX(rice_grain_id), 0) + 1, 
                    false
                ) FROM api.ricegrain;
            """))

            for session_dir in all_sessions:
                json_path = session_dir / "data.json"
                if not json_path.exists(): continue
                
                with open(json_path, 'r', encoding='utf-8') as f:
                    grain_data = json.load(f)

                # 🚀 3. สร้างรายการ Inspection ใหม่
                result = db.execute(text("""
                    INSERT INTO api.inspection (date_time, unit_id) 
                    VALUES (NOW(), :unit_id)
                    RETURNING inspection_id
                """), {"unit_id": current_unit_id})
                new_insp_id = result.fetchone()[0]

                # 🚀 4. บันทึกข้อมูลเมล็ดข้าวแต่ละเมล็ด
                for item in grain_data:
                    file_name = os.path.basename(item["Image Path"])
                    # กำหนด Path ใหม่ที่จะย้ายไปเก็บถาวร
                    final_image_path = str(STORE_ROOT / session_dir.name / file_name)
                    
                    db.execute(text("""
                        INSERT INTO api.ricegrain (inspection_id, image, belly_white_level, belly_white_ratio)
                        VALUES (:insp_id, :img, :lvl, :ratio)
                    """), {
                        "insp_id": new_insp_id,
                        "img": final_image_path,
                        "lvl": item.get("bellyWhiteLevel", 0),
                        "ratio": item.get("bellyWhiteRatio", 0.0)
                    })

                db.commit() 

                # 🚀 5. ย้ายโฟลเดอร์จาก results/ ไปยัง store/ (เก็บถาวร)
                dest_session_dir = STORE_ROOT / session_dir.name
                STORE_ROOT.mkdir(parents=True, exist_ok=True)
                if dest_session_dir.exists(): 
                    shutil.rmtree(dest_session_dir)
                shutil.move(str(session_dir), str(dest_session_dir))

        except Exception as e:
            db.rollback()
            print(f"[Sweeper] SQL Error: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"[Sweeper] General Error: {e}")

def clear_signal():
    """ลบไฟล์ signal เพื่อให้ระบบพร้อมสำหรับการทำงานครั้งถัดไป"""
    try:
        if SIGNAL_FILE.exists():
            os.remove(SIGNAL_FILE)
            print(f"[System] Signal file cleared.")
    except Exception as e:
        print(f"[System] Error clearing signal file: {e}")
# ================= 🚀 [API ROUTERS] =================
@router.get("/status")
def status(db: Session = Depends(get_db)):
    obj = db.query(ModelStatus).first()
    return success(obj.status if obj else None, MessageEnum.SUCCESS)

@router.put("/start")
def start(db: Session = Depends(get_db)):
    """สั่งเริ่มทำงาน AI"""
    # ลบไฟล์สัญญาณหยุดถ้ามีค้างอยู่
    clear_signal()

    # อัปเดตสถานะใน DB ว่ากำลังทำงาน
    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
    if not obj:
        obj = ModelStatus(id=1, status=True)
        db.add(obj)
    else:
        obj.status = True
    db.commit()

    def run_ai_task():
        try:
            # รัน AI Engine ผ่าน Subprocess
            python_exe = str(AI_DIR / "venv_ai" / "bin" / "python")
            subprocess.run([python_exe, "main_ai.py"], cwd=str(AI_DIR))
        finally:
            # 🚀 2. เมื่อ AI จบการทำงาน (ไม่ว่าจะจบแบบปกติ หรือถูกสั่ง Stop)
            # ต้องล้าง Signal ทันที เพื่อไม่ให้ค้างคาในการรันครั้งหน้า
            clear_signal()
            
            # กวาดข้อมูลลง DB
            data_sweeper() 
            
            # อัปเดตสถานะกลับเป็น False เมื่อทุกอย่างเสร็จสิ้น (กรณี AI จบงานเอง)
            with SessionLocal() as db_session:
                status_obj = db_session.query(ModelStatus).filter(ModelStatus.id == 1).first()
                if status_obj:
                    status_obj.status = False
                    db_session.commit()

    threading.Thread(target=run_ai_task, daemon=True).start()
    return success(True, MessageEnum.SUCCESS)

@router.put("/stop")
def stop(data: dict = Body(...), db: Session = Depends(get_db)):
    """สั่งหยุด AI พร้อมส่ง unit_id มาบันทึก"""
    unit_id = data.get("unit_id")
    print("STOP BODY =", data)
    
    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
    if obj:
        obj.status = False
        obj.unit_id = unit_id  # 🚀 บันทึก unit_id ไว้ให้ Sweeper ใช้งาน
        db.commit()
        db.refresh(obj)
    # สร้างไฟล์ stop_ai.signal เพื่อบอกให้ main_ai.py หยุดทำงาน
    try:
        with open(SIGNAL_FILE, "w") as f:
            f.write("stop")
    except Exception as e:
        print(f"[Backend] Signal Error: {e}")

    return success(True, MessageEnum.SUCCESS)