# jobs/constituency_brief_job.py

from models.constituency import get_all_constituencies
from services.constituency_ai_service import (
    build_constituency_brief_prompt
)
from models.constituency_activity import get_constituency_activity_snapshot
from models.constituency_brief import save_brief
from services.ai_client import run_comment_reply
from datetime import datetime, timezone


def run_constituency_brief_job():
    """
    Generates fresh AI summaries for all constituencies.
    This should be run every 1 hour via cron.
    """

    print("🔄 Running constituency brief cron job...")

    constituencies = get_all_constituencies()

    for constituency in constituencies:
        constituency_id = constituency["id"]

        try:
            print(f"Generating summary for {constituency_id}...")

            snapshot = get_constituency_activity_snapshot(constituency_id)

            prompt = build_constituency_brief_prompt(snapshot)

            summary = run_comment_reply(prompt)

            save_brief(constituency_id, summary)

            print(f"✅ Saved summary for {constituency_id}")

        except Exception as e:
            print(f"❌ Failed for {constituency_id}: {e}")

    print("🎉 Cron job completed successfully.")


if __name__ == "__main__":
    run_constituency_brief_job()