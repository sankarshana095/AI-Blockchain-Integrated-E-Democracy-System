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
from models.candidate import get_candidates_with_names
from models.voter import (
    get_voters_by_constituency,
    get_voter_by_user_id
)
from services.issue_service import get_threaded_comments
from models.issue_timeline import get_issue_timeline
from models.issue_feedback import get_feedback
from models.issue_feedback import submit_feedback as save_feedback
from services.issue_service import close_issue






bp = Blueprint("citizen", __name__, url_prefix="/citizen")


# -----------------------------
# Dashboard
# -----------------------------

@bp.route("/dashboard")
@login_required
@role_required("CITIZEN")
def dashboard():
    constituency_id = session.get("constituency_id")
    user_id = session.get("user_id")

    all_issues = get_constituency_issues(constituency_id)
    my_issues = get_my_issues(user_id)

    trending_issues = all_issues[:5]
    resolved_issues = [
        i for i in all_issues
        if i["status"] in ("Resolved", "Closed")
    ][:5]


    return render_template(
        "citizen/dashboard.html",
        trending_issues=trending_issues,
        my_issues=my_issues[:5],
        resolved_issues=resolved_issues
    )


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
            voter = get_voter_by_user_id(session.get("user_id"))
            if not voter:
                raise ValueError("Voter record not found")
            voter_id = voter["id"]

            result = submit_vote(
                election_id=election_id,
                constituency_id=constituency_id,
                voter_id=voter_id,
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
        candidates = get_candidates_with_names(
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

    issues = sorted(
        issues,
        key=lambda i: i["created_at"],
        reverse=True
    )

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
        return {"error": "Invalid vote"}, 400

    from services.issue_service import toggle_issue_vote

    toggle_issue_vote(
        issue_id=issue_id,
        user_id=session["user_id"],
        vote_type=vote.lower()
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

@bp.route("/issues/<issue_id>")
@login_required
@role_required("CITIZEN")
def issue_detail(issue_id):
    from models.issue import (
        get_issue_by_id,
        get_issue_comments,
        get_issue_resolution,
        get_issue_score,
        get_user_issue_vote
    )

    issue = get_issue_by_id(issue_id)
    if not issue:
        flash("Issue not found", "error")
        return redirect(url_for("citizen.issues_feed"))

    comments = get_threaded_comments(issue_id)
    resolution = get_issue_resolution(issue_id)
    timeline = get_issue_timeline(issue_id)
    feedback = get_feedback(issue_id)
    issue = get_issue_by_id(issue_id)
    issue["score"] = get_issue_score(issue_id) 
    user_vote = get_user_issue_vote(
        issue_id,
        session["user_id"]
    )
    user_vote = user_vote if user_vote else None
    user_vote = user_vote["vote_type"] if user_vote is not None else 0



    is_issue_owner = issue["created_by"] == session.get("user_id")

    return render_template(
        "citizen/issue_detail.html",
        issue=issue,
        comments=comments,
        resolution=resolution,
        timeline=timeline, 
        feedback=feedback,
        is_issue_owner=is_issue_owner,
        user_vote=user_vote
    )

@bp.route("/issues/<issue_id>/comment", methods=["POST"])
@login_required
@role_required("CITIZEN")
def add_issue_comment(issue_id):
    from services.issue_service import comment_on_issue

    comment = request.form.get("comment")
    parent_id = request.form.get("parent_comment_id")
    print(parent_id)
    comment_on_issue(
        issue_id=issue_id,
        user_id=session.get("user_id"),
        comment=comment,
        parent_comment_id=parent_id
    )

    return redirect(url_for("citizen.issue_detail", issue_id=issue_id))

@bp.route("/issues/<issue_id>/feedback", methods=["POST"])
@login_required
@role_required("CITIZEN")
def submit_issue_feedback(issue_id):

    rating = request.form.get("rating")
    review = request.form.get("review")

    # Save feedback
    save_feedback(
        issue_id=issue_id,
        citizen_id=session["user_id"],
        rating=int(rating),
        review=review
    )

    # Close issue after feedback
    close_issue(issue_id, session["user_id"])

    return redirect(
        url_for("citizen.issue_detail", issue_id=issue_id)
    )

