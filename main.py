from fastapi import FastAPI
from routers import auth, units,roles,user
import models
app = FastAPI(title="Agency Service")

app.include_router(auth.router)
app.include_router(units.router)
app.include_router(roles.router)
app.include_router(user.router)

@app.get("/")
def root():
    return {"message": "API is running"}
