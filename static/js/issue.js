/* =========================
   ISSUE INTERACTIONS
========================= */

/*
 This file handles:
 - Upvote / Downvote UI (counts hidden)
 - Mark issue as resolved (only by issue creator)
 - Simple confirmation prompts

 Backend responsibility:
 - Actual vote counts
 - Permission validation
 - Status updates
*/


/* -------------------------
   Confirm Issue Resolution
------------------------- */

function confirmResolveIssue(issueId) {
    const confirmed = confirm(
        "Are you sure you want to mark this issue as resolved?\n" +
        "This action cannot be undone."
    );

    if (!confirmed) {
        return;
    }

    fetch(`/citizen/issues/${issueId}/resolve`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert("Unable to resolve issue. Please try again.");
        }
    })
    .catch(() => {
        alert("Network error. Please try again.");
    });
}


/* -------------------------
   Issue Voting (UI only)
------------------------- */

function voteIssue(issueId, voteType) {
    fetch(`/citizen/issues/${issueId}/vote`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            vote: voteType  // "up" or "down"
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Vote failed");
        }

        // Do NOT show vote counts (privacy rule)
        const btn = document.getElementById(`${voteType}-btn-${issueId}`);
        if (btn) {
            btn.classList.add("voted");
        }
    })
    .catch(() => {
        alert("Unable to submit vote.");
    });
}


/* -------------------------
   Helper: Disable buttons
------------------------- */

document.addEventListener("DOMContentLoaded", () => {
    const votedButtons = document.querySelectorAll(".voted");
    votedButtons.forEach(btn => {
        btn.disabled = true;
    });
});

function voteIssue(issueId, voteType) {
    fetch(`/citizen/issues/${issueId}/vote`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ vote: voteType })
    }).then(() => location.reload());
}

function confirmResolution(issueId) {
    fetch(`/citizen/issues/${issueId}/resolve`, {
        method: "POST"
    }).then(() => location.reload());
}

function toggleReply(commentId) {
    const form = document.getElementById(`reply-form-${commentId}`);
    form.style.display = form.style.display === "none" ? "block" : "none";
}

function toggleThread(commentId) {
    const replies = document.getElementById(`replies-${commentId}`);
    const icon = document.getElementById(`toggle-icon-${commentId}`);

    if (!replies) return;

    if (replies.style.display === "none") {
        replies.style.display = "block";
        icon.textContent = "[–]";
    } else {
        replies.style.display = "none";
        icon.textContent = "[+]";
    }
}
