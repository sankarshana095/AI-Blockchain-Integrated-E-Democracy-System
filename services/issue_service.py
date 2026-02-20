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
from models.issue import get_issue_by_id
from services.issue_ai_prompt import build_issue_comment_prompt
from services.ai_client import run_comment_reply, AIClientError
from supabase_db.db import insert_record
from utils.helpers import utc_now
import os
from utils.helpers import format_datetime,_time_ago_issue



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

def should_trigger_ai_reply(text: str) -> bool:
    return "@ai" in text.lower()

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


def comment_on_issue(issue_id, user_id, comment, parent_comment_id=None):

    # Save user comment
    result = add_issue_comment(
        issue_id=issue_id,
        user_id=user_id,
        comment=comment,
        parent_comment_id=parent_comment_id
    )
    # 🔥 AI trigger
    if should_trigger_ai_reply(comment):

        issue = get_issue_by_id(issue_id)

        # -------------------------
        # Build parent context
        # -------------------------
        parent_context = ""

        if parent_comment_id:
            from models.issue import get_issue_comments
            all_comments = get_issue_comments(issue_id)

            # collect chain upwards
            comment_map = {c["id"]: c for c in all_comments}
            current = comment_map.get(parent_comment_id)

            chain = []
            while current:
                chain.append(current["comment"])
                pid = current.get("parent_comment_id")
                current = comment_map.get(pid) if pid else None

            parent_context = "\n".join(reversed(chain))

        # -------------------------
        # Build prompt
        # -------------------------
        prompt = build_issue_comment_prompt(
            issue,
            parent_context,
            comment
        )

        try:
            ai_text = run_comment_reply(prompt)

            ai_user_id = os.getenv("AI_SYSTEM_USER_ID")

            insert_record(
                "issue_comments",
                {
                    "issue_id": issue_id,
                    "user_id": ai_user_id,
                    "comment": ai_text,
                    "parent_comment_id": result[0]["id"],
                    "created_at": utc_now().isoformat()
                },
                use_admin=True
            )

        except AIClientError:
            pass

    return result



def citizen_confirm_resolution(issue_id: str, user_id: str):
    confirm_issue_resolution(issue_id)

    # Optional but recommended
    update_issue_status(issue_id, "Closed")
    add_issue_status(
        issue_id=issue_id,
        status="Closed",
        changed_by=user_id,
        note="Citizen confirmed resolution"
    )

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
    for c in comments:                
        c["time_ago"]=_time_ago_issue(c["created_at"])
        c["created_at"]=format_datetime(c["created_at"])
    return build_comment_tree(comments)

def accept_issue(issue_id, rep_id, note, estimated_start):
    update_issue_status(issue_id, "Accepted")

    add_issue_status(
        issue_id=issue_id,
        status="Accepted",
        changed_by=rep_id,
        note=note,
        estimated_start_at=estimated_start,
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

def _resolve_issue(issue_id: str, resolved_by: str,note: str):
    issue = get_issue_by_id(issue_id)
    if not issue:
        raise ValueError("Issue not found")

    # 1. Mark resolution
    mark_issue_resolved(issue_id, resolved_by)

    # 2. Update issue status
    update_issue_status(issue_id, "Resolved")

    add_issue_status(
        issue_id=issue_id,
        status="Resolved",
        changed_by=resolved_by,
        note=note
    )

    # 3. Audit
    create_audit_log(
        user_id=resolved_by,
        action="RESOLVE_ISSUE",
        entity_type="ISSUE",
        entity_id=issue_id
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

def should_trigger_ai_reply(text: str) -> bool:
    return "@ai" in text.lower()
