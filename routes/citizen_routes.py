from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.decorators import login_required, role_required
from services.voting_service import submit_vote
from services.issue_service import raise_issue
from models.issue import get_issues_by_constituency,get_issue_resolution
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
from services.issue_service import citizen_confirm_resolution
from services.citizen_service import ensure_citizen_alias
from models.user import get_user_by_id
from models.user import get_display_name_by_user_id
from models.comment_vote import get_comment_score, get_user_comment_vote
from models.user import get_user_by_id, get_display_name_by_user_id
import cloudinary.uploader
from models.issue_image import add_issue_image
from services.score_service import reward_successful_issue_resolution
from models.issue import get_issue_resolution
import os
from utils.helpers import format_datetime,_time_ago_issue
from services.rep_policy_service import get_policy_feed
from models.representative import get_representatives_with_photo
from services.constituency_ai_service import generate_constituency_brief
from models.constituency_brief import get_brief
from datetime import datetime, timezone
from utils.helpers import utc_now




bp = Blueprint("citizen", __name__, url_prefix="/citizen")


# -----------------------------
# Dashboard
# -----------------------------

@bp.route("/dashboard")
@login_required
@role_required("CITIZEN","OPPOSITION_REP")
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

    policy_posts = get_policy_feed(constituency_id)[:5]

    # 🧠 Live AI constituency brief
    brief_row = get_brief(constituency_id)
    live_summary = brief_row["summary_text"] if brief_row else "No civic summary available."

    last_updated = brief_row["generated_at"] if brief_row else None
    minutes_ago = None
    if last_updated:
        if isinstance(last_updated, str):
            last_updated = datetime.fromisoformat(last_updated)
        last_updated = brief_row["generated_at"] if brief_row else None
        minutes_ago = None

        if last_updated:

            # 🔧 Convert string → datetime
            if isinstance(last_updated, str):
                try:
                    last_updated = datetime.fromisoformat(last_updated)
                except Exception:
                    last_updated = None

            if last_updated:

                # 🔧 Force timezone awareness
                if last_updated.tzinfo is None:
                    last_updated = last_updated.replace(tzinfo=timezone.utc)

                now = utc_now()

                if now.tzinfo is None:
                    now = now.replace(tzinfo=timezone.utc)

                minutes_ago = int((now - last_updated).total_seconds() // 60)

    return render_template(
        "citizen/dashboard.html",
        trending_issues=trending_issues,
        my_issues=my_issues[:5],
        resolved_issues=resolved_issues,
        policy_posts=policy_posts,
        live_summary=live_summary, 
        last_updated=last_updated,
        last_updated_minutes=minutes_ago
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
@role_required("CITIZEN","OPPOSITION_REP")
def new_issue():
    if request.method == "POST":
        try:
            files = request.files.getlist("images")
            image_urls = []

            for file in files:
                if file and file.filename:
                    if not file.mimetype.startswith("image/"):
                        continue

                    upload_result = cloudinary.uploader.upload(
                        file,
                        folder="issues",
                        resource_type="image",
                        transformation=[
                            {"width": 1200, "height": 1200, "crop": "limit"},
                            {"quality": "auto"},
                            {"fetch_format": "auto"}
                        ]
                    )
                    image_urls.append(upload_result["secure_url"])
            issue = raise_issue(
                title=request.form.get("title"),
                description=request.form.get("description"),
                category=request.form.get("category"),
                created_by=session["user_id"],
                constituency_id=session["constituency_id"],
            )

            issue_id = issue[0]["id"]

            # 🔗 Save images
            for url in image_urls:
                add_issue_image(issue_id, url)

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
@role_required("CITIZEN","OPPOSITION_REP")
def issues_feed():
    from models.issue import (
        get_issue_score,
        get_user_issue_vote,
        get_issue_comments,
        get_comment_author_alias
    )
    from models.issue_image import get_issue_images
    from utils.helpers import time_ago

    constituency_id = session.get("constituency_id")
    raw_issues = get_constituency_issues(constituency_id)

    enriched = []

    for issue in raw_issues:
        issue_id = issue["id"]

        # 👤 Username
        issue["username"] = get_comment_author_alias(issue["created_by"])

        # ⭐ Score
        issue["score"] = get_issue_score(issue_id)

        # 🗳 User Vote
        user_vote = get_user_issue_vote(issue_id, session["user_id"])
        issue["user_vote"] = user_vote["vote_type"] if user_vote else None

        # 💬 Comment count (including replies)
        comments = get_issue_comments(issue_id)
        issue["comment_count"] = len(comments)  # replies are already in DB as rows

        # 🖼 First image
        images = get_issue_images(issue_id)
        issue["first_image"] = images[0]["image_url"] if images else None

        # ⏳ Time ago
        issue["time_ago"] = time_ago(issue["created_at"])

        enriched.append(issue)

    return render_template(
        "citizen/issues_feed.html",
        issues=enriched
    )




# -----------------------------
# My Issues
# -----------------------------

@bp.route("/my-issues")
@login_required
@role_required("CITIZEN","OPPOSITION_REP")
def my_issues():
    from models.issue import (
        get_issue_score,
        get_user_issue_vote,
        get_issue_comments
    )
    from models.issue_image import get_issue_images
    from utils.helpers import time_ago

    user_id = session.get("user_id")
    raw_issues = get_my_issues(user_id)

    # Sort newest first
    raw_issues = sorted(
        raw_issues,
        key=lambda i: i["created_at"],
        reverse=True
    )

    enriched = []

    for issue in raw_issues:
        issue_id = issue["id"]

        # 👤 You are the creator
        issue["username"] = "You"

        # ⭐ Score
        issue["score"] = get_issue_score(issue_id)

        # 🗳 User vote
        user_vote = get_user_issue_vote(issue_id, user_id)
        issue["user_vote"] = user_vote["vote_type"] if user_vote else None

        # 💬 Comment count
        comments = get_issue_comments(issue_id)
        issue["comment_count"] = len(comments)

        # 🖼 First image
        images = get_issue_images(issue_id)
        issue["first_image"] = images[0]["image_url"] if images else None

        # ⏳ Time ago
        issue["time_ago"] = time_ago(issue["created_at"])

        enriched.append(issue)

    return render_template(
        "citizen/my_issues.html",
        issues=enriched
    )



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
@role_required("CITIZEN","OPPOSITION_REP")
def representatives():
    reps = get_representatives_with_photo(session.get("constituency_id"))
    for r in reps:
        if r.get("term_start"):
            r["term_start"] = format_datetime(r["term_start"])
        if r.get("term_end"):
            r["term_end"] = format_datetime(r["term_end"])
    reps = sorted(
        reps,
        key=lambda r: 0 if r.get("type") == "ELECTED_REP" else 1
    )
    return render_template("citizen/representatives.html", representatives=reps)


# -----------------------------
# Representative Posts
# -----------------------------

@bp.route("/representatives/posts")
@login_required
@role_required("CITIZEN","OPPOSITION_REP")
def representative_posts():
    posts = get_representative_posts(session.get("constituency_id"))
    return render_template("citizen/rep_posts.html", posts=posts)


# -----------------------------
# Citizen Profile
# -----------------------------

@bp.route("/profile")
@login_required
@role_required("CITIZEN","OPPOSITION_REP")
def profile():
    profile_data = get_citizen_profile(session.get("user_id"))
    return render_template("citizen/profile.html", profile=profile_data)



@bp.route("/issues/<issue_id>/vote", methods=["POST"])
@login_required
@role_required("CITIZEN","ELECTED_REP", "OPPOSITION_REP")
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
@role_required("CITIZEN","OPPOSITION_REP")
def confirm_resolution(issue_id):
    from services.issue_service import citizen_confirm_resolution

    citizen_confirm_resolution(
        issue_id=issue_id,
        user_id=session.get("user_id")
    )
    issue = get_issue_resolution(issue_id)
    reward_successful_issue_resolution(
        rep_user_id=issue["resolved_by"],  # or resolved_by
        issue_id=issue_id
    )
    return "", 204

@bp.route("/issues/<issue_id>")
@login_required
@role_required("CITIZEN","ELECTED_REP", "OPPOSITION_REP")
def issue_detail(issue_id):
    from models.issue import (
        get_issue_by_id,
        get_issue_comments,
        get_issue_resolution,
        get_issue_score,
        get_user_issue_vote,
        get_comment_author_alias
    )
    from models.issue_image import get_issue_images

    images = get_issue_images(issue_id)

    issue = get_issue_by_id(issue_id)
    if not issue:
        flash("Issue not found", "error")
        return redirect(url_for("citizen.issues_feed"))

    comments = get_threaded_comments(issue_id)
    resolution = get_issue_resolution(issue_id)
    timeline = get_issue_timeline(issue_id)
    feedback = get_feedback(issue_id)
    issue = get_issue_by_id(issue_id)
    issue["username"] = get_comment_author_alias(issue["created_by"])
    issue["score"] = get_issue_score(issue_id) 
    issue["created_at"]=format_datetime(issue["created_at"])
    for t in timeline:
        t["created_at"] = format_datetime(t["created_at"])
        t["estimated_start_at"]=format_datetime(t["estimated_start_at"])
        t["estimated_completion_at"]=format_datetime(t["estimated_completion_at"])
    user_vote = get_user_issue_vote(
        issue_id,
        session["user_id"]
    )
    user_vote = user_vote if user_vote else None
    user_vote = user_vote["vote_type"] if user_vote is not None else 0
    is_issue_owner = issue["created_by"] == session.get("user_id")
    def attach_usernames_to_comments(comments, issue_owner_id):
        for c in comments:
            c["display_name"] = get_display_name_by_user_id(c["user_id"])
            c["is_op"] = c["user_id"] == issue_owner_id  # ⭐ OP FLAG
            user = get_user_by_id(c["user_id"])
            role = user["role"] if user else "CITIZEN"
            c["role"] = role
            c["is_official"] = role in ["ELECTED_REP", "OPPOSITION_REP"] 

            c["score"] = get_comment_score(c["id"])

            user_vote = get_user_comment_vote(c["id"], session["user_id"])
            c["user_vote"] = user_vote["vote_type"] if user_vote else None
            # 🔁 recurse into replies
            if c.get("replies"):
                attach_usernames_to_comments(c["replies"], issue_owner_id)
    attach_usernames_to_comments(comments,issue["created_by"])
    return render_template(
    "citizen/issue_detail.html",
    issue=issue,
    comments=comments,
    resolution=resolution,
    timeline=timeline,
    feedback=feedback,
    is_issue_owner=is_issue_owner,
    user_vote=user_vote,
    images=images,
    AI_SYSTEM_USER_ID=os.getenv("AI_SYSTEM_USER_ID")
)


@bp.route("/issues/<issue_id>/comment", methods=["POST"])
@login_required
@role_required("CITIZEN", "ELECTED_REP", "OPPOSITION_REP")
def add_issue_comment(issue_id):
    from services.issue_service import comment_on_issue
    ensure_citizen_alias(session["user_id"])
    comment = request.form.get("comment")
    parent_id = request.form.get("parent_comment_id")
    comment_on_issue(
        issue_id=issue_id,
        user_id=session.get("user_id"),
        comment=comment,
        parent_comment_id=parent_id
    )

    return redirect(url_for("citizen.issue_detail", issue_id=issue_id))

@bp.route("/issues/<issue_id>/feedback", methods=["POST"])
@login_required
@role_required("CITIZEN","OPPOSITION_REP")
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
    citizen_confirm_resolution(issue_id, session["user_id"])


    return redirect(
        url_for("citizen.issue_detail", issue_id=issue_id)
    )

@bp.route("/comments/<comment_id>/vote", methods=["POST"])
@login_required
def vote_comment(comment_id):
    data = request.get_json()
    vote = data.get("vote")

    if vote not in {"up", "down"}:
        return {"error": "Invalid vote"}, 400

    from services.comment_vote_service import toggle_comment_vote

    toggle_comment_vote(
        comment_id=comment_id,
        user_id=session["user_id"],
        vote_type=vote
    )

    return "", 204
