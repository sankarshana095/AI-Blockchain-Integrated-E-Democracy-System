from utils.helpers import today_ist
from models.representative import (
    get_active_representatives,
    get_all_representatives,
    get_terminated_representatives
)
from models.user import update_user_role
from utils.helpers import utc_now


def sync_user_roles_from_representatives():
    """
    Synchronizes user roles based on representative status.
    SAFE to run multiple times.
    """

    today = today_ist()

    # 1️⃣ Active representatives
    active_reps = get_active_representatives(today)
    active_user_roles = {}

    for rep in active_reps:
        if rep.get("user_id"):
            active_user_roles[rep["user_id"]] = rep["type"]

    # Assign roles to active reps
    for user_id, role in active_user_roles.items():
        update_user_role(user_id, role)

    # 2️⃣ Explicitly downgrade TERMINATED reps
    terminated_reps = get_terminated_representatives(utc_now().date())

    for rep in terminated_reps:
        if rep.get("user_id"):
            update_user_role(rep["user_id"], "CITIZEN")

    # 3️⃣ Handle expired terms (not active anymore but not terminated)
    all_reps = get_all_representatives()

    all_rep_users = {
        r["user_id"] for r in all_reps if r.get("user_id")
    }

    expired_users = all_rep_users - set(active_user_roles.keys())

    for user_id in expired_users:
        update_user_role(user_id, "CITIZEN")