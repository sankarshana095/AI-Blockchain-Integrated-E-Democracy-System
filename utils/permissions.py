from config import Config


# -----------------------------
# Role Groups
# -----------------------------

ELECTION_COMMISSION_ROLES = {
    "CEC",
    "CEO",
    "DEO",
    "RO",
    "ERO",
    "BLO"
}

REPRESENTATIVE_ROLES = {
    "ELECTED_REP",
    "OPPOSITION_REP"
}

CITIZEN_ROLES = {
    "CITIZEN"
}


# -----------------------------
# Permission Matrix
# -----------------------------

PERMISSIONS = {
    # -------- Public --------
    "VIEW_LEDGER": {
        "CITIZEN",
        "ELECTED_REP",
        "OPPOSITION_REP",
        *ELECTION_COMMISSION_ROLES
    },

    # -------- Citizen --------
    "CAST_VOTE": {"CITIZEN"},
    "RAISE_ISSUE": {"CITIZEN"},
    "VOTE_ON_ISSUE": {"CITIZEN"},
    "CONFIRM_ISSUE_RESOLUTION": {"CITIZEN"},

    # -------- Representatives --------
    "CREATE_REP_POST": REPRESENTATIVE_ROLES,
    "COMMENT_ON_REP_POST": REPRESENTATIVE_ROLES,
    "MANAGE_ISSUES": {"ELECTED_REP"},
    "VIEW_OWN_SCORE": REPRESENTATIVE_ROLES,

    # -------- Election Commission --------
    "CREATE_ELECTION": {"CEO"},
    "APPROVE_ELECTION": {"CEC"},
    "MANAGE_DEO": {"CEO"},
    "MANAGE_RO": {"DEO"},
    "MANAGE_ERO": {"RO"},
    "MANAGE_BLO": {"ERO"},
    "MANAGE_VOTERS": {"ERO", "BLO"},
    "VERIFY_VOTERS": {"BLO"},
    "PUBLISH_ELECTORAL_ROLL": {"BLO"},

    # -------- Admin --------
    "VIEW_AUDIT_LOGS": {"CEC"}
}


# -----------------------------
# Permission Helpers
# -----------------------------

def has_permission(role: str, permission: str) -> bool:
    """
    Check if a role has a specific permission
    """
    if not role or not permission:
        return False

    role = role.upper()
    allowed_roles = PERMISSIONS.get(permission, set())

    return role in allowed_roles


def get_permissions_for_role(role: str) -> set:
    """
    Get all permissions available for a role
    """
    role = role.upper()
    return {
        permission
        for permission, roles in PERMISSIONS.items()
        if role in roles
    }


def is_valid_role(role: str) -> bool:
    """
    Validate role against defined system roles
    """
    return role in Config.ROLES
