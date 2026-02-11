from supabase_db.db import fetch_one, fetch_all, insert_record, update_record
from utils.helpers import generate_uuid, utc_now


# -----------------------------
# Table Names
# -----------------------------

ELECTIONS_TABLE = "elections"
ELECTION_CONSTITUENCIES_TABLE = "election_constituencies"


# -----------------------------
# Elections
# -----------------------------

def create_election(
    election_name: str,
    election_type: str,
    state_id: str,
    start_time,
    end_time,
    created_by: str
):
    payload = {
        "id": generate_uuid(),
        "election_name": election_name,
        "election_type": election_type,
        "state_id": state_id,
        "start_time": start_time.isoformat() if hasattr(start_time, "isoformat") else start_time,
        "end_time": end_time.isoformat() if hasattr(end_time, "isoformat") else end_time,
        "status": "Draft",
        "created_by": created_by,
        "approved_by": None,
        "created_at": utc_now().isoformat()
    }
    return insert_record(ELECTIONS_TABLE, payload, use_admin=True)


def get_election_by_id(election_id: str):
    return fetch_one(ELECTIONS_TABLE, {"id": election_id})


def get_elections_by_state(state_id: str):
    return fetch_all(ELECTIONS_TABLE, {"state_id": state_id})


def get_all_elections():
    return fetch_all(ELECTIONS_TABLE)



def approve_election(election_id: str, approved_by: str):
    return update_record(
        ELECTIONS_TABLE,
        {"id": election_id},
        {
            "status": "Approved",
            "approved_by": approved_by
        },
        use_admin=True
    )


# -----------------------------
# Election Constituencies
# -----------------------------

def add_constituency_to_election(election_id: str, constituency_id: str):
    payload = {
        "id": generate_uuid(),
        "election_id": election_id,
        "constituency_id": constituency_id
    }
    return insert_record(ELECTION_CONSTITUENCIES_TABLE, payload, use_admin=True)


def get_constituencies_for_election(election_id):
    """
    Returns constituency_id + constituency_name for an election
    """

    mappings = fetch_all(
        "election_constituencies",
        {"election_id": election_id}
    )

    results = []

    for m in mappings:
        constituency = fetch_one(
            "constituencies",
            {"id": m["constituency_id"]}
        )

        if not constituency:
            continue

        results.append({
            "constituency_id": constituency["id"],
            "constituency_name": constituency["constituency_name"]
        })

    return results


def is_constituency_in_election(election_id: str, constituency_id: str) -> bool:
    record = fetch_one(
        ELECTION_CONSTITUENCIES_TABLE,
        {
            "election_id": election_id,
            "constituency_id": constituency_id
        }
    )
    return record is not None

def get_active_elections_by_constituency(constituency_id: str):
    """
    Step 1: Find election_ids mapped to this constituency
    Step 2: Fetch only approved + active elections
    """

    now = utc_now().isoformat()

    # 1️⃣ Get election IDs for constituency
    mappings = fetch_all(
        ELECTION_CONSTITUENCIES_TABLE,
        {"constituency_id": constituency_id}
    )

    if not mappings:
        return []

    election_ids = [row["election_id"] for row in mappings]

    # 2️⃣ Fetch elections one-by-one (safe + simple)
    elections = []
    for eid in election_ids:
        election = fetch_one(
            ELECTIONS_TABLE,
            {
                "id": eid,
                "status": "Approved"
            }
        )

        if not election:
            continue

        # Date window check
        if election["start_time"] <= now <= election["end_time"]:
            elections.append(election)

    return elections

def get_current_active_election():
    now = utc_now().isoformat()

    elections = fetch_all("elections", {"status": "Approved"})

    for election in elections:
        if election["start_time"] <= now <= election["end_time"]:
            return election

    return None

def get_completed_elections():
    elections = fetch_all("elections", {"status": "COMPLETED"})
    return [e for e in elections]

def mark_election_completed(election_id: str):
    """
    Marks an election as COMPLETED.
    This should be done only once, after end_time.
    """
    return update_record(
        ELECTIONS_TABLE,
        {"id": election_id},
        {
            "status": "COMPLETED"
        },
        use_admin=True
    )
