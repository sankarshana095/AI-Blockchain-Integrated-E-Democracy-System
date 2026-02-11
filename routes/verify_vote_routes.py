from flask import Blueprint, request, jsonify, render_template
from models.vote_merkle_proof import get_merkle_proof
from services.blockchain_service import verify_receipt_on_chain

bp = Blueprint("verify_vote", __name__, url_prefix="/verify-vote")


# -------------------------------
# PAGE: show form
# -------------------------------
@bp.route("", methods=["GET"])
def verify_vote_page():
    return render_template("evote/verify_vote.html")


# -------------------------------
# API: verify receipt
# -------------------------------
@bp.route("/check", methods=["POST"])
def verify_vote_check():
    data = request.json

    election_id = data.get("election_id")
    receipt_hash = data.get("receipt_hash")

    if not election_id or not receipt_hash:
        return jsonify({
            "valid": False,
            "message": "Election ID and receipt hash are required"
        }), 400

    record = get_merkle_proof(election_id, receipt_hash)

    if not record:
        return jsonify({
            "valid": False,
            "message": "Receipt not found for this election"
        }), 404

    is_valid = verify_receipt_on_chain(
        election_id=election_id,
        receipt_hash=receipt_hash,
        proof=record["proof"]
    )

    if is_valid:
        return jsonify({
            "valid": True,
            "message": "Vote successfully verified on blockchain"
        })

    return jsonify({
        "valid": False,
        "message": "Receipt exists but proof verification failed"
    })
