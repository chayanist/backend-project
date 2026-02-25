import os
import json
import shutil
import subprocess
import threading
import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, Body, WebSocket, WebSocketDisconnect
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from jose import jwt, JWTError

# Import ส่วนจัดการ Database และ Model
from core.database import SessionLocal  # ใช้สร้าง Session ใน Background Thread
from core.deps import get_db, get_current_user
from core.config import SECRET_KEY, ALGORITHM
from core.messages import MessageEnum
from core.response import success
from models.classified import Classified
from models.user import User
from models.modelstatus import ModelStatus

router = APIRouter(prefix="/model", tags=["model"])

# ================= ⚙️ CONFIGURATION =================
BASE_DIR = Path(__file__).resolve().parents[2]
AI_DIR = BASE_DIR / "ai_engine"
RESULTS_DIR = AI_DIR / "results"
STORE_ROOT = AI_DIR / "store"
SIGNAL_FILE = AI_DIR / "stop_ai.signal"

# WebSocket broadcast state
ws_connections = set()
broadcast_loop = None

# ================= 🧹 [SWEEPER] Helper Functions =================
def check_inspection_available(db, inspection_id: int):
    """
    คืน (ok, count, message)
    ok = True ถ้ายัง start ได้
    """

    count = (
        db.query(func.count(Classified.classified_id))
        .filter(Classified.inspection_id == inspection_id)
        .scalar()
    )

    if count >= 3:
        return False, count, "inspection นี้ตรวจครบ 3 รอบแล้ว"

    return True, count, None

def data_sweeper():
    """ทำหน้าที่กวาดไฟล์ JSON ใน results/ เข้า Database"""
    try:
        if not RESULTS_DIR.exists():
            return
        
        all_sessions = [d for d in RESULTS_DIR.iterdir() if d.is_dir()]
        if not all_sessions:
            return

        db = SessionLocal()
        try:
            # 🚀 1. ดึง unit_id ล่าสุดที่เพิ่งบันทึกไว้ตอน Stop
            status_obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
            current_unit_id = status_obj.unit_id if (status_obj and status_obj.unit_id) else 1

            # 🚀 2. รีเซ็ต Sequence ของ Primary Key ทั้งสองตาราง
            db.execute(text("""
                -- รีเซ็ตของ ricegrain (ที่มีอยู่แล้ว)
                SELECT setval(
                    pg_get_serial_sequence('api.ricegrain', 'rice_grain_id'),
                    COALESCE(MAX(rice_grain_id), 0) + 1,
                    false
                ) FROM api.ricegrain;

                -- เพิ่ม: รีเซ็ตของ inspection (ตัวปัญหา)
                SELECT setval(
                    pg_get_serial_sequence('api.inspection', 'inspection_id'),
                    COALESCE(MAX(inspection_id), 0) + 1,
                    false
                ) FROM api.inspection;
            """))

            for session_dir in all_sessions:
                json_path = session_dir / "data.json"
                if not json_path.exists():
                    continue

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
            print("[System] Signal file cleared.")
    except Exception as e:
        print(f"[System] Error clearing signal file: {e}")

# ================= 🔌 [WEBSOCKET] =================

@router.websocket("/stream")
async def stream_websocket(websocket: WebSocket):
    """WebSocket stream AI subprocess output in real-time."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=1008)
            return

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
        finally:
            db.close()

        if not user:
            await websocket.close(code=1008)
            return
            
    except JWTError:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    
    global broadcast_loop
    broadcast_loop = asyncio.get_event_loop()
    ws_connections.add(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("[WS] Web terminal disconnected.")
    finally:
        ws_connections.discard(websocket)

# ================= 🚀 [API ROUTERS] =================

@router.get("/status")
def get_model_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    obj = db.query(ModelStatus).first()
    return success(obj, MessageEnum.SUCCESS)

@router.post("/start")
def start(data: dict = Body(...),db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clear_signal()
    unit_id = data.get("unit_id")
    inspection_id = data.get("inspection_id")
    # BOOLEAN สำหรับโหมดการรัน
    basic_mode = data.get("basic_mode")

    ok, count, msg = check_inspection_available(db, inspection_id)

    if not ok:
        return {
            "data": False,
            "message": msg,
            "round_count": count
        }

    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
    if not obj:
        obj = ModelStatus(
            id=1,
            status=True,
            unit_id=unit_id,
            inspection_id=inspection_id,
            basic_mode=basic_mode
        )
        db.add(obj)
    else:
        obj.status = True
        obj.unit_id = unit_id
        obj.inspection_id = inspection_id
        obj.basic_mode = basic_mode
    db.commit()

    def run_ai_task():
        global broadcast_loop, ws_connections
        try:
            python_exe = str(AI_DIR / "venv_ai" / "bin" / "python")
            proc = subprocess.Popen(
                [python_exe, "main_ai.py"],
                cwd=str(AI_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
            )

            for raw_line in proc.stdout:
                line = raw_line.rstrip()
                print(line)
                if broadcast_loop and ws_connections:
                    for ws in list(ws_connections):
                        try:
                            asyncio.run_coroutine_threadsafe(ws.send_text(line), broadcast_loop)
                        except:
                            ws_connections.discard(ws)
            
            proc.wait() # รอจนกว่า Subprocess จะจบจริงๆ

        except Exception as e:
            print(f"[Thread Error] {e}")
        
        finally:
            # --- ขั้นตอนหลังจาก AI หยุด (กด Stop หรือจบเอง) ---
            print("[System] Finalizing process...")
            
            # 1. แจ้ง Terminal หน้าเว็บ
            if broadcast_loop and ws_connections:
                for ws in list(ws_connections):
                    asyncio.run_coroutine_threadsafe(
                        ws.send_text("\n[SYSTEM] AI Stopped. Saving data to database..."), 
                        broadcast_loop
                    )

            # 2. จัดการข้อมูล (Sweeper)
            data_sweeper() 
            clear_signal()
            
            # 3. อัปเดตสถานะใน DB เป็น False (เพื่อให้ปุ่มหน้าเว็บเปลี่ยนสี)
            with SessionLocal() as db_session:
                status_obj = db_session.query(ModelStatus).filter(ModelStatus.id == 1).first()
                if status_obj:
                    status_obj.status = False
                    db_session.commit()

            # 4. ส่งสัญญาณสุดท้ายบอกหน้าเว็บว่า "เสร็จสิ้นทุกอย่างแล้ว"
            if broadcast_loop and ws_connections:
                for ws in list(ws_connections):
                    try:
                        asyncio.run_coroutine_threadsafe(ws.send_text("PROCESS_COMPLETE"), broadcast_loop)
                    except:
                        pass

    threading.Thread(target=run_ai_task, daemon=True).start()
    return success(True, MessageEnum.SUCCESS)

@router.put("/stop")
def stop_ai(data: dict = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """สั่งหยุด AI โดยส่งสัญญาณผ่านไฟล์"""
    unit_id = data.get("unit_id")
    
    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
    if obj:
        obj.unit_id = unit_id  
        obj.status = False 

    db.commit()
    try:
        with open(SIGNAL_FILE, "w") as f:
            f.write("stop")
        print("[Backend] Stop signal sent to AI Engine.")
    except Exception as e:
        print(f"[Backend] Signal Error: {e}")

    return success(True, MessageEnum.SUCCESS)