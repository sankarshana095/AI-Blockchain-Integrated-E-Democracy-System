# routes/evote_routes.py

from flask import Blueprint, render_template, jsonify, session, request, redirect, flash,url_for
from utils.decorators import login_required, role_required
from services.voting_service import submit_vote
from models.candidate import  get_candidates_by_election_and_constituency
from services.booth_session_service import (
    get_active_voter,
    register_voting_terminal,
    is_valid_voting_terminal,
    unregister_voting_terminal,
    end_voter_session
)
import uuid
from datetime import datetime
from models.election import get_election_by_id

bp = Blueprint("evote", __name__, url_prefix="/evote")


# =====================================================
# WAITING SCREEN (Voting PC Idle State)
# =====================================================
@bp.route("/waiting")
@login_required
@role_required("PO")
def waiting():
    booth_id = session.get("booth_id")
    election_id = session.get("active_election_id")
    if not election_id:
        flash("No election set for this booth", "error")
        return redirect(url_for("presiding_officer.dashboard"))
    if election_id:
        election = get_election_by_id(election_id)
        now = datetime.utcnow().isoformat()

        if now > election["end_time"]:
        # Election over → deactivate
            session.pop("active_election_id", None)
            session.pop("active_election_name", None)

            flash("Election has ended", "error")
            return redirect(url_for("presiding_officer.dashboard"))

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
    election_id = session.get("active_election_id")
    constituency_id = session.get("constituency_id")
    if not election_id:
        flash("No election set for this booth", "error")
        return redirect(url_for("presiding_officer.dashboard"))

    if election_id:
        election = get_election_by_id(election_id)
        now = datetime.utcnow().isoformat()

        if now > election["end_time"]:
        # Election over → deactivate
            session.pop("active_election_id", None)
            session.pop("active_election_name", None)

            flash("Election has ended", "error")
            return redirect(url_for("presiding_officer.dashboard"))

    # 🚫 No active voter → lock screen
    if not voter_id:
        return redirect("/evote/waiting")

    # -----------------------------
    # POST → Vote submission
    # -----------------------------
    if request.method == "POST":
        try:
            result = submit_vote(
                voter_id=voter_id,
                constituency_id=session.get("constituency_id"),
                election_id=session.get("active_election_id"),
                vote_payload=request.form.get("candidate_id")
            )

            # End voter session AFTER vote
            end_voter_session(booth_id)

            # ✅ Show success page instead of redirect
            return render_template(
                "evote/vote_success.html",
                result=result
            )


        except Exception as e:
            flash(str(e), "error")

    # -----------------------------
    # GET → Show voting UI
    # -----------------------------
    candidates = get_candidates_by_election_and_constituency(
        election_id=election_id,
        constituency_id=constituency_id
    )
    return render_template("evote/vote.html", candidates=candidates)
