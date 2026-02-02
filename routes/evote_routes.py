# routes/evote_routes.py

from flask import Blueprint, render_template, jsonify, session, request, redirect, flash
from utils.decorators import login_required, role_required
from services.voting_service import submit_vote
from models.candidate import get_candidates_by_constituency
from services.booth_session_service import (
    get_active_voter,
    register_voting_terminal,
    is_valid_voting_terminal,
    unregister_voting_terminal,
    end_voter_session
)
import uuid


bp = Blueprint("evote", __name__, url_prefix="/evote")


# =====================================================
# WAITING SCREEN (Voting PC Idle State)
# =====================================================
@bp.route("/waiting")
@login_required
@role_required("PO")
def waiting():
    booth_id = session.get("booth_id")

    # Assign a unique ID ONCE per browser session
    if "terminal_session_id" not in session:
        session["terminal_session_id"] = str(uuid.uuid4())

    terminal_session_id = session["terminal_session_id"]

    # ✅ CASE 1: This browser is already the registered terminal (reload)
    if is_valid_voting_terminal(booth_id, terminal_session_id):
        return render_template("evote/dashboard.html")

    # ✅ CASE 2: No terminal yet → register this one
    if register_voting_terminal(booth_id, terminal_session_id):
        return render_template("evote/dashboard.html")

    # ❌ CASE 3: Another device owns the terminal
    return render_template("evote/terminal_locked.html")


# =====================================================
# POLLING API – Check if voter is authorized
# =====================================================
@bp.route("/booth-status")
@login_required
@role_required("PO")
def booth_status():
    booth_id = session.get("booth_id")
    terminal_session_id = session.get("terminal_session_id")

    if not is_valid_voting_terminal(booth_id, terminal_session_id):
        return jsonify({"locked": True})

    voter_id = get_active_voter(booth_id)
    return jsonify({"active": bool(voter_id), "locked": False})



# =====================================================
# VOTING SCREEN (Unlocked when voter is active)
# =====================================================
@bp.route("/vote", methods=["GET", "POST"])
@login_required
@role_required("PO")
def vote():
    booth_id = session.get("booth_id")
    voter_id = get_active_voter(booth_id)

    # 🚫 No active voter → lock screen
    if not voter_id:
        return redirect("/evote/waiting")

    # -----------------------------
    # POST → Vote submission
    # -----------------------------
    if request.method == "POST":
        try:
            submit_vote(
                voter_id=voter_id,
                constituency_id=session.get("constituency_id"),
                election_id=request.form.get("election_id"),
                vote_payload=request.form.get("candidate_id")
            )

            # ✅ END VOTER SESSION HERE
            end_voter_session(booth_id)

            flash("Vote recorded successfully", "success")
            return redirect("/evote/waiting")

        except Exception as e:
            flash(str(e), "error")

    # -----------------------------
    # GET → Show voting UI
    # -----------------------------
    candidates = get_candidates_by_constituency(session.get("constituency_id"))
    return render_template("evote/vote.html", candidates=candidates)
