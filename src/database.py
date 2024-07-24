from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_USER = os.getenv('PGUSER')
DATABASE_PASSWORD = os.getenv('PGPASSWORD')
DATABASE_HOST = os.getenv('PGHOST')
DATABASE_NAME = os.getenv('PGDATABASE')
DATABASE_PORT = os.getenv('PGPORT')

DATABASE_URL = f"postgresql://{DATABASE_USER}:{
    DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
