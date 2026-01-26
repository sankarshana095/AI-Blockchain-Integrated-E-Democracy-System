import random
import string

PREFIX = "Citizen"

def generate_random_username(length: int = 6) -> str:
    """
    Example: Citizen_A9F3KQ
    """
    random_part = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )
    return f"{PREFIX}_{random_part}"
