"""
Comprehensive Representative Scoring System

This module implements a sophisticated scoring formula that evaluates representative
performance across multiple dimensions:

1. ACCOUNTABILITY DIMENSION (40%):
   - Issue Resolution Rate (20%): Percentage of accepted issues resolved
   - Response Time Average (10%): How quickly they respond
   - Citizen Satisfaction (10%): Percentage of citizen confirmations

2. ENGAGEMENT DIMENSION (30%):
   - Policy Post Quality (15%): Engagement per post (comments + upvotes)
   - Consistency (10%): Regular activity within term
   - Participation Depth (5%): Debate participation & discussion

3. INTEGRITY DIMENSION (20%):
   - Discourse Balance Index (15%): AI assessment of balanced arguments (0-100)
   - Controversy Flag (5%): Negative marks for contentious behavior

4. IMPACT DIMENSION (10%):
   - Constituency Engagement Index (5%): Community participation rate
   - Issue Scope Impact (5%): Severity/scope of resolved issues

Overall Score Formula:
FINAL_SCORE = (Accountability × 0.40) + (Engagement × 0.30) + (Integrity × 0.20) + (Impact × 0.10)
"""

from datetime import datetime, timedelta
from models.representative import get_rep_score
from models.issue import get_issues_by_constituency, get_issue_by_id, get_issues_for_elected_rep_term,get_issues_with_acceptance_time
from models.rep_policy import get_policy_posts_by_constituency, get_policy_posts_by_user
from models.rep_policy_comments import get_policy_comments
from supabase_db.db import fetch_all, fetch_one
from statistics import mean, stdev
import math


# ============================================================================
# ACCOUNTABILITY DIMENSION (40%)
# ============================================================================

def calculate_issue_resolution_rate(rep_user_id: str, constituency_id: str) -> float:
    """
    Calculate the percentage of issues accepted by this rep that were resolved.
    
    Returns:
        float: Score from 0-100 (0% = 0 points, 100% = 100 points)
    """
    issues = get_issues_for_elected_rep_term(constituency_id)
    
    # Filter issues that rep has taken action on
    accepted_issues = [
        i for i in issues 
        if i.get("status") in ("Accepted", "In Progress", "Resolved", "Closed")
        and i.get("rep_user_id") == rep_user_id
    ]
    
    if not accepted_issues:
        return 0.0
    
    resolved = [i for i in accepted_issues if i["status"] in ("Resolved", "Closed")]
    resolution_rate = len(resolved) / len(accepted_issues)
    
    return round(resolution_rate * 100, 2)


def calculate_response_time_score(rep_user_id: str, constituency_id: str) -> float:
    """
    Calculate score based on average response time to issues.
    
    Scoring:
    - <24 hours: 100 points
    - 24-72 hours: 80 points
    - 72-168 hours (7 days): 60 points
    - >7 days: 20-40 points
    - No response: 0 points
    
    Returns:
        float: Score from 0-100
    """
    issues = get_issues_with_acceptance_time(constituency_id)
    accepted_issues = [
        i for i in issues 
        if i.get("rep_user_id") == rep_user_id
        and i.get("status") in ("Accepted", "In Progress", "Resolved", "Closed")
    ]
    
    if not accepted_issues:
        return 0.0
    
    response_times = []
    for issue in accepted_issues:
        created_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        status_updated = issue.get("accepted_at")  # Timestamp when status first changed to 'Accepted'
        
        if status_updated:
            status_updated = datetime.fromisoformat(status_updated.replace("Z", "+00:00"))
            hours_to_respond = (status_updated - created_at).total_seconds() / 3600
            response_times.append(hours_to_respond)
    
    if not response_times:
        return 0.0
    
    avg_response_time = mean(response_times)
    
    # Scoring rubric
    if avg_response_time <= 24:
        return 100.0
    elif avg_response_time <= 72:
        return 80.0
    elif avg_response_time <= 168:  # 7 days
        return 60.0
    elif avg_response_time <= 336:  # 14 days
        return 40.0
    else:
        return 20.0


def calculate_citizen_satisfaction_score(rep_user_id: str, constituency_id: str) -> float:
    """
    Calculate based on percentage of issues where citizen confirmed resolution.
    
    Returns:
        float: Score from 0-100 (percentage of confirmed resolutions)
    """
    issues = get_issues_for_elected_rep_term(constituency_id)
    resolved_issues = [
        i for i in issues
        if i.get("rep_user_id") == rep_user_id
    and i.get("status") in ("Closed", "Resolved")
    ]

    
    if not resolved_issues:
        return 0.0
    
    confirmed = [
        i for i in resolved_issues 
        if i.get("status") == "Closed"
    ]
    
    satisfaction_rate = len(confirmed) / len(resolved_issues) if resolved_issues else 0
    return round(satisfaction_rate * 100, 2)



def get_accountability_score(rep_user_id: str, constituency_id: str) -> dict:
    """
    Calculate overall Accountability Dimension (40% weight).
    
    Returns:
        dict: {
            'resolution_rate': float,
            'response_time': float,
            'citizen_satisfaction': float,
            'total': float  # weighted average
        }
    """
    resolution_rate = calculate_issue_resolution_rate(rep_user_id, constituency_id)
    response_time = calculate_response_time_score(rep_user_id, constituency_id)
    citizen_satisfaction = calculate_citizen_satisfaction_score(rep_user_id, constituency_id)
    
    # Weighted formula: 50% resolution + 25% response + 25% satisfaction
    total = (resolution_rate * 0.50) + (response_time * 0.25) + (citizen_satisfaction * 0.25)
    
    return {
        'resolution_rate': round(resolution_rate, 2),
        'response_time': round(response_time, 2),
        'citizen_satisfaction': round(citizen_satisfaction, 2),
        'total': round(total, 2)
    }


# ============================================================================
# ENGAGEMENT DIMENSION (30%)
# ============================================================================
def count_comments_recursive(comments):
    total = 0

    for comment in comments:
        total += 1  # count this comment

        replies = comment.get("replies") or []
        if replies:
            total += count_comments_recursive(replies)

    return total


def calculate_policy_post_quality_score(rep_user_id: str, constituency_id: str) -> float:
    """
    Calculate quality of policy posts based on engagement metrics.
    
    Quality = (Total Comments + Total Upvotes) / Number of Posts
    
    Scoring:
    - 0-5 engagement per post: 20 points
    - 5-15 engagement per post: 50 points
    - 15-30 engagement per post: 80 points
    - 30+ engagement per post: 100 points
    - No posts: 0 points
    
    Returns:
        float: Score from 0-100
    """
    posts = get_policy_posts_by_user(rep_user_id)
    
    if not posts:
        return 0.0
    
    total_engagement = 0
    for post in posts:
        upvotes = post.get("upvotes", 0) or 0
        downvotes = post.get("downvotes", 0) or 0
        comments = get_policy_comments(post["id"])
        comment_count = count_comments_recursive(comments) if comments else 0
        total_engagement += upvotes + downvotes + comment_count
    avg_engagement_per_post = total_engagement / len(posts)
    
    if avg_engagement_per_post >= 30:
        return 100.0
    elif avg_engagement_per_post >= 15:
        return 80.0
    elif avg_engagement_per_post >= 5:
        return 50.0
    else:
        return 20.0


def calculate_consistency_score(rep_user_id: str, constituency_id: str) -> float:
    """
    Calculate consistency based on activity spread across term period.
    
    Measures: How evenly distributed is activity across the term?
    - Perfect consistency (equal activity each month): 100 points
    - Good consistency (no gaps >3 months): 80 points
    - Fair consistency (occasional gaps): 50 points
    - Poor consistency (large gaps): 20 points
    - No activity: 0 points
    
    Returns:
        float: Score from 0-100
    """
    posts = get_policy_posts_by_user(rep_user_id)
    
    if not posts:
        return 0.0
    
    # Group posts by month
    post_months = {}
    for post in posts:
        created_at = datetime.fromisoformat(post["created_at"].replace("Z", "+00:00"))
        month_key = created_at.strftime("%Y-%m")
        post_months[month_key] = post_months.get(month_key, 0) + 1
    
    if len(post_months) == 0:
        return 0.0
    
    # Calculate variance in activity
    activity_counts = list(post_months.values())
    
    if len(activity_counts) == 1:
        return 50.0  # Only one month of activity
    
    avg_activity = mean(activity_counts)
    activity_variance = stdev(activity_counts) if len(activity_counts) > 1 else 0
    coefficient_of_variation = (activity_variance / avg_activity) if avg_activity > 0 else 0
    
    # Lower variance = higher consistency
    if coefficient_of_variation <= 0.3:
        return 100.0
    elif coefficient_of_variation <= 0.6:
        return 80.0
    elif coefficient_of_variation <= 1.0:
        return 50.0
    else:
        return 20.0

from models.issue import get_issue_comments_by_constituency

def calculate_participation_depth_score(rep_user_id: str, constituency_id: str) -> float:
    """
    Calculate depth of participation in debates, comments, and discussions.
    
    Measures:
    - Comments on other rep posts
    - Responses to citizen feedback
    - Debate participation
    
    Returns:
        float: Score from 0-100
    """
    try:
        # Count comments made by this rep on OTHER reps' posts
        total_comments_made = 0
        
        # Get all policy posts in constituency
        posts = get_policy_posts_by_constituency(constituency_id)
        for post in posts:
            if post.get("created_by_user_id") != rep_user_id:  # Comments on OTHER reps' posts
                print(post["id"])
                comments = get_policy_comments(post["id"])
                rep_comments = [c for c in comments if c.get("user_id") == rep_user_id]
                total_comments_made += len(rep_comments)

        comments=get_issue_comments_by_constituency(constituency_id)
        for c in comments:
            rep_comments = [c for c in comments if c.get("user_id") == rep_user_id]
            total_comments_made += len(rep_comments)
        # Scoring rubric
        if total_comments_made >= 50:
            return 100.0
        elif total_comments_made >= 30:
            return 80.0
        elif total_comments_made >= 10:
            return 60.0
        elif total_comments_made > 0:
            return 40.0
        else:
            return 0.0
    except Exception:
        return 0.0


def get_engagement_score(rep_user_id: str, constituency_id: str) -> dict:
    """
    Calculate overall Engagement Dimension (30% weight).
    
    Returns:
        dict: {
            'post_quality': float,
            'consistency': float,
            'participation_depth': float,
            'total': float  # weighted average
        }
    """
    post_quality = calculate_policy_post_quality_score(rep_user_id, constituency_id)
    consistency = calculate_consistency_score(rep_user_id, constituency_id)
    participation = calculate_participation_depth_score(rep_user_id, constituency_id)
    
    # Weighted formula: 60% quality + 30% consistency + 10% participation
    total = (post_quality * 0.60) + (consistency * 0.30) + (participation * 0.10)
    
    return {
        'post_quality': round(post_quality, 2),
        'consistency': round(consistency, 2),
        'participation_depth': round(participation, 2),
        'total': round(total, 2)
    }


# ============================================================================
# INTEGRITY DIMENSION (20%)
# ============================================================================

def calculate_discourse_balance_score(rep_user_id: str, constituency_id: str) -> float:
    """
    Calculate AI assessment of balanced, fair discourse.
    
    Uses existing ai_confidence_score from policy posts.
    
    Returns:
        float: Score from 0-100 (average AI confidence score)
    """
    posts = get_policy_posts_by_user(rep_user_id)
    if not posts:
        return 50.0  # Neutral if no posts
    
    ai_scores = [
        float(p.get("ai_integrity_score", 50))
        for p in posts
        if p.get("ai_integrity_score") is not None
    ]
    
    if not ai_scores:
        return 50.0
    return round(mean(ai_scores), 2)

def calculate_controversy_penalty(rep_user_id: str, constituency_id: str) -> float:
    """
    Calculate penalty for controversial or negative behavior.
    
    Deductions:
    - High downvote ratio on posts: -10 to -30 points
    - Reported for misconduct: -20 to -50 points
    - Deleted/flagged content: -5 to -20 points
    
    Returns:
        float: Penalty score (negative value)
    """
    posts = get_policy_posts_by_user(rep_user_id)
    
    if not posts:
        return 0.0  # No penalty if no posts
    total_penalty = 0
    
    for post in posts:
        upvotes = post.get("upvotes", 0) or 0
        downvotes = post.get("downvotes", 0) or 0
        total_votes = upvotes + downvotes
        
        if total_votes > 0:
            downvote_ratio = downvotes / total_votes
            
            # Penalty for high downvote ratio
            if downvote_ratio > 0.5:
                total_penalty -= (downvote_ratio * 30)
            elif downvote_ratio > 0.3:
                total_penalty -= (downvote_ratio * 15)
    # Cap penalty at -30 points
    return max(total_penalty, -30.0)


def get_integrity_score(rep_user_id: str, constituency_id: str) -> dict:
    """
    Calculate overall Integrity Dimension (20% weight).
    
    Returns:
        dict: {
            'discourse_balance': float,
            'controversy_penalty': float,
            'total': float  # balance - penalty
        }
    """
    balance = calculate_discourse_balance_score(rep_user_id, constituency_id)
    controversy = calculate_controversy_penalty(rep_user_id, constituency_id)
    
    # Total = balance score plus controversy penalty
    total = max(0, balance + controversy)  # Can't go below 0
    
    return {
        'discourse_balance': round(balance, 2),
        'controversy_penalty': round(controversy, 2),
        'total': round(total, 2)
    }


# ============================================================================
# IMPACT DIMENSION (10%)
# ============================================================================

def calculate_constituency_engagement_index(rep_user_id: str, constituency_id: str) -> float:
    """
    Measure how engaged the constituency is with this representative.
    
    Metrics:
    - Total unique citizens interacting with rep's content
    - Participation rate in rep's posts
    
    Returns:
        float: Score from 0-100
    """
    posts = get_policy_posts_by_user(rep_user_id)
    
    if not posts:
        return 0.0
    
    # Count unique commenters
    unique_commenters = set()
    total_engagement = 0
    
    for post in posts:
        comments = get_policy_comments(post["id"])
        for comment in comments:
            unique_commenters.add(comment.get("user_id"))
            total_engagement += 1
        total_engagement += post.get("upvotes", 0) or 0
    # Scoring: more unique engaged citizens = higher score
    if total_engagement >= 100:
        return 100.0
    elif total_engagement >= 50:
        return 80.0
    elif total_engagement >= 20:
        return 60.0
    elif total_engagement >= 5:
        return 40.0
    else:
        return max(20.0, total_engagement * 4)


def calculate_issue_scope_impact(rep_user_id: str, constituency_id: str) -> float:
    """
    Measure impact based on severity/scope of issues resolved.
    
    Issue categories have different weights:
    - Critical (health, safety): 100 points each
    - Major (infrastructure, services): 60 points each
    - Standard (general issues): 30 points each
    
    Returns:
        float: Score 0-100 (capped)
    """
    issues = get_issues_for_elected_rep_term(constituency_id)
    resolved_issues = [
        i for i in issues 
        if i.get("rep_user_id") == rep_user_id
        and i["status"] in ("Resolved", "Closed")
    ]
    
    if not resolved_issues:
        return 0.0
    
    critical_keywords = ["health", "safety", "emergency", "critical", "urgent"]
    major_keywords = ["infrastructure", "transport", "water", "electricity", "road", "street", "education", "public service","sanitation"]
    
    total_impact = 0
    
    for issue in resolved_issues:
        category = issue.get("category", "").lower()
        title = issue.get("title", "").lower()
        description = issue.get("description", "").lower()
        
        # Check category and title for keywords
        if any(keyword in category or keyword in title or keyword in description for keyword in critical_keywords):
            total_impact += 100
        elif any(keyword in category or keyword in title or keyword in description for keyword in major_keywords):
            total_impact += 60
        else:
            total_impact += 30
    
    # Normalize to 0-100 scale
    # Assuming average rep resolves 5-10 issues
    normalized_score = min(100.0, (total_impact / 30) * 10)
    
    return round(normalized_score, 2)


def get_impact_score(rep_user_id: str, constituency_id: str) -> dict:
    """
    Calculate overall Impact Dimension (10% weight).
    
    Returns:
        dict: {
            'constituency_engagement': float,
            'issue_scope_impact': float,
            'total': float  # weighted average
        }
    """
    engagement = calculate_constituency_engagement_index(rep_user_id, constituency_id)
    scope_impact = calculate_issue_scope_impact(rep_user_id, constituency_id)
    
    # Weighted formula: 50% engagement + 50% scope impact
    total = (engagement * 0.50) + (scope_impact * 0.50)
    
    return {
        'constituency_engagement': round(engagement, 2),
        'issue_scope_impact': round(scope_impact, 2),
        'total': round(total, 2)
    }


# ============================================================================
# FINAL COMPOSITE SCORE
# ============================================================================

def calculate_representative_score(rep_user_id: str, constituency_id: str) -> dict:
    """
    Calculate comprehensive representative performance score.
    
    Formula:
    FINAL_SCORE = (Accountability × 0.40) + (Engagement × 0.30) 
                  + (Integrity × 0.20) + (Impact × 0.10)
    
    Returns:
        dict: Complete scoring breakdown with final score
    """

    accountability = get_accountability_score(rep_user_id, constituency_id)
    engagement = get_engagement_score(rep_user_id, constituency_id)
    integrity = get_integrity_score(rep_user_id, constituency_id)
    impact = get_impact_score(rep_user_id, constituency_id)
    
    # Weighted composite score
    final_score = (
        (accountability['total'] * 0.40) +
        (engagement['total'] * 0.30) +
        (integrity['total'] * 0.20) +
        (impact['total'] * 0.10)
    )
    
    # Determine rating
    if final_score >= 85:
        rating = "EXCELLENT"
    elif final_score >= 70:
        rating = "GOOD"
    elif final_score >= 55:
        rating = "SATISFACTORY"
    elif final_score >= 40:
        rating = "NEEDS_IMPROVEMENT"
    else:
        rating = "POOR"
    
    return {
        'final_score': round(final_score, 2),
        'rating': rating,
        'breakdown': {
            'accountability': accountability,
            'engagement': engagement,
            'integrity': integrity,
            'impact': impact
        }
    }


def get_score_interpretation(score: float) -> str:
    """
    Get human-readable interpretation of the score.
    """
    if score >= 85:
        return "Excellent performance. Strong commitment to accountability and citizen engagement."
    elif score >= 70:
        return "Good performance. Demonstrated responsibility and active engagement."
    elif score >= 55:
        return "Satisfactory performance. Meets baseline expectations."
    elif score >= 40:
        return "Needs improvement. More focus required on accountability and engagement."
    else:
        return "Poor performance. Significant improvement needed across all dimensions."
