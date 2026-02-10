from collections import defaultdict
from services.blockchain_service import get_contract


def tally_votes_from_blockchain(election_id: str) -> dict:
    """
    Tally votes by reading VoteCast events from blockchain.

    Returns:
        {
            candidate_id: vote_count
        }
    """

    contract = get_contract()

    # Get all VoteCast events for the election
    events = contract.events.VoteCast.get_logs(
        fromBlock=0,
        argument_filters={
            "electionId": int(election_id)
        }
    )

    tally = defaultdict(int)

    for event in events:
        candidate_id = event["args"]["candidateId"]
        tally[candidate_id] += 1

    return dict(tally)
