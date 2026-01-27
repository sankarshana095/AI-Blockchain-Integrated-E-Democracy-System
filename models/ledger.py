from supabase_db.db import fetch_one, fetch_all, insert_record
from utils.helpers import generate_uuid, utc_now


# -----------------------------
# Table Name
# -----------------------------

LEDGER_TABLE = "ledger_transactions"


# -----------------------------
# Ledger Transactions
# -----------------------------

def create_ledger_entry(
    entity_type: str,
    entity_id: str,
    transaction_hash: str,
    block_number: int = None
):
    payload = {
        "id": generate_uuid(),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "transaction_hash": transaction_hash,
        "block_number": block_number,
        "timestamp": utc_now().isoformat()
    }
    return insert_record(LEDGER_TABLE, payload, use_admin=True)


def get_ledger_entry_by_hash(transaction_hash: str):
    return fetch_one(LEDGER_TABLE, {"transaction_hash": transaction_hash})


def get_ledger_entries_by_entity(entity_type: str, entity_id: str):
    return fetch_all(
        LEDGER_TABLE,
        {
            "entity_type": entity_type,
            "entity_id": entity_id
        }
    )


def get_all_ledger_entries():
    return fetch_all(LEDGER_TABLE)
