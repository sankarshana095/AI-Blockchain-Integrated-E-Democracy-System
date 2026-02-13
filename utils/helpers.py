import hashlib
import uuid
from datetime import date, datetime, timezone
import pytz



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

def generate_voter_id():
    return f"VTR-{uuid.uuid4().hex[:10].upper()}"


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

def assign_constituencies_to_election(election_id: str, constituency_ids: list[str]):
    for cid in constituency_ids:
        add_constituency_to_election(election_id, cid)

def parse_iso_date(value) -> date:
    """
    Converts ISO date/datetime string to date object.
    Works with:
    - 'YYYY-MM-DD'
    - 'YYYY-MM-DDTHH:MM:SS'
    """
    if isinstance(value, date):
        return value

    # Strip time part if present
    return date.fromisoformat(value[:10])

IST = pytz.timezone("Asia/Kolkata")

def today_ist() -> date:
    return datetime.now(IST).date()

def time_ago(timestamp):
    if not timestamp:
        return ""

    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", ""))

    now = datetime.utcnow()
    diff = now - timestamp

    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    elif seconds < 604800:
        return f"{int(seconds // 86400)}d ago"
    else:
        return timestamp.strftime("%d %b %Y")