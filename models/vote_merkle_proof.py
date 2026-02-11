# models/vote_merkle_proof.py

from supabase_db.db import insert_record, fetch_one
from utils.helpers import generate_uuid, utc_now

TABLE = "vote_merkle_proofs"


def store_merkle_proof(election_id, receipt_hash, proof):
    return insert_record(
        TABLE,
        {
            "id": generate_uuid(),
            "election_id": election_id,
            "receipt_hash": receipt_hash,
            "proof": proof,
            "created_at": utc_now().isoformat()
        },
        use_admin=True
    )


def get_merkle_proof(election_id, receipt_hash):
    return fetch_one(
        TABLE,
        {
            "election_id": election_id,
            "receipt_hash": receipt_hash
        }
    )
