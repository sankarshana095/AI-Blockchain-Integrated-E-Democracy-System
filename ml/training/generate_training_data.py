import random
import pandas as pd

def generate_row():
    # Base civic signals
    trending = random.randint(0, 10)
    backlash = random.randint(0, 6)
    supported = random.randint(0, 12)
    debates = random.randint(0, 8)
    new_issues = random.randint(0, 15)
    resolved = random.randint(0, 10)

    # Governance events
    elections = random.choice([0, 0, 0, 1])   # elections are rare
    rep_term_ending = random.choice([0, 0, 1])  # somewhat rare

    # ---------- Label logic ----------
    # election dominates everything
    if elections == 1:
        label = "election_activity"

    # strong negative sentiment
    elif backlash >= 4 and supported <= 3:
        label = "governance_risk"

    # citizens very active
    elif trending >= 6 or debates >= 5 or new_issues >= 10:
        label = "public_pressure"

    # lots of support + resolutions
    elif supported >= 6 and resolved >= 5:
        label = "high_engagement"

    # calm situation
    else:
        label = "stable"

    return {
        "trending_issues": trending,
        "backlash_signals": backlash,
        "supported_issues": supported,
        "policy_debates": debates,
        "new_issues": new_issues,
        "issues_resolved": resolved,
        "active_elections": elections,
        "rep_term_ending": rep_term_ending,
        "label": label
    }


def generate_dataset(n=5000):
    rows = [generate_row() for _ in range(n)]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_dataset(8000)   # generate 8k rows
    df.to_csv("constituency_training_data.csv", index=False)
    print("Dataset generated:", df.shape)