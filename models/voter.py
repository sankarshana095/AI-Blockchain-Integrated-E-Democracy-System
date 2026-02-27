from supabase_db.db import fetch_one, fetch_all, insert_record, update_record
from utils.helpers import generate_uuid,generate_voter_id, utc_now
from supabase_db.client import supabase_public, supabase_admin


# -----------------------------
# Table Names
# -----------------------------

VOTERS_TABLE = "voters"
VOTER_USER_MAP_TABLE = "voter_user_map"


# -----------------------------
# Voters
# -----------------------------

def create_voter(
    full_name: str,
    guardian_name: str,
    gender: str,
    date_of_birth,
    address: str,
    state_id: str,
    district_id: str,
    constituency_id: str,
    booth_id: str,
    photo_url: str = None
):
    payload = {
        "id": generate_uuid(),
        "voter_id_number": generate_voter_id(),
        "full_name": full_name,
        "guardian_name": guardian_name,
        "gender": gender,
        "date_of_birth": date_of_birth.isoformat() if hasattr(date_of_birth, "isoformat") else date_of_birth,
        "address": address,
        "photo_url": photo_url,
        "state_id": state_id,
        "district_id": district_id,
        "constituency_id": constituency_id,
        "booth_id": booth_id,
        "is_active": True,
        "created_at": utc_now().isoformat(),
        "updated_at": utc_now().isoformat()
    }
    return insert_record(VOTERS_TABLE, payload, use_admin=True)


def get_voter_by_id(voter_id: str):
    return fetch_one(VOTERS_TABLE, {"id": voter_id})


def get_voter_by_voter_id_number(voter_id_number: str):
    return fetch_one(VOTERS_TABLE, {"voter_id_number": voter_id_number})


def get_voters_by_constituency(constituency_id: str):
    """
    Returns voters with booth_name and booth_number instead of booth_id
    """

    voters = fetch_all(
        VOTERS_TABLE,
        {"constituency_id": constituency_id}
    )

    if not voters:
        return []

    result = []

    for voter in voters:
        booth = None

        if voter.get("booth_id"):
            booth = fetch_one(
                "booths",
                {"id": voter["booth_id"]}
            )

        result.append({
            "id": voter["id"],
            "voter_id_number": voter["voter_id_number"],
            "full_name": voter["full_name"],
            "guardian_name": voter["guardian_name"],
            "gender": voter["gender"],
            "date_of_birth": voter["date_of_birth"],
            "address": voter["address"],
            "booth_name": booth["booth_name"] if booth else None,
            "booth_number": booth["booth_number"] if booth else None,
            "is_active": voter["is_active"]
        })

    return result


def update_voter_details(voter_id, data,use_admin=True):
    return (
        supabase_public
        .table("voters")
        .update(data)
        .eq("id", voter_id)
        .execute()
    )




def deactivate_voter(voter_id: str):
    return update_record(
        VOTERS_TABLE,
        {"id": voter_id},
        {"is_active": False, "updated_at": utc_now().isoformat()},
        use_admin=True
    )


# -----------------------------
# Voter ↔ User Mapping
# -----------------------------

def map_voter_to_user(voter_id: str, user_id: str):
    payload = {
        "id": generate_uuid(),
        "voter_id": voter_id,
        "user_id": user_id,
        "created_at": utc_now().isoformat()
    }
    return insert_record(VOTER_USER_MAP_TABLE, payload, use_admin=True)


def get_voter_user_mapping_by_user(user_id: str):
    return fetch_one(VOTER_USER_MAP_TABLE, {"user_id": user_id})


def get_voter_user_mapping_by_voter(voter_id: str):
    return fetch_one(VOTER_USER_MAP_TABLE, {"voter_id": voter_id})

def get_voters_by_booth(booth_id: str):
    return fetch_all(VOTERS_TABLE, {"booth_id": booth_id})

from supabase_db.db import fetch_one

def get_voter_by_user_id(user_id: str):
    """
    Resolve voter using voter_user_map
    """
    mapping = fetch_one("voter_user_map", {"user_id": user_id})

    if not mapping:
        return None

    return fetch_one("voters", {"id": mapping["voter_id"]})


def get_user_id_by_voter_id(voter_id: str):
    """
    Returns the mapped user_id for a voter_id.
    """
    record = fetch_one(
        "voter_user_map",
        {"voter_id": voter_id}
    )

    if not record:
        return None

    return record.get("user_id")

def get_user_id_by_voter_id_number(voter_id_number: str):
    """
    Using voter_id_number:
    1. Fetch voter
    2. Get mapped user_id
    """
    print(f"Fetching user_id for voter_id_number: {voter_id_number}")
    # Step 1: Get voter using voter_id_number
    voter = get_voter_by_voter_id_number(voter_id_number)

    if not voter:
        return None

    # Step 2: Get user_id using voter_id
    return get_user_id_by_voter_id(voter["id"])