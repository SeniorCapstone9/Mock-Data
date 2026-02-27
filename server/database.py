from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, Float, ForeignKey, UniqueConstraint
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
    user_id = Column(Integer, ForeignKey("users.id"))

    #medical stats
    hba1c = Column(Float, nullable=True) # Add this
    bmi = Column(Float, nullable=True)   # Add this
    glucose_level = Column(Float, nullable=True) # Add this
    
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


class NotificationVisit(Base):
    __tablename__ = "notification_visits"

    id = Column(Integer, primary_key=True, index=True)
    visit_date = Column(Date, index=True, nullable=False)
    location = Column(String, index=True, nullable=False)
    symptoms_json = Column(Text, nullable=False)  # JSON string array
    source = Column(String, default="import")  # import | mock
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("group_date", "location", "symptom", name="uq_notification_group"),
    )

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    group_date = Column(Date, index=True, nullable=False)
    location = Column(String, index=True, nullable=False)
    symptom = Column(String, index=True, nullable=False)
    severity = Column(String, nullable=False)  # info | warning | critical
    total_visits = Column(Integer, nullable=False)
    symptom_count = Column(Integer, nullable=False)
    rate = Column(Float, nullable=False)  # 0..1
    threshold_used = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String)


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)  # email | sms
    recipient = Column(String, nullable=False)
    status = Column(String, nullable=False)  # sent | failed
    provider = Column(String, nullable=False)  # smtp | twilio
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
