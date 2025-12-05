from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
import os
import uuid
from database import get_db, init_db, Record
from services import transcribe_audio, process_transcript_with_ai

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

async def process_file_background(record_id: int, file_path: str, db: Session):
    try:
        # 1. Transcribe
        transcript_json = await transcribe_audio(file_path)
        
        # 2. Process (Redact + SOAP)
        redacted, soap = process_transcript_with_ai(transcript_json)
        
        # 3. Update DB
        record = db.query(Record).filter(Record.id == record_id).first()
        if record:
            record.raw_transcript = transcript_json
            record.redacted_transcript = redacted
            record.soap_summary = soap
            record.status = "completed"
            db.commit()
            
    except Exception as e:
        print(f"Processing Error: {e}")
        record = db.query(Record).filter(Record.id == record_id).first()
        if record:
            record.status = "failed"
            db.commit()
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/api/upload")
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]
    file_path = os.path.join(TEMP_DIR, f"{file_id}.{file_extension}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create DB Record
    new_record = Record(filename=file.filename, status="processing")
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    # Trigger Background Processing
    # We need a new session for the background task or pass the ID and create a new session inside
    # Passing the ID is safer, but for simplicity here we'll use a wrapper or just pass the logic
    # Actually, background tasks run after the response, so the db session might be closed. 
    # Better to create a new session in the background task function? 
    # For now, let's just pass the ID and create a new session in the background function manually if needed, 
    # but `process_file_background` takes `db`. 
    # Let's modify `process_file_background` to create its own session.
    
    background_tasks.add_task(run_background_process, new_record.id, file_path)
    
    return {"id": new_record.id, "status": "processing"}

def run_background_process(record_id: int, file_path: str):
    # Helper to create a fresh session for the background task
    from database import SessionLocal
    db = SessionLocal()
    try:
        import asyncio
        asyncio.run(process_file_background(record_id, file_path, db))
    finally:
        db.close()

@app.get("/api/results/{record_id}")
def get_results(record_id: int, db: Session = Depends(get_db)):
    record = db.query(Record).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return {
        "id": record.id,
        "status": record.status,
        "redacted_transcript": record.redacted_transcript,
        "soap_summary": record.soap_summary
    }
