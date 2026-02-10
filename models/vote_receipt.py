from supabase_db.db import fetch_all, insert_record


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
