from datetime import date, timedelta
from models.representative import get_rep_score_history


def get_last_90_day_average(rep_user_id: str, election_id: str):
    """
    Computes average score over the last 90 days.
    """

    rows = get_rep_score_history(rep_user_id, election_id)

    if not rows:
        return None

    cutoff = date.today() - timedelta(days=90)

    recent = []
    for r in rows:
        d = r.get("score_date")

        if isinstance(d, str):
            d = date.fromisoformat(d)

        if d >= cutoff:
            recent.append(r)

    if not recent:
        return None

    def avg(field):
        vals = [r[field] for r in recent if r.get(field) is not None]
        return round(sum(vals)/len(vals), 2) if vals else 0

    return {
        "final_score": avg("final_score"),
        "accountability": avg("accountability_score"),
        "engagement": avg("engagement_score"),
        "integrity": avg("integrity_score"),
        "impact": avg("impact_score"),
        "days_used": len(recent)
    }