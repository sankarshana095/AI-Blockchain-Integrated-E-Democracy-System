from supabase_db.db import fetch_one, fetch_all, insert_record, update_record
from utils.helpers import generate_uuid, utc_now, format_datetime
from datetime import datetime


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
    created_by: str,
    nomination_deadline,
    draft_roll_publish_at,
    final_roll_publish_at,
):
    payload = {
        "id": generate_uuid(),
        "election_name": election_name,
        "election_type": election_type,
        "state_id": state_id,
        "start_time": start_time.isoformat() if hasattr(start_time, "isoformat") else start_time,
        "end_time": end_time.isoformat() if hasattr(end_time, "isoformat") else end_time,
        "nomination_deadline": nomination_deadline.isoformat() if hasattr(start_time, "isoformat") else start_time,
        "draft_roll_publish_at": draft_roll_publish_at.isoformat() if hasattr(end_time, "isoformat") else end_time,
        "final_roll_publish_at": final_roll_publish_at.isoformat() if hasattr(start_time, "isoformat") else start_time,
        "status": "Draft",
        "created_by": created_by,
        "approved_by": None,
        "created_at": utc_now().isoformat()
    }
    return insert_record(ELECTIONS_TABLE, payload, use_admin=True)

def get_state_name_by_state_id(state_id):
    return fetch_one("states", {"id": state_id})

def get_election_by_id(election_id: str):
    election=fetch_one(ELECTIONS_TABLE, {"id": election_id})
    state=get_state_name_by_state_id(election['state_id'])
    election["state_name"]=state["state_name"]
    return election


def get_elections_by_state(state_id: str):
    elections=fetch_all(ELECTIONS_TABLE, {"state_id": state_id})
    for election in elections:
        election["start_time"]=format_datetime(election["start_time"])
        election["end_time"]=format_datetime(election["end_time"])
    return elections

def get_all_elections():
    elections=fetch_all(ELECTIONS_TABLE)
    for election in elections:
        state=get_state_name_by_state_id(election['state_id'])
        election["state_name"]=state["state_name"]
        election["_start_time"]=format_datetime(election["start_time"])
        election["_end_time"]=election["end_time"]
        election["start_time"]=format_datetime(election["start_time"])
        election["end_time"]=format_datetime(election["end_time"])
    return elections


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
'''
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
'''

def get_active_elections_by_constituency(constituency_id: str):
    """
    Returns ACTIVE elections mapped to this constituency.
    Lifecycle logic handled elsewhere — we only fetch ACTIVE ones.
    """

    # 1️⃣ Get election IDs mapped to this constituency
    mappings = fetch_all(
        ELECTION_CONSTITUENCIES_TABLE,
        {"constituency_id": constituency_id}
    )

    if not mappings:
        return []

    election_ids = [row["election_id"] for row in mappings]

    # 2️⃣ Fetch ACTIVE elections only
    elections = []

    for eid in election_ids:
        election = fetch_one(
            ELECTIONS_TABLE,
            {
                "id": eid,
                "status": "ACTIVE"
            }
        )

        if election:
            elections.append(election)

    return elections

def get_current_active_election():
    now = utc_now().isoformat()

    elections = fetch_all("elections", {"status": "Approved"})

    for election in elections:
        if election["start_time"] <= now <= election["end_time"]:
            return election

    return None

def get_current_active_election_for_results():
    now = utc_now().isoformat()

    elections = fetch_all("elections", {"status": "ACTIVE"})

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

def get_district_name_by_district_id(district_id):
    return fetch_one("districts", {"id": district_id})

def update_election(election_id, update_data):
    return update_record(
        "elections",
        {"id": election_id},
        update_data,
        use_admin=True
    )



def parse_dt(value):
    """
    Accepts both ISO timestamps and human readable timestamps
    """
    if not value:
        return None

    # Try ISO first
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        pass

    # Try your display format
    try:
        return datetime.strptime(str(value), "%d %b %Y, %I:%M %p")
    except Exception:
        return None


def is_roll_locked(election):
    if not election:
        return False

    final_dt = parse_dt(election.get("final_roll_publish_at"))
    end_dt = parse_dt(election.get("end_time"))

    if not final_dt or not end_dt:
        return False

    now = datetime.utcnow()
    return final_dt <= now <= end_dt


def get_elections_by_constituency(constituency_id: str):
    """
    Returns all elections mapped to a constituency
    """

    # Step 1: fetch mapping rows
    mappings = fetch_all(
        ELECTION_CONSTITUENCIES_TABLE,
        {"constituency_id": constituency_id}
    )

    if not mappings:
        return []

    # Step 2: extract election IDs
    election_ids = [m["election_id"] for m in mappings]

    # Step 3: fetch elections one by one
    elections = []
    for eid in election_ids:
        e = fetch_one(ELECTIONS_TABLE, {"id": eid})
        if e:
            # format times same as your state function
            e["start_time"] = format_datetime(e["start_time"])
            e["end_time"] = format_datetime(e["end_time"])
            elections.append(e)

    return elections

def mark_election_active(election_id: str):
    """
    Marks an election as ACTIVE.
    Should be triggered once when start_time is reached.
    """
    return update_record(
        ELECTIONS_TABLE,
        {"id": election_id},
        {
            "status": "ACTIVE"
        },
        use_admin=True
    )

def get_approved_elections():
    """
    Returns all elections whose status is 'Approved'
    """

    elections = fetch_all(ELECTIONS_TABLE, {"status": "Approved"})

    for election in elections:
        # Add state name (like in get_all_elections)
        state = get_state_name_by_state_id(election["state_id"])
        if state:
            election["state_name"] = state["state_name"]

        # Format datetime fields
        election["start_time"] = format_datetime(election["start_time"])
        election["end_time"] = format_datetime(election["end_time"])

    return elections

def get_approved_elections_by_state(state_id: str):
    """
    Returns all APPROVED elections for a given state_id.
    """

    elections = fetch_all(
        ELECTIONS_TABLE,
        {
            "state_id": state_id,
            "status": "Approved"
        }
    )

    if not elections:
        return []

    for election in elections:
        election["start_time"] = format_datetime(election["start_time"])
        election["end_time"] = format_datetime(election["end_time"])

    return elections

def get_candidates_by_constituency_and_election(constituency_id: str, election_id: str):
    """
    Returns candidates for a given constituency + election
    with resolved display name
    """

    # Step 1: Fetch candidates matching both filters
    candidates = fetch_all(
        "candidates",
        {
            "constituency_id": constituency_id,
            "election_id": election_id
        }
    )

    if not candidates:
        return []

    result = []

    for c in candidates:
        # Step 2: map user_id → voter_id
        voter_map = fetch_one(
            "voter_user_map",
            {"user_id": c["user_id"]}
        )

        if not voter_map:
            continue

        # Step 3: voter_id → voter full name
        voter = fetch_one(
            "voters",
            {"id": voter_map["voter_id"]}
        )

        if not voter:
            continue

        result.append({
            "id": c["id"],
            "candidate_name": voter["full_name"],
            "party_name": c["party_name"],
            "created_at": format_datetime(c["created_at"]),
            "election_id": c["election_id"]
        })

    return result