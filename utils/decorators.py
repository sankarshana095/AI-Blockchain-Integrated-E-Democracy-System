from functools import wraps
from flask import session, redirect, url_for, abort
from utils.permissions import has_permission


# -----------------------------
# Login Required
# -----------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------
# Role Required
# -----------------------------

def role_required(*allowed_roles):
    """
    Usage:
    @role_required("CEC", "CEO")
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("role")

            if not user_role or user_role not in allowed_roles:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# -----------------------------
# Permission Required
# -----------------------------

def permission_required(permission):
    """
    Usage:
    @permission_required("CAST_VOTE")
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("role")

            if not user_role or not has_permission(user_role, permission):
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
