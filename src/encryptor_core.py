import os
import json
import struct
import tempfile
import secrets
from typing import List, Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from src.utils import derive_key, xor_stream, compress_bytes, decompress_bytes, sha256_bytes
from src.merkle import build_merkle_root
from src.keyutils import load_private_key_from_bytes, load_public_key_from_bytes, load_public_pem, load_private_pem


MAGIC = b'BXCRYPT1\x00'  # 8 bytes
VERSION = 1
DEFAULT_CHUNK = 1024 * 1024  # 1 MB


def _rsa_wrap(pub_pem: bytes, key: bytes) -> bytes:
    pub = load_public_key_from_bytes(pub_pem)
    return pub.encrypt(key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))


def _rsa_unwrap(priv_pem: bytes, wrapped: bytes, password: Optional[bytes] = None) -> bytes:
    clean_pass = None
    if password:
        if password.strip():
            clean_pass = password    
    priv = load_private_key_from_bytes(priv_pem, password=clean_pass)
    return priv.decrypt(wrapped, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))


def encrypt_file(in_path: str, out_path: str,
                 level: str = 'aes',
                 password: Optional[str] = None,
                 rsa_public_pems: Optional[List[bytes]] = None,
                 compress: bool = False,
                 chunk_size: int = DEFAULT_CHUNK) -> None:
    """
    Encodes file into container with header + chunk index + encrypted payload.
    level: 'general', 'aes', 'rsa'
    """
    if level == 'general' and not password:
        raise ValueError("Password required for 'general' level")
    if level == 'rsa' and (not rsa_public_pems or len(rsa_public_pems) == 0):
        raise ValueError("At least one recipient public key required for 'rsa'")

    orig_name = os.path.basename(in_path)
    orig_size = os.path.getsize(in_path)
    salt = secrets.token_bytes(16)
    header = {
        'magic': MAGIC.hex(),
        'version': VERSION,
        'orig_name': orig_name,
        'orig_size': orig_size,
        'chunk_size': chunk_size,
        'compress': bool(compress),
        'enc_level': level,
        'salt': salt.hex(),
        'nonce_base': None,
        'key_wrapped': [],   # for rsa
        'merkle_root': None,
        'chunk_count': 0
    }

    # derive or generate symmetric key
    if level == 'general' or level == 'aes':
        sym_key = derive_key(password.encode('utf-8'), salt, length=32)
    else:
        sym_key = secrets.token_bytes(32)

    # if rsa, wrap sym_key for each recipient and store wrapped bytes (hex)
    if level == 'rsa':
        for pem in rsa_public_pems:
            wrapped = _rsa_wrap(pem, sym_key)
            header['key_wrapped'].append(wrapped.hex())

    aesgcm = AESGCM(sym_key)
    nonce_base = secrets.token_bytes(12)
    header['nonce_base'] = nonce_base.hex()

    # We'll write encrypted chunks to a temp file while building index and hashes
    chunk_index = []
    chunk_hashes = []
    temp_payload = tempfile.NamedTemporaryFile(delete=False)
    try:
        with open(in_path, 'rb') as fin, temp_payload:
            chunk_no = 0
            while True:
                chunk = fin.read(chunk_size)
                if not chunk:
                    break
                pt = chunk
                if compress:
                    pt = compress_bytes(pt, method='zlib')
                # encryption
                if level == 'general':
                    ct = xor_stream(pt, sym_key)
                else:
                    # build nonce: nonce_base ^ counter in last 4 bytes
                    nb = bytearray(nonce_base)
                    counter = chunk_no.to_bytes(4, 'big')
                    for i in range(4):
                        nb[-1 - i] ^= counter[-1 - i]
                    nonce = bytes(nb)
                    ct = aesgcm.encrypt(nonce, pt, None)
                # write ct to temp, record offset/len/hash
                cur_off = temp_payload.tell()
                temp_payload.write(ct)
                cur_len = len(ct)
                h = sha256_bytes(ct)
                chunk_index.append({'offset': cur_off, 'length': cur_len, 'hash': h.hex()})
                chunk_hashes.append(h)
                chunk_no += 1

        # merkle
        merkle_root = build_merkle_root(chunk_hashes)
        header['merkle_root'] = merkle_root.hex()
        header['chunk_count'] = len(chunk_index)

        # write final container
        header_json = json.dumps(header).encode('utf-8')
        with open(out_path, 'wb') as fout:
            fout.write(MAGIC)
            fout.write(struct.pack('B', VERSION))
            fout.write(struct.pack('<I', len(header_json)))
            fout.write(header_json)
            # write chunk index count then index entries (binary)
            fout.write(struct.pack('<I', len(chunk_index)))
            for e in chunk_index:
                fout.write(struct.pack('<Q', e['offset']))   # 8 bytes
                fout.write(struct.pack('<I', e['length']))   # 4 bytes
                fout.write(bytes.fromhex(e['hash']))         # 32 bytes SHA-256
            # append payload
            with open(temp_payload.name, 'rb') as tp:
                while True:
                    buf = tp.read(1 << 20)
                    if not buf:
                        break
                    fout.write(buf)
    finally:
        try:
            os.remove(temp_payload.name)
        except Exception:
            pass


def decrypt_file(enc_path: str, out_path: str, password: Optional[str] = None, rsa_priv_pem: Optional[bytes] = None, rsa_priv_pass: Optional[bytes] = None) -> None:
    with open(enc_path, 'rb') as fin:
        magic = fin.read(len(MAGIC))
        if magic != MAGIC:
            raise ValueError("Not a valid container")
        version = struct.unpack('B', fin.read(1))[0]
        header_len = struct.unpack('<I', fin.read(4))[0]
        header_json = fin.read(header_len)
        header = json.loads(header_json)
        chunk_count = struct.unpack('<I', fin.read(4))[0]
        chunk_index = []
        for _ in range(chunk_count):
            off = struct.unpack('<Q', fin.read(8))[0]
            ln = struct.unpack('<I', fin.read(4))[0]
            h = fin.read(32)
            chunk_index.append({'offset': off, 'length': ln, 'hash': h.hex()})
        payload_start = fin.tell()

        enc_level = header['enc_level']
        salt = bytes.fromhex(header['salt'])
        nonce_base = bytes.fromhex(header['nonce_base']) if header.get('nonce_base') else None

        if enc_level == 'general' or enc_level == 'aes':
            if not password:
                raise ValueError("Password required")
            sym_key = derive_key(password.encode('utf-8'), salt, length=32)
        elif enc_level == 'rsa':
            if not rsa_priv_pem:
                raise ValueError("Private key required for RSA mode")
            # unwrap first wrapped key (we only stored wrapped symmetric keys)
            wrapped_hex = header['key_wrapped'][0]
            sym_key = _rsa_unwrap(rsa_priv_pem, bytes.fromhex(wrapped_hex), password=rsa_priv_pass)
        else:
            raise ValueError("Unknown encryption level")

        aesgcm = AESGCM(sym_key) if sym_key else None

        with open(out_path, 'wb') as fout:
            for i, e in enumerate(chunk_index):
                fin.seek(payload_start + e['offset'])
                ct = fin.read(e['length'])
                if sha256_bytes(ct).hex() != e['hash']:
                    raise ValueError(f"Chunk hash mismatch @ {i}")
                if enc_level == 'general':
                    pt = xor_stream(ct, sym_key)
                else:
                    nb = bytearray(nonce_base)
                    counter = i.to_bytes(4, 'big')
                    for j in range(4):
                        nb[-1 - j] ^= counter[-1 - j]
                    nonce = bytes(nb)
                    pt = aesgcm.decrypt(nonce, ct, None)
                if header.get('compress'):
                    pt = decompress_bytes(pt, method='zlib')
                fout.write(pt)
