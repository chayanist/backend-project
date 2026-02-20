from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.deps import get_db, get_current_user
from core.messages import MessageEnum
from core.response import success


router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(get_current_user)])

@router.get("/dropdown")
def role_dropdown(db: Session = Depends(get_db)):
    roles = db.execute(
        text("""
        SELECT role_id AS key, role_name AS label
        FROM api.roles
        ORDER BY role_id
        """)
    ).mappings().all()

    return success(roles, MessageEnum.SUCCESS)
