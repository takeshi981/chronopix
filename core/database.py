from sqlmodel import SQLModel, Session, create_engine
import os

DB_PATH = os.path.join("data", "photos.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
