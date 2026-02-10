from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from utils.decorators import login_required, role_required

from models.voter import get_voter_by_user_id
from models.user import get_user_by_id
from models.election import get_active_elections_by_constituency

from services.booth_session_service import start_voter_session, end_voter_session
from services.otp_service import generate_otp, verify_otp
from services.email_service import send_otp_email




bp = Blueprint("presiding_officer", __name__, url_prefix="/po")


# =====================================================
# PO Dashboard
# =====================================================
@bp.route("/dashboard", methods=["GET", "POST"])
@login_required
@role_required("PO")
def dashboard():
    constituency_id = session.get("constituency_id")

    # Fetch active elections for this constituency
    elections = get_active_elections_by_constituency(constituency_id)

    # PO selects election
    if request.method == "POST":
        election_id = request.form.get("election_id")

        if not election_id:
            flash("Please select an election", "error")
            return redirect(url_for("presiding_officer.dashboard"))

        # Lock election for booth
        session["active_election_id"] = election_id

        # Store election name for display
        selected = next(e for e in elections if e["id"] == election_id)
        session["active_election_name"] = selected["election_name"]

        flash("Election locked for this booth", "success")
        return redirect(url_for("presiding_officer.dashboard"))

    return render_template(
        "election_commission/po/dashboard.html",
        elections=elections
    )



# =====================================================
# Authorize Voter (OTP Based)
# =====================================================
@bp.route("/authorize", methods=["POST"])
@login_required
@role_required("PO")
def authorize_voter():
    voter_user_id = request.form.get("voter_user_id")
    otp_input = request.form.get("otp")
    action = request.form.get("action")

    # -----------------------------
    # Validate voter user
    # -----------------------------
    voter_user = get_user_by_id(voter_user_id)
    if not voter_user:
        flash("Invalid voter user ID", "error")
        return redirect(url_for("presiding_officer.dashboard"))

    # -----------------------------
    # STEP 1: REQUEST OTP
    # -----------------------------
    if action == "request_otp":
        otp = generate_otp(voter_user_id)
        send_otp_email(voter_user["email"], otp)

        flash("OTP sent to voter's registered email ID", "success")
        return redirect(
            url_for("presiding_officer.dashboard", voter=voter_user_id)
        )

    # -----------------------------
    # STEP 2: VERIFY OTP
    # -----------------------------
    if action == "verify_otp":
        if not otp_input:
            flash("Please enter OTP", "error")
            return redirect(
                url_for("presiding_officer.dashboard", voter=voter_user_id)
            )

        if not verify_otp(voter_user_id, otp_input):
            flash("Invalid or expired OTP", "error")
            return redirect(
                url_for("presiding_officer.dashboard", voter=voter_user_id)
            )

        # -----------------------------
        # STEP 3: START VOTER SESSION
        # -----------------------------
        voter = get_voter_by_user_id(voter_user_id)
        if not voter:
            flash("Voter record not found", "error")
            return redirect(url_for("presiding_officer.dashboard"))

        start_voter_session(
            booth_id=session.get("booth_id"),
            voter_id=voter["id"]
        )

        flash("Voter authorized successfully. Voting terminal unlocked.", "success")
        return redirect(url_for("presiding_officer.dashboard"))

    # -----------------------------
    # FALLBACK
    # -----------------------------
    flash("Invalid action", "error")
    return redirect(url_for("presiding_officer.dashboard"))


# =====================================================
# Force End Voter Session
# =====================================================
@bp.route("/end-session", methods=["POST"])
@login_required
@role_required("PO")
def end_session():
    end_voter_session(session.get("booth_id"))
    flash("Voter session force-ended", "success")
    return redirect(url_for("presiding_officer.dashboard"))

@bp.route("/release-terminal", methods=["POST"])
@login_required
@role_required("PO")
def release_terminal():
    from services.booth_session_service import unregister_voting_terminal

    unregister_voting_terminal(session.get("booth_id"))



    flash("Voting terminal released", "success")
    return redirect(url_for("presiding_officer.dashboard"))

