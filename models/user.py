from sqlalchemy import Column, Integer, String , Boolean,DateTime
from core.database import Base

class User(Base):
    __tablename__ = "users"


    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    full_name = Column(String)
    email = Column(String)

    role_id = Column(Integer)
    status = Column(Boolean)
    create_date = Column(DateTime)
    default = Column(Boolean, default=False)