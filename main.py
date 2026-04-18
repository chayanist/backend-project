import os
from fastapi import FastAPI
from routers import auth, home, units, roles, user, modelstatus
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Agency Service")

# 🚀 1. กำหนด Path ของโฟลเดอร์
RESULTS_DIR = "/home/ricebelly/riceBellyProjectV4/ai_engine/results"
STORE_DIR = "/home/ricebelly/riceBellyProjectV4/ai_engine/store"

# 🚀 2. สั่งสร้างโฟลเดอร์อัตโนมัติ (ถ้ายังไม่มี) ป้องกัน Backend พังตอนรัน!
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(STORE_DIR, exist_ok=True)

# 🚀 3. Mount โฟลเดอร์ได้ตามปกติ
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")
app.mount(
    "/images",
    StaticFiles(directory="/home/ricebelly/riceBellyProjectV4/ai_engine/store"),
    name="images",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*", 
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(units.router)
app.include_router(roles.router)
app.include_router(user.router)
app.include_router(modelstatus.router)
app.include_router(home.router)

@app.get("/")
def root():
    return {"message": "API is running"}