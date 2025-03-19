"""
Stats command implementation for git-stats.

This module provides functionality to generate contribution statistics for a Git repository.
"""

import json
from typing import Optional

from rich.console import Console

from git_stats.config import OutputFormat
from git_stats.formatting import (
    create_console,
    create_score_bar,
    create_stats_table,
    format_longevity,
    get_rank_style,
)
from git_stats.git import repository, parser
from git_stats.scoring import rank_contributors


def execute(
    repo_path: str,
    recency_period: int,
    output_format: OutputFormat,
    path: Optional[str] = None,
    language: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    console: Optional[Console] = None,
) -> int:
    """
    Execute the stats command to generate contribution statistics.

    Args:
        repo_path: Path to the Git repository
        recency_period: Recency period in months
        output_format: Format for output (text or json)
        path: Filter by specific directory or file path
        language: Filter by specific language
        since: Start date for the analysis
        until: End date for the analysis
        console: Rich console instance for output

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if console is None:
        console = create_console()

    # Validate repository
    if not repository.validate_repo(repo_path):
        console.print(
            f"[bold red]Error:[/bold red] {repo_path} is not a valid Git repository"
        )
        return 1

    # Get git log
    git_log = repository.get_commit_history(
        repo_path=repo_path,
        path=path,
        since=since,
        until=until,
        ignore_merges=True,
    )

    # Parse git log
    commits = parser.parse_git_log(git_log)

    # Filter by language if specified
    if language:
        commits = [
            commit
            for commit in commits
            if any(
                file_path.get("path", "").endswith(f".{language}")
                for file_path in commit.files
            )
        ]

    # Calculate author statistics
    author_stats = {}
    for commit in commits:
        author = commit.author
        if author not in author_stats:
            author_stats[author] = {
                "total_commits": 0,
                "total_lines_added": 0,
                "total_lines_deleted": 0,
                "first_commit_date": commit.date,
                "last_commit_date": commit.date,
            }

        author_stats[author]["total_commits"] += 1
        author_stats[author]["total_lines_added"] += commit.total_lines_added
        author_stats[author]["total_lines_deleted"] += commit.total_lines_deleted

        if commit.date < author_stats[author]["first_commit_date"]:
            author_stats[author]["first_commit_date"] = commit.date
        if commit.date > author_stats[author]["last_commit_date"]:
            author_stats[author]["last_commit_date"] = commit.date

    # Rank contributors
    ranking = rank_contributors(author_stats, recency_period_months=recency_period)

    if output_format == OutputFormat.JSON:
        # Prepare JSON output
        result = []
        for author, score, normalized_metrics in ranking:
            author_data = author_stats[author].copy()
            # Convert datetime objects to strings for JSON serialization
            if "first_commit_date" in author_data:
                author_data["first_commit_date"] = author_data[
                    "first_commit_date"
                ].isoformat()
            if "last_commit_date" in author_data:
                author_data["last_commit_date"] = author_data[
                    "last_commit_date"
                ].isoformat()

            result.append(
                {
                    "author": author,
                    "score": score,
                    "normalized_metrics": normalized_metrics,
                    "stats": author_data,
                }
            )

        console.print(json.dumps(result, indent=2))
    else:
        # Create table for text output
        table = create_stats_table()

        # Add data to table
        for i, (author, score, normalized_metrics) in enumerate(ranking, 1):
            stats = author_stats[author]

            # Calculate longevity in a human-readable format
            longevity = ""
            if "first_commit_date" in stats and "last_commit_date" in stats:
                days = (stats["last_commit_date"] - stats["first_commit_date"]).days
                longevity = format_longevity(days)

            # Calculate total lines
            total_lines = stats.get("total_lines_added", 0) + stats.get(
                "total_lines_deleted", 0
            )

            # Format recency as percentage
            recency_pct = f"{normalized_metrics.get('recency', 0) * 100:.0f}%"

            # Create score visualization
            score_bar = create_score_bar(score)

            # Apply rank styling
            rank_style = get_rank_style(i)
            rank_text = f"[{rank_style}]{i}[/{rank_style}]"

            table.add_row(
                rank_text,
                author,
                str(score_bar),
                str(stats.get("total_commits", 0)),
                str(total_lines),
                longevity,
                recency_pct,
            )

        # Print summary statistics
        console.print()
        console.print(f"[bold]Total Contributors:[/bold] {len(ranking)}")
        console.print(f"[bold]Total Commits:[/bold] {len(commits)}")

        if path:
            console.print(f"[bold]Path Filter:[/bold] {path}")
        if language:
            console.print(f"[bold]Language Filter:[/bold] {language}")

        console.print()
        console.print(table)

    return 0
