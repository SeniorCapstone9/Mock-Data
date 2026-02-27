import random
from faker import Faker
from datetime import datetime
from database import SessionLocal, Record, User

fake = Faker()

def seed_faker_data(num_sessions=50):
    db = SessionLocal()
    try:
        # 1. Get our existing patients (Dave and Chris) to attach records to
        patients = db.query(User).filter(User.role == "patient").all()
        if not patients:
            print("Error: No patients found. Run reset_db.py first!")
            return

        print(f"Generating {num_sessions} realistic medical sessions...")

        for _ in range(num_sessions):
            target_patient = random.choice(patients)
            scenario = random.random()
            
            # Default healthy vitals
            diag = "Healthy/Normal"
            hba1c = round(random.uniform(4.5, 5.6), 1)
            bmi = round(random.uniform(18.5, 24.9), 1)
            transcript = "Annual wellness checkup. No acute complaints."

            # --- MEDICAL SCENARIO LOGIC (From your original script) ---
            if scenario < 0.40:  # CHRONIC SCENARIO
                diag = "Type 2 Diabetes / Obesity Risk"
                hba1c = round(random.uniform(6.5, 10.5), 1) # High HbA1c
                bmi = round(random.uniform(30.0, 45.0), 1)   # High BMI
                transcript = "Patient here for chronic disease management and lipid screening."
            
            elif scenario < 0.70: # ACUTE/FLU SCENARIO
                diag = "Influenza (Flu)"
                transcript = "Patient reports sudden onset of chills, body aches, and fever."

            # 2. Save using the official Record model so the Engine can see it
            new_record = Record(
                patient_id=target_patient.id,
                title=f"Visit: {diag}",
                hba1c=hba1c,
                bmi=bmi,
                full_transcript=transcript,
                status="completed",
                created_at=datetime.utcnow()
            )
            db.add(new_record)

        db.commit()
        print(f"Success! {num_sessions} sessions added to the database.")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_faker_data()