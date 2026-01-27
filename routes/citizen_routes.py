from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.decorators import login_required, role_required
from services.voting_service import submit_vote
from services.issue_service import raise_issue
from models.issue import get_issues_by_constituency
from services.citizen_service import (
    get_constituency_issues,
    get_my_issues,
    get_citizen_profile,
    get_representatives,
    get_representative_posts
)
from models.election import get_active_elections_by_constituency
from models.candidate import get_candidates_by_election_and_constituency
bp = Blueprint("citizen", __name__, url_prefix="/citizen")


# -----------------------------
# Dashboard
# -----------------------------

@bp.route("/dashboard")
@login_required
@role_required("CITIZEN")
def dashboard():
    constituency_id = session.get("constituency_id")
    issues = get_issues_by_constituency(constituency_id)
    return render_template("citizen/dashboard.html", issues=issues)


# -----------------------------
# Vote
# -----------------------------

@bp.route("/vote", methods=["GET", "POST"])
@login_required
@role_required("CITIZEN")
def vote():
    constituency_id = session.get("constituency_id")

    # -----------------------------
    # POST: Submit Vote
    # -----------------------------
    if request.method == "POST":
        try:
            election_id = request.form.get("election_id")
            vote_payload = request.form.get("vote_payload")

            result = submit_vote(
                election_id=election_id,
                constituency_id=constituency_id,
                voter_id=session.get("user_id"),
                vote_payload=vote_payload
            )

            flash("Vote cast successfully!", "success")
            return render_template("citizen/vote_success.html", result=result)

        except Exception as e:
            flash(str(e), "error")

    # -----------------------------
    # GET: Load Elections & Candidates
    # -----------------------------
    elections = get_active_elections_by_constituency(constituency_id)

    selected_election_id = request.args.get("election_id")
    candidates = []

    if selected_election_id:
        candidates = get_candidates_by_election_and_constituency(
            election_id=selected_election_id,
            constituency_id=constituency_id
        )

    return render_template(
        "citizen/vote.html",
        elections=elections,
        candidates=candidates,
        selected_election_id=selected_election_id
    )



# -----------------------------
# Raise Issue
# -----------------------------

@bp.route("/issue/new", methods=["GET", "POST"])
@login_required
@role_required("CITIZEN")
def new_issue():
    if request.method == "POST":
        try:
            raise_issue(
                title=request.form.get("title"),
                description=request.form.get("description"),
                category=request.form.get("category"),
                created_by=session.get("user_id"),
                constituency_id=session.get("constituency_id")
            )
            flash("Issue raised successfully", "success")
            return redirect(url_for("citizen.dashboard"))

        except Exception as e:
            flash(str(e), "error")

    return render_template("citizen/raise_issue.html")


# -----------------------------
# Issues Feed
# -----------------------------

@bp.route("/issues")
@login_required
@role_required("CITIZEN")
def issues_feed():
    issues = get_constituency_issues(session.get("constituency_id"))
    return render_template("citizen/issues_feed.html", issues=issues)


# -----------------------------
# My Issues
# -----------------------------

@bp.route("/my-issues")
@login_required
@role_required("CITIZEN")
def my_issues():
    issues = get_my_issues(session.get("user_id"))
    return render_template("citizen/my_issues.html", issues=issues)


# -----------------------------
# Vote Verification
# -----------------------------

@bp.route("/verify-vote")
@login_required
@role_required("CITIZEN")
def verify_vote():
    return render_template("citizen/verify_vote.html")


# -----------------------------
# Representatives
# -----------------------------

@bp.route("/representatives")
@login_required
@role_required("CITIZEN")
def representatives():
    reps = get_representatives(session.get("constituency_id"))
    return render_template("citizen/representatives.html", representatives=reps)


# -----------------------------
# Representative Posts
# -----------------------------

@bp.route("/representatives/posts")
@login_required
@role_required("CITIZEN")
def representative_posts():
    posts = get_representative_posts(session.get("constituency_id"))
    return render_template("citizen/rep_posts.html", posts=posts)


# -----------------------------
# Citizen Profile
# -----------------------------

@bp.route("/profile")
@login_required
@role_required("CITIZEN")
def profile():
    profile_data = get_citizen_profile(session.get("user_id"))
    return render_template("citizen/profile.html", profile=profile_data)



@bp.route("/issues/<issue_id>/vote", methods=["POST"])
@login_required
@role_required("CITIZEN")
def vote_issue(issue_id):
    vote = request.json.get("vote")

    if vote not in {"up", "down"}:
        return "Invalid vote", 400

    from services.issue_service import upvote_downvote_issue

    upvote_downvote_issue(
        issue_id=issue_id,
        user_id=session.get("user_id"),
        vote_type=vote.upper()
    )

    return "", 204

@bp.route("/issues/<issue_id>/resolve", methods=["POST"])
@login_required
@role_required("CITIZEN")
def confirm_resolution(issue_id):
    from services.issue_service import citizen_confirm_resolution

    citizen_confirm_resolution(
        issue_id=issue_id,
        user_id=session.get("user_id")
    )

    return "", 204

