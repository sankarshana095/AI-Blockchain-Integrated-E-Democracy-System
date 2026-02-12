from supabase_db.db import insert_record, fetch_all
from utils.helpers import generate_uuid, utc_now

TABLE = "issue_status_timeline"


def add_issue_status(
    issue_id,
    status,
    changed_by,
    note,
    estimated_start_at=None,
    estimated_completion_at=None
):
    payload = {
        "id": generate_uuid(),
        "issue_id": issue_id,
        "status": status,
        "changed_by": changed_by,
        "note": note,
        "estimated_start_at": estimated_start_at,
        "estimated_completion_at": estimated_completion_at,
        "created_at": utc_now().isoformat()
    }
    return insert_record(TABLE, payload, use_admin=True)


def get_issue_timeline(issue_id):
    return fetch_all(TABLE, {"issue_id": issue_id})
