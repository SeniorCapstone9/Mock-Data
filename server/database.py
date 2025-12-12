from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./medical_scribe.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    title = Column(String, nullable=True)
    raw_transcript = Column(Text, nullable=True)
    full_transcript = Column(Text, nullable=True)
    redacted_transcript = Column(Text, nullable=True)
    soap_summary = Column(Text, nullable=True)
    status = Column(String, default="processing") # processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Analytics
    duration = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    speaker_count = Column(Integer, default=0)
    
    # Advanced AI Analytics
    sentiment = Column(String, nullable=True)
    medical_tags = Column(Text, nullable=True) # JSON string
    action_items = Column(Text, nullable=True) # JSON string
    
    # RBAC
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    doctor = relationship("User", foreign_keys=[doctor_id])
    patient = relationship("User", foreign_keys=[patient_id])

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="patient") # admin, doctor, patient

class ScannedNote(Base):
    __tablename__ = "scanned_notes"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String)
    extracted_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    doctor_id = Column(Integer, ForeignKey("users.id"))
    doctor = relationship("User", back_populates="scanned_notes")

User.scanned_notes = relationship("ScannedNote", back_populates="doctor")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
