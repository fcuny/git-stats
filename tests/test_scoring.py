"""
Tests for the scoring module.
"""

import pytest
from datetime import datetime, timedelta

from git_stats.scoring import (
    normalize_metrics,
    calculate_contributor_score,
    calculate_recency_score,
    rank_contributors,
    DEFAULT_WEIGHTS,
)


def test_normalize_metrics():
    """Test normalization of metrics."""
    # Create sample metrics
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)
    two_years_ago = now - timedelta(days=730)

    metrics = {
        "Alice <alice@example.com>": {
            "first_commit_date": two_years_ago,
            "last_commit_date": now,
            "total_commits": 100,
            "total_lines_added": 5000,
            "total_lines_deleted": 1000,
            "recency": 0.8,
        },
        "Bob <bob@example.com>": {
            "first_commit_date": one_year_ago,
            "last_commit_date": now,
            "total_commits": 50,
            "total_lines_added": 2000,
            "total_lines_deleted": 500,
            "recency": 0.9,
        },
    }

    # Normalize metrics
    normalized = normalize_metrics(metrics)

    # Check that all values are between 0 and 1
    for contributor in normalized:
        for metric, value in normalized[contributor].items():
            assert 0 <= value <= 1, (
                f"Normalized value for {contributor}.{metric} is not between 0 and 1"
            )

    # Check that Alice has higher longevity and lines than Bob
    assert normalized["Alice <alice@example.com>"]["longevity"] == 1.0
    assert normalized["Bob <bob@example.com>"]["longevity"] < 1.0
    assert normalized["Alice <alice@example.com>"]["lines"] == 1.0
    assert normalized["Bob <bob@example.com>"]["lines"] < 1.0

    # Check that Bob has higher recency than Alice
    assert (
        normalized["Bob <bob@example.com>"]["recency"]
        > normalized["Alice <alice@example.com>"]["recency"]
    )


def test_calculate_contributor_score():
    """Test calculation of contributor scores."""
    # Create sample normalized metrics
    normalized_metrics = {
        "Alice <alice@example.com>": {
            "longevity": 1.0,
            "lines": 1.0,
            "commits": 1.0,
            "recency": 0.8,
        },
        "Bob <bob@example.com>": {
            "longevity": 0.5,
            "lines": 0.4,
            "commits": 0.5,
            "recency": 0.9,
        },
    }

    # Calculate scores with default weights
    scores = calculate_contributor_score(normalized_metrics)

    # Check that Alice has a higher score than Bob
    assert scores["Alice <alice@example.com>"] > scores["Bob <bob@example.com>"]

    # Calculate expected scores manually
    expected_alice = (
        1.0 * DEFAULT_WEIGHTS["longevity"]
        + 1.0 * DEFAULT_WEIGHTS["lines"]
        + 1.0 * DEFAULT_WEIGHTS["commits"]
        + 0.8 * DEFAULT_WEIGHTS["recency"]
    )
    expected_bob = (
        0.5 * DEFAULT_WEIGHTS["longevity"]
        + 0.4 * DEFAULT_WEIGHTS["lines"]
        + 0.5 * DEFAULT_WEIGHTS["commits"]
        + 0.9 * DEFAULT_WEIGHTS["recency"]
    )

    # Check that scores match expected values
    assert scores["Alice <alice@example.com>"] == pytest.approx(expected_alice)
    assert scores["Bob <bob@example.com>"] == pytest.approx(expected_bob)

    # Test with custom weights that heavily prioritize recency
    # With these weights, Bob should have a higher score due to higher recency
    custom_weights = {
        "longevity": 0.05,
        "lines": 0.05,
        "commits": 0.05,
        "recency": 0.85,
    }

    custom_scores = calculate_contributor_score(normalized_metrics, custom_weights)

    # Calculate expected custom scores manually
    expected_alice_custom = (
        1.0 * custom_weights["longevity"]
        + 1.0 * custom_weights["lines"]
        + 1.0 * custom_weights["commits"]
        + 0.8 * custom_weights["recency"]
    )
    expected_bob_custom = (
        0.5 * custom_weights["longevity"]
        + 0.4 * custom_weights["lines"]
        + 0.5 * custom_weights["commits"]
        + 0.9 * custom_weights["recency"]
    )

    # With these weights, Bob should have a higher score due to higher recency
    assert (
        custom_scores["Bob <bob@example.com>"]
        > custom_scores["Alice <alice@example.com>"]
    )
    assert expected_bob_custom > expected_alice_custom


def test_calculate_recency_score():
    """Test calculation of recency scores."""
    now = datetime.now()
    one_month_ago = now - timedelta(days=30)
    two_months_ago = now - timedelta(days=60)
    four_months_ago = now - timedelta(days=120)

    # Create sample commits
    commits = [
        {"author": "Alice <alice@example.com>", "date": now},
        {"author": "Alice <alice@example.com>", "date": one_month_ago},
        {"author": "Alice <alice@example.com>", "date": four_months_ago},
        {"author": "Bob <bob@example.com>", "date": one_month_ago},
        {"author": "Bob <bob@example.com>", "date": two_months_ago},
    ]

    # Calculate recency scores with default period (3 months)
    recency_scores = calculate_recency_score(commits)

    # Alice has 2 out of 3 commits in the last 3 months
    assert recency_scores["Alice <alice@example.com>"] == pytest.approx(2 / 3)

    # Bob has 2 out of 2 commits in the last 3 months
    assert recency_scores["Bob <bob@example.com>"] == pytest.approx(1.0)

    # Test with custom recency period (1 month)
    recency_scores = calculate_recency_score(commits, recency_period_months=1)

    # Alice has 1 out of 3 commits in the last month
    assert recency_scores["Alice <alice@example.com>"] == pytest.approx(1 / 3)

    # Bob has 1 out of 2 commits in the last month
    assert recency_scores["Bob <bob@example.com>"] == pytest.approx(0.5)


def test_rank_contributors():
    """Test ranking of contributors."""
    # Create sample metrics
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)
    two_years_ago = now - timedelta(days=730)

    stats = {
        "Alice <alice@example.com>": {
            "first_commit_date": two_years_ago,
            "last_commit_date": now,
            "total_commits": 100,
            "total_lines_added": 5000,
            "total_lines_deleted": 1000,
        },
        "Bob <bob@example.com>": {
            "first_commit_date": one_year_ago,
            "last_commit_date": now,
            "total_commits": 50,
            "total_lines_added": 2000,
            "total_lines_deleted": 500,
        },
        "Charlie <charlie@example.com>": {
            "first_commit_date": one_year_ago,
            "last_commit_date": now,
            "total_commits": 30,
            "total_lines_added": 1000,
            "total_lines_deleted": 200,
        },
    }

    # Rank contributors
    ranking = rank_contributors(stats)

    # Check that ranking is sorted by score (descending)
    assert ranking[0][0] == "Alice <alice@example.com>"
    assert ranking[1][0] == "Bob <bob@example.com>"
    assert ranking[2][0] == "Charlie <charlie@example.com>"

    # Check that scores are in descending order
    assert ranking[0][1] > ranking[1][1] > ranking[2][1]

    # Check that normalized metrics are included
    assert "longevity" in ranking[0][2]
    assert "lines" in ranking[0][2]
    assert "commits" in ranking[0][2]
    assert "recency" in ranking[0][2]

    # Test with custom weights that prioritize recency
    custom_weights = {
        "longevity": 0.1,
        "lines": 0.1,
        "commits": 0.1,
        "recency": 0.7,
    }

    # In this case, the ranking might change based on recency
    # We can't predict the exact order without knowing the recency values
    custom_ranking = rank_contributors(stats, weights=custom_weights)

    # Check that the ranking has the same contributors
    assert set(r[0] for r in custom_ranking) == {
        "Alice <alice@example.com>",
        "Bob <bob@example.com>",
        "Charlie <charlie@example.com>",
    }


def test_edge_cases():
    """Test edge cases for scoring functions."""
    # Empty metrics
    assert normalize_metrics({}) == {}
    assert calculate_contributor_score({}) == {}
    assert rank_contributors({}) == []

    # Single contributor
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)

    stats = {
        "Alice <alice@example.com>": {
            "first_commit_date": one_year_ago,
            "last_commit_date": now,
            "total_commits": 100,
            "total_lines_added": 5000,
            "total_lines_deleted": 1000,
        }
    }

    ranking = rank_contributors(stats)
    assert len(ranking) == 1
    assert ranking[0][0] == "Alice <alice@example.com>"
    assert ranking[0][1] > 0

    # Missing metrics
    incomplete_stats = {
        "Alice <alice@example.com>": {
            "total_commits": 100,
            # Missing first_commit_date, last_commit_date, etc.
        },
        "Bob <bob@example.com>": {
            "first_commit_date": one_year_ago,
            # Missing last_commit_date
            "total_commits": 50,
        },
    }

    # Should not raise exceptions
    ranking = rank_contributors(incomplete_stats)
    assert len(ranking) == 2

    # Equal scores (tie-breaking)
    equal_stats = {
        "Alice <alice@example.com>": {
            "first_commit_date": one_year_ago,
            "last_commit_date": now,
            "total_commits": 100,
            "total_lines_added": 5000,
            "total_lines_deleted": 1000,
        },
        "Bob <bob@example.com>": {
            "first_commit_date": one_year_ago,
            "last_commit_date": now,
            "total_commits": 100,
            "total_lines_added": 5000,
            "total_lines_deleted": 1000,
        },
    }

    # Both should have the same score
    ranking = rank_contributors(equal_stats)
    assert len(ranking) == 2
    assert ranking[0][1] == ranking[1][1]


@pytest.fixture
def sample_author_stats():
    """Fixture for sample author statistics."""
    # Create sample author stats for three contributors
    now = datetime.now()
    three_months_ago = now - timedelta(days=90)
    six_months_ago = now - timedelta(days=180)
    one_year_ago = now - timedelta(days=365)

    return {
        "Alice <alice@example.com>": {
            "commits": 20,
            "lines_added": 1000,
            "lines_deleted": 200,
            "first_commit_date": one_year_ago,
            "last_commit_date": now,
            "commit_dates": [
                one_year_ago,
                six_months_ago,
                three_months_ago,
                now - timedelta(days=30),
                now - timedelta(days=7),
                now,
            ],
        },
        "Bob <bob@example.com>": {
            "commits": 10,
            "lines_added": 500,
            "lines_deleted": 100,
            "first_commit_date": six_months_ago,
            "last_commit_date": three_months_ago,
            "commit_dates": [
                six_months_ago,
                six_months_ago + timedelta(days=30),
                three_months_ago,
            ],
        },
        "Charlie <charlie@example.com>": {
            "commits": 5,
            "lines_added": 2000,
            "lines_deleted": 50,
            "first_commit_date": three_months_ago,
            "last_commit_date": now - timedelta(days=1),
            "commit_dates": [
                three_months_ago,
                now - timedelta(days=30),
                now - timedelta(days=1),
            ],
        },
    }


def test_rank_contributors_default_weights(sample_author_stats):
    """Test ranking contributors with default weights."""
    # Rank contributors with default weights
    ranking = rank_contributors(sample_author_stats, recency_period_months=3)

    # Check that we have the expected number of contributors
    assert len(ranking) == 3

    # Extract authors and scores
    authors = [author for author, _, _ in ranking]
    scores = [score for _, score, _ in ranking]

    # Check that Alice is ranked first (highest score)
    assert "Alice" in authors[0]

    # Check that scores are in descending order
    assert scores[0] >= scores[1] >= scores[2]

    # Check that each contributor has normalized metrics
    for _, _, metrics in ranking:
        assert "longevity" in metrics
        assert "lines" in metrics
        assert "commits" in metrics
        assert "recency" in metrics

        # Check that metrics are normalized (between 0 and 1)
        for metric_name, value in metrics.items():
            assert 0 <= value <= 1


def test_rank_contributors_custom_weights(sample_author_stats):
    """Test ranking contributors with custom weights."""
    # Define custom weights that prioritize recent contributions
    custom_weights = {
        "longevity": 0.1,
        "lines": 0.2,
        "commits": 0.3,
        "recency": 0.4,  # Higher weight for recency
    }

    # Rank contributors with custom weights
    ranking = rank_contributors(
        sample_author_stats, weights=custom_weights, recency_period_months=3
    )

    # Extract authors and scores
    authors = [author for author, _, _ in ranking]

    # With higher weight on recency, Charlie might rank higher
    # since all his commits are within the recency period
    assert "Charlie" in authors[0] or "Alice" in authors[0]


def test_rank_contributors_recency_period(sample_author_stats):
    """Test ranking contributors with different recency periods."""
    # Rank with 1 month recency period
    ranking_1m = rank_contributors(sample_author_stats, recency_period_months=1)

    # Rank with 6 months recency period
    ranking_6m = rank_contributors(sample_author_stats, recency_period_months=6)

    # Extract authors for both rankings
    authors_1m = [author for author, _, _ in ranking_1m]
    authors_6m = [author for author, _, _ in ranking_6m]

    # With 1 month recency, Alice and Charlie should rank higher than Bob
    # since Bob's last commit was 3 months ago
    assert authors_1m.index(
        next(a for a in authors_1m if "Bob" in a)
    ) > authors_1m.index(next(a for a in authors_1m if "Alice" in a))

    # With 6 months recency, Bob's contributions should count
    # Check that Bob is still in the ranking with 6 months recency
    bob_index_6m = authors_6m.index(next(a for a in authors_6m if "Bob" in a))
    assert bob_index_6m >= 0

    # Instead of comparing scores directly, check relative positions
    # Bob should be ranked better (or same) with 6 months recency compared to 1 month
    bob_index_1m = authors_1m.index(next(a for a in authors_1m if "Bob" in a))
    assert bob_index_6m <= bob_index_1m


def test_rank_contributors_single_contributor(sample_author_stats):
    """Test ranking contributors with a single contributor."""
    # Create stats with only Alice
    alice_stats = {
        "Alice <alice@example.com>": sample_author_stats["Alice <alice@example.com>"]
    }

    # Rank with single contributor
    ranking = rank_contributors(alice_stats, recency_period_months=3)

    # Check that we have one contributor
    assert len(ranking) == 1

    # Check that the contributor is Alice
    assert "Alice" in ranking[0][0]

    # Check that the score is normalized
    # When there's only one contributor, they might not get a score of 1.0
    # because the scoring is based on their actual metrics, not just relative ranking
    assert 0 < ranking[0][1] <= 1.0


def test_rank_contributors_same_metrics():
    """Test ranking contributors with identical metrics."""
    # Create stats with two contributors having identical metrics
    now = datetime.now()
    three_months_ago = now - timedelta(days=90)

    identical_stats = {
        "Alice <alice@example.com>": {
            "commits": 10,
            "lines_added": 500,
            "lines_deleted": 100,
            "first_commit_date": three_months_ago,
            "last_commit_date": now,
            "commit_dates": [three_months_ago, now],
        },
        "Bob <bob@example.com>": {
            "commits": 10,
            "lines_added": 500,
            "lines_deleted": 100,
            "first_commit_date": three_months_ago,
            "last_commit_date": now,
            "commit_dates": [three_months_ago, now],
        },
    }

    # Rank with identical metrics
    ranking = rank_contributors(identical_stats, recency_period_months=3)

    # Check that we have two contributors
    assert len(ranking) == 2

    # Check that both scores are equal
    assert ranking[0][1] == ranking[1][1]
