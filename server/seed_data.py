import os
import json
import random
from datetime import datetime, timedelta
from database import get_db, Record, User, ScannedNote
from sqlalchemy.orm import Session

def seed_data():
    print("Seeding database with sample data...")
    db: Session = next(get_db())

    # 1. Get Users
    dave = db.query(User).filter(User.username == "Dave").first()
    chris = db.query(User).filter(User.username == "Chris").first()
    
    if not dave or not chris:
        print("Error: Default users (Dave, Chris) not found. Run reset_db.py first.")
        return

    # 2. Sample Data Constants
    TAGS_POOL = ["Hypertension", "Type 2 Diabetes", "Influenza", "Migraine", "Anxiety", "Insomnia", "Asthma", "Dermatitis"]
    SENTIMENTS = ["Anxious", "Relieved", "Hopeful", "Frustrated", "Optimistic", "Exhausted"]
    
    SAMPLE_TRANSCRIPTS = [
        {
            "title": "Hypertension Follow-up",
            "text": "Doctor: How have you been feeling since started the Lisinopril?\nPatient: meaningful improvement. The headaches are basically gone.\nDoctor: That's great to hear. Let's check your blood pressure... Okay, it's 130 over 85. That is much better than last time.\nPatient: Is that good enough?\nDoctor: It's definitely in the right direction. I want you to keep taking the medication and we'll monitor it.",
            "soap": "S: Patient reports reduced headaches.\nO: BP 130/85.\nA: Hypertension stable.\nP: Continue current medication.",
            "tags": ["Hypertension", "Headache"],
            "action_items": ["Monitor BP daily", "Continue Lisinopril"]
        },
        {
            "title": "Flu Symptoms Assessment",
            "text": "Doctor: What brings you in today?\nPatient: I feel terrible. I've had a fever of 102 since yesterday, chills, and my whole body aches.\nDoctor: Have you had a cough or sore throat?\nPatient: A little sore throat, but mostly just the aches and fever.\nDoctor: I'm going to run a rapid flu test... Okay, it's positive for Flu A.\nPatient: Ugh, I knew it.\nDoctor: You're within the window for Tamiflu, so I'll prescribe that. You need to rest and drink plenty of fluids.",
            "soap": "S: Fever, chills, aches x2 days.\nO: Temp 102F. Flu A Positive.\nA: Influenza A.\nP: Rest, fluids, Tamiflu.",
            "tags": ["Influenza", "Fever"],
            "action_items": ["Rest and fluids", "Take Tamiflu as prescribed", "Isolate for 5 days"]
        },
        {
            "title": "Diabetes Check-in",
            "text": "Doctor: How have your sugars been this week?\nPatient: Not great. Fasting was 150 this morning.\nDoctor: That is a bit high. Have you been taking the Metformin every day?\nPatient: I miss it sometimes when I'm busy at work.\nDoctor: Consistency is really key here. If we can't control it with the Metformin, we might need insulin.\nPatient: I really don't want shots.\nDoctor: Then let's try to get back on track with the pills.",
            "soap": "S: Fasting glucose 150. Non-adherent to meds.\nO: A1C pending.\nA: Type 2 Diabetes uncontrolled.\nP: Re-education on medication adherence.",
            "tags": ["Type 2 Diabetes", "Hyperglycemia"],
            "action_items": ["Resume Metformin daily", "Log food assessments"]
        },
        {
            "title": "Migraine Consultation",
            "text": "Doctor: Tell me about this headache.\nPatient: It's on the left side, throbbing, like a heartbeat. The light hurts my eyes so much.\nDoctor: Any nausea?\nPatient: Yes, I feel sick to my stomach.\nDoctor: It sounds like a classic migraine. I'm going to prescribe Sumatriptan. You take it as soon as you feel it coming on.\nPatient: Will it make it go away fast?\nDoctor: It should help significantly within an hour.",
            "soap": "S: Left-sided throbbing, photophobia, nausea.\nO: Neuro exam normal.\nA: Acute Migraine.\nP: Sumatriptan prescribed.",
            "tags": ["Migraine", "Nausea", "Photophobia"],
            "action_items": ["Take Sumatriptan at onset", "Keep headache diary"]
        },
        {
            "title": "Anxiety Screening",
            "text": "Doctor: You mentioned feeling overwhelmed?\nPatient: Yeah, work has been crazy. I can't sleep. I lay there for hours.\nDoctor: Do you feel physical symptoms?\nPatient: Sometimes my chest feels tight, like I can't breathe.\nDoctor: I want to rule out heart issues, but your EKG is normal. This sounds like generalized anxiety.\nPatient: Is there something I can take?\nDoctor: We can discuss an SSRI, but I also want you to try therapy.",
            "soap": "S: Work stress, insomnia, chest tightness.\nO: HR 90. EKG Normal.\nA: Generalized Anxiety.\nP: Refer to therapy, start SSRI.",
            "tags": ["Anxiety", "Insomnia", "Chest Pain"],
            "action_items": ["Schedule therapy appointment", "Practice breathing exercises"]
        }
    ]

    # 3. generate Records (Last 7 Days)
    # We want a nice distribution for the graph
    today = datetime.utcnow()
    
    # Clean up existing records for these users to avoid duplicates if run multiple times? 
    # Whatever, let's just append. Use reset_db to clear.

    records_created = 0
    
    for i in range(8): # 0 to 7 days ago
        day_date = today - timedelta(days=i)
        
        # Random number of sessions per day (0 to 3)
        num_sessions = random.randint(1, 3)
        if i == 0: num_sessions = 3 # Ensure today has data
        
        for _ in range(num_sessions):
            sample = random.choice(SAMPLE_TRANSCRIPTS)
            
            # Create Record
            rec = Record(
                filename=f"recording_{random.randint(1000,9999)}.wav",
                title=sample["title"],
                raw_transcript=json.dumps([{"text": sample["text"], "speaker": "0", "start": 0, "end": 10}]),
                full_transcript=f"Speaker 0: {sample['text']}",
                redacted_transcript=f"Speaker 0: {sample['text']}", # No actual redaction for seed
                soap_summary=sample["soap"],
                status="completed",
                created_at=day_date - timedelta(hours=random.randint(1, 8)), # Random time during day
                duration=random.uniform(120.0, 900.0),
                word_count=len(sample["text"].split()),
                confidence=random.uniform(0.85, 0.99),
                speaker_count=2,
                sentiment=random.choice(SENTIMENTS),
                medical_tags=json.dumps(sample["tags"]),
                action_items=json.dumps(sample["action_items"]),
                doctor_id=dave.id,
                patient_id=chris.id
            )
            db.add(rec)
            records_created += 1

    # 4. Generate Scanned Notes
    note_content = "Patient: Chris\nDate: 2024-10-10\nReason: Annual Physical\n\nNotes:\nLungs clear. Heart RRR. Abdomen soft, non-tender."
    note = ScannedNote(
        image_path=None, # No file for seed
        extracted_text=note_content,
        created_at=today - timedelta(days=2),
        doctor_id=dave.id
    )
    db.add(note)
    
    db.commit()
    print(f"Successfully created {records_created} records and 1 scanned note.")
    
    # Reload Server
    print("Triggering server reload...")
    try:
        if os.path.exists("main.py"):
            os.utime("main.py", None)
            print("Server reload triggered.")
    except:
        pass

if __name__ == "__main__":
    seed_data()
