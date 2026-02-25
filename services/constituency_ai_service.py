import json
from datetime import timedelta
from utils.helpers import utc_now
from models.constituency_brief import get_brief, save_brief
from models.constituency_activity import get_constituency_activity_snapshot
#from services.ai_client import run_comment_reply, AIClientError
from datetime import datetime, timezone
from services.constituency_ml_service import generate_constituency_summary


# --------------------------------------------------
# Prompt Builder
# --------------------------------------------------

def build_constituency_brief_prompt(snapshot: dict) -> str:
    """
    Builds the AI prompt for real-time constituency summary.
    Keep prompt short and structured (<500 words).
    """

    return f"""
You are a civic intelligence assistant for a democratic governance platform.

Your task is to produce a concise real-time constituency brief summarizing what is happening now.

Focus on:
• governance risks or elections
• representative term changes
• issues gaining strong support or backlash
• major public concerns or debates
• important developments today

Rules:
- Be neutral, factual, and non-political
- Do NOT invent facts
- Do NOT mention database fields or raw data
- Combine related signals into insights
- Maximum 5 bullet points

Data snapshot:
{json.dumps(snapshot, indent=2)}

Output format:

Today in the constituency:

• Bullet insight 1
• Bullet insight 2
• Bullet insight 3
• Bullet insight 4
• Bullet insight 5

If activity is low, say so briefly.
"""


# --------------------------------------------------
# Main Service
# --------------------------------------------------
def utc_now():
    return datetime.now(timezone.utc)

REFRESH_INTERVAL = timedelta(hours=1)


def generate_constituency_brief(constituency_id: str) -> str:
    """
    Returns cached constituency brief.
    Regenerates only if older than 1 hour.
    """

    cached = get_brief(constituency_id)

    # 🟢 Use cached if fresh
    if cached:
        generated_at = cached.get("generated_at")

        if generated_at:

            # 🔧 Convert string → datetime safely
            if isinstance(generated_at, str):
                try:
                    generated_at = datetime.fromisoformat(generated_at)
                except Exception:
                    generated_at = None

            if generated_at:

                # 🔧 Force timezone awareness
                if generated_at.tzinfo is None:
                    generated_at = generated_at.replace(tzinfo=timezone.utc)

                now = utc_now()

                # Ensure utc_now is also aware
                if now.tzinfo is None:
                    now = now.replace(tzinfo=timezone.utc)

                age = now - generated_at

                if age < REFRESH_INTERVAL:
                    return cached["summary_text"]
    snapshot = get_constituency_activity_snapshot(constituency_id)

    summary = generate_constituency_summary(snapshot)

    save_brief(constituency_id, summary)
    return summary

    '''
    # 🔁 Need fresh summary
    snapshot = get_constituency_activity_snapshot(constituency_id)

    prompt = build_constituency_brief_prompt(snapshot)

    try:
        summary = run_comment_reply(prompt)
        save_brief(constituency_id, summary)
        return summary

    except AIClientError:
        return cached["summary_text"] if cached else "No civic summary available."
    '''