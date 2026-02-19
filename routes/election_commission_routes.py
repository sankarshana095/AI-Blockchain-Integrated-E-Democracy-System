from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.decorators import login_required, role_required
from services.election_service import (
    create_state_election,
    approve_state_election
)
from models.election import get_all_elections, get_elections_by_state,get_district_name_by_district_id
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
from models.election import add_constituency_to_election,is_roll_locked
from models.constituency import get_constituencies_by_state
from services.election_finalizer import finalize_election_if_needed
from models.election import get_state_name_by_state_id,get_election_by_id, get_elections_by_constituency
from models.booth import get_booths_by_constituency
from supabase_db.client import supabase_admin, supabase_public
import uuid



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
        for election in elections:
            finalize_election_if_needed(election)
        return render_template("election_commission/cec/dashboard.html", elections=elections)

    if role == "CEO":
        elections = get_elections_by_state(session.get("state_id"))
        return render_template("election_commission/ceo/dashboard.html", elections=elections)

    if role == "DEO":
        return render_template("election_commission/deo/dashboard.html")

    if role == "RO":
        candidates = get_candidates_by_constituency(session.get("constituency_id"))
        elections = get_elections_by_constituency(session.get("constituency_id"))
        return render_template("election_commission/ro/nomination_management.html", candidates=candidates,elections=elections)

    if role == "ERO":
        voters = get_voters_by_constituency(session.get("constituency_id"))
        elections = get_elections_by_state(session.get("state_id"))
        booths = get_booths_by_constituency(session.get("constituency_id"))
        return render_template("election_commission/ero/voter_management.html", voters=voters,elections=elections,booths=booths)

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

    # Always runs (GET + POST)
    print("DEBUG state_id:", session.get("state_id"))

    if request.method == "POST":
        try:
            election = create_state_election(
                election_name=request.form.get("name"),
                election_type=request.form.get("type"),
                state_id=session.get("state_id"),
                start_time=request.form.get("start_time"),
                end_time=request.form.get("end_time"),
                nomination_deadline=request.form.get("nomination_deadline"),
                draft_roll_publish_at=request.form.get("draft_roll_publish_at"),
                final_roll_publish_at=request.form.get("final_roll_publish_at"),
                created_by=session.get("user_id")
            )



            election_id = election[0]["id"]

            constituency_ids = request.form.getlist("constituencies")

            for cid in constituency_ids:
                add_constituency_to_election(
                    election_id=election_id,
                    constituency_id=cid
                )

            flash("Election created and constituencies assigned", "success")
            return redirect(url_for("election_commission.dashboard"))

        except Exception as e:
            flash(str(e), "error")

    constituencies = get_constituencies_by_state(session.get("state_id"))

    return render_template(
        "election_commission/ceo/create_election.html",
        constituencies=constituencies
    )



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
    for ceo in ceos:
        ceo["state"]=get_state_name_by_state_id(ceo["state_id"])
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
    for deo in deos:
        district=get_district_name_by_district_id(deo["district_id"])
        deo["district_name"]=district["district_name"]
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
    elections = get_elections_by_state(session.get("state_id"))
    candidates = get_candidates_by_constituency(session.get("constituency_id"))
    return render_template(
        "election_commission/ro/nomination_management.html",
        candidates=candidates,
        elections=elections
    )

@bp.route("/ro/nominations/add", methods=["POST"])
@login_required
@role_required("RO")
def add_candidate():
    try:
        election_id = request.form.get("election_id")

        # Fetch election to check deadline
        election = get_election_by_id(election_id)

        if not election:
            flash("Invalid election", "error")
            return redirect(url_for("election_commission.nomination_management"))

        # Parse deadline
        deadline = election.get("nomination_deadline")

        if deadline:
            deadline_dt = datetime.fromisoformat(str(deadline))

            if datetime.utcnow() > deadline_dt:
                flash("Nomination deadline has passed. No more candidates can be added.", "error")
                return redirect(url_for("election_commission.nomination_management"))

        # Create candidate if deadline not crossed
        create_candidate(
            user_id=request.form.get("user_id"),
            election_id=election_id,
            constituency_id=session.get("constituency_id"),
            party_name=request.form.get("party_name")
        )

        flash("Candidate added successfully", "success")

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
        from models.voter import create_voter, map_voter_to_user
        from models.user import create_user
        from utils.helpers import generate_temp_password
        from supabase_db.client import supabase_admin as supabase   # adjust if your import path differs

        email = request.form.get("email")
        booth_id = request.form.get("booth_id")

        # --------------------------------------------------
        # 1️⃣ Generate temporary password
        # --------------------------------------------------
        temp_password = generate_temp_password()

        # --------------------------------------------------
        # 2️⃣ Create Supabase Auth user
        # --------------------------------------------------
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": temp_password,
            "email_confirm": True
        })

        if not auth_response or not auth_response.user:
            raise Exception("Failed to create authentication account")

        auth_user_id = auth_response.user.id

        # --------------------------------------------------
        # 3️⃣ Insert into USERS table (authorization layer)
        # --------------------------------------------------
        create_user(
            id=auth_user_id,
            email=email,
            role="CITIZEN",
            state_id=session.get("state_id"),
            district_id=session.get("district_id"),
            constituency_id=session.get("constituency_id"),
            booth_id=booth_id
        )

        # --------------------------------------------------
        # 4️⃣ Create VOTER row (electoral data)
        # --------------------------------------------------
        voter = create_voter(
            full_name=request.form.get("full_name"),
            guardian_name=request.form.get("guardian_name"),
            gender=request.form.get("gender"),
            date_of_birth=request.form.get("date_of_birth"),
            address=request.form.get("address"),
            state_id=session.get("state_id"),
            district_id=session.get("district_id"),
            constituency_id=session.get("constituency_id"),
            booth_id=booth_id
        )

        voter_id = voter[0]["id"]

        # --------------------------------------------------
        # 5️⃣ Map voter ↔ user
        # --------------------------------------------------
        map_voter_to_user(voter_id, auth_user_id)

        # --------------------------------------------------
        # 6️⃣ Success message
        # --------------------------------------------------
        flash(
            f"Voter created successfully. Temporary password: {temp_password}",
            "success"
        )

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
            "booth_id": request.form.get("booth_id"),
            "is_active": True,
            "is_verified": False,
            "verified_at": None,
            "verified_by": None
        })

        flash("Voter updated", "success")
    except Exception as e:
        flash(str(e), "error")


    return redirect(url_for("election_commission.dashboard"))

@bp.route("/ero/voters/remove/<voter_id>", methods=["POST"])
@login_required
@role_required("ERO")
def remove_voter(voter_id):
    try:
        deactivate_voter(voter_id)
        update_voter_details(voter_id, {
            "is_verified": False,
            "verified_at": None,
            "verified_by": None
        })

        flash("Voter removed", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("election_commission.dashboard"))

@bp.route("/ero/voters/reset-verification", methods=["POST"])
@login_required
@role_required("ERO")
def reset_verification():
    voters = get_voters_by_constituency(session.get("constituency_id"))

    for v in voters:
        update_voter_details(v["id"], {
            "is_verified": False,
            "verified_at": None,
            "verified_by": None
        })

    flash("All voters marked for re-verification", "success")
    return redirect(url_for("election_commission.dashboard"))

@bp.route("/ero/roll/<election_id>/publish-draft", methods=["POST"])
@login_required
@role_required("ERO")
def publish_draft_roll(election_id):
    from models.election import update_election

    update_election(election_id, {"draft_roll_released": True})
    flash("Draft Electoral Roll released to public", "success")
    return redirect(url_for("election_commission.dashboard"))


@bp.route("/ero/roll/<election_id>/publish-final", methods=["POST"])
@login_required
@role_required("ERO")
def publish_final_roll(election_id):
    from models.election import update_election

    update_election(election_id, {"final_roll_released": True})
    flash("Final Electoral Roll released to public", "success")
    return redirect(url_for("election_commission.dashboard"))

# =====================================================
# BLO – VERIFICATION & ROLL PUBLISH
# =====================================================

@bp.route("/blo/voters/verify/<voter_id>", methods=["POST"])
@login_required
@role_required("BLO")
def verify_voter(voter_id):

    try:
        client = supabase_admin if supabase_admin else supabase_public

        file = request.files.get("photo")

        if not file or file.filename == "":
            flash("Please select a photo", "error")
            return redirect(url_for("election_commission.dashboard"))

        # Keep extension
        ext = file.filename.rsplit(".", 1)[-1]
        filename = f"{voter_id}_{uuid.uuid4()}.{ext}"
        print(filename)
        # Upload
        client.storage.from_("voter-photos").upload(
            filename,
            file.read(),
            {"content-type": file.content_type}
        )

        # ✅ Your SDK returns string
        photo_url = client.storage.from_("voter-photos").get_public_url(filename)
        print(photo_url)
        update_voter_details(voter_id, {
            "photo_url": photo_url,
            "is_verified": True,
            "verified_at": datetime.utcnow().isoformat(),
            "verified_by": session.get("user_id")
        })

        flash("Voter verified successfully", "success")

    except Exception as e:
        flash(f"Upload failed: {e}", "error")

    return redirect(url_for("election_commission.dashboard"))

@bp.route("/blo/publish-roll")
@login_required
@role_required("BLO")
def publish_electoral_roll():
    return render_template("election_commission/blo/electoral_roll_publish.html")

@bp.route("/results/<election_id>")
@login_required
@role_required("CEC", "RO")
def view_results(election_id):
    results = get_election_results(
        election_id,
        session.get("constituency_id")
    )

    return render_template(
        "results/view.html",
        results=results
    )

@bp.route("/public/roll/<election_id>/<constituency_id>")
def view_public_roll(election_id, constituency_id):

    from models.election import get_election_by_id
    from models.voter import get_voters_by_constituency

    election = get_election_by_id(election_id)

    if not election:
        return "Election not found", 404

    if not election.get("draft_roll_released") and not election.get("final_roll_released"):
        return "Electoral roll not published yet", 403

    voters = get_voters_by_constituency(constituency_id)

    return render_template(
        "public/electoral_roll.html",
        election=election,
        voters=voters
    )

@bp.route("/public/roll")
def public_roll_page():

    from models.election import get_all_elections

    elections = get_all_elections()

    return render_template(
        "public/electoral_roll.html",
        elections=elections
    )


@bp.route("/api/public-roll/<election_id>/<constituency_id>")
def api_public_roll(election_id, constituency_id):

    from models.election import get_election_by_id
    from models.voter import get_voters_by_constituency

    election = get_election_by_id(election_id)

    if not election:
        return {"error": "Election not found"}

    if not election.get("draft_roll_released") and not election.get("final_roll_released"):
        return {"error": "Electoral roll not released yet"}

    voters = get_voters_by_constituency(constituency_id)

    return {
        "election_name": election["election_name"],
        "is_final": election.get("final_roll_released"),
        "voters": voters
    }

@bp.route("/api/constituencies/<election_id>")
def api_constituencies_for_election(election_id):

    from models.election import get_election_by_id
    from models.constituency import get_constituencies_by_state

    election = get_election_by_id(election_id)

    if not election:
        return {"error": "Invalid election"}, 404

    constituencies = get_constituencies_by_state(election["state_id"])

    return constituencies
