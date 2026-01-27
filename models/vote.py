from supabase_db.db import fetch_one, fetch_all, insert_record, update_record
from utils.helpers import generate_uuid, utc_now


# -----------------------------
# Table Names
# -----------------------------

VOTES_TABLE = "votes"
VOTE_STATUS_TABLE = "vote_status"


# -----------------------------
# Votes (Blockchain-safe)
# -----------------------------

def cast_vote(
    election_id: str,
    constituency_id: str,
    voter_id: str,
    vote_hash: str,
    block_number: int = None,
    transaction_id: str = None
):
    payload = {
        "id": generate_uuid(),
        "election_id": election_id,
        "constituency_id": constituency_id,
        "voter_id": voter_id,
        "vote_hash": vote_hash,
        "block_number": block_number,
        "transaction_id": transaction_id,
        "timestamp": utc_now().isoformat()
    }
    return insert_record(VOTES_TABLE, payload, use_admin=True)


def get_vote_by_hash(vote_hash: str):
    return fetch_one(VOTES_TABLE, {"vote_hash": vote_hash})


def get_votes_by_election(election_id: str):
    return fetch_all(VOTES_TABLE, {"election_id": election_id})


def get_votes_by_constituency(constituency_id: str):
    return fetch_all(VOTES_TABLE, {"constituency_id": constituency_id})


# -----------------------------
# Vote Status (One vote per voter)
# -----------------------------

def initialize_vote_status(voter_id: str, election_id: str):
    payload = {
        "voter_id": voter_id,
        "election_id": election_id,
        "has_voted": False,
        "voted_at": None
    }
    return insert_record(VOTE_STATUS_TABLE, payload, use_admin=True)


def mark_voter_as_voted(voter_id: str, election_id: str):
    return update_record(
        VOTE_STATUS_TABLE,
        {
            "voter_id": voter_id,
            "election_id": election_id
        },
        {
            "has_voted": True,
            "voted_at": utc_now().isoformat()
        },
        use_admin=True
    )


def has_voter_voted(voter_id: str, election_id: str) -> bool:
    record = fetch_one(
        VOTE_STATUS_TABLE,
        {
            "voter_id": voter_id,
            "election_id": election_id
        }
    )
    return bool(record and record.get("has_voted"))
