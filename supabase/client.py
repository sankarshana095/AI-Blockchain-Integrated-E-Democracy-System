from supabase import create_client, Client
from config import Config


# -----------------------------
# Supabase Clients
# -----------------------------

def get_supabase_client(use_service_role: bool = False) -> Client:
    """
    Returns a Supabase client.

    use_service_role = False
        → Normal user-level operations (RLS applied)

    use_service_role = True
        → Admin/system-level operations (bypasses RLS)
    """

    if use_service_role:
        key = Config.SUPABASE_SERVICE_ROLE_KEY
        if not key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is not configured")
    else:
        key = Config.SUPABASE_ANON_KEY
        if not key:
            raise ValueError("SUPABASE_ANON_KEY is not configured")

    if not Config.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not configured")

    return create_client(Config.SUPABASE_URL, key)


# -----------------------------
# Pre-initialized Clients
# -----------------------------

# Use this for most operations (citizens, reps, etc.)
supabase: Client = get_supabase_client()

# Use this ONLY for trusted backend operations
supabase_admin: Client = get_supabase_client(use_service_role=True)
