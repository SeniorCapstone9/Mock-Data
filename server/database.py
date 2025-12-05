from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./medical_scribe.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    raw_transcript = Column(Text, nullable=True)
    redacted_transcript = Column(Text, nullable=True)
    soap_summary = Column(Text, nullable=True)
    status = Column(String, default="processing") # processing, completed, failed

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
