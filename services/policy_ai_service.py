from models.rep_policy import (
    get_policy_post_by_id,
    update_representative_statement,
    update_opposition_statement
)
from supabase_db.db import update_record
from utils.helpers import utc_now

REP_POLICY_TABLE = "rep_policy_posts"


def should_run_ai(post):
    return (
        post.get("representative_statement")
        and post.get("opposition_statement")
        and not post.get("ai_summary")
    )


def store_ai_analysis(post_id, summary, fact_check, confidence_score,integrity_score):
    update_record(
        REP_POLICY_TABLE,
        {"id": post_id},
        {
            "ai_summary": summary,
            "ai_fact_check": fact_check,
            "ai_confidence_score": confidence_score,
            "ai_integrity_score": integrity_score,
            "updated_at": utc_now().isoformat()
        },
        use_admin=True
    )
