from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.decorators import login_required, role_required
from services.election_service import (
    create_state_election,
    approve_state_election
)
from models.election import get_all_elections, get_elections_by_state
from models.voter import (
    get_voters_by_constituency,
    get_voters_by_booth,
    create_voter,
    update_voter_details,
    deactivate_voter
)
from models.user import get_users_by_role
from models.candidate import get_candidates_by_constituency, create_candidate
from datetime import datetime


bp = Blueprint("election_commission", __name__, url_prefix="/commission")

# =====================================================
# MAIN DASHBOARD (ROLE BASED)
# =====================================================

@bp.route("/dashboard")
@login_required
@role_required("CEC", "CEO", "DEO", "RO", "ERO", "BLO")
def dashboard():
    role = session.get("role")

    if role == "CEC":
        elections = get_all_elections()
        return render_template("election_commission/cec/dashboard.html", elections=elections)

    if role == "CEO":
        elections = get_elections_by_state(session.get("state_id"))
        return render_template("election_commission/ceo/dashboard.html", elections=elections)

    if role == "DEO":
        return render_template("election_commission/deo/dashboard.html")

    if role == "RO":
        candidates = get_candidates_by_constituency(session.get("constituency_id"))
        return render_template("election_commission/ro/nomination_management.html", candidates=candidates)

    if role == "ERO":
        voters = get_voters_by_constituency(session.get("constituency_id"))
        return render_template("election_commission/ero/voter_management.html", voters=voters)

    if role == "BLO":
        voters = get_voters_by_booth(session.get("booth_id"))
        return render_template("election_commission/blo/voter_verification.html", voters=voters)

    flash("Unauthorized access", "error")
    return redirect(url_for("auth.login"))

# =====================================================
# CEO – CREATE ELECTION
# =====================================================

@bp.route("/election/new", methods=["GET", "POST"])
@login_required
@role_required("CEO")
def create_election():
    if request.method == "POST":
        try:
            create_state_election(
                election_name=request.form.get("name"),
                election_type=request.form.get("type"),
                state_id=session.get("state_id"),
                start_time=request.form.get("start_time"),
                end_time=request.form.get("end_time"),
                created_by=session.get("user_id")
            )
            flash("Election created successfully", "success")
            return redirect(url_for("election_commission.dashboard"))
        except Exception as e:
            flash(str(e), "error")

    return render_template("election_commission/ceo/create_election.html")

# =====================================================
# CEC – APPROVE ELECTION
# =====================================================

@bp.route("/election/<election_id>/approve")
@login_required
@role_required("CEC")
def approve_election(election_id):
    try:
        approve_state_election(
            election_id=election_id,
            approved_by=session.get("user_id")
        )
        flash("Election approved", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("election_commission.dashboard"))

# =====================================================
# CEC MANAGEMENT
# =====================================================

@bp.route("/cec/manage-ceo")
@login_required
@role_required("CEC")
def manage_ceo():
    ceos = get_users_by_role("CEO")
    return render_template("election_commission/cec/manage_ceo.html", ceos=ceos)

@bp.route("/cec/approve-elections")
@login_required
@role_required("CEC")
def approve_elections_page():
    elections = get_all_elections()
    return render_template("election_commission/cec/approve_elections.html", elections=elections)

# =====================================================
# CEO – MANAGE DEO
# =====================================================

@bp.route("/ceo/manage-deo")
@login_required
@role_required("CEO")
def manage_deo():
    deos = get_users_by_role("DEO")
    return render_template("election_commission/ceo/manage_deo.html", deos=deos)

# =====================================================
# DEO – MANAGE RO
# =====================================================

@bp.route("/deo/manage-ro")
@login_required
@role_required("DEO")
def manage_ro():
    ros = get_users_by_role("RO")
    return render_template("election_commission/deo/manage_ro.html", ros=ros)

# =====================================================
# RO – NOMINATION MANAGEMENT
# =====================================================

@bp.route("/ro/nominations")
@login_required
@role_required("RO")
def nomination_management():
    candidates = get_candidates_by_constituency(session.get("constituency_id"))
    return render_template("election_commission/ro/nomination_management.html", candidates=candidates)

@bp.route("/ro/nominations/add", methods=["POST"])
@login_required
@role_required("RO")
def add_candidate():
    try:
        create_candidate(
            user_id=request.form.get("user_id"),
            election_id=request.form.get("election_id"),
            constituency_id=session.get("constituency_id"),
            party_name=request.form.get("party_name")
        )
        flash("Candidate added (offline nomination verified)", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("election_commission.nomination_management"))

# =====================================================
# ERO – VOTER MANAGEMENT
# =====================================================

@bp.route("/ero/voters/add", methods=["POST"])
@login_required
@role_required("ERO")
def add_voter():
    try:
        create_voter(
            full_name=request.form.get("full_name"),
            guardian_name=request.form.get("guardian_name"),
            gender=request.form.get("gender"),
            date_of_birth=request.form.get("date_of_birth"),
            address=request.form.get("address"),
            state_id=session.get("state_id"),
            district_id=session.get("district_id"),
            constituency_id=session.get("constituency_id"),
            booth_id=request.form.get("booth_id")
        )
        flash("Voter added successfully", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("election_commission.dashboard"))

@bp.route("/ero/voters/update/<voter_id>", methods=["POST"])
@login_required
@role_required("ERO")
def update_voter(voter_id):
    try:
        update_voter_details(voter_id, {
            "full_name": request.form.get("full_name"),
            "address": request.form.get("address"),
            "booth_id": request.form.get("booth_id")
        })
        flash("Voter updated", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("election_commission.dashboard"))

@bp.route("/ero/voters/remove/<voter_id>")
@login_required
@role_required("ERO")
def remove_voter(voter_id):
    try:
        deactivate_voter(voter_id)
        flash("Voter removed", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("election_commission.dashboard"))

# =====================================================
# BLO – VERIFICATION & ROLL PUBLISH
# =====================================================

@bp.route("/blo/voters/verify/<voter_id>", methods=["POST"])
@login_required
@role_required("BLO")
def verify_voter(voter_id):
    try:
        update_voter_details(voter_id, {
            "photo_url": request.form.get("photo_url"),
            "is_verified": True,
            "verified_at": datetime.utcnow().isoformat(),
            "verified_by": session.get("user_id")
        })
        flash("Voter verified successfully", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("election_commission.dashboard"))

@bp.route("/blo/publish-roll")
@login_required
@role_required("BLO")
def publish_electoral_roll():
    return render_template("election_commission/blo/electoral_roll_publish.html")
