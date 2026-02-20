from flask import Blueprint, render_template, session
from services.accountability_service import build_accountability_snapshot
from utils.decorators import login_required
from services.representative_scoring import calculate_representative_score
from services.representative_score_history import get_last_90_day_average
from models.representative import get_current_representative_by_constituency

bp = Blueprint("accountability", __name__, url_prefix="/accountability")


@bp.route("/<rep_user_id>")
@login_required
def view_rep_accountability(rep_user_id):
    # constituency resolution can be inferred or passed
    score = calculate_representative_score(
        rep_user_id=rep_user_id,
        constituency_id=session.get("constituency_id")
    )
    rep=get_current_representative_by_constituency(session.get("constituency_id"))
    if rep["user_id"] == rep_user_id:
        avg90 = get_last_90_day_average(
            rep_user_id=rep_user_id,
            election_id=rep["election_id"]
        )

    return render_template(
        "accountability/rep_dashboard.html",
        score=score,
        avg90=avg90
    )
