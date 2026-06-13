import os
import zlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import hashlib

def derive_key(password: bytes, salt: bytes, length: int = 32, iterations: int = 200_000) -> bytes:
    """PBKDF2-HMAC-SHA256"""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=length, salt=salt, iterations=iterations, backend=default_backend())
    return kdf.derive(password)

def xor_stream(data: bytes, key: bytes) -> bytes:
    out = bytearray(len(data))
    klen = len(key)
    for i, b in enumerate(data):
        out[i] = b ^ key[i % klen]
    return bytes(out)

def compress_bytes(data: bytes, method: str = 'zlib') -> bytes:
    if method == 'zlib':
        return zlib.compress(data)
    return data

def decompress_bytes(data: bytes, method: str = 'zlib') -> bytes:
    if method == 'zlib':
        return zlib.decompress(data)
    return data

def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


