from jobs.daily_score_job import run_daily_score_job
from models.constituency import get_all_constituencies

def run_all_daily_scores():
    constituencies = get_all_constituencies()

    for c in constituencies:
        run_daily_score_job(
            constituency_id=c["id"],
        )