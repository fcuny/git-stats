"""
DRIs (Directly Responsible Individuals) command implementation for git-stats.

This module provides functionality to identify experts for specific files in a Git repository.
"""

import json
import os
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from git_stats.config import OutputFormat
from git_stats.git import repository, parser
from git_stats.scoring import rank_contributors


def get_current_diff_files(repo_path: str) -> List[str]:
    """
    Get the list of files in the current diff.

    Args:
        repo_path: Path to the Git repository

    Returns:
        List of file paths in the current diff
    """
    try:
        # Get the list of modified files in the working directory
        diff_output = repository.run_git_command(repo_path, "diff", "--name-only")
        staged_output = repository.run_git_command(
            repo_path, "diff", "--staged", "--name-only"
        )

        # Combine and deduplicate the lists
        files = set(diff_output.splitlines() + staged_output.splitlines())
        return [f for f in files if f.strip()]
    except Exception:
        return []


def get_file_experts(
    repo_path: str, file_path: str, recency_period: int
) -> List[Tuple[str, float, Dict[str, float]]]:
    """
    Get experts for a specific file.

    Args:
        repo_path: Path to the Git repository
        file_path: Path to the file
        recency_period: Recency period in months

    Returns:
        List of tuples (contributor, score, normalized_metrics) sorted by score
    """
    try:
        # Get file history
        log_output = repository.get_file_history(
            repo_path=repo_path,
            file_path=file_path,
            ignore_merges=True,
        )

        # Parse file history
        commits = parser.parse_git_log(log_output)

        # Group commits by author
        author_commits = parser.group_commits_by_author(commits)

        # Calculate stats for each author
        author_stats = {}
        for author, author_commits_list in author_commits.items():
            author_stats[author] = parser.calculate_author_stats(commits, author)

        # Rank contributors
        ranking = rank_contributors(author_stats, recency_period_months=recency_period)

        return ranking
    except Exception:
        return []


def determine_expertise_level(score: float) -> str:
    """
    Determine expertise level based on score.

    Args:
        score: Contributor score

    Returns:
        Expertise level (High, Medium, Low)
    """
    if score >= 0.7:
        return "High"
    elif score >= 0.4:
        return "Medium"
    else:
        return "Low"


def execute(
    repo_path: str,
    recency_period: int,
    output_format: OutputFormat,
    files: Optional[List[str]] = None,
    top: int = 3,
    console: Optional[Console] = None,
) -> int:
    """
    Execute the dris command to identify experts for specific files.

    Args:
        repo_path: Path to the Git repository
        recency_period: Recency period in months
        output_format: Format for output (text or json)
        files: List of files to analyze
        top: Number of experts to recommend
        console: Rich console instance for output

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if console is None:
        console = Console()

    # Display command parameters
    console.print(
        Panel(
            f"[bold]Git DRIs[/bold]\n\n"
            f"Repository: [cyan]{repo_path}[/cyan]\n"
            f"Recency period: [cyan]{recency_period} months[/cyan]\n"
            f"Output format: [cyan]{output_format.name.lower()}[/cyan]\n"
            f"Top experts: [cyan]{top}[/cyan]"
            + (f"\nFiles: [cyan]{', '.join(files)}[/cyan]" if files else ""),
            title="DRIs Command",
            expand=False,
        )
    )

    # Validate repository
    if not repository.validate_repo(repo_path):
        console.print(
            f"[bold red]Error:[/bold red] {repo_path} is not a valid Git repository"
        )
        return 1

    # If no files specified, use current diff
    if not files:
        files = get_current_diff_files(repo_path)
        if not files:
            console.print(
                "[yellow]Warning:[/yellow] No files specified and no changes detected"
            )
            return 0

    # Filter out non-existent files
    valid_files = []
    for file_path in files:
        full_path = os.path.join(repo_path, file_path)
        if os.path.exists(full_path) and not os.path.isdir(full_path):
            valid_files.append(file_path)
        else:
            console.print(f"[yellow]Warning:[/yellow] File not found: {file_path}")

    if not valid_files:
        console.print("[bold red]Error:[/bold red] No valid files to analyze")
        return 1

    # Get experts for each file
    file_experts = {}
    for file_path in valid_files:
        experts = get_file_experts(repo_path, file_path, recency_period)
        file_experts[file_path] = experts[:top]  # Limit to top N experts

    # Calculate overall experts across all files
    overall_scores = {}
    for file_path, experts in file_experts.items():
        for author, score, _ in experts:
            if author not in overall_scores:
                overall_scores[author] = 0
            overall_scores[author] += score

    # Normalize overall scores
    if overall_scores:
        max_score = max(overall_scores.values())
        overall_experts = [
            (author, score / max_score) for author, score in overall_scores.items()
        ]
        overall_experts.sort(key=lambda x: x[1], reverse=True)
        overall_experts = overall_experts[:top]
    else:
        overall_experts = []

    if output_format == OutputFormat.JSON:
        # Prepare JSON output
        result = {
            "files": {},
            "overall": [
                {
                    "author": author,
                    "score": score,
                    "expertise_level": determine_expertise_level(score),
                }
                for author, score in overall_experts
            ],
        }

        for file_path, experts in file_experts.items():
            result["files"][file_path] = [
                {
                    "author": author,
                    "score": score,
                    "expertise_level": determine_expertise_level(score),
                    "normalized_metrics": normalized_metrics,
                }
                for author, score, normalized_metrics in experts
            ]

        console.print(json.dumps(result, indent=2))
    else:
        # Create table for file experts
        table = Table(title="File Experts")
        table.add_column("File", style="cyan")
        table.add_column("Expert", style="magenta")
        table.add_column("Score", justify="right")
        table.add_column("Expertise Level", justify="center")

        # Add data to table
        for file_path, experts in file_experts.items():
            if not experts:
                table.add_row(file_path, "No experts found", "", "")
                continue

            for i, (author, score, _) in enumerate(experts):
                expertise_level = determine_expertise_level(score)
                if i == 0:
                    table.add_row(file_path, author, f"{score:.2f}", expertise_level)
                else:
                    table.add_row("", author, f"{score:.2f}", expertise_level)

        console.print(table)

        # Create table for overall experts
        if overall_experts:
            overall_table = Table(title="Overall Experts")
            overall_table.add_column("Expert", style="magenta")
            overall_table.add_column("Score", justify="right")
            overall_table.add_column("Expertise Level", justify="center")

            for author, score in overall_experts:
                expertise_level = determine_expertise_level(score)
                overall_table.add_row(author, f"{score:.2f}", expertise_level)

            console.print("\n")
            console.print(overall_table)

    return 0
