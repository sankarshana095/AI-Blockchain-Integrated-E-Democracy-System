from supabase_db.db import fetch_one, fetch_all, insert_record, update_record
from utils.helpers import generate_uuid, utc_now


# -----------------------------
# Table Names
# -----------------------------

CANDIDATES_TABLE = "candidates"
REPRESENTATIVES_TABLE = "representatives"


# -----------------------------
# Candidates (Nomination)
# -----------------------------

def create_candidate(
    user_id: str,
    election_id: str,
    constituency_id: str,
    party_name: str
):
    payload = {
        "id": generate_uuid(),
        "user_id": user_id,
        "election_id": election_id,
        "constituency_id": constituency_id,
        "party_name": party_name,
        "status": "Pending",
        "created_at": utc_now().isoformat()
    }
    return insert_record(CANDIDATES_TABLE, payload, use_admin=True)


def get_candidate_by_id(candidate_id: str):
    return fetch_one(CANDIDATES_TABLE, {"id": candidate_id})


def get_candidates_by_election(election_id: str):
    return fetch_all(CANDIDATES_TABLE, {"election_id": election_id})


def get_candidates_by_constituency(constituency_id: str):
    return fetch_all(CANDIDATES_TABLE, {"constituency_id": constituency_id})

def get_candidates_by_election_and_constituency(election_id: str, constituency_id: str):
    return fetch_all(
        "candidates",
        {
            "election_id": election_id,
            "constituency_id": constituency_id
        }
    )


def update_candidate_status(candidate_id: str, status: str):
    return update_record(
        CANDIDATES_TABLE,
        {"id": candidate_id},
        {"status": status},
        use_admin=True
    )


# -----------------------------
# Representatives
# -----------------------------

def create_representative(
    user_id: str,
    constituency_id: str,
    rep_type: str,
    term_start,
    term_end
):
    payload = {
        "id": generate_uuid(),
        "user_id": user_id,
        "constituency_id": constituency_id,
        "type": rep_type,
        "term_start": term_start,
        "term_end": term_end
    }
    return insert_record(REPRESENTATIVES_TABLE, payload, use_admin=True)


def get_representative_by_user(user_id: str):
    return fetch_one(REPRESENTATIVES_TABLE, {"user_id": user_id})


def get_representatives_by_constituency(constituency_id: str):
    return fetch_all(REPRESENTATIVES_TABLE, {"constituency_id": constituency_id})

def get_candidates_with_names(election_id: str, constituency_id: str):
    candidates = fetch_all(
        "candidates",
        {
            "election_id": election_id,
            "constituency_id": constituency_id
        }
    )

    enriched = []

    for c in candidates:
        # Step 1: user → voter mapping
        mapping = fetch_one(
            "voter_user_map",
            {"user_id": c["user_id"]}
        )

        if not mapping:
            continue

        # Step 2: voter → name
        voter = fetch_one(
            "voters",
            {"id": mapping["voter_id"]}
        )

        if not voter:
            continue

        enriched.append({
            **c,
            "candidate_name": voter["full_name"]
        })

    return enriched
