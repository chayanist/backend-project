from fastapi import FastAPI
from routers import auth, home, units,roles,user,modelstatus
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Agency Service")

# app.mount(
#     "/images",
#     StaticFiles(directory="/home/ricebelly/riceBellyProjectV4/ai_engine/store"),
#     name="images",
# )

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*", 
    allow_origins=["*"],        # 👈 allow ALL origins
    allow_credentials=True,
    allow_methods=["*"],        # 👈 allow ALL HTTP methods
    allow_headers=["*"],        # 👈 allow ALL headers
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
