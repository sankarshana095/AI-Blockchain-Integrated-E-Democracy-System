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
    assert len(receipt_bytes32) == 32
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
    
def count_votes_from_blockchain(election_id: str) -> dict:
    """
    Counts votes for an election by reading VoteCast events
    from the blockchain.
    """

    from web3 import Web3
    import json
    from utils.crypto import uuid_to_uint256

    WEB3_PROVIDER = Config.WEB3_PROVIDER_URL
    CONTRACT_ADDRESS = Config.VOTING_CONTRACT_ADDRESS

    w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

    with open("blockchain/abi/VotingContractABI.json") as f:
        abi = json.load(f)

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=abi
    )

    election_uint = uuid_to_uint256(election_id)

    # 🔍 Fetch all VoteCast events for this election
    events = contract.events.VoteCast.get_logs(
        fromBlock=0,
        toBlock="latest",
        argument_filters={
            "electionId": election_uint
        }
    )

    results = {}

    for event in events:
        candidate_id = event["args"]["candidateId"]

        results[candidate_id] = results.get(candidate_id, 0) + 1

    return results

def publish_merkle_root_on_chain(election_id, merkle_root):
    if BLOCKCHAIN_MODE == "STUB":
        print(f"[STUB] Published Merkle Root for election {election_id}: {merkle_root}")
        return True

    from web3 import Web3
    import json

    w3 = Web3(Web3.HTTPProvider(Config.WEB3_PROVIDER_URL))

    with open("blockchain/abi/VotingContractABI.json") as f:
        abi = json.load(f)

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(Config.VOTING_CONTRACT_ADDRESS),
        abi=abi
    )

    account = w3.eth.account.from_key(Config.BOOTH_PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address)

    txn = contract.functions.publishMerkleRoot(
        uuid_to_uint256(election_id),
        Web3.to_bytes(hexstr=merkle_root)
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": 11155111,
        "gas": 200000,
        "gasPrice": w3.eth.gas_price
    })

    signed = w3.eth.account.sign_transaction(txn, Config.BOOTH_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    return tx_hash.hex()

def _web3_verify_receipt(election_id, receipt_hash, proof):
    from web3 import Web3
    import json
    from config import Config
    from utils.crypto import uuid_to_uint256

    w3 = Web3(Web3.HTTPProvider(Config.WEB3_PROVIDER_URL))

    if not w3.is_connected():
        raise Exception("Blockchain node not reachable")

    # Load ABI
    with open("blockchain/abi/VotingContractABI.json") as f:
        abi = json.load(f)

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(Config.VOTING_CONTRACT_ADDRESS),
        abi=abi
    )

    # Convert values to correct Solidity types
    election_uint = uuid_to_uint256(election_id)
    receipt_bytes32 = Web3.to_bytes(hexstr=receipt_hash)
    proof_bytes32 = [Web3.to_bytes(hexstr=p) for p in proof]

    # Call view function (NO GAS, NO TX)
    return contract.functions.verifyReceipt(
        election_uint,
        receipt_bytes32,
        proof_bytes32
    ).call()

def verify_receipt_on_chain(election_id, receipt_hash, proof):
    """
    Verifies a vote receipt using Merkle proof on blockchain.
    """

    if BLOCKCHAIN_MODE == "STUB":
        # In stub mode, always return True for demo
        print("[STUB] Verifying receipt:", receipt_hash)
        return True

    if BLOCKCHAIN_MODE == "WEB3":
        return _web3_verify_receipt(election_id, receipt_hash, proof)

    raise Exception("Invalid BLOCKCHAIN_MODE")


