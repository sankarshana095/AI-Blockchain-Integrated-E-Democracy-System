from ml.inference.ml_predictor import predict_constituency_status

def snapshot_to_features(snapshot: dict):
    return {
        "trending_issues": len(snapshot.get("trending_issues", [])),
        "backlash_signals": len(snapshot.get("backlash_signals", [])),
        "supported_issues": len(snapshot.get("supported_issues", [])),
        "policy_debates": len(snapshot.get("active_policy_debates", [])),
        "new_issues": len(snapshot.get("new_issues", [])),
        "issues_resolved": len(snapshot.get("issues_resolved", [])),
        "active_elections": 1 if snapshot.get("active_elections") else 0,
        "rep_term_ending": 1 if snapshot.get("rep_terms_ending") else 0
    }


def generate_constituency_summary(snapshot: dict) -> str:
    features = snapshot_to_features(snapshot)

    label = predict_constituency_status(features)

    templates = {
        "stable":
            "• Civic activity remains stable with no major governance disruptions detected.",

        "public_pressure":
            "• Citizens are actively raising concerns, indicating strong public engagement in governance.",

        "governance_risk":
            "• Warning signals detected — rising dissatisfaction or unresolved issues may require intervention.",

        "high_engagement":
            "• High civic participation observed with strong community support and issue resolutions.",

        "election_activity":
            "• Electoral processes are active in this constituency. Governance attention is currently election-focused."
    }

    return f"""Today in the constituency:{templates.get(label, "• Civic activity is being monitored.")}"""