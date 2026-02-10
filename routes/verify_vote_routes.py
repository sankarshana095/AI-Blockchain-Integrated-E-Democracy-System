from flask import Blueprint, render_template, request, flash
from utils.decorators import login_required
from models.vote_receipt import get_all_receipts_for_election
from utils.merkle import get_merkle_proof
from services.blockchain_service import verify_receipt_on_chain

bp = Blueprint("verify_vote", __name__, url_prefix="/verify-vote")


@bp.route("/", methods=["GET", "POST"])
@login_required
def verify_vote():
    result = None

    if request.method == "POST":
        election_id = request.form.get("election_id")
        receipt_hash = request.form.get("receipt_hash")

        try:
            receipts = get_all_receipts_for_election(election_id)

            proof = get_merkle_proof(receipts, receipt_hash)

            is_valid = verify_receipt_on_chain(
                election_id=election_id,
                receipt_hash=receipt_hash,
                proof=proof
            )

            result = is_valid

        except Exception as e:
            flash(str(e), "error")

    return render_template(
        "evote/verify_vote.html",
        result=result
    )
