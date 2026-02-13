from supabase_db.db import insert_record, fetch_all
from utils.helpers import generate_uuid, utc_now

TABLE = "issue_images"


def add_issue_image(issue_id: str, image_url: str):
    return insert_record(
        TABLE,
        {
            "id": generate_uuid(),
            "issue_id": issue_id,
            "image_url": image_url,
            "created_at": utc_now().isoformat(),
        },
        use_admin=True
    )


def get_issue_images(issue_id: str):
    return fetch_all(TABLE, {"issue_id": issue_id})
