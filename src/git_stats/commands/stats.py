"""
Stats command implementation for git-stats.

This module provides functionality to generate contribution statistics for a Git repository.
"""

import json
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from git_stats.config import OutputFormat
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
        console = Console()

    # Display command parameters
    console.print(
        Panel(
            f"[bold]Git Stats[/bold]\n\n"
            f"Repository: [cyan]{repo_path}[/cyan]\n"
            f"Recency period: [cyan]{recency_period} months[/cyan]\n"
            f"Output format: [cyan]{output_format.name.lower()}[/cyan]"
            + (f"\nPath filter: [cyan]{path}[/cyan]" if path else "")
            + (f"\nLanguage filter: [cyan]{language}[/cyan]" if language else "")
            + (f"\nSince: [cyan]{since}[/cyan]" if since else "")
            + (f"\nUntil: [cyan]{until}[/cyan]" if until else ""),
            title="Stats Command",
            expand=False,
        )
    )

    # Validate repository
    if not repository.validate_repo(repo_path):
        console.print(
            f"[bold red]Error:[/bold red] {repo_path} is not a valid Git repository"
        )
        return 1

    # Get commit history
    try:
        log_output = repository.get_commit_history(
            repo_path=repo_path,
            path=path,
            since=since,
            until=until,
            ignore_merges=True,
        )
    except Exception as e:
        console.print(
            f"[bold red]Error:[/bold red] Failed to get commit history: {str(e)}"
        )
        return 1

    # Parse commit history
    commits = parser.parse_git_log(log_output)

    # Filter by language if specified
    if language:
        filtered_commits = []
        for commit in commits:
            language_files = [
                file
                for file in commit.files
                if repository.get_file_type(repo_path, file["path"]) == language
            ]
            if language_files:
                # Create a new commit with only the filtered files
                filtered_commit = parser.Commit(
                    hash=commit.hash,
                    author_name=commit.author_name,
                    author_email=commit.author_email,
                    date=commit.date,
                    subject=commit.subject,
                    body=commit.body,
                    files=language_files,
                )
                filtered_commits.append(filtered_commit)
        commits = filtered_commits

    # Group commits by author
    author_commits = parser.group_commits_by_author(commits)

    # Calculate stats for each author
    author_stats = {}
    for author, author_commits_list in author_commits.items():
        author_stats[author] = parser.calculate_author_stats(commits, author)

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
        table = Table(title="Contribution Statistics")
        table.add_column("Rank", style="dim")
        table.add_column("Contributor", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Commits", justify="right")
        table.add_column("Lines", justify="right")
        table.add_column("Longevity", justify="right")
        table.add_column("Recency", justify="right")

        # Add data to table
        for i, (author, score, normalized_metrics) in enumerate(ranking, 1):
            stats = author_stats[author]

            # Calculate longevity in a human-readable format
            longevity = ""
            if "first_commit_date" in stats and "last_commit_date" in stats:
                days = (stats["last_commit_date"] - stats["first_commit_date"]).days
                years = days // 365
                months = (days % 365) // 30
                longevity = f"{years}y {months}m" if years > 0 else f"{months}m"

            # Calculate total lines
            total_lines = stats.get("total_lines_added", 0) + stats.get(
                "total_lines_deleted", 0
            )

            # Format recency as percentage
            recency_pct = f"{normalized_metrics.get('recency', 0) * 100:.0f}%"

            table.add_row(
                str(i),
                author,
                f"{score:.2f}",
                str(stats.get("total_commits", 0)),
                str(total_lines),
                longevity,
                recency_pct,
            )

        console.print(table)

    return 0
