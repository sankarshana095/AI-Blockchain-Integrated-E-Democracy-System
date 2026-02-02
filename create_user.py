"""
One-time admin script to create users.

This script:
1. Creates user in Supabase Auth (email + password)
2. Inserts user into public.users table
3. Assigns role and election hierarchy

Run manually:
python scripts/create_user.py
"""

from supabase import create_client
from config import Config
from datetime import datetime


# -----------------------------
# Supabase Admin Client
# -----------------------------

supabase = create_client(
    Config.SUPABASE_URL,
    Config.SUPABASE_SERVICE_ROLE_KEY
)


# -----------------------------
# CONFIGURE USER HERE
# -----------------------------

USER_DATA = {
    "email": "po.1.mangalore_city_north.dakshina_kannada.karnataka@eci.gov.in",
    "password": "admin@123",
    "role": "PO",

    # Hierarchy (set None if not applicable)
    "state_id": 'c44b37b1-ced8-4344-b091-4e60465dbbf3',
    "district_id": '0f6cc110-7e8c-4f1f-9ed1-25621e414765',
    "constituency_id":'c6cefb8a-1c89-4818-b278-80c17ad34bbf',
    "booth_id": '8b8aba7b-4e4e-4c67-b65f-812630ea7c47'
}


# -----------------------------
# CREATE USER
# -----------------------------

def create_user():
    print("Creating user in Supabase Auth...")

    # 1️⃣ Create user in auth.users
    auth_response = supabase.auth.admin.create_user({
        "email": USER_DATA["email"],
        "password": USER_DATA["password"],
        "email_confirm": True
    })

    user = auth_response.user
    if not user:
        raise Exception("Failed to create auth user")

    print(f"Auth user created: {user.id}")

    # 2️⃣ Insert into public.users
    print("Inserting into public.users...")

    db_response = supabase.table("users").insert({
        "id": user.id,                     # IMPORTANT: same UUID
        "email": USER_DATA["email"],
        "role": USER_DATA["role"],
        "state_id": USER_DATA["state_id"],
        "district_id": USER_DATA["district_id"],
        "constituency_id": USER_DATA["constituency_id"],
        "booth_id": USER_DATA["booth_id"],
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    print("User created successfully!")
    print(db_response.data)

def update_user_credentials(user_id, new_email=None, new_password=None):
    payload = {}

    if new_email:
        payload["email"] = new_email
        payload["email_confirm"] = True

    if new_password:
        payload["password"] = new_password

    supabase.auth.admin.update_user_by_id(user_id, payload)

    if new_email:
        supabase.table("users").update({
            "email": new_email
        }).eq("id", user_id).execute()

    print("User updated successfully")



if __name__ == "__main__":
    create_user()
    #update_user_credentials('f7a63834-4fe3-4d92-97c3-7bc881aff227', new_email='ro.mangalore_city_north.dakshina_kannada.karnataka@eci.gov.in', new_password='admin@123')
