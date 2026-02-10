// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

contract VotingContract {

    // --------------------------------------------------
    // EVENTS (FOR COUNTING)
    // --------------------------------------------------

    event VoteCast(
        uint256 indexed electionId,
        uint256 indexed candidateId,
        uint256 timestamp
    );

    // --------------------------------------------------
    // STORAGE (FOR VERIFICATION)
    // --------------------------------------------------

    // Election → Merkle root of all vote receipts
    mapping(uint256 => bytes32) public electionMerkleRoot;

    // --------------------------------------------------
    // CAST VOTE (NO RECEIPTS STORED)
    // --------------------------------------------------

    function castVote(
        uint256 electionId,
        uint256 candidateId
    ) external {
        emit VoteCast(
            electionId,
            candidateId,
            block.timestamp
        );
    }

    // --------------------------------------------------
    // POST-ELECTION: PUBLISH ROOT
    // --------------------------------------------------

    function publishMerkleRoot(
        uint256 electionId,
        bytes32 root
    ) external {
        electionMerkleRoot[electionId] = root;
    }

    // --------------------------------------------------
    // RECEIPT VERIFICATION (SAFE)
    // --------------------------------------------------

    function verifyReceipt(
        uint256 electionId,
        bytes32 receiptHash,
        bytes32[] calldata proof
    ) external view returns (bool) {
        return MerkleProof.verify(
            proof,
            electionMerkleRoot[electionId],
            receiptHash
        );
    }
}
