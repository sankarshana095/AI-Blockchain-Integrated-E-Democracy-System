from datetime import datetime
from models.election import get_election_by_id, mark_election_completed
from services.election_closure_service import close_election_and_assign_reps

def finalize_election_if_needed(election):
    """
    Finalizes election ONLY ONCE:
    - Marks election COMPLETED
    - Assigns representatives
    """

    if election["status"] == "COMPLETED":
        return  # already done

    now = datetime.utcnow().isoformat()

    if now <= election["end_time"]:
        return  # election still running

    # 1️⃣ Mark election completed
    mark_election_completed(election["id"])

    # 2️⃣ Assign representatives
    close_election_and_assign_reps(election)
