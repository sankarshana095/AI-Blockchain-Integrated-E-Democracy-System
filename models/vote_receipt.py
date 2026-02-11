from supabase_db.db import fetch_all, insert_record

VOTE_RECEIPTS_TABLE = "vote_receipts"

def store_receipt(election_id: str, receipt_hash: str):
    insert_record(
        "vote_receipts",
        {
            "election_id": election_id,
            "receipt_hash": receipt_hash,
        }
    )


def get_all_receipts_for_election(election_id: str):
    rows = fetch_all(
        table="vote_receipts",
        filters={"election_id": election_id},
        order_by=("created_at", "asc"),
        columns=["receipt_hash"],
    )

    return [row["receipt_hash"] for row in rows]

def get_receipts_by_election(election_id):
    """
    Returns all vote receipts for an election.
    Used for Merkle tree construction.
    """
    return fetch_all(
        VOTE_RECEIPTS_TABLE,
        {"election_id": election_id}
    )