import os
from database import init_db, get_db, User
from auth import get_password_hash

DB_FILE = "medical_scribe.db"

def reset_database():
    print(f"Removing {DB_FILE}...")
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Database deleted.")
    else:
        print("Database file not found, skipping delete.")

    print("Initializing new database...")
    init_db()
    print("Database schema created.")

    print("Creating default users...")
    db = next(get_db())

    # Admin
    admin_pw = get_password_hash("admin")
    admin = User(username="admin", hashed_password=admin_pw, role="admin")
    db.add(admin)
    print("Created User: admin / admin (Role: admin)")

    # Doctor (Dave)
    doc_pw = get_password_hash("dave")
    doctor = User(username="Dave", hashed_password=doc_pw, role="doctor")
    db.add(doctor)
    print("Created User: Dave / dave (Role: doctor)")

    # Patient (Chris)
    pat_pw = get_password_hash("chris")
    patient = User(username="Chris", hashed_password=pat_pw, role="patient")
    db.add(patient)
    print("Created User: Chris / chris (Role: patient)")

    db.commit()
    print("Done! Database reset complete.")

    # Trigger Uvicorn reload to release old DB connection
    print("Triggering server reload...")
    try:
        if os.path.exists("main.py"):
            os.utime("main.py", None)
            print("Server reload triggered (updated main.py timestamp).")
        else:
            print("Warning: main.py not found, could not trigger reload.")
    except Exception as e:
        print(f"Failed to trigger reload: {e}")

if __name__ == "__main__":
    reset_database()
