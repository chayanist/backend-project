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
from core.database import SessionLocal  # ใช้สร้าง Session ใน Background Thread
from core.deps import get_db, get_current_user
from core.messages import MessageEnum
from core.response import success
from models.modelstatus import ModelStatus

router = APIRouter(prefix="/model", tags=["model"], dependencies=[Depends(get_current_user)])

# ================= ⚙️ CONFIGURATION =================
BASE_DIR = Path(__file__).resolve().parents[2]
AI_DIR = BASE_DIR / "ai_engine"
RESULTS_DIR = AI_DIR / "results"
STORE_ROOT = AI_DIR / "store"
SIGNAL_FILE = AI_DIR / "stop_ai.signal"

# ================= 🧹 [SWEEPER] กวาดลง DB ก่อน แล้วค่อยย้าย =================
def data_sweeper():
    try:
        if not RESULTS_DIR.exists():
            return

        all_sessions = [d for d in RESULTS_DIR.iterdir() if d.is_dir()]
        if not all_sessions:
            return
        
        db = SessionLocal()
        try:
            for session_dir in all_sessions:
                json_path = session_dir / "data.json"
                if not json_path.exists():
                    continue

                with open(json_path, 'r', encoding='utf-8') as f:
                    grain_data = json.load(f)

                # --- 🚀 ขั้นตอนที่ 1: Insert ลงตาราง inspection ---
                # ปล่อยให้ DB เจน ID ให้เอง และใช้ RETURNING เพื่อเอาค่ามาใช้ต่อ
                result = db.execute(text("""
                    INSERT INTO api.inspection (date_time, unit_id) 
                    VALUES (NOW(), :unit_id)
                    RETURNING inspection_id
                """), {"unit_id": 1})
                
                new_insp_id = result.fetchone()[0]
                print(f"[Sweeper] DB Generated Inspection ID: {new_insp_id}")

                # --- 🚀 ขั้นตอนที่ 2: บันทึกข้อมูลลง ricegrain โดยใช้ ID ที่ได้มา ---
                for item in grain_data:
                    file_name = os.path.basename(item["Image Path"])
                    final_image_path = str(STORE_ROOT / session_dir.name / file_name)

                    db.execute(text("""
                        INSERT INTO api.ricegrain (inspection_id, image, belly_white_level, belly_white_ratio)
                        VALUES (:insp_id, :img, :lvl, :ratio)
                    """), {
                        "insp_id": new_insp_id,
                        "img": final_image_path,
                        "lvl": item["bellyWhiteLevel"],
                        "ratio": item["bellyWhiteRatio"]
                    })

                # --- 🚀 ขั้นตอนที่ 3: Commit และย้ายไฟล์ ---
                db.commit() 
                print(f"[Sweeper] DB Sync completed for Inspection {new_insp_id}")

                dest_session_dir = STORE_ROOT / session_dir.name
                STORE_ROOT.mkdir(parents=True, exist_ok=True)
                
                if dest_session_dir.exists():
                    shutil.rmtree(dest_session_dir)
                
                shutil.move(str(session_dir), str(dest_session_dir))
                print(f"[Sweeper] Folder moved to store: {session_dir.name}")

            print("[Sweeper] All processes finished successfully.")
        except Exception as e:
            db.rollback() 
            print(f"[Sweeper] SQL Error: {e}")
        finally:
            db.close() 
            
    except Exception as e:
        print(f"[Sweeper] General Error: {e}")

# ================= 🚀 [STATUS & CONTROL] API ROUTERS =================

@router.get("/status")
def status(db: Session = Depends(get_db)):
    """[STATUS] เช็กสถานะจากตาราง api.modelstatus"""
    obj = db.query(ModelStatus).first()
    return success(obj.status if obj else None, MessageEnum.SUCCESS)

@router.put("/start")
def start(db: Session = Depends(get_db)):
    """[START] เริ่มรัน AI และรอจนจบเพื่อกวาดข้อมูล"""
    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
    if not obj:
        obj = ModelStatus(id=1, status=True)
        db.add(obj)
    else:
        obj.status = True
    db.commit()

    def run_ai_task():
        # รัน AI ผ่าน venv_ai
        python_exe = str(AI_DIR / "venv_ai" / "bin" / "python")
        subprocess.run([python_exe, "main_ai.py"], cwd=str(AI_DIR))
        
        # เมื่อ AI ปิดตัวลง (Exit) ให้กวาดข้อมูลลง DB และย้ายโฟลเดอร์
        data_sweeper()

    threading.Thread(target=run_ai_task, daemon=True).start()
    return success(True, MessageEnum.SUCCESS)

@router.put("/stop")
def stop(data: dict = Body(...), db: Session = Depends(get_db)):
    """[STOP] ส่งสัญญาณหยุดและรีเซ็ตค่าระบบ"""
    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
    if obj:
        obj.status = False
        if hasattr(obj, "unit_id"):
            obj.unit_id = None
        db.commit()
        db.refresh(obj)

    # ส่งสัญญาณผ่านไฟล์สัญญาณ
    try:
        with open(SIGNAL_FILE, "w") as f:
            f.write("stop")
    except Exception as e:
        print(f"[Backend] Signal Error: {e}")

    return success(True, MessageEnum.SUCCESS)