from supabase_db.db import fetch_one, fetch_all, insert_record, update_record
from utils.helpers import generate_uuid,generate_voter_id, utc_now


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
    return fetch_all(VOTERS_TABLE, {"constituency_id": constituency_id})


def update_voter_details(voter_id: str, update_data: dict):
    update_data["updated_at"] = utc_now().isoformat()
    return update_record(
        VOTERS_TABLE,
        {"id": voter_id},
        update_data,
        use_admin=True
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

