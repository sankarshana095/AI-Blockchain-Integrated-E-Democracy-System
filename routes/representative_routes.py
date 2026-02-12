from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.decorators import login_required, role_required
from models.representative import get_rep_posts_by_constituency
from services.representative_service import (
    post_update, 
    comment_on_rep_post,
    get_my_posts,
    get_constituency_issues_for_rep,
    get_my_performance_score
)
from services.issue_service import (
    accept_issue,
    mark_in_progress,
    resolve_issue,
    reject_issue
)


bp = Blueprint("representative", __name__, url_prefix="/representative")


# -----------------------------
# Dashboard
# -----------------------------

@bp.route("/dashboard")
@login_required
@role_required("ELECTED_REP", "OPPOSITION_REP")
def dashboard():
    constituency_id = session.get("constituency_id")

    from services.representative_service import get_constituency_issues_for_rep

    issues = get_constituency_issues_for_rep(constituency_id)

    return render_template(
        "representative/dashboard.html",
        issues=issues
    )


# -----------------------------
# Create Post
# -----------------------------

@bp.route("/post/new", methods=["GET", "POST"])
@login_required
@role_required("ELECTED_REP", "OPPOSITION_REP")
def create_post():
    if request.method == "POST":
        try:
            post_update(
                user_id=session.get("user_id"),
                constituency_id=session.get("constituency_id"),
                content=request.form.get("content")
            )
            flash("Post created successfully", "success")
            return redirect(url_for("representative.dashboard"))

        except Exception as e:
            flash(str(e), "error")

    return render_template("representative/create_post.html")


# -----------------------------
# Comment on Post (Debate)
# -----------------------------

@bp.route("/post/<post_id>/comment", methods=["POST"])
@login_required
@role_required("ELECTED_REP", "OPPOSITION_REP")
def comment_post(post_id):
    try:
        comment_on_rep_post(
            post_id=post_id,
            user_id=session.get("user_id"),
            comment=request.form.get("comment")
        )
        flash("Comment added", "success")

    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("representative.dashboard"))


@bp.route("/my-posts")
@login_required
@role_required("ELECTED_REP", "OPPOSITION_REP")
def my_posts():
    posts = get_my_posts(session.get("user_id"))
    return render_template("representative/my_posts.html", posts=posts)


@bp.route("/debate/<post_id>")
@login_required
@role_required("ELECTED_REP", "OPPOSITION_REP")
def debate(post_id):
    from models.representative import get_rep_comments
    comments = get_rep_comments(post_id)
    return render_template("representative/debate.html", post_id=post_id, comments=comments)


@bp.route("/issues")
@login_required
@role_required("ELECTED_REP")
def issue_management():
    issues = get_constituency_issues_for_rep(session.get("constituency_id"))
    return render_template("representative/issue_management.html", issues=issues)


@bp.route("/score")
@login_required
@role_required("ELECTED_REP", "OPPOSITION_REP")
def performance_score():
    score = get_my_performance_score(session.get("user_id"))
    return render_template("representative/performance_score.html", score=score)

@bp.route("/issues/<issue_id>/resolve", methods=["POST"])
@login_required
@role_required("ELECTED_REP")
def resolve_issue(issue_id):
    from services.issue_service import resolve_issue

    resolve_issue(
        issue_id=issue_id,
        resolved_by=session.get("user_id")
    )

    return redirect(url_for("representative.issue_management"))

@bp.route("/issues/<issue_id>/accept", methods=["POST"])
@login_required
@role_required("ELECTED_REP")
def accept(issue_id):
    note = request.form.get("note")
    estimated_start = request.form.get("estimated_start")

    if not note or not estimated_start:
        flash("Note and estimated start time are required.", "error")
        return redirect(url_for("representative.issue_management"))

    accept_issue(
        issue_id=issue_id,
        rep_id=session["user_id"],
        note=note,
        estimated_start=estimated_start
    )

    flash("Issue accepted successfully.", "success")
    return redirect(url_for("representative.issue_management"))

@bp.route("/issues/<issue_id>/progress", methods=["POST"])
@login_required
@role_required("ELECTED_REP")
def progress(issue_id):
    note = request.form.get("note")
    estimated_completion = request.form.get("estimated_completion")

    if not note or not estimated_completion:
        flash("Note and estimated completion time are required.", "error")
        return redirect(url_for("representative.issue_management"))

    mark_in_progress(
        issue_id=issue_id,
        rep_id=session["user_id"],
        note=note,
        estimated_completion=estimated_completion
    )

    flash("Issue marked as in progress.", "success")
    return redirect(url_for("representative.issue_management"))
@bp.route("/issues/<issue_id>/resolve", methods=["POST"])
@login_required
@role_required("ELECTED_REP")
def resolve(issue_id):
    note = request.form.get("note")

    if not note:
        flash("Resolution note is required.", "error")
        return redirect(url_for("representative.issue_management"))

    resolve_issue(
        issue_id=issue_id,
        rep_id=session["user_id"],
        note=note
    )

    flash("Issue marked as resolved.", "success")
    return redirect(url_for("representative.issue_management"))

@bp.route("/issues/<issue_id>/reject", methods=["POST"])
@login_required
@role_required("ELECTED_REP")
def reject(issue_id):
    note = request.form.get("note")

    if not note:
        flash("Rejection reason is required.", "error")
        return redirect(url_for("representative.issue_management"))

    reject_issue(
        issue_id=issue_id,
        rep_id=session["user_id"],
        note=note
    )

    flash("Issue rejected.", "success")
    return redirect(url_for("representative.issue_management"))
