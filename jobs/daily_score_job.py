from models.representative import get_current_representative_by_constituency
from services.rep_daily_score_service import store_today_rep_score
from services.performance_trigger_service import evaluate_performance_and_terminate

def run_daily_score_job(constituency_id: str):
    rep = get_current_representative_by_constituency(constituency_id)

    if not rep:
        return

    store_today_rep_score(
        rep_user_id=rep["user_id"],
        election_id=rep["election_id"],
        constituency_id=rep["constituency_id"]
    )

    # ✅ NEW: termination check
    evaluate_performance_and_terminate(rep)