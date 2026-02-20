from datetime import date
from services.representative_scoring import calculate_representative_score
from models.representative import (
    insert_daily_rep_score,
    get_daily_rep_score
)

def store_today_rep_score(rep_user_id: str, election_id: str, constituency_id: str):
    today = date.today()

    # Prevent duplicate entry
    existing = get_daily_rep_score(rep_user_id, election_id, today)
    if existing:
        return "Already stored"

    score = calculate_representative_score(rep_user_id, constituency_id)

    insert_daily_rep_score(
        rep_user_id=rep_user_id,
        election_id=election_id,
        constituency_id=constituency_id,
        final_score=score["final_score"],
        rating=score["rating"],
        accountability_score=score["breakdown"]["accountability"]["total"],
        engagement_score=score["breakdown"]["engagement"]["total"],
        integrity_score=score["breakdown"]["integrity"]["total"],
        impact_score=score["breakdown"]["impact"]["total"],
        score_date=today
    )

    return "Stored"