from models.representative import (
    get_representatives_by_constituency,
    REPRESENTATIVES_TABLE,
    update_record
)
from utils.helpers import utc_now
from services.representative_role_sync_service import sync_user_roles_from_representatives
from models.notification import create_notification
from models.constituency import get_constituency_by_id,get_state_id_by_constituency_id

def terminate_constituency_terms(constituency_id: str):
    reps = get_representatives_by_constituency(constituency_id)

    for r in reps:
        if r.get("status") == "ACTIVE":
            update_record(
                REPRESENTATIVES_TABLE,
                {"id": r["id"]},
                {
                    "status": "TERMINATED",
                    "termination_reason": "PERFORMANCE_THRESHOLD_BREACH",
                    "terminated_at": utc_now().isoformat(),
                    "term_end": utc_now().date().isoformat()
                },
                use_admin=True
            )
    sync_user_roles_from_representatives()
    constituency = get_constituency_by_id(constituency_id)
    state_id = get_state_id_by_constituency_id(constituency_id)

    create_notification(
        title="Representative Term Ended",
        message=f"The term of representatives in {constituency['constituency_name']} has ended due to low performance.",
        role_target="CEO",
        state_id=state_id,
        constituency_id=constituency_id
    )

def completed_constituency_terms(constituency_id: str):
    reps = get_representatives_by_constituency(constituency_id)

    for r in reps:
        if r.get("status") == "ACTIVE":
            update_record(
                REPRESENTATIVES_TABLE,
                {"id": r["id"]},
                {
                    "status": "COMPLETED",
                    "term_end": utc_now().date().isoformat()
                },
                use_admin=True
            )
    sync_user_roles_from_representatives()