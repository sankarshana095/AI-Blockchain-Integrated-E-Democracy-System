# utils/merkle.py

import hashlib
from typing import List


def _hash(data: bytes) -> bytes:
    """SHA-256 hash helper"""
    return hashlib.sha256(data).digest()


def hash_leaf(value: str) -> bytes:
    """
    Hash a receipt hash string into a Merkle leaf.
    """
    return _hash(value.encode("utf-8"))


def build_merkle_tree(receipt_hashes: List[str]) -> List[List[bytes]]:
    """
    Builds a Merkle tree from receipt hashes.

    Returns:
        tree[level][index]
        level 0 = leaves
        last level = root
    """

    if not receipt_hashes:
        raise ValueError("No receipt hashes provided")

    # Level 0: leaf hashes
    level = [hash_leaf(r) for r in receipt_hashes]
    tree = [level]

    # Build upwards
    while len(level) > 1:
        next_level = []

        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left

            parent = _hash(left + right)
            next_level.append(parent)

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
