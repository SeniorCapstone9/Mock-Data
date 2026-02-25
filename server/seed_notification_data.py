import argparse
import json
import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from database import SessionLocal, init_db, NotificationVisit, Notification


DEFAULT_LOCATIONS = ["FL", "CA", "NY", "TX", "WA", "IL", "GA", "AZ"]
NON_FLU_SYMPTOMS = [
    "fever",
    "cough",
    "fatigue",
    "headache",
    "sore throat",
    "nausea",
    "shortness of breath",
    "body ache",
    "runny nose",
    "chills",
]


def parse_locations(raw: str) -> List[str]:
    values = [v.strip().upper() for v in raw.split(",") if v.strip()]
    return values or DEFAULT_LOCATIONS


def add_background_symptoms(symptoms: List[str]) -> List[str]:
    # Add 0-2 extra symptoms to increase realism/diversity.
    extra_count = random.randint(0, 2)
    extras = random.sample(NON_FLU_SYMPTOMS, k=min(extra_count, len(NON_FLU_SYMPTOMS)))
    merged = list(dict.fromkeys(symptoms + extras))
    return merged


def build_visit_symptoms(is_flu_case: bool) -> List[str]:
    symptoms: List[str] = []
    if is_flu_case:
        symptoms.append("flu")
        # Common co-occurring symptoms for flu-like visits.
        symptoms.extend(random.sample(["fever", "cough", "body ache", "chills"], k=random.randint(1, 2)))
    return add_background_symptoms(symptoms)


def choose_flu_rate(scenario: str, location: str, day_index: int, days: int, spike_location: str) -> float:
    if scenario == "normal":
        return random.uniform(0.05, 0.10)

    if scenario == "abnormal":
        if location == spike_location and day_index == max(0, days // 2):
            return random.uniform(0.40, 0.60)
        return random.uniform(0.05, 0.10)

    # mixed
    if location == spike_location and day_index in {max(0, days // 3), max(0, (2 * days) // 3)}:
        return random.uniform(0.35, 0.55)
    if location in {"FL", "TX"}:
        return random.uniform(0.12, 0.22)
    return random.uniform(0.05, 0.12)


def seed_notification_data(
    db: Session,
    scenario: str,
    days: int,
    visits_per_day: int,
    locations: List[str],
    spike_location: str,
    clear_existing: bool,
    seed: int,
) -> None:
    random.seed(seed)

    if clear_existing:
        db.query(Notification).delete()
        db.query(NotificationVisit).delete()
        db.commit()

    start_date = datetime.utcnow().date() - timedelta(days=max(days - 1, 0))

    inserted = 0
    for day_index in range(days):
        visit_date = start_date + timedelta(days=day_index)

        for location in locations:
            flu_rate = choose_flu_rate(scenario, location, day_index, days, spike_location)

            for _ in range(visits_per_day):
                is_flu_case = random.random() < flu_rate
                symptoms = build_visit_symptoms(is_flu_case)

                if not symptoms:
                    symptoms = [random.choice(NON_FLU_SYMPTOMS)]

                row = NotificationVisit(
                    visit_date=visit_date,
                    location=location,
                    symptoms_json=json.dumps(symptoms),
                    source="mock",
                )
                db.add(row)
                inserted += 1

    db.commit()

    print("Notification mock data seeded successfully.")
    print(f"Scenario: {scenario}")
    print(f"Days: {days}")
    print(f"Locations: {', '.join(locations)}")
    print(f"Visits per day per location: {visits_per_day}")
    print(f"Total rows inserted: {inserted}")
    print(f"Spike location (if used): {spike_location}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed standalone notification mock data")
    parser.add_argument("--scenario", choices=["normal", "abnormal", "mixed"], default="abnormal")
    parser.add_argument("--days", type=int, default=14, help="Number of days to generate")
    parser.add_argument(
        "--visits-per-day",
        type=int,
        default=150,
        help="Visits per day per location",
    )
    parser.add_argument(
        "--locations",
        type=str,
        default=",".join(DEFAULT_LOCATIONS),
        help="Comma-separated state codes (e.g. FL,CA,NY)",
    )
    parser.add_argument("--spike-location", type=str, default="FL")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clear", action="store_true", help="Delete existing notification_visits + notifications before seeding")

    args = parser.parse_args()

    if args.days < 1:
        raise ValueError("--days must be >= 1")
    if args.visits_per_day < 1:
        raise ValueError("--visits-per-day must be >= 1")

    locations = parse_locations(args.locations)
    spike_location = args.spike_location.strip().upper()
    if spike_location not in locations:
        # Keep scenario behavior deterministic while avoiding an invalid spike target.
        spike_location = locations[0]

    init_db()
    db = SessionLocal()
    try:
        seed_notification_data(
            db=db,
            scenario=args.scenario,
            days=args.days,
            visits_per_day=args.visits_per_day,
            locations=locations,
            spike_location=spike_location,
            clear_existing=args.clear,
            seed=args.seed,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
