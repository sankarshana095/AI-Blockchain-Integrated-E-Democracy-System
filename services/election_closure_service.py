from datetime import timedelta
from models.representative import create_representative
from services.result_service import get_constituency_results
from models.election import get_constituencies_for_election
from utils.helpers import parse_iso_date
import random
from services.merkle_service import finalize_merkle_tree_for_election


def close_election_and_assign_reps(election):
    """
    Called once when election ends.
    Assigns ELECTED_REP and OPPOSITION_REP for each constituency.
    """

    election_id = election["id"]
    constituencies = get_constituencies_for_election(election_id)

    # Term dates
    election_end = parse_iso_date(election["end_time"])
    term_start = parse_iso_date(election["end_time"]) + timedelta(days=1)
    term_end = term_start.replace(year=term_start.year + 5)


    for c in constituencies:
        constituency_id = c["constituency_id"]

        # Get final vote counts
        results = get_constituency_results(
            election_id=election_id,
            constituency_id=constituency_id
        )
        print(results)
        if not results:
            continue

        # Sort by votes desc
        results.sort(key=lambda x: x["votes"], reverse=True)

        # -----------------------------
        # WINNER (handle tie)
        # -----------------------------
        top_votes = results[0]["votes"]
        winners = [r for r in results if r["votes"] == top_votes]
        winner = random.choice(winners)

        # Remove winner from list
        remaining = [r for r in results if r["user_id"] != winner["user_id"]]

        # -----------------------------
        # RUNNER UP (handle tie)
        # -----------------------------
        if remaining:
            second_votes = remaining[0]["votes"]
            runners = [r for r in remaining if r["votes"] == second_votes]
            runner_up = random.choice(runners)
        else:
            runner_up = None

        # -----------------------------
        # INSERT REPRESENTATIVES
        # -----------------------------
        create_representative(
            user_id=winner["user_id"],
            constituency_id=constituency_id,
            rep_type="ELECTED_REP",
            term_start=term_start,
            term_end=term_end
        )

        if runner_up:
            create_representative(
                user_id=runner_up["user_id"],
                constituency_id=constituency_id,
                rep_type="OPPOSITION_REP",
                term_start=term_start,
                term_end=term_end
            )

    finalize_merkle_tree_for_election(election["id"])
