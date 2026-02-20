from supabase_db.db import fetch_one, fetch_all, insert_record, update_record
from utils.helpers import generate_uuid, utc_now


# -----------------------------
# Table Names
# -----------------------------

ISSUES_TABLE = "issues"
ISSUE_VOTES_TABLE = "issue_votes"
ISSUE_COMMENTS_TABLE = "issue_comments"
ISSUE_RESOLUTION_TABLE = "issue_resolution"


# -----------------------------
# Issues
# -----------------------------

def create_issue(
    title: str,
    description: str,
    category: str,
    created_by: str,
    constituency_id: str,
    image_url: str = None
):
    payload = {
        "id": generate_uuid(),
        "title": title,
        "description": description,
        "category": category,
        "created_by": created_by,
        "constituency_id": constituency_id,
        "status": "Open",
        "image_url": image_url,
        "created_at": utc_now().isoformat()
    }
    return insert_record(ISSUES_TABLE, payload, use_admin=True)


def get_issue_by_id(issue_id: str):
    return fetch_one(ISSUES_TABLE, {"id": issue_id})


def get_issues_by_constituency(constituency_id: str):
    return fetch_all(ISSUES_TABLE, {"constituency_id": constituency_id})


def update_issue_status(issue_id: str, status: str):
    return update_record(
        ISSUES_TABLE,
        {"id": issue_id},
        {"status": status},
        use_admin=True
    )


# -----------------------------
# Issue Votes (Upvote / Downvote)
# -----------------------------

def vote_on_issue(issue_id: str, user_id: str, vote_type: str):
    existing = fetch_one(
        ISSUE_VOTES_TABLE,
        {"issue_id": issue_id, "user_id": user_id}
    )

    if existing:
        if existing["vote_type"] == vote_type:
            return {"status": "ignored"}
        else:
            # update vote
            update_record(
                ISSUE_VOTES_TABLE,
                {"id": existing["id"]},
                {"vote_type": vote_type},
                use_admin=True
            )
            return {"status": "updated"}

    payload = {
        "id": generate_uuid(),
        "issue_id": issue_id,
        "user_id": user_id,
        "vote_type": vote_type,
        "created_at": utc_now().isoformat()
    }
    return insert_record(ISSUE_VOTES_TABLE, payload, use_admin=True)



def get_issue_votes(issue_id: str):
    return fetch_all(ISSUE_VOTES_TABLE, {"issue_id": issue_id})


# -----------------------------
# Issue Comments
# -----------------------------

def add_issue_comment(
    issue_id: str,
    user_id: str,
    comment: str,
    parent_comment_id: str = None
):
    payload = {
        "id": generate_uuid(),
        "issue_id": issue_id,
        "user_id": user_id,
        "comment": comment,
        "parent_comment_id": parent_comment_id,
        "created_at": utc_now().isoformat()
    }
    return insert_record(ISSUE_COMMENTS_TABLE, payload, use_admin=True)


def get_issue_comments(issue_id: str):
    return fetch_all(
        ISSUE_COMMENTS_TABLE,
        {"issue_id": issue_id}
    )

# -----------------------------
# Issue Resolution
# -----------------------------

def mark_issue_resolved(issue_id: str, resolved_by: str):
    payload = {
        "id": generate_uuid(),
        "issue_id": issue_id,
        "resolved_by": resolved_by,
        "citizen_confirmed": False,
        "confirmed_at": None
    }
    return insert_record(ISSUE_RESOLUTION_TABLE, payload, use_admin=True)


def confirm_issue_resolution(issue_id: str):
    return update_record(
        ISSUE_RESOLUTION_TABLE,
        {"issue_id": issue_id},
        {
            "citizen_confirmed": True,
            "confirmed_at": utc_now().isoformat()
        },
        use_admin=True
    )


def get_issue_resolution(issue_id: str):
    return fetch_one(ISSUE_RESOLUTION_TABLE, {"issue_id": issue_id})

def get_issues_by_user(user_id: str):
    return fetch_all(ISSUES_TABLE, {"created_by": user_id})


def get_issue_score(issue_id: str):
    votes = fetch_all(ISSUE_VOTES_TABLE, {"issue_id": issue_id})

    score = 0
    for v in votes:
        if v["vote_type"] == "up":
            score += 1
        elif v["vote_type"] == "down":
            score -= 1

    return score

def get_user_issue_vote(issue_id: str, user_id: str):
    return fetch_one(
        ISSUE_VOTES_TABLE,
        {"issue_id": issue_id, "user_id": user_id}
    )

def remove_issue_vote(issue_id: str, user_id: str):
    from supabase_db.db import delete_record
    return delete_record(
        ISSUE_VOTES_TABLE,
        {"issue_id": issue_id, "user_id": user_id},
        use_admin=True
    )
    
def upsert_issue_vote(issue_id: str, user_id: str, vote_type: str):
    existing = get_user_issue_vote(issue_id, user_id)

    if existing:
        # Update vote
        return update_record(
            ISSUE_VOTES_TABLE,
            {"id": existing["id"]},
            {"vote_type": vote_type},
            use_admin=True
        )
    else:
        # Insert new vote
        payload = {
            "id": generate_uuid(),
            "issue_id": issue_id,
            "user_id": user_id,
            "vote_type": vote_type,
            "created_at": utc_now().isoformat()
        }
        return insert_record(ISSUE_VOTES_TABLE, payload, use_admin=True)

def get_comment_author_alias(user_id: str):
    from models.user import get_citizen_alias
    alias = get_citizen_alias(user_id)
    return alias["random_username"] if alias else "Anonymous"


def get_issues_for_elected_rep_term(constituency_id: str):
    """
    Get issues created during the elected representative's term
    along with the rep's user_id.
    """

    from models.representative import get_representatives_by_constituency
    from datetime import datetime

    reps = get_representatives_by_constituency(constituency_id)

    elected_rep = next(
        (r for r in reps if r.get("type") == "ELECTED_REP"),
        None
    )

    if not elected_rep:
        return []

    rep_user_id = elected_rep.get("user_id")

    term_start = elected_rep.get("term_start")
    term_end = elected_rep.get("term_end")

    if not term_start:
        return []

    term_start_date = datetime.fromisoformat(str(term_start))
    term_end_date = (
        datetime.fromisoformat(str(term_end))
        if term_end
        else None
    )

    issues = fetch_all(ISSUES_TABLE, {"constituency_id": constituency_id})

    filtered_issues = []

    for issue in issues:
        created_at = issue.get("created_at")
        if not created_at:
            continue

        created_date = datetime.fromisoformat(
            created_at.replace("Z", "+00:00")
        )

        if created_date >= term_start_date:
            if term_end_date:
                if created_date <= term_end_date:
                    issue_copy = issue.copy()
                    issue_copy["rep_user_id"] = rep_user_id
                    filtered_issues.append(issue_copy)
            else:
                issue_copy = issue.copy()
                issue_copy["rep_user_id"] = rep_user_id
                filtered_issues.append(issue_copy)

    return filtered_issues


def get_issues_with_acceptance_time(constituency_id: str):
    """
    Returns issues during elected rep term
    along with:
      - rep_user_id
      - accepted_at (timestamp when status first changed to 'Accepted')
    """

    from models.issue_timeline import get_issue_timeline
    from datetime import datetime

    issues = get_issues_for_elected_rep_term(constituency_id)

    enriched_issues = []

    for issue in issues:
        issue_id = issue.get("id")
        timeline = get_issue_timeline(issue_id)

        accepted_at = None

        if timeline:
            # Find first Accepted entry
            accepted_entries = [
                t for t in timeline
                if t.get("status") == "Accepted"
            ]

            if accepted_entries:
                # Get earliest Accepted timestamp
                accepted_entries.sort(
                    key=lambda x: x.get("created_at")
                )
                accepted_at = accepted_entries[0].get("created_at")

        issue_copy = issue.copy()
        issue_copy["accepted_at"] = accepted_at

        enriched_issues.append(issue_copy)

    return enriched_issues


def get_issue_comments_by_constituency(constituency_id):
    from flask import session
    from utils.helpers import format_datetime, _time_ago
    # -----------------------------------
    # Get all issues in this constituency
    # -----------------------------------
    issues = fetch_all("issues", {"constituency_id": constituency_id}) or []
    issue_ids = [i["id"] for i in issues]

    if not issue_ids:
        return []

    # -----------------------------------
    # Get all comments for those issues
    # -----------------------------------
    comments = []
    for issue_id in issue_ids:
        issue_comments = fetch_all("issue_comments", {"issue_id": issue_id}) or []
        comments.extend(issue_comments)
    return comments