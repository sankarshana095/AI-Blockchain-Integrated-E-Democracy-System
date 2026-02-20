from supabase_db.db import fetch_one, fetch_all, insert_record, update_record
from utils.helpers import generate_uuid, utc_now
from datetime import date



# -----------------------------
# Table Names
# -----------------------------
REPRESENTATIVES_TABLE = "representatives"
REP_POSTS_TABLE = "rep_posts"
REP_COMMENTS_TABLE = "rep_comments"
REP_SCORES_TABLE = "rep_scores"
REP_DAILY_SCORE_TABLE = "representative_daily_scores"


def create_representative(
    user_id: str,
    constituency_id: str,
    rep_type: str,
    term_start,
    term_end,
    election_id: str,
    candidate_id: str,
    candidate_name: str,
    party_name: str
):
    payload = {
        "id": generate_uuid(),
        "user_id": user_id,
        "constituency_id": constituency_id,
        "type": rep_type,
        "term_start": term_start.isoformat(),
        "term_end": term_end.isoformat(),
        "election_id": election_id,
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "party_name": party_name,
        "created_at": utc_now().isoformat(),
        "status": "ACTIVE"
    }
    initialize_rep_score(user_id)
    return insert_record(REPRESENTATIVES_TABLE, payload, use_admin=True)

# -----------------------------
# Representative Posts
# -----------------------------

def create_rep_post(user_id: str, constituency_id: str, content: str):
    payload = {
        "id": generate_uuid(),
        "user_id": user_id,
        "constituency_id": constituency_id,
        "content": content,
        "created_at": utc_now().isoformat()
    }
    return insert_record(REP_POSTS_TABLE, payload, use_admin=True)


def get_rep_post_by_id(post_id: str):
    return fetch_one(REP_POSTS_TABLE, {"id": post_id})


def get_rep_posts_by_constituency(constituency_id: str):
    return fetch_all(REP_POSTS_TABLE, {"constituency_id": constituency_id})


def get_rep_posts_by_user(user_id: str):
    return fetch_all(REP_POSTS_TABLE, {"user_id": user_id})


# -----------------------------
# Representative Comments (Debate)
# -----------------------------

def add_rep_comment(post_id: str, user_id: str, comment: str):
    payload = {
        "id": generate_uuid(),
        "post_id": post_id,
        "user_id": user_id,
        "comment": comment,
        "created_at": utc_now().isoformat()
    }
    return insert_record(REP_COMMENTS_TABLE, payload, use_admin=True)


def get_rep_comments(post_id: str):
    return fetch_all(REP_COMMENTS_TABLE, {"post_id": post_id})


# -----------------------------
# Representative Scores (Private)
# -----------------------------

def initialize_rep_score(user_id: str):
    payload = {
        "id": generate_uuid(),
        "user_id": user_id,
        "post_score": 0,
        "issue_resolution_score": 0,
        "overall_score": 0,
        "updated_at": utc_now().isoformat()
    }
    return insert_record(REP_SCORES_TABLE, payload, use_admin=True)


def get_rep_score(user_id: str):
    return fetch_one(REP_SCORES_TABLE, {"user_id": user_id})


def update_rep_score(
    user_id: str,
    post_score_delta: int = 0,
    issue_score_delta: int = 0
):
    current = get_rep_score(user_id)

    if not current:
        current = initialize_rep_score(user_id)[0]

    new_post_score = current["post_score"] + post_score_delta
    new_issue_score = current["issue_resolution_score"] + issue_score_delta
    new_overall_score = new_post_score + new_issue_score

    return update_record(
        REP_SCORES_TABLE,
        {"user_id": user_id},
        {
            "post_score": new_post_score,
            "issue_resolution_score": new_issue_score,
            "overall_score": new_overall_score,
            "updated_at": utc_now().isoformat()
        },
        use_admin=True
    )

def get_active_representatives(today: date):
    reps = fetch_all(REPRESENTATIVES_TABLE)

    active = []
    for r in reps:
        if r["term_start"] <= today.isoformat() <= r["term_end"]:
            active.append(r)

    return active


def get_all_representatives():
    return fetch_all(REPRESENTATIVES_TABLE)


def get_rep_by_election_id_constituency_id(election_id: str, constituency_id: str):
    return fetch_all(
        REPRESENTATIVES_TABLE,
        {
            "election_id": election_id,
            "constituency_id": constituency_id
        }
    )

VOTER_MAP_TABLE = "voter_user_map"
VOTERS_TABLE = "voters"


def get_representatives_with_photo(constituency_id: str):
    reps = fetch_all(
        REPRESENTATIVES_TABLE,
        {"constituency_id": constituency_id}
    )

    if not reps:
        return []

    for rep in reps:
        photo_url = None

        # 🔎 Step 1 — find voter id mapped to this user
        voter_map = fetch_one(
            VOTER_MAP_TABLE,
            {"user_id": rep.get("user_id")}
        )

        if voter_map:
            voter = fetch_one(
                VOTERS_TABLE,
                {"id": voter_map.get("voter_id")}
            )

            if voter:
                photo_url = voter.get("photo_url")

        rep["photo_url"] = photo_url

    return reps



def get_representatives_by_constituency(constituency_id: str):
    """
    Get all representatives for a given constituency.
    """
    return fetch_all(
        REPRESENTATIVES_TABLE,
        {"constituency_id": constituency_id}
    )


def get_elected_representative_by_constituency(constituency_id: str):
    """
    Get the ELECTED_REP for a given constituency.
    """
    reps = get_representatives_by_constituency(constituency_id)

    for rep in reps:
        if rep.get("type") == "ELECTED_REP":
            return rep

    return None

def insert_daily_rep_score(
    rep_user_id: str,
    election_id: str,
    constituency_id: str,
    final_score: float,
    rating: str,
    accountability_score: float,
    engagement_score: float,
    integrity_score: float,
    impact_score: float,
    score_date: date
):
    payload = {
        "id": generate_uuid(),
        "rep_user_id": rep_user_id,
        "election_id": election_id,
        "constituency_id": constituency_id,
        "final_score": final_score,
        "rating": rating,
        "accountability_score": accountability_score,
        "engagement_score": engagement_score,
        "integrity_score": integrity_score,
        "impact_score": impact_score,
        "score_date": score_date.isoformat(),
        "created_at": utc_now().isoformat()
    }

    return insert_record(REP_DAILY_SCORE_TABLE, payload, use_admin=True)

def get_daily_rep_score(
    rep_user_id: str,
    election_id: str,
    score_date: date
):
    return fetch_one(
        REP_DAILY_SCORE_TABLE,
        {
            "rep_user_id": rep_user_id,
            "election_id": election_id,
            "score_date": score_date.isoformat()
        }
    )

def get_rep_score_history(
    rep_user_id: str,
    election_id: str
):
    return fetch_all(
        REP_DAILY_SCORE_TABLE,
        {
            "rep_user_id": rep_user_id,
            "election_id": election_id
        }
    )

from datetime import date


def get_current_representative_by_constituency(constituency_id: str):
    reps = get_elected_representative_by_constituency(constituency_id)

    if not reps:
        return None

    # If single dict returned, convert to list
    if isinstance(reps, dict):
        reps = [reps]

    today = date.today()

    for rep in reps:
        start = rep.get("term_start")
        end = rep.get("term_end")

        if not start or not end:
            continue

        if isinstance(start, str):
            start = date.fromisoformat(start)
        if isinstance(end, str):
            end = date.fromisoformat(end)

        if start <= today <= end:
            return rep

    return None

def get_current_representatives_by_constituency(constituency_id: str):
    reps = get_representatives_by_constituency(constituency_id)

    if not reps:
        return None

    # If single dict returned, convert to list
    if isinstance(reps, dict):
        reps = [reps]

    today = date.today()

    for rep in reps:
        start = rep.get("term_start")
        end = rep.get("term_end")

        if not start or not end:
            continue

        if isinstance(start, str):
            start = date.fromisoformat(start)
        if isinstance(end, str):
            end = date.fromisoformat(end)

        if start <= today <= end:
            return rep

    return None

def get_terminated_representatives(today: date):
    reps = fetch_all(REPRESENTATIVES_TABLE)

    terminated = []
    for r in reps:
        if r["status"] == "TERMINATED":
            terminated.append(r)

    return terminated