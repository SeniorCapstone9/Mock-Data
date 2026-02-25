from collections import Counter
from datetime import date, datetime, timedelta
import json
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from database import Notification, NotificationVisit

INFO_THRESHOLD = 0.15
WARNING_THRESHOLD = 0.30
CRITICAL_THRESHOLD = 0.50

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


def run_notification_engine(
    db: Session,
    days: int = 7,
    symptoms: Optional[List[str]] = None,
    source: Optional[str] = None,
    delete_source_after_run: bool = False,
) -> Dict[str, int]:
    today = datetime.utcnow().date()
    cutoff = today - timedelta(days=max(days - 1, 0))

    visit_query = db.query(NotificationVisit).filter(NotificationVisit.visit_date >= cutoff)
    if source:
        visit_query = visit_query.filter(NotificationVisit.source == source)
    visits = visit_query.all()
    visit_ids = [visit.id for visit in visits]

    grouped = _group_visits(visits)
    filter_set: Optional[Set[str]] = None
    if symptoms:
        filter_set = {canonicalize_symptom(s) for s in symptoms if canonicalize_symptom(s)}

    alerts_upserted = 0

    for (group_date, location), payload in grouped.items():
        total_visits = payload["total_visits"]
        if total_visits <= 0:
            continue

        symptom_counts: Counter = payload["symptom_counts"]
        for symptom, symptom_count in symptom_counts.items():
            if filter_set and symptom not in filter_set:
                continue

            rate = symptom_count / total_visits
            severity, threshold_used = severity_for_rate(rate)
            if not severity or threshold_used is None:
                continue

            message = build_message(
                symptom=symptom,
                location=location,
                group_date=group_date,
                count=symptom_count,
                total=total_visits,
                rate=rate,
                severity=severity,
            )

            existing = (
                db.query(Notification)
                .filter(Notification.group_date == group_date)
                .filter(Notification.location == location)
                .filter(Notification.symptom == symptom)
                .first()
            )

            if existing:
                existing.created_at = datetime.utcnow()
                existing.severity = severity
                existing.total_visits = total_visits
                existing.symptom_count = symptom_count
                existing.rate = rate
                existing.threshold_used = threshold_used
                existing.message = message
            else:
                db.add(
                    Notification(
                        group_date=group_date,
                        location=location,
                        symptom=symptom,
                        severity=severity,
                        total_visits=total_visits,
                        symptom_count=symptom_count,
                        rate=rate,
                        threshold_used=threshold_used,
                        message=message,
                    )
                )
            alerts_upserted += 1

    deleted_source_visits = 0
    if delete_source_after_run and visit_ids:
        deleted_source_visits = (
            db.query(NotificationVisit)
            .filter(NotificationVisit.id.in_(visit_ids))
            .delete(synchronize_session=False)
        )

    return {
        "groups_processed": len(grouped),
        "source_visits": len(visits),
        "alerts_upserted": alerts_upserted,
        "deleted_source_visits": deleted_source_visits,
    }


def distribution_for_group(db: Session, group_date: date, location: str) -> Dict[str, object]:
    visits = (
        db.query(NotificationVisit)
        .filter(NotificationVisit.visit_date == group_date)
        .filter(NotificationVisit.location == location)
        .all()
    )

    total_visits = len(visits)
    symptom_counts: Counter = Counter()
    for visit in visits:
        for symptom in symptoms_from_json(visit.symptoms_json):
            symptom_counts[symptom] += 1

    distribution = []
    for symptom, count in symptom_counts.most_common():
        rate = (count / total_visits) if total_visits else 0.0
        distribution.append(
            {
                "symptom": symptom,
                "count": count,
                "rate": round(rate, 4),
            }
        )

    return {
        "group_date": group_date.isoformat(),
        "location": location,
        "total_visits": total_visits,
        "distribution": distribution,
    }
