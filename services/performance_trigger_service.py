from services.representative_score_history import get_last_90_day_average
from models.representative import get_rep_score_history
from services.representative_termination_service import terminate_constituency_terms
from datetime import date, timedelta

THRESHOLD = 35
MIN_DAYS_REQUIRED = 90

def evaluate_performance_and_terminate(rep):
    history = get_rep_score_history(
        rep_user_id=rep["user_id"],
        election_id=rep["election_id"]
    )

    if not history:
        return

    # ✅ ensure at least 90 days since first score
    earliest = min(
        date.fromisoformat(r["score_date"])
        for r in history
        if r.get("score_date")
    )
    days_since_first_score = (date.today() - earliest).days

    if days_since_first_score < MIN_DAYS_REQUIRED:
        return

    # Now compute rolling avg
    avg90 = get_last_90_day_average(
        rep_user_id=rep["user_id"],
        election_id=rep["election_id"]
    )

    if avg90 is None:
        return

    if avg90["final_score"] < THRESHOLD:
        terminate_constituency_terms(rep["constituency_id"])