# services/merkle_service.py

from models.vote_receipt import get_receipts_by_election
from models.vote_merkle_proof import store_merkle_proof
from utils.merkle import get_merkle_root, get_merkle_proof,build_merkle_tree
from services.blockchain_service import publish_merkle_root_on_chain


def finalize_merkle_tree_for_election(election_id):
    """
    Called ONCE after election ends.
    """
    receipts = get_receipts_by_election(election_id)

    if not receipts:
        raise ValueError("No votes found for election")

    receipt_hashes = [r["receipt_hash"] for r in receipts]
    # 1️⃣ Compute root
    merkle_root = get_merkle_root(receipt_hashes)

    # 2️⃣ Store proof for each receipt
    for r in receipt_hashes:
        proof = get_merkle_proof(receipt_hashes, r)
        store_merkle_proof(election_id, r, proof)

    # 3️⃣ Publish root on-chain
    publish_merkle_root_on_chain(election_id, merkle_root)

    return merkle_root
