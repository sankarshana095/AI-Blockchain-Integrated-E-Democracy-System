from datetime import datetime
import hashlib
import uuid

def generate_uuid():
    return str(uuid.uuid4())


def current_timestamp():
    return datetime.utcnow()


def hash_string(value: str) -> str:
    """
    Used for:
    - issue blockchain hash
    - vote hash (before sending to blockchain)
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
