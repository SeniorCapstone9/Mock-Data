from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import shutil
import os
import uuid
import json
import subprocess
from datetime import timedelta
from database import get_db, init_db, Record, User
from services import transcribe_audio, process_transcript_with_ai
from auth import create_access_token, get_current_user, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_active_admin, get_current_doctor
from pydantic import BaseModel

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB
init_db()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# Create a default admin user if not exists
def create_default_admin():
    db = next(get_db())
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        hashed_pw = get_password_hash("admin") # Default password: admin
        new_user = User(username="admin", hashed_password=hashed_pw, role="admin")
        db.add(new_user)
        db.commit()

create_default_admin()

async def process_file_background(record_id: int, file_path: str, db: Session):
    wav_path = file_path.rsplit('.', 1)[0] + ".wav"
    try:
        # 0. Convert to WAV (16kHz, Mono) for best compatibility
        subprocess.run(["ffmpeg", "-i", file_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path, "-y"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 1. Transcribe
        result = await transcribe_audio(wav_path)
        transcript_json = result["json"]
        
        # 2. Process (Redact + SOAP + Title + Analytics)
        redacted, soap, title, full_text, analytics = process_transcript_with_ai(transcript_json)
        
        # 3. Update DB
        record = db.query(Record).filter(Record.id == record_id).first()
        if record:
            record.raw_transcript = transcript_json
            record.full_transcript = full_text
            record.redacted_transcript = redacted
            record.soap_summary = soap
            record.title = title
            record.status = "completed"
            
            # Save Advanced Analytics
            record.sentiment = analytics.get("sentiment", "Neutral")
            record.medical_tags = json.dumps(analytics.get("tags", []))
            record.action_items = json.dumps(analytics.get("action_items", []))
            
            # Save Analytics
            record.duration = result["duration"]
            record.word_count = result["word_count"]
            record.confidence = result["confidence"]
            record.speaker_count = result["speaker_count"]
            
            db.commit()
            
    except Exception as e:
        print(f"Processing Error: {e}")
        record = db.query(Record).filter(Record.id == record_id).first()
        if record:
            record.status = "failed"
            db.commit()
    finally:
        # Cleanup temp files
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

@app.post("/api/users")
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    return {"username": new_user.username, "role": new_user.role}

@app.get("/api/patients")
def list_patients(db: Session = Depends(get_db), current_user: User = Depends(get_current_doctor)):
    patients = db.query(User).filter(User.role == "patient").all()
    return [{"id": p.id, "username": p.username} for p in patients]

@app.get("/api/users")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]

@app.post("/api/upload")
async def upload_audio(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    patient_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]
    file_path = os.path.join(TEMP_DIR, f"{file_id}.{file_extension}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create DB Record
    new_record = Record(
        filename=file.filename, 
        status="processing",
        doctor_id=current_user.id,
        patient_id=patient_id
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    background_tasks.add_task(run_background_process, new_record.id, file_path)
    
    return {"id": new_record.id, "status": "processing"}

def run_background_process(record_id: int, file_path: str):
    from database import SessionLocal
    db = SessionLocal()
    try:
        import asyncio
        asyncio.run(process_file_background(record_id, file_path, db))
    finally:
        db.close()

@app.get("/api/results/{record_id}")
def get_results(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(Record).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # RBAC Check
    if current_user.role == "doctor" and record.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "patient" and record.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": record.id,
        "status": record.status,
        "full_transcript": record.full_transcript,
        "redacted_transcript": record.redacted_transcript,
        "soap_summary": record.soap_summary,
        "created_at": record.created_at,
        "sentiment": record.sentiment,
        "medical_tags": json.loads(record.medical_tags) if record.medical_tags else [],
        "action_items": json.loads(record.action_items) if record.action_items else []
    }

@app.get("/api/records")
def list_records(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Record)
    
    if current_user.role == "doctor":
        query = query.filter(Record.doctor_id == current_user.id)
    elif current_user.role == "patient":
        query = query.filter(Record.patient_id == current_user.id)
    # Admin sees all
        
    records = query.order_by(Record.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "title": r.title or "Untitled Session",
            "duration": r.duration,
            "status": r.status,
            "created_at": r.created_at,
            "patient_name": r.patient.username if r.patient else "Unknown"
        }
        for r in records
    ]

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(Record).filter(Record.status == "completed").all()
    
    total_sessions = len(records)
    total_duration = sum([r.duration for r in records])
    avg_confidence = sum([r.confidence for r in records]) / total_sessions if total_sessions > 0 else 0
    total_words = sum([r.word_count for r in records])
    
    # Last 7 days activity
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    activity = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = len([r for r in records if r.created_at.date() == date])
        activity.append({"date": date.strftime("%Y-%m-%d"), "count": count})
        
    # Aggregate Tags
    all_tags = []
    for r in records:
        if r.medical_tags:
            all_tags.extend(json.loads(r.medical_tags))
    
    from collections import Counter
    tag_counts = Counter(all_tags).most_common(10)
    tags_data = [{"text": tag, "value": count} for tag, count in tag_counts]
    
    # Aggregate Sentiment
    sentiments = [r.sentiment for r in records if r.sentiment]
    sentiment_counts = Counter(sentiments)
    sentiment_data = [{"name": s, "value": c} for s, c in sentiment_counts.items()]

    return {
        "total_sessions": total_sessions,
        "total_duration": round(total_duration / 60, 2), # in minutes
        "avg_confidence": round(avg_confidence * 100, 1), # percentage
        "total_words": total_words,
        "activity": activity,
        "tags": tags_data,
        "sentiment": sentiment_data
    }
