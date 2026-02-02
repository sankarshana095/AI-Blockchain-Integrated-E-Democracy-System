# services/otp_service.py

import random
from datetime import datetime, timedelta

# In-memory OTP store (perfect for college demo)
OTP_STORE = {}


def generate_otp(user_id):
    otp = str(random.randint(100000, 999999))
    OTP_STORE[user_id] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    }
    return otp


def verify_otp(user_id, otp_input):
    record = OTP_STORE.get(user_id)
    if not record:
        return False

    if datetime.utcnow() > record["expires_at"]:
        OTP_STORE.pop(user_id, None)
        return False

    if record["otp"] != otp_input:
        return False

    OTP_STORE.pop(user_id, None)
    return True
