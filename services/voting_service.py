from datetime import datetime

from models.vote import (
    has_voter_voted,
    mark_voter_as_voted
)

from models.vote_receipt import store_receipt
from utils.crypto import generate_vote_receipt
from services.blockchain_service import cast_vote_on_chain


# -----------------------------
# Voting Service
# -----------------------------

def submit_vote(
    election_id: str,
    constituency_id: str,
    voter_id: str,
    vote_payload: str
):
    """
    Privacy-preserving blockchain vote casting:

    - DB prevents double voting
    - Generates anonymous receipt hash
    - Records vote on blockchain (event only)
    - Stores receipt off-chain for Merkle proof
    """

    # ------------------------------------------------
    # 1. Prevent double voting
    # ------------------------------------------------
    if has_voter_voted(voter_id, election_id):
        raise ValueError("Voter has already voted in this election")

    candidate_id = vote_payload

    # ------------------------------------------------
    # 2. Generate anonymous receipt
    # ------------------------------------------------
    receipt_hash = generate_vote_receipt(
        election_id=election_id,
        constituency_id=constituency_id,
        candidate_id=candidate_id
    )

    # ------------------------------------------------
    # 3. Cast vote on blockchain (NO receipt stored)
    # ------------------------------------------------
    tx_hash = cast_vote_on_chain(
        election_id=election_id,
        candidate_id=candidate_id,
        receipt_hash=receipt_hash
    )

    # ------------------------------------------------
    # 4. Store receipt off-chain (for Merkle proof)
    # ------------------------------------------------
    store_receipt(
        election_id=election_id,
        receipt_hash=receipt_hash
    )

    # ------------------------------------------------
    # 5. Mark voter as voted
    # ------------------------------------------------
    mark_voter_as_voted(voter_id, election_id)

    # ------------------------------------------------
    # 6. Return receipt to UI
    # ------------------------------------------------
    return {
        "receipt_hash": receipt_hash,
        "tx_hash": tx_hash
    }
