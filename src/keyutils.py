from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import os
from typing import Optional

KEYS_DIR = "keys"
os.makedirs(KEYS_DIR, exist_ok=True)


def generate_keys():
    """Generate RSA key pair and save them as PEM files."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key = private_key.public_key()

    # Save private key
    with open(os.path.join(KEYS_DIR, "private_key.pem"), "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Save public key
    with open(os.path.join(KEYS_DIR, "public_key.pem"), "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    print("✅ RSA key pair generated and saved in 'keys/' folder.")


# --- PATH-BASED LOADERS  ---

def load_private_pem(path: str = "keys/private_key.pem", password: Optional[bytes] = None):
    """Load an RSA private key from a PEM file path."""
    with open(path, "rb") as f:
        key_data = f.read()
    return serialization.load_pem_private_key(
        key_data,
        password=password,
        backend=default_backend()
    )


def load_public_pem(path: str = "keys/public_key.pem"):
    """Load an RSA public key from a PEM file path."""
    with open(path, "rb") as f:
        key_data = f.read()
    return serialization.load_pem_public_key(
        key_data,
        backend=default_backend()
    )

# --- BYTES-BASED LOADERS  ---

def load_private_key_from_bytes(key_bytes: bytes, password: Optional[bytes] = None):
    """Load an RSA private key directly from bytes content."""
    return serialization.load_pem_private_key(
        key_bytes,
        password=password,
        backend=default_backend()
    )

def load_public_key_from_bytes(key_bytes: bytes):
    """Load an RSA public key directly from bytes content."""
    return serialization.load_pem_public_key(
        key_bytes,
        backend=default_backend()
    )