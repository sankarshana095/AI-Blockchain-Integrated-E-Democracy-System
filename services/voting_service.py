import hashlib
import json
from models.vote import (
    cast_vote,
    has_voter_voted,
    mark_voter_as_voted
)
from models.ledger import create_ledger_entry
from utils.helpers import sha256_hash, generate_transaction_id

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
    Handles secure vote casting:
    - Prevents double voting
    - Hashes vote payload
    - Writes vote to DB
    - Creates ledger entry
    """

    # Prevent double voting
    if has_voter_voted(voter_id, election_id):
        raise ValueError("Voter has already voted in this election")

    # Create vote hash (privacy-safe)
    vote_hash = sha256_hash(vote_payload)

    # Generate transaction ID
    transaction_id = generate_transaction_id(prefix="VOTE")

    # Store vote
    cast_vote(
        election_id=election_id,
        constituency_id=constituency_id,
        voter_id=voter_id,
        vote_hash=vote_hash,
        transaction_id=transaction_id
    )

    # Mark voter as voted
    mark_voter_as_voted(voter_id, election_id)

    # Create ledger entry
    create_ledger_entry(
        entity_type="VOTE",
        entity_id=voter_id,
        transaction_hash=transaction_id
    )

    return {
        "transaction_id": transaction_id,
        "vote_hash": vote_hash
    }

def hash_vote(candidate_id, election_id, voter_id):
    payload = {
        "candidate_id": candidate_id,
        "election_id": election_id,
        "voter_id": voter_id
    }

    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()