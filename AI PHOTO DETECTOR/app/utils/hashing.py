import hashlib

def sha256_hash(data: str) -> str:
    """Returns the SHA-256 hash of the given data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


