from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
DATABASE_URL = "postgresql://api_user:api_password@172.20.10.4:5432/postgres"



engine = create_engine(
    DATABASE_URL,
    connect_args={
        "options": "-csearch_path=api"
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
