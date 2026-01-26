import random
import string


# -----------------------------
# Citizen Random Username
# -----------------------------

USERNAME_PREFIX = "Citizen"


def generate_random_username(length: int = 6) -> str:
    """
    Generate a random anonymous username for citizens.
    Example: Citizen_4F9A2K
    """
    if length < 4:
        raise ValueError("Username length must be at least 4")

    suffix = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )
    return f"{USERNAME_PREFIX}_{suffix}"


def generate_unique_username(existing_usernames: set, max_attempts: int = 5) -> str:
    """
    Generate a unique username not present in existing_usernames.
    existing_usernames: set of usernames already in DB
    """
    for _ in range(max_attempts):
        username = generate_random_username()
        if username not in existing_usernames:
            return username

    raise RuntimeError("Unable to generate unique username after multiple attempts")
