import hashlib
import uuid
from datetime import datetime, timezone


# -----------------------------
# Time Helpers
# -----------------------------

def utc_now():
    """Return current UTC timestamp"""
    return datetime.now(timezone.utc)


def format_datetime(dt):
    """Format datetime for UI display"""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# -----------------------------
# ID & Hash Helpers
# -----------------------------

def generate_uuid():
    """Generate UUID4 string"""
    return str(uuid.uuid4())


def sha256_hash(value: str) -> str:
    """Generate SHA256 hash for any string value"""
    if value is None:
        raise ValueError("Value cannot be None for hashing")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_transaction_id(prefix: str = "TX") -> str:
    """
    Generate readable transaction ID
    Example: TX-9f3a7c2e-20260126
    """
    short_id = uuid.uuid4().hex[:8]
    date_part = datetime.utcnow().strftime("%Y%m%d")
    return f"{prefix}-{short_id}-{date_part}"


# -----------------------------
# Validation Helpers
# -----------------------------

def is_valid_email(email: str) -> bool:
    if not email:
        return False
    return "@" in email and "." in email


def is_strong_password(password: str, min_length: int = 8) -> bool:
    if not password or len(password) < min_length:
        return False
    return True


# -----------------------------
# Pagination Helper
# -----------------------------

def paginate(query_result: list, page: int = 1, per_page: int = 10):
    """
    Simple pagination for Supabase responses
    """
    if page < 1:
        page = 1
    start = (page - 1) * per_page
    end = start + per_page
    return query_result[start:end]


# -----------------------------
# Response Helpers
# -----------------------------

def success_response(message: str = "Success", data=None):
    return {
        "status": "success",
        "message": message,
        "data": data
    }


def error_response(message: str = "Error", errors=None):
    return {
        "status": "error",
        "message": message,
        "errors": errors
    }


# -----------------------------
# Role & Access Helpers
# -----------------------------

def normalize_role(role: str) -> str:
    """Normalize role names to uppercase"""
    if not role:
        return None
    return role.strip().upper()


def is_commission_role(role: str) -> bool:
    return normalize_role(role) in {"CEC", "CEO", "DEO", "RO", "ERO", "BLO"}
