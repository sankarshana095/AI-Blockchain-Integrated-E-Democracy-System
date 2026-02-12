from supabase_db.db import insert_record, fetch_one
from utils.helpers import generate_uuid, utc_now

TABLE = "issue_feedback"


def submit_feedback(issue_id, citizen_id, rating, review):
    payload = {
        "id": generate_uuid(),
        "issue_id": issue_id,
        "citizen_id": citizen_id,
        "rating": rating,
        "review": review,
        "created_at": utc_now().isoformat()
    }
    return insert_record(TABLE, payload, use_admin=True)


def get_feedback(issue_id):
    return fetch_one(TABLE, {"issue_id": issue_id})
