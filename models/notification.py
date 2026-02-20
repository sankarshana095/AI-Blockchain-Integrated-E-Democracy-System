from supabase_db.db import insert_record, fetch_all, update_record
from utils.helpers import generate_uuid, utc_now

NOTIFICATIONS_TABLE = "system_notifications"


def create_notification(title, message, role_target, state_id=None, constituency_id=None):
    payload = {
        "id": generate_uuid(),
        "title": title,
        "message": message,
        "role_target": role_target,
        "state_id": state_id,
        "constituency_id": constituency_id,
        "created_at": utc_now().isoformat(),
        "is_read": False
    }
    return insert_record(NOTIFICATIONS_TABLE, payload, use_admin=True)


def get_notifications_for_user(role, state_id=None):
    filters = {"role_target": role}

    if state_id:
        filters["state_id"] = state_id

    return fetch_all(NOTIFICATIONS_TABLE, filters)


def mark_notification_read(notification_id):
    return update_record(
        NOTIFICATIONS_TABLE,
        {"id": notification_id},
        {"is_read": True},
        use_admin=True
    )