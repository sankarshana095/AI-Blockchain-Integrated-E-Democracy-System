# services/blockchain_service.py

import hashlib
from datetime import datetime
from config import Config
from utils.crypto import uuid_to_uint256
from web3 import Web3


BLOCKCHAIN_MODE = Config.BLOCKCHAIN_MODE


# -------------------------------------------------
# STUB IMPLEMENTATION
# -------------------------------------------------

def _stub_cast_vote(election_id, candidate_id, receipt_hash):
    raw = f"{uuid_to_uint256(election_id)}|{uuid_to_uint256(candidate_id)}|{receipt_hash}|{datetime.utcnow().isoformat()}"
    fake_tx_hash = "0x" + hashlib.sha256(raw.encode()).hexdigest()
    return fake_tx_hash


# -------------------------------------------------
# PUBLIC API
# -------------------------------------------------

def cast_vote_on_chain(election_id, candidate_id, receipt_hash):
    print("BLOCKCHAIN_MODE =", BLOCKCHAIN_MODE)
    if BLOCKCHAIN_MODE == "STUB":
        return _stub_cast_vote(election_id, candidate_id, receipt_hash)

    if BLOCKCHAIN_MODE == "WEB3":
        return _web3_cast_vote(election_id, candidate_id, receipt_hash)

    raise Exception("Invalid BLOCKCHAIN_MODE configuration")


# -------------------------------------------------
# REAL WEB3 IMPLEMENTATION
# -------------------------------------------------

def _web3_cast_vote(election_id, candidate_id, receipt_hash):
    from web3 import Web3
    import json

    WEB3_PROVIDER = Config.WEB3_PROVIDER_URL
    CONTRACT_ADDRESS = Config.VOTING_CONTRACT_ADDRESS
    BOOTH_PRIVATE_KEY = Config.BOOTH_PRIVATE_KEY

    if not all([WEB3_PROVIDER, CONTRACT_ADDRESS, BOOTH_PRIVATE_KEY]):
        raise Exception("Blockchain configuration missing")

    w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

    if not w3.is_connected():
        raise Exception("Blockchain node not reachable")

    # Load ABI
    with open("blockchain/abi/VotingContractABI.json") as f:
        abi = json.load(f)

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=abi
    )

    account = w3.eth.account.from_key(BOOTH_PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address)
    # 🔑 Convert receipt hash → bytes32
    receipt_bytes32 = Web3.to_bytes(hexstr=receipt_hash)
    print('after:',receipt_bytes32)
    print('election_id:', election_id)
    print('candidate_id:', candidate_id)
    txn = contract.functions.castVote(
        uuid_to_uint256(election_id),
        uuid_to_uint256(candidate_id)
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": 11155111,   # Sepolia
        "gas": 300000,
        "gasPrice": w3.eth.gas_price
    })

    signed_txn = w3.eth.account.sign_transaction(txn, BOOTH_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    return tx_hash.hex()
