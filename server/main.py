from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import shutil
import os
import uuid
import json
import subprocess
import csv
import io
import re
from datetime import timedelta, datetime, date
from database import get_db, init_db, Record, User, NotificationVisit, Notification, NotificationDelivery
from auth import create_access_token, get_current_user, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_active_admin, get_current_doctor
from pydantic import BaseModel
from notification_engine import canonicalize_symptom, run_notification_engine, distribution_for_group
from notification_delivery import send_email_notification


def _load_ai_services():
    # Lazy import heavy ML stack so the API can start without optional AI deps.
    from services import transcribe_audio, process_transcript_with_ai
    return transcribe_audio, process_transcript_with_ai


def _load_ocr_service():
    # Lazy import OCR stack only when OCR endpoints are called.
    from ocr_service import get_ocr_service
    return get_ocr_service

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
        transcribe_audio, process_transcript_with_ai = _load_ai_services()

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


STATE_CODE_RE = re.compile(r"^[A-Z]{2}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_NOTIFICATION_RECIPIENTS = [
    email.strip().lower()
    for email in os.getenv("NOTIFICATION_ALWAYS_EMAILS", "").split(",")
    if email.strip()
]


def normalize_location(location: str) -> str:
    value = (location or "").strip().upper()
    #if not STATE_CODE_RE.match(value):
   #     raise HTTPException(status_code=400, detail="location must be a 2-letter uppercase state code")
    return value


def normalize_symptoms(symptoms):
    normalized = []
    for symptom in symptoms or []:
        if not isinstance(symptom, str):
            continue
        canonical = canonicalize_symptom(symptom)
        if canonical:
            normalized.append(canonical)
    unique = sorted(set(normalized))
    if not unique:
        raise HTTPException(status_code=400, detail="symptoms must contain at least one valid symptom string")
    return unique


def normalize_emails(values):
    if not values:
        return []
    result = []
    for value in values:
        email = (value or "").strip().lower()
        if not email:
            continue
        if not EMAIL_RE.match(email):
            raise HTTPException(status_code=400, detail=f"Invalid email format: {value}")
        result.append(email)
    return sorted(set(result))


class NotificationVisitItem(BaseModel):
    visit_date: date
    location: str
    symptoms: list[str]


class NotificationVisitImportRequest(BaseModel):
    visits: list[NotificationVisitItem]
    source: str = "temp"


class NotificationRunRequest(BaseModel):
    days: int = 7
    symptoms: list[str] | None = None
    source: str = "temp"
    delete_source_after_run: bool = True


class NotificationSendRequest(BaseModel):
    emails: list[str] | None = None
    include_email: bool = True

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


# --- Notification System ---

@app.post("/api/notification-visits/import")
def import_notification_visits(
    payload: NotificationVisitImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    source = (payload.source or "temp").strip().lower()
    if source not in {"temp", "import", "mock"}:
        raise HTTPException(status_code=400, detail="source must be one of: temp, import, mock")

    rows = [
        NotificationVisit(
            visit_date=item.visit_date,
            location=normalize_location(item.location),
            symptoms_json=json.dumps(normalize_symptoms(item.symptoms)),
            source=source,
        )
        for item in payload.visits
    ]

    if not rows:
        raise HTTPException(status_code=400, detail="visits payload must contain at least one record")

    db.add_all(rows)
    db.commit()
    return {"inserted": len(rows), "source": source}


@app.post("/api/notification-visits/import-csv")
async def import_notification_visits_csv(
    file: UploadFile = File(...),
    source: str = Form("temp"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    parsed_source = (source or "temp").strip().lower()
    if parsed_source not in {"temp", "import", "mock"}:
        raise HTTPException(status_code=400, detail="source must be one of: temp, import, mock")

    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    expected_columns = {"visit_date", "location", "symptoms"}
    if not reader.fieldnames or not expected_columns.issubset(set(reader.fieldnames)):
        raise HTTPException(status_code=400, detail="CSV must include headers: visit_date, location, symptoms")

    rows = []
    errors = []
    for index, row in enumerate(reader, start=2):
        try:
            parsed_date = datetime.strptime((row.get("visit_date") or "").strip(), "%Y-%m-%d").date()
            location = normalize_location((row.get("location") or "").strip())
            symptoms_raw = row.get("symptoms") or ""
            split_symptoms = [s.strip() for s in re.split(r"[;,|]", symptoms_raw) if s.strip()]
            symptoms = normalize_symptoms(split_symptoms)
            rows.append(
                NotificationVisit(
                    visit_date=parsed_date,
                    location=location,
                    symptoms_json=json.dumps(symptoms),
                    source=parsed_source,
                )
            )
        except ValueError:
            errors.append(f"line {index}: visit_date must be YYYY-MM-DD")
        except HTTPException as exc:
            errors.append(f"line {index}: {exc.detail}")

    if errors:
        raise HTTPException(status_code=400, detail={"message": "CSV validation failed", "errors": errors[:20]})
    if not rows:
        raise HTTPException(status_code=400, detail="No valid rows found in CSV")

    db.add_all(rows)
    db.commit()
    return {"inserted": len(rows), "source": parsed_source}


@app.post("/api/notifications/run")
def run_notifications(
    payload: NotificationRunRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    request = payload or NotificationRunRequest()
    if request.days < 1 or request.days > 365:
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")

    normalized_symptoms = normalize_symptoms(request.symptoms) if request.symptoms else None
    source_value = (request.source or "temp").strip().lower()
    if source_value not in {"temp", "import", "mock"}:
        raise HTTPException(status_code=400, detail="source must be one of: temp, import, mock")

    result = run_notification_engine(
        db=db,
        days=request.days,
        symptoms=normalized_symptoms,
        source=source_value,
        delete_source_after_run=request.delete_source_after_run,
    )
    db.commit()
    return result


@app.get("/api/notifications")
def list_notifications(
    days: int = 7,
    severity: str | None = None,
    location: str | None = None,
    symptom: str | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    days = min(max(days, 1), 365)
    limit = min(max(limit, 1), 1000)
    cutoff = datetime.utcnow().date() - timedelta(days=days - 1)

    query = db.query(Notification).filter(Notification.group_date >= cutoff)
    
    # Filter by Severity (Internal logic)
    if severity:
        severity_value = severity.strip().lower()
        if severity_value not in {"info", "warning", "critical"}:
            raise HTTPException(status_code=400, detail="severity must be one of: info, warning, critical")
        query = query.filter(Notification.severity == severity_value)
    
    # Filter by Location (Matches the 'FL' requirement)
    if location:
        query = query.filter(Notification.location == normalize_location(location))
        
    if symptom:
        query = query.filter(Notification.symptom == canonicalize_symptom(symptom))

    rows = query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()
    
    return [
        {
            "id": n.id,
            "created_at": n.created_at,
            "group_date": n.group_date,
            "location": n.location,       # Now returns 'FL' for search compatibility
            "symptom": n.symptom,
            "severity": n.severity,
            "alert_type": getattr(n, 'alert_type', None),   # Now returns AI-determined High/Medium
            "total_visits": n.total_visits,
            "symptom_count": n.symptom_count,
            "rate": n.rate,
            "threshold_used": n.threshold_used,
            "message": n.message,
        }
        for n in rows
    ]


def _get_notification_or_404(db: Session, notification_id: int):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@app.get("/api/notifications/{notification_id}")
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    n = _get_notification_or_404(db, notification_id)
    return {
        "id": n.id,
        "created_at": n.created_at,
        "group_date": n.group_date,
        "location": n.location,
        "symptom": n.symptom,
        "severity": n.severity,
        "total_visits": n.total_visits,
        "symptom_count": n.symptom_count,
        "rate": n.rate,
        "threshold_used": n.threshold_used,
        "message": n.message,
    }


@app.get("/api/notifications/{notification_id}/distribution")
def get_notification_distribution(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    n = _get_notification_or_404(db, notification_id)
    return distribution_for_group(db, n.group_date, n.location)


@app.get("/api/notifications/{notification_id}/deliveries")
def list_notification_deliveries(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    _get_notification_or_404(db, notification_id)
    rows = (
        db.query(NotificationDelivery)
        .filter(NotificationDelivery.notification_id == notification_id)
        .order_by(NotificationDelivery.created_at.desc(), NotificationDelivery.id.desc())
        .all()
    )
    return [
        {
            "id": row.id,
            "notification_id": row.notification_id,
            "channel": row.channel,
            "recipient": row.recipient,
            "status": row.status,
            "provider": row.provider,
            "error_message": row.error_message,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@app.post("/api/notifications/{notification_id}/send")
def send_notification(
    notification_id: int,
    payload: NotificationSendRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    n = _get_notification_or_404(db, notification_id)
    request = payload or NotificationSendRequest()

    recipients = []
    if request.include_email:
        recipients.extend(DEFAULT_NOTIFICATION_RECIPIENTS)
    recipients.extend(normalize_emails(request.emails))
    recipients = sorted(set(recipients))
    if not recipients:
        raise HTTPException(status_code=400, detail="No email recipients provided/configured")

    subject = f"[{n.severity.upper()}] {n.symptom} alert in {n.location}"
    body = (
        f"{n.message}\n\n"
        f"Date: {n.group_date.isoformat()}\n"
        f"Location: {n.location}\n"
        f"Symptom: {n.symptom}\n"
        f"Severity: {n.severity}\n"
        f"Total visits: {n.total_visits}\n"
        f"Symptom count: {n.symptom_count}\n"
        f"Rate: {round(n.rate * 100, 1)}%\n"
        f"Threshold used: {round(n.threshold_used * 100, 1)}%\n"
    )

    sent = 0
    failed = 0
    for email in recipients:
        ok, provider, error_message = send_email_notification(email, subject, body)
        db.add(
            NotificationDelivery(
                notification_id=n.id,
                channel="email",
                recipient=email,
                status="sent" if ok else "failed",
                provider=provider,
                error_message=error_message or None,
            )
        )
        if ok:
            sent += 1
        else:
            failed += 1

    db.commit()
    return {"notification_id": n.id, "sent": sent, "failed": failed, "total": len(recipients)}

# --- OCR Feature ---

from database import ScannedNote

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
        service = _load_ocr_service()()
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
