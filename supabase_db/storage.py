import uuid
from typing import Optional
from supabase_db.client import supabase_public, supabase_admin


# -----------------------------
# Storage Operations
# -----------------------------

def upload_file(
    bucket: str,
    file,
    filename: Optional[str] = None,
    use_admin: bool = False
) -> str:
    """
    Upload file to Supabase Storage.

    Returns: Public URL (string)
    """

    client = supabase_admin if use_admin else supabase_public
    # Generate unique filename if not provided
    if not filename:
        filename = f"{uuid.uuid4()}_{file.filename}"

    # Upload file
    client.storage.from_(bucket).upload(
        filename,
        file.read(),
        {"content-type": file.content_type}
    )

    # Return public URL
    return client.storage.from_(bucket).get_public_url(filename)


def delete_file(
    bucket: str,
    filename: str,
    use_admin: bool = False
):
    """
    Delete file from Supabase Storage.
    """

    client = supabase_admin if use_admin else supabase_public

    client.storage.from_(bucket).remove([filename])