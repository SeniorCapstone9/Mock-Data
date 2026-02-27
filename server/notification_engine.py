from collections import Counter
from datetime import date, datetime, timedelta
import json
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from database import Notification, NotificationVisit
import ollama

INFO_THRESHOLD = 0.02
WARNING_THRESHOLD = 0.05
CRITICAL_THRESHOLD = 0.10

# Deterministic normalization for common symptom aliases.
SYMPTOM_SYNONYMS = {
    "influenza": "flu",
    "flu a": "flu",
    "flu b": "flu",
    "influenza a": "flu",
    "influenza b": "flu",
    "pyrexia": "fever",
    "temperature": "fever",
    "high temperature": "fever",
    "dyspnea": "shortness of breath",
    "sob": "shortness of breath",
}


def canonicalize_symptom(raw: str) -> str:
    if raw is None:
        return ""
    normalized = " ".join(raw.strip().lower().split())
    return SYMPTOM_SYNONYMS.get(normalized, normalized)


def symptoms_from_json(symptoms_json: str) -> Set[str]:
    if not symptoms_json:
        return set()

    try:
        parsed = json.loads(symptoms_json)
    except json.JSONDecodeError:
        return set()

    if not isinstance(parsed, list):
        return set()

    result: Set[str] = set()
    for symptom in parsed:
        if not isinstance(symptom, str):
            continue
        canonical = canonicalize_symptom(symptom)
        if canonical:
            result.add(canonical)
    return result


def severity_for_rate(rate: float) -> Tuple[Optional[str], Optional[float]]:
    if rate >= CRITICAL_THRESHOLD:
        return "critical", CRITICAL_THRESHOLD
    if rate >= WARNING_THRESHOLD:
        return "warning", WARNING_THRESHOLD
    if rate >= INFO_THRESHOLD:
        return "info", INFO_THRESHOLD
    return None, None


def build_message(symptom: str, location: str, group_date: date, count: int, total: int, rate: float, severity: str) -> str:
    pct = round(rate * 100, 1)
    return (
        f"{severity.title()} alert: {symptom} rate reached {pct}% "
        f"in {location} on {group_date.isoformat()} ({count}/{total} visits)."
    )


def _group_visits(visits: List[NotificationVisit]) -> Dict[Tuple[date, str], Dict[str, object]]:
    grouped: Dict[Tuple[date, str], Dict[str, object]] = {}

    for visit in visits:
        key = (visit.visit_date, visit.location)
        bucket = grouped.setdefault(
            key,
            {
                "total_visits": 0,
                "symptom_counts": Counter(),
            },
        )
        bucket["total_visits"] += 1

        normalized_symptoms = symptoms_from_json(visit.symptoms_json)
        for symptom in normalized_symptoms:
            bucket["symptom_counts"][symptom] += 1

    return grouped


def distribution_for_group(db: Session, group_date: date, location: str):
    """
    Returns the distribution of symptoms for a specific location on a specific day.
    Used by the frontend to display the breakdown of outbreaks.
    """
    visits = db.query(NotificationVisit).filter(
        NotificationVisit.visit_date == group_date,
        NotificationVisit.location == location
    ).all()

    total_visits = len(visits)
    symptom_counts = {}
    
    for v in visits:
        if v.symptoms_json:
            try:
                symps = json.loads(v.symptoms_json)
                for s in symps:
                    symptom_counts[s] = symptom_counts.get(s, 0) + 1
            except json.JSONDecodeError:
                continue

    distribution = {s: count / total_visits for s, count in symptom_counts.items()} if total_visits > 0 else {}

    return {
        "group_date": group_date,
        "location": location,
        "total_visits": total_visits,
        "symptom_counts": symptom_counts,
        "distribution": distribution
    }


def run_notification_engine(
    db: Session,
    days: int = 7,
    symptoms: Optional[List[str]] = None,
    source: Optional[str] = None,
    delete_source_after_run: bool = False,
) -> Dict[str, int]:
    import ollama
    import json
    
    today = datetime.now().date()
    cutoff = today - timedelta(days=max(days - 1, 0))

    # 1. Fetch the raw visit data
    visit_query = db.query(NotificationVisit).filter(NotificationVisit.visit_date >= cutoff)
    if source:
        visit_query = visit_query.filter(NotificationVisit.source == source)
    visits = visit_query.all()
    
    # 2. Group visits by Date and Location
    grouped = _group_visits(visits)
    alerts_upserted = 0

    for (group_date, location), payload in grouped.items():
        total_visits = payload["total_visits"]
        if total_visits <= 0:
            continue

        # Format the symptom counts for the AI to read
        symptom_summary = ", ".join([f"{s}: {c}" for s, c in payload["symptom_counts"].items()])

        # THE EPIDEMIOLOGIST PROMPT
        prompt = f"""
        You are an AI Epidemiologist. Analyze the following symptom data for {location} on {group_date}.
        Total Patient Visits: {total_visits}
        Symptom Breakdown: {symptom_summary}
        
        Evaluate if these symptoms represent a significant public health outbreak (e.g., Flu, COVID-19, Food Poisoning).
        Return ONLY valid JSON in this format:
        {{
            "outbreak_detected": true/false,
            "diagnosis": "Name of suspected outbreak",
            "severity": "critical", "warning", or "info",
            "justification": "One sentence explaining why."
        }}
        """

        try:
            response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}], format='json')
            ai_eval = json.loads(response['message']['content'])

            if ai_eval.get("outbreak_detected"):
                diagnosis = ai_eval.get("diagnosis", "Unknown Outbreak")
                severity = ai_eval.get("severity", "info")
                justification = ai_eval.get("justification", "")

                # Update or Create the Notification
                existing = (
                    db.query(Notification)
                    .filter(Notification.group_date == group_date)
                    .filter(Notification.location == location)
                    .filter(Notification.symptom == diagnosis)
                    .first()
                )

                msg = f"AI OUTBREAK ALERT: {diagnosis} detected in {location}. {justification}"
                
                if existing:
                    existing.severity = severity
                    existing.message = msg
                    existing.created_at = datetime.now()
                else:
                    db.add(Notification(
                        group_date=group_date,
                        location=location,
                        symptom=diagnosis,
                        severity=severity,
                        total_visits=total_visits,
                        symptom_count=0, # Aggregated, so individual count is N/A
                        rate=0.0,
                        threshold_used=0.0,
                        message=msg
                    ))
                alerts_upserted += 1

        except Exception as e:
            print(f"AI Public Health Analysis failed for {location}: {e}")

    return {
        "groups_processed": len(grouped),
        "source_visits": len(visits),
        "alerts_upserted": alerts_upserted,
    }


if __name__ == "__main__":
    from database import SessionLocal, Record
    import ollama  
    import json
    
    db = SessionLocal()
    print("🚀 Starting AI-Driven Integrated Notification Engine...")
    
    try:
        # --- PART 1: Contagious Spike Detection (Unchanged)
        print("\nChecking for Contagious Spikes (Influenza)...")
        results = run_notification_engine(db, days=2)
        print(f"📊 Spike Alerts Created: {results['alerts_upserted']}")

        # --- PART 2: AI Chronic Disease Detection 
        print("\n🧠 AI analyzing Patient Transcripts for Chronic Diseases...")
        
        # Grab records that actually have a transcript
        recent_records = db.query(Record).filter(Record.full_transcript.isnot(None)).all()

        chronic_count = 0
        for rec in recent_records:
            r_id = rec.id 
            p_id = rec.patient_id 
            
            # The STRICT Clinical Prompt with Patient Vitals
            prompt = f"""
            You are a strict medical AI. Analyze this patient's clinical data and transcript for SPECIFIC chronic diseases (e.g., Type 2 Diabetes, Obesity, Hypertension).
            
            Clinical Vitals:
            - HbA1c: {getattr(rec, 'hba1c', 'N/A')}
            - BMI: {getattr(rec, 'bmi', 'N/A')}
            
            Transcript: {rec.full_transcript}
            
            Do NOT return vague terms like "Chronic Disease". If an exact medical condition is not explicitly supported by the vitals or transcript, you MUST return {{"detected": false}}.
            Return ONLY valid JSON in this exact format:
            {{
                "detected": true,
                "condition": "Exact Diagnosis Name Only",
                "severity": "High" or "Medium",
                "justification": "Short reason why based on the vitals and transcript"
            }}
            """
            
            try:
                # Ask Ollama to evaluate the transcript
                response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}], format='json')
                ai_eval = json.loads(response['message']['content'])
                
                # If the AI detects a risk, create the alert!
                if ai_eval.get("detected"):
                    condition = ai_eval.get("condition", "Chronic Condition")
                    severity = ai_eval.get("severity", "Medium")
                    justification = ai_eval.get("justification", "AI detected risk in transcript.")
                    
                    patient_symptom = f"{condition} (Patient ID: {p_id})" 
                    
                    # Check for duplicates so we don't spam the dashboard
                    existing_alert = db.query(Notification).filter(
                        Notification.symptom == patient_symptom
                    ).first()

                    if not existing_alert:
                        msg = f"CHRONIC ALERT: {condition} risk detected for Patient ID: {p_id}. Justification: {justification}"
                        
                        new_alert = Notification(
                            group_date=datetime.now().date(),
                            location="FL",       
                            symptom=patient_symptom,
                            severity="warning",   
                            alert_type=severity, 
                            message=msg,
                            rate=1.0,            
                            total_visits=1,
                            symptom_count=1,
                            threshold_used=0.0
                        )
                        db.add(new_alert)
                        chronic_count += 1
                        print(f"   -> ⚠️ AI Flagged Patient {p_id} for {condition} ({severity} Severity)")
            
            except Exception as e:
                print(f"   -> ❌ AI processing failed for Record {r_id}: {e}")
        
        db.commit()
        print(f"✅ AI Chronic Disease Alerts Created: {chronic_count}")
        print("\n--- Execution Complete ---")

    except Exception as e:
        print(f"❌ Error running engine: {e}")
        db.rollback()
    finally:
        db.close()