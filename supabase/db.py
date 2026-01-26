from supabase.client import supabase, supabase_admin


# -----------------------------
# Read Operations
# -----------------------------

def fetch_one(table: str, filters: dict, use_admin: bool = False):
    """
    Fetch a single record from a table based on filters.
    """
    client = supabase_admin if use_admin else supabase

    query = client.table(table).select("*")
    for key, value in filters.items():
        query = query.eq(key, value)

    response = query.limit(1).execute()
    data = response.data

    return data[0] if data else None


def fetch_all(table: str, filters: dict = None, use_admin: bool = False):
    """
    Fetch all records from a table with optional filters.
    """
    client = supabase_admin if use_admin else supabase

    query = client.table(table).select("*")

    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)

    response = query.execute()
    return response.data


# -----------------------------
# Write Operations
# -----------------------------

def insert_record(table: str, payload: dict, use_admin: bool = False):
    """
    Insert a new record into a table.
    """
    client = supabase_admin if use_admin else supabase

    response = client.table(table).insert(payload).execute()
    return response.data


def update_record(table: str, filters: dict, payload: dict, use_admin: bool = False):
    """
    Update record(s) in a table based on filters.
    """
    client = supabase_admin if use_admin else supabase

    query = client.table(table).update(payload)
    for key, value in filters.items():
        query = query.eq(key, value)

    response = query.execute()
    return response.data


def delete_record(table: str, filters: dict, use_admin: bool = False):
    """
    Delete record(s) from a table based on filters.
    """
    client = supabase_admin if use_admin else supabase

    query = client.table(table).delete()
    for key, value in filters.items():
        query = query.eq(key, value)

    response = query.execute()
    return response.data
