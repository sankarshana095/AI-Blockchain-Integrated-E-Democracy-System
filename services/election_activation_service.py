from datetime import datetime
from utils.helpers import utc_now
from models.election import mark_election_active, parse_dt

def activate_election_if_needed(election):
    """
    Activates election ONLY ONCE:
    - Marks election ACTIVE when start_time is reached
    """

    if election["status"] in ["Draft","ACTIVE", "COMPLETED"]:
        return

    start_dt = parse_dt(election.get("start_time"))
    if not start_dt:
        return

    now = utc_now().isoformat()

    if now < str(start_dt):
        return

    mark_election_active(election["id"])
    print(f"Election activated: {election['election_name']}")