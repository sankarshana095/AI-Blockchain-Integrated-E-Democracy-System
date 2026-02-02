from datetime import datetime

BOOTH_SESSIONS = {}
ACTIVE_VOTING_TERMINAL = {}  # booth_id -> terminal_session_id


# =====================================================
# Voting Terminal Lock
# =====================================================

def register_voting_terminal(booth_id, session_id):
    """
    Register a voting terminal for a booth.
    Only ONE terminal allowed per booth.
    """
    if booth_id in ACTIVE_VOTING_TERMINAL:
        return False

    ACTIVE_VOTING_TERMINAL[booth_id] = session_id
    return True


def unregister_voting_terminal(booth_id):
    """
    FORCE release terminal lock for a booth.
    Presiding Officer authority.
    """
    ACTIVE_VOTING_TERMINAL.pop(booth_id, None)


def is_valid_voting_terminal(booth_id, session_id):
    """
    Check if this browser session is the active voting terminal.
    """
    return ACTIVE_VOTING_TERMINAL.get(booth_id) == session_id


# =====================================================
# Voter Session Control
# =====================================================

def start_voter_session(booth_id, voter_id):
    BOOTH_SESSIONS[booth_id] = {
        "voter_id": voter_id,
        "status": "ACTIVE",
        "started_at": datetime.utcnow().isoformat()
    }


def end_voter_session(booth_id):
    BOOTH_SESSIONS.pop(booth_id, None)


def get_active_voter(booth_id):
    session = BOOTH_SESSIONS.get(booth_id)
    if session and session["status"] == "ACTIVE":
        return session["voter_id"]
    return None
