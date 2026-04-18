import os
import json
import shutil
import subprocess
import threading
import asyncio
from pathlib import Path
import time
import glob
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
# SIGNAL_FILE = AI_DIR / "stop_ai.signal" # เปลี่ยนไปใช้การเคลียร์ทั้ง 2 ไฟล์ในฟังก์ชันแทน

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

def parse_accuracy_value(val_str):
    """ฟังก์ชันช่วยตัดตัวหนังสือและ % ออก แล้วแปลงเป็น Float ทศนิยม 2 ตำแหน่ง"""
    if not val_str or "Not tested" in str(val_str):
        return 0.00
    try:
        # ตัดตรง '%' แล้วเอาตัวเลขด้านหน้ามาแปลงเป็น float
        return float(str(val_str).split('%')[0])
    except Exception:
        return 0.00

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
            #1. ดึง status ล่าสุด (ประยุกต์จาก: ดึง unit_id ล่าสุดที่เพิ่งบันทึกไว้ตอน Stop)
            status_obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
            if not status_obj or not status_obj.inspection_id:
                print("[Sweeper] Error: No active inspection_id found in ModelStatus.")
                return
            
            current_insp_id = status_obj.inspection_id

            #2. รีเซ็ต Sequence ของ Primary Key ทั้งสองตาราง
            db.execute(text("""
                -- รีเซ็ตของ ricegrain (ที่มีอยู่แล้ว)
                SELECT setval(pg_get_serial_sequence('api.ricegrain', 'rice_grain_id'), COALESCE(MAX(rice_grain_id), 0) + 1, false) FROM api.ricegrain;
                
                -- เพิ่ม: รีเซ็ตของ classified (แทน inspection ตัวปัญหาเดิม)
                SELECT setval(pg_get_serial_sequence('api.classified', 'classified_id'), COALESCE(MAX(classified_id), 0) + 1, false) FROM api.classified;
            """))

            for session_dir in all_sessions:
                json_path = session_dir / "data.json"
                summary_path = session_dir / "accuracy_summary.json" 
                
                if not json_path.exists():
                    continue

                with open(json_path, 'r', encoding='utf-8') as f:
                    grain_data = json.load(f)

                # คำนวณ Round Number
                round_count = db.execute(text("""
                    SELECT COUNT(*) FROM api.classified WHERE inspection_id = :insp_id
                """), {"insp_id": current_insp_id}).scalar()
                
                new_round_number = round_count + 1

                if new_round_number > 3:
                    print(f"[Sweeper] Warning: Inspection {current_insp_id} already has 3 rounds. Skipping.")
                    continue

                # นับจำนวนเมล็ดข้าวแยกตาม Level
                levels = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for item in grain_data:
                    lv = item.get("bellyWhiteLevel", 0)
                    if lv in levels:
                        levels[lv] += 1
                
                total_grains = len(grain_data)

                #3. สร้างรายการ Classified ใหม่ (แทน: สร้างรายการ Inspection ใหม่)
                result = db.execute(text("""
                    INSERT INTO api.classified (
                        inspection_id, level0, level1, level2, level3, level4, level5, total, round_number, date_time
                    )
                    VALUES (
                        :insp_id, :l0, :l1, :l2, :l3, :l4, :l5, :total, :round_number, NOW()
                    )
                    RETURNING classified_id
                """), {
                    "insp_id": current_insp_id,
                    "l0": levels[0], "l1": levels[1], "l2": levels[2],
                    "l3": levels[3], "l4": levels[4], "l5": levels[5],
                    "total": total_grains,
                    "round_number": new_round_number
                })
                
                new_classified_id = result.fetchone()[0]

                #4. บันทึกข้อมูลเมล็ดข้าวแต่ละเมล็ด
                for item in grain_data:
                    file_name = os.path.basename(item["Image Path"])
                    final_image_path = str(STORE_ROOT / session_dir.name / file_name)

                    db.execute(text("""
                        INSERT INTO api.ricegrain (classified_id, image, belly_white_level, belly_white_ratio)
                        VALUES (:class_id, :img, :lvl, :ratio)
                    """), {
                        "class_id": new_classified_id,
                        "img": final_image_path,
                        "lvl": item.get("bellyWhiteLevel", 0),
                        "ratio": item.get("bellyWhiteRatio", 0.0)
                    })

                # ตรวจสอบและบันทึกข้อมูลตาราง Accuracy (กรณีเป็น Test Mode)
                if summary_path.exists():
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        summary_file_data = json.load(f).get("summary", {})
                    
                    db.execute(text("""
                        INSERT INTO api.accuracy (
                            classified_id, level0, level1, level2, level3, level4, level5, overall
                        ) VALUES (
                            :cls_id, :acc0, :acc1, :acc2, :acc3, :acc4, :acc5, :overall
                        )
                    """), {
                        "cls_id": new_classified_id,
                        "acc0": parse_accuracy_value(summary_file_data.get("class_0")),
                        "acc1": parse_accuracy_value(summary_file_data.get("class_1")),
                        "acc2": parse_accuracy_value(summary_file_data.get("class_2")),
                        "acc3": parse_accuracy_value(summary_file_data.get("class_3")),
                        "acc4": parse_accuracy_value(summary_file_data.get("class_4")),
                        "acc5": parse_accuracy_value(summary_file_data.get("class_5")),
                        "overall": parse_accuracy_value(summary_file_data.get("overall_accuracy"))
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
        for signal_file in ["stop_ai.signal", "stop_eval.signal"]:
            sig_path = AI_DIR / signal_file
            if sig_path.exists():
                os.remove(sig_path)
                print(f"[System] {signal_file} cleared.")
    except Exception as e:
        print(f"[System] Error clearing signal files: {e}")

# ================= [WEBSOCKET] =================

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

# ================= [API ROUTERS] =================

@router.get("/status")
def get_model_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    obj = db.query(ModelStatus).first()
    return success(obj, MessageEnum.SUCCESS)

@router.post("/start")
def start(data: dict = Body(...),db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clear_signal()
    
    # ล้างโฟลเดอร์ results ก่อนเริ่มทำงานเสมอ ป้องกันไฟล์ค้าง
    try:
        if RESULTS_DIR.exists():
            shutil.rmtree(RESULTS_DIR)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        print("[System] Cleared 'results' directory successfully.")
    except Exception as e:
        print(f"[System] Warning: Failed to clear 'results' directory: {e}")

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
    
    if obj and obj.status == True:
        return {
            "data": False,
            "message": "ระบบกำลังทำงานอยู่แล้ว ไม่สามารถรันซ้ำได้",
            "round_count": count
        }

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

    def run_ai_task(is_basic_mode):
        global broadcast_loop, ws_connections 
        time.sleep(1) 
        
        try:
            python_exe = str(AI_DIR / "venv_ai" / "bin" / "python")
            
            script_to_run = "accuracy_ai.py" if is_basic_mode else "main_ai.py"
            
            proc = subprocess.Popen(
                [python_exe, script_to_run],
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
                    try:
                        asyncio.run_coroutine_threadsafe(
                            ws.send_text("\n[SYSTEM] AI Stopped. Saving data to database..."), 
                            broadcast_loop
                        )
                    except:
                        pass

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

    threading.Thread(
        target=run_ai_task, 
        args=(basic_mode,), 
        daemon=True
    ).start()
    
    return success(True, MessageEnum.SUCCESS)

@router.put("/stop")
def stop_ai(data: dict = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """สั่งหยุด AI โดยส่งสัญญาณผ่านไฟล์"""
    
    raw_unit_id = data.get("unit_id")
    unit_id = raw_unit_id.get("unit_id") if isinstance(raw_unit_id, dict) else raw_unit_id
    
    obj = db.query(ModelStatus).filter(ModelStatus.id == 1).first()
    if obj:
        obj.unit_id = unit_id  

    db.commit()
    try:
        with open(AI_DIR / "stop_ai.signal", "w") as f:
            f.write("stop")
        with open(AI_DIR / "stop_eval.signal", "w") as f:
            f.write("stop")
            
        print("[Backend] Stop signals sent to AI Engine.")
    except Exception as e:
        print(f"[Backend] Signal Error: {e}")

    return success(True, MessageEnum.SUCCESS)

@router.get("/latest-image")
def get_latest_result_image():
    # 1. กำหนดโฟลเดอร์เป้าหมาย
    results_dir = "/home/ricebelly/riceBellyProjectV4/ai_engine/results"
    
    # 2. ค้นหาไฟล์ .jpg และ .png ทั้งหมดในโฟลเดอร์ results และซับโฟลเดอร์
    list_of_files = glob.glob(f"{results_dir}/**/*.jpg", recursive=True) + \
                    glob.glob(f"{results_dir}/**/*.png", recursive=True)
    
    # 3. ถ้าไม่มีไฟล์เลย
    if not list_of_files:
        return {"latest_image": None}
        
    # 4. หาไฟล์ที่เพิ่งถูกสร้างขึ้นมาใหม่ที่สุด (Latest by creation/modification time)
    latest_file = max(list_of_files, key=os.path.getmtime)
    
    # 5. ตัด Path ส่วนหน้าทิ้ง ให้เหลือแค่ results/... เพื่อส่งให้หน้าเว็บ
    # ตัวอย่าง: /home/.../ai_engine/results/session1/img.jpg -> results/session1/img.jpg
    relative_path = latest_file.split("ai_engine/")[-1]
    
    return {"latest_image": f"http://localhost:8000/{relative_path}"}