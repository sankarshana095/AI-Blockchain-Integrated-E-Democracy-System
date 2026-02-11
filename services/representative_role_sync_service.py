from utils.helpers import today_ist
from models.representative import (
    get_active_representatives,
    get_all_representatives
)
from models.user import update_user_role


def sync_user_roles_from_representatives():
    """
    Synchronizes user roles based on active representative terms.
    SAFE to run multiple times.
    """

    today = today_ist()

    # 1️⃣ Active representatives (today within term)
    active_reps = get_active_representatives(today)
    active_user_roles = {}  # user_id -> role

    for rep in active_reps:
        active_user_roles[rep["user_id"]] = rep["type"]

    # 2️⃣ Assign roles to active reps
    for user_id, role in active_user_roles.items():
        update_user_role(user_id, role)

    # 3️⃣ Find users whose terms ended and are no longer reps
    all_reps = get_all_representatives()

    all_rep_users = {r["user_id"] for r in all_reps}

    expired_users = all_rep_users - set(active_user_roles.keys())

    for user_id in expired_users:
        update_user_role(user_id, "CITIZEN")
