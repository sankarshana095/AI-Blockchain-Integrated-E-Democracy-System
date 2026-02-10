# utils/crypto.py

import hashlib
import uuid
from datetime import datetime


def generate_vote_receipt(
    election_id: str,
    constituency_id: str,
    candidate_id: str
) -> str:
    """
    Generates an anonymous, non-reversible receipt hash for a vote.

    Nothing about the voter identity can be derived from this hash.
    """

    # High-entropy salt (prevents pattern attacks)
    salt = uuid.uuid4().hex

    # Timestamp adds uniqueness and ordering entropy
    timestamp = datetime.utcnow().isoformat()

    # Combine vote parameters
    raw_data = f"{election_id}|{constituency_id}|{candidate_id}|{salt}|{timestamp}"

    # SHA-256 cryptographic hash
    receipt_hash = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

    return receipt_hash

def uuid_to_uint256(uuid_str: str) -> int:
    """
    Converts UUID string to deterministic uint256
    suitable for blockchain.
    """
    hash_bytes = hashlib.sha256(uuid_str.encode()).digest()
    return int.from_bytes(hash_bytes, byteorder="big")