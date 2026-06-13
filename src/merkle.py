import hashlib
from typing import List

def hash_block(data: bytes) -> str:
    """Hashes a data block using SHA-256"""
    return hashlib.sha256(data).hexdigest()

def build_merkle_root(hashes: list[bytes]) -> bytes:
    if not hashes:
        return b'\x00' * 32
    nodes = hashes.copy()
    while len(nodes) > 1:
        if len(nodes) % 2:
            nodes.append(nodes[-1])  # duplicate last if odd
        new_level = []
        for i in range(0, len(nodes), 2):
            new_level.append(hashlib.sha256(nodes[i] + nodes[i+1]).digest())
        nodes = new_level
    return nodes[0]
