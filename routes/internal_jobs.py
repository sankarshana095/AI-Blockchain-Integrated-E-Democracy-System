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