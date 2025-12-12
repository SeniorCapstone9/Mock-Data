from database import SessionLocal
from main import get_analytics
from database import get_db

def test_analytics():
    db = SessionLocal()
    try:
        # Mock dependency
        analytics = get_analytics(db=db)
        print("--- Tags Over Time ---")
        import json
        print(json.dumps(analytics['tags_over_time'], indent=2))
        
        print("\n--- Top Tags ---")
        print(json.dumps(analytics['top_tags'], indent=2))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_analytics()
