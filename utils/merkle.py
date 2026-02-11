# utils/merkle.py

from eth_hash.auto import keccak
from typing import List


def _hash(data: bytes) -> bytes:
    return keccak(data)


def hash_leaf(value: str) -> bytes:
    # value is already a hash (hex string)
    return bytes.fromhex(value)



def build_merkle_tree(receipt_hashes):
    level = [bytes.fromhex(r) for r in receipt_hashes]
    tree = [level]

    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left

            # ✅ SORT before hashing
            combined = left + right if left < right else right + left
            next_level.append(_hash(combined))

        level = next_level
        tree.append(level)

    return tree



def get_merkle_root(receipt_hashes: List[str]) -> str:
    """
    Returns Merkle root as hex string.
    """
    tree = build_merkle_tree(receipt_hashes)
    root = tree[-1][0]
    return root.hex()


def get_merkle_proof(receipt_hashes: List[str], target_receipt: str) -> List[str]:
    """
    Generates Merkle proof for a given receipt hash.

    Returns:
        List of sibling hashes (hex strings)
    """

    if target_receipt not in receipt_hashes:
        raise ValueError("Receipt not found")

    tree = build_merkle_tree(receipt_hashes)
    index = receipt_hashes.index(target_receipt)

    proof = []

    for level in tree[:-1]:
        sibling_index = index ^ 1  # flip last bit

        if sibling_index < len(level):
            proof.append(level[sibling_index].hex())

        index //= 2

    return proof
