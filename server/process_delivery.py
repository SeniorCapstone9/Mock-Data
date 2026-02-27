import re
from datetime import datetime, timedelta
from database import SessionLocal, Notification, User
from notification_delivery import send_email_notification
from dotenv import load_dotenv
load_dotenv()

# The list of administrators who should get the Mass Flu Alerts
MASS_EMAIL_RECIPIENTS = ["mediscribecapstone@gmail.com"]

def process_and_deliver():
    db = SessionLocal()
    print("📬 Starting Intelligent Alert Routing Process...\n")

    try:
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=7)
        alerts = db.query(Notification).filter(Notification.group_date >= cutoff_date).all()

        if not alerts:
            print("No new alerts to deliver for today.")
            return

        # Split the alerts just like we did on the React dashboard!
        flu_spikes = [a for a in alerts if "CHRONIC ALERT" not in a.message]
        chronic_alerts = [a for a in alerts if "CHRONIC ALERT" in a.message]

        # ---------------------------------------------------------
        # WORKFLOW 1: MASS EMAIL FOR FLU SPIKES (Administrators)
        # ---------------------------------------------------------
        if flu_spikes:
            print(f"📢 Processing Mass Email for {len(flu_spikes)} Flu/Acute Spikes...")
            
            # 1. Find all the unique states/locations that had a spike today
            affected_locations = set([a.location for a in flu_spikes])
            
            # 2. Generate one clean warning line per location
            report_lines = []
            for loc in affected_locations:
                report_lines.append(f"PUBLIC HEALTH ALERT: Contagious Spikes Detected ({today}) in {loc}")
            
            full_mass_report = "\n".join(report_lines)
            
            for admin_email in MASS_EMAIL_RECIPIENTS:
                print(f"   -> Sending mass digest to: {admin_email}")
                success, protocol, err = send_email_notification(to_email=admin_email, subject="URGENT: Contagious Spike Report", body=full_mass_report)
                if not success:
                    print(f"   ❌ Email Failed: {err}")
            
            print("✅ Mass flu alerts dispatched.\n")

        # ---------------------------------------------------------
        # WORKFLOW 2: INDIVIDUAL EMAIL FOR CHRONIC PATIENTS
        # ---------------------------------------------------------
        if chronic_alerts:
            print(f"🩺 Processing Individual Emails for {len(chronic_alerts)} Chronic Patients...")
            
            for alert in chronic_alerts:
                # Use regex to extract the Patient ID from your custom message string
                match = re.search(r"Patient ID:\s*(\d+)", alert.message)
                if match:
                    patient_id = int(match.group(1))
                    patient = db.query(User).filter(User.id == patient_id).first()
                    
                    if patient:
                        # Fallback to a mock email if the patient doesn't have one in the DB yet
                        #patient_email = f"{patient.username.lower().replace(' ', '')}@example.com"
                        patient_email = "mediscribecapstone@gmail.com"
                        
                        subject = "Important Update Regarding Your Recent Health Visit"
                        body = (
                            f"Dear {patient.username},\n\n"
                            f"During your recent visit, our clinical system noted a risk factor regarding your health: {alert.symptom}.\n"
                            f"Please log into your secure patient portal or call the clinic to schedule a follow-up appointment with your physician.\n\n"
                            f"Thank you,\nMediScribe Clinical Team"
                        )
                        
                        print(f"   -> Sending private alert to Patient: {patient.username} ({patient_email})")
                        send_email_notification(to_email=patient_email, subject=subject, body=body)

            print("✅ Individual chronic patient alerts dispatched.\n")

    except Exception as e:
        print(f"❌ Delivery Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    process_and_deliver()