import pandas as pd
import joblib

model = joblib.load("ml/model/civic_model.pkl")

FEATURE_ORDER = [
    "trending_issues",
    "backlash_signals",
    "supported_issues",
    "policy_debates",
    "new_issues",
    "issues_resolved",
    "active_elections",
    "rep_term_ending"
]

def predict_constituency_status(data: dict):
    df = pd.DataFrame([[data[f] for f in FEATURE_ORDER]], columns=FEATURE_ORDER)
    return model.predict(df)[0]