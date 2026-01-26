from supabase.client import supabase
from config import Config
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timezone


# -----------------------------
# Supabase Authentication
# -----------------------------

def login_with_email_password(email: str, password: str):
    """
    Authenticate user using Supabase Auth.
    Returns session object on success.
    """
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    if not response or not response.session:
        raise ValueError("Invalid email or password")

    return response.session


def logout_user():
    """
    Logout current user
    """
    supabase.auth.sign_out()


# -----------------------------
# Token Validation
# -----------------------------

def decode_access_token(access_token: str):
    """
    Decode Supabase JWT access token.
    Used to extract user metadata securely.
    """
    try:
        payload = jwt.decode(
            access_token,
            options={"verify_signature": False},
            algorithms=["HS256"]
        )
        return payload

    except ExpiredSignatureError:
        raise ValueError("Token has expired")

    except InvalidTokenError:
        raise ValueError("Invalid token")


def is_token_expired(payload: dict) -> bool:
    """
    Check token expiration manually
    """
    exp = payload.get("exp")
    if not exp:
        return True

    expiry_time = datetime.fromtimestamp(exp, tz=timezone.utc)
    return datetime.now(timezone.utc) > expiry_time


# -----------------------------
# User Metadata Extraction
# -----------------------------

def extract_user_identity(session):
    """
    Extract useful user info from Supabase session
    """
    access_token = session.access_token
    payload = decode_access_token(access_token)

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("user_metadata", {}).get("role"),
        "issued_at": payload.get("iat"),
        "expires_at": payload.get("exp")
    }
