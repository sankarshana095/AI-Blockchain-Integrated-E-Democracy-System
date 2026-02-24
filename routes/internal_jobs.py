from flask import Blueprint, request, abort, jsonify
from jobs.run_daily_jobs import run_all_daily_scores
#import os


bp = Blueprint("internal_jobs", __name__, url_prefix="/internal")

#SECRET = os.getenv("CRON_SECRET")

@bp.route("/run-daily-score", methods=["GET"])
def run_daily_score():
    '''
    if request.headers.get("X-CRON-KEY") != SECRET:
        abort(403)
    '''
    run_all_daily_scores()
    return jsonify({"status": "ok"})

# -----------------------------
# Manual Cron Trigger (AI Brief Job)
# -----------------------------

@bp.route("/run-brief-job", methods=["GET"])
def run_brief_job():
    """
    Manually triggers constituency AI brief generation.
    Should be protected and not public.
    """

    from jobs.constituency_brief_job import run_constituency_brief_job

    try:
        run_constituency_brief_job()
        return {"message": "Brief job executed successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 500