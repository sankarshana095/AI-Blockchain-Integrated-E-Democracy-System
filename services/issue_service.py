from models.issue import (
    create_issue,
    vote_on_issue,
    add_issue_comment,
    mark_issue_resolved,
    confirm_issue_resolution,
    get_issue_by_id
)
from models.audit import create_audit_log
from models.ledger import create_ledger_entry
from utils.helpers import sha256_hash
from models.issue import get_issue_comments as fetch_comments
from models.issue import update_issue_status
from models.issue_timeline import add_issue_status
from models.issue import (
    get_user_issue_vote,
    upsert_issue_vote,
    remove_issue_vote
)
from services.citizen_service import ensure_citizen_alias



# -----------------------------
# Issue Service
# -----------------------------

def raise_issue(
    title: str,
    description: str,
    category: str,
    created_by: str,
    constituency_id: str,
    image_url: str = None
):
    """
    Citizen raises an issue.
    Issue content is hashed and stored in ledger for integrity.
    """
    ensure_citizen_alias(created_by)
    issue_hash = sha256_hash(f"{title}:{description}:{created_by}")

    issue = create_issue(
        title=title,
        description=description,
        category=category,
        created_by=created_by,
        constituency_id=constituency_id,
        image_url=image_url
    )

    issue_id = issue[0]["id"]

    # Ledger entry
    create_ledger_entry(
        entity_type="ISSUE",
        entity_id=issue_id,
        transaction_hash=issue_hash
    )

    # Audit log
    create_audit_log(
        user_id=created_by,
        action="RAISE_ISSUE",
        entity_type="ISSUE",
        entity_id=issue_id
    )

    return issue


def upvote_downvote_issue(issue_id: str, user_id: str, vote_type: str):
    """
    Citizen upvotes or downvotes an issue.
    vote_type = UP | DOWN
    """
    vote_on_issue(issue_id, user_id, vote_type)

    create_audit_log(
        user_id=user_id,
        action=f"{vote_type}_ISSUE",
        entity_type="ISSUE",
        entity_id=issue_id
    )


def comment_on_issue(issue_id: str, user_id: str, comment: str,parent_comment_id: str = None):
    add_issue_comment(issue_id, user_id, comment,parent_comment_id)

    create_audit_log(
        user_id=user_id,
        action="COMMENT_ISSUE",
        entity_type="ISSUE",
        entity_id=issue_id
    )


from models.issue import update_issue_status

def resolve_issue_rep(issue_id: str, resolved_by: str):
    issue = get_issue_by_id(issue_id)
    if not issue:
        raise ValueError("Issue not found")

    # 1. Mark resolution
    mark_issue_resolved(issue_id, resolved_by)

    # 2. Update issue status
    update_issue_status(issue_id, "Resolved")

    # 3. Audit
    create_audit_log(
        user_id=resolved_by,
        action="RESOLVE_ISSUE",
        entity_type="ISSUE",
        entity_id=issue_id
    )



def citizen_confirm_resolution(issue_id: str, user_id: str):
    confirm_issue_resolution(issue_id)

    # Optional but recommended
    update_issue_status(issue_id, "Closed")

    create_audit_log(
        user_id=user_id,
        action="CONFIRM_ISSUE_RESOLUTION",
        entity_type="ISSUE",
        entity_id=issue_id
    )

def build_comment_tree(comments):
    comment_map = {c["id"]: {**c, "replies": []} for c in comments}
    roots = []

    for c in comment_map.values():
        parent_id = c.get("parent_comment_id")
        if parent_id and parent_id in comment_map:
            comment_map[parent_id]["replies"].append(c)
        else:
            roots.append(c)

    return roots

def get_threaded_comments(issue_id: str):
    comments = fetch_comments(issue_id)
    return build_comment_tree(comments)

def accept_issue(issue_id, rep_id, note, estimated_start):
    update_issue_status(issue_id, "Accepted")

    add_issue_status(
        issue_id=issue_id,
        status="Accepted",
        changed_by=rep_id,
        note=note,
        estimated_start_at=estimated_start
    )

def mark_in_progress(issue_id, rep_id, note, estimated_completion):
    update_issue_status(issue_id, "In Progress")

    add_issue_status(
        issue_id=issue_id,
        status="In Progress",
        changed_by=rep_id,
        note=note,
        estimated_completion_at=estimated_completion
    )

def resolve_issue(issue_id, rep_id, note):
    update_issue_status(issue_id, "Resolved")

    add_issue_status(
        issue_id=issue_id,
        status="Resolved",
        changed_by=rep_id,
        note=note
    )


def reject_issue(issue_id, rep_id, note):
    update_issue_status(issue_id, "Rejected")

    add_issue_status(
        issue_id=issue_id,
        status="Rejected",
        changed_by=rep_id,
        note=note
    )

def close_issue(issue_id, citizen_id):
    update_issue_status(issue_id, "Closed")

    add_issue_status(
        issue_id=issue_id,
        status="Closed",
        changed_by=citizen_id,
        note="Citizen confirmed resolution"
    )

def toggle_issue_vote(issue_id: str, user_id: str, vote_type: str):
    """
    vote_type = up | down
    """

    existing = get_user_issue_vote(issue_id, user_id)

    if existing:
        if existing["vote_type"] == vote_type:
            # Same vote clicked again → remove vote
            remove_issue_vote(issue_id, user_id)
            return "REMOVED"
        else:
            # Switch vote
            upsert_issue_vote(issue_id, user_id, vote_type)
            return "SWITCHED"
    else:
        # New vote
        upsert_issue_vote(issue_id, user_id, vote_type)
        return "ADDED"