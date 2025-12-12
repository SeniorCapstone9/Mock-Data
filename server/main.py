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
        
        # 1.5 Fetch Existing Tags (Context for AI)
        all_records = db.query(Record).all()
        all_tags = []
        for r in all_records:
            if r.medical_tags:
                all_tags.extend(json.loads(r.medical_tags))
        
        from collections import Counter
        existing_tags = [tag for tag, count in Counter(all_tags).most_common(20)]

        # 2. Process (Redact + SOAP + Title + Analytics)
        redacted, soap, title, full_text, analytics = process_transcript_with_ai(transcript_json, existing_tags)
        
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
        import traceback
        error_msg = traceback.format_exc()
        print(f"Processing Error: {error_msg}")
        
        # Log to file for debugging
        with open("error_log.txt", "w") as f:
            f.write(error_msg)
            
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


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(Record).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # RBAC: patients cannot delete; doctors can delete own; admins can delete any
    if current_user.role == "patient":
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "doctor" and record.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(record)
    db.commit()
    return {"ok": True}

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
        
    # Aggregate Tags (Global)
    all_tags = []
    for r in records:
        if r.medical_tags:
            all_tags.extend(json.loads(r.medical_tags))
    
    from collections import Counter
    tag_counts_counter = Counter(all_tags)
    tag_counts = tag_counts_counter.most_common(10)
    tags_data = [{"text": tag, "value": count} for tag, count in tag_counts]
    
    # Temporal Tags (Top 5 for Forecasting)
    top_5_tags = [tag for tag, count in tag_counts_counter.most_common(5)]
    tags_over_time = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_records = [r for r in records if r.created_at.date() == date]
        
        day_data = {"date": date.strftime("%Y-%m-%d")}
        # Initialize 0
        for tag in top_5_tags:
            day_data[tag] = 0
            
        for r in day_records:
            if r.medical_tags:
                r_tags = json.loads(r.medical_tags)
                for t in r_tags:
                    if t in top_5_tags:
                        day_data[t] += 1
        
        tags_over_time.append(day_data)

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
        "tags": tags_data, # Keep original for reference if needed
        "tags_over_time": tags_over_time, # New temporal data
        "top_tags": top_5_tags, # Keys for the frontend
        "sentiment": sentiment_data
    }

# --- OCR Feature ---

from database import ScannedNote
from ocr_service import get_ocr_service

@app.post("/api/scan-note")
async def scan_note(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    # 1. Save Image
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]
    file_path = os.path.join(TEMP_DIR, f"note_{file_id}.{file_extension}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 2. Run OCR
        service = get_ocr_service()
        # Run in threadpool to not block async event loop
        import asyncio
        loop = asyncio.get_event_loop()
        extracted_text = await loop.run_in_executor(None, service.process_image, file_path)
        
        # 3. Save to DB
        new_note = ScannedNote(
            image_path=file_path,
            extracted_text=extracted_text,
            doctor_id=current_user.id
        )
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        
        return {
            "id": new_note.id,
            "extracted_text": new_note.extracted_text,
            "created_at": new_note.created_at
        }
        
    except Exception as e:
        print(f"OCR Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notes")
def list_notes(db: Session = Depends(get_db), current_user: User = Depends(get_current_doctor)):
    notes = db.query(ScannedNote).filter(ScannedNote.doctor_id == current_user.id).order_by(ScannedNote.created_at.desc()).all()
    
    # We need to serve the images too, but for now just returning text and ID
    # In a real app, we'd add StaticFiles mount for the temp dir or storage
    return [
        {
            "id": n.id,
            "extracted_text": n.extracted_text,
            "created_at": n.created_at,
            "image_path": n.image_path # Client might not be able to access this directly without mount
        }
        for n in notes
    ]


@app.get("/api/notes/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_doctor)):
    note = db.query(ScannedNote).filter(ScannedNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "id": note.id,
        "extracted_text": note.extracted_text,
        "created_at": note.created_at,
        "image_path": note.image_path,
    }


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_doctor)):
    note = db.query(ScannedNote).filter(ScannedNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    image_path = note.image_path
    db.delete(note)
    db.commit()

    # Best-effort cleanup of uploaded temp image/pdf
    try:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        print(f"Failed to remove note file {image_path}: {e}")

    return {"ok": True}

# Mount temp dir (Must be before static catch-all)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
app.mount("/temp", StaticFiles(directory="temp"), name="temp")

# Serve React App (Production Build)
# Check if dist exists to avoid errors in dev mode without build
if os.path.exists("../client/dist"):
    app.mount("/assets", StaticFiles(directory="../client/dist/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Allow API calls to pass through
        if full_path.startswith("api") or full_path.startswith("token"):
            raise HTTPException(status_code=404, detail="Not found")
            
        # Serve index.html for any other route (SPA)
        file_path = f"../client/dist/{full_path}"
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse("../client/dist/index.html")
else:
    print("Warning: '../client/dist' not found. Frontend will not be served by backend.")
