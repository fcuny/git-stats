"""
DRIs (Directly Responsible Individuals) command implementation for git-stats.

This module provides functionality to identify experts for specific files in a Git repository.
"""

import json
import os
from typing import Dict, List, Optional, Tuple

from rich.console import Console

from git_stats.config import OutputFormat
from git_stats.formatting import (
    create_command_panel,
    create_console,
    create_experts_table,
    create_overall_experts_table,
    create_score_bar,
    format_expertise_level,
    get_expertise_level,
)
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
    Get the experts for a specific file.

    Args:
        repo_path: Path to the Git repository
        file_path: Path to the file
        recency_period: Recency period in months

    Returns:
        List of tuples (author, score, normalized_metrics)
    """
    try:
        # Get git log for the file
        git_log = repository.get_file_history(
            repo_path=repo_path,
            file_path=file_path,
            ignore_merges=True,
        )

        # Parse git log
        commits = parser.parse_git_log(git_log)

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

        return ranking
    except Exception:
        return []


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
        console = create_console()

    # Display command parameters
    parameters = {
        "repository": repo_path,
        "recency_period": f"{recency_period} months",
        "output_format": output_format.name.lower(),
        "top_experts": top,
        "files": files,
    }
    console.print(create_command_panel("DRIs Command", "Git DRIs", parameters))

    # Validate repository
    if not repository.validate_repo(repo_path):
        console.print(
            f"[bold red]Error:[/bold red] {repo_path} is not a valid Git repository"
        )
        return 1

    # If no files specified, use current diff
    if not files:
        console.print("[bold blue]Detecting changed files...[/bold blue]")
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
        if os.path.exists(full_path) and os.path.isfile(full_path):
            valid_files.append(file_path)
        else:
            console.print(f"[yellow]Warning:[/yellow] File not found: {file_path}")

    if not valid_files:
        console.print("[bold red]Error:[/bold red] No valid files to analyze")
        return 1

    # Get experts for each file
    console.print(f"[bold blue]Analyzing {len(valid_files)} files...[/bold blue]")
    file_experts = {}
    overall_scores = {}

    for file_path in valid_files:
        console.print(f"[blue]Analyzing: {file_path}[/blue]")
        # Get experts for the file
        experts = get_file_experts(repo_path, file_path, recency_period)
        file_experts[file_path] = experts[:top]  # Limit to top N experts

        # Update overall scores
        for author, score, _ in experts:
            if author in overall_scores:
                overall_scores[author] += score
            else:
                overall_scores[author] = score

    # Calculate overall experts
    if overall_scores:
        overall_experts = [
            (author, score / len(valid_files))
            for author, score in overall_scores.items()
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
                    "expertise_level": get_expertise_level(score).label,
                }
                for author, score in overall_experts
            ],
        }

        for file_path, experts in file_experts.items():
            result["files"][file_path] = [
                {
                    "author": author,
                    "score": score,
                    "expertise_level": get_expertise_level(score).label,
                    "normalized_metrics": normalized_metrics,
                }
                for author, score, normalized_metrics in experts
            ]

        console.print(json.dumps(result, indent=2))
    else:
        # Group files by directory for better organization
        file_groups = {}
        for file_path, experts in file_experts.items():
            directory = os.path.dirname(file_path) or "."
            if directory not in file_groups:
                file_groups[directory] = {}
            file_groups[directory][file_path] = experts

        # Create tables for each directory
        for directory, files in file_groups.items():
            # Create table for file experts
            table = create_experts_table(f"File Experts - {directory}")

            for file_path, experts in files.items():
                # Get just the filename without the directory
                filename = os.path.basename(file_path)

                if not experts:
                    table.add_row(filename, "No experts found", "", "")
                    continue

                for i, (author, score, _) in enumerate(experts):
                    # Create score visualization
                    score_bar = create_score_bar(score)

                    # Format expertise level
                    expertise_text = format_expertise_level(score)

                    if i == 0:
                        table.add_row(filename, author, str(score_bar), expertise_text)
                    else:
                        table.add_row("", author, str(score_bar), expertise_text)

            console.print(table)
            console.print()

        # Create table for overall experts
        if overall_experts:
            overall_table = create_overall_experts_table()

            for author, score in overall_experts:
                # Create score visualization
                score_bar = create_score_bar(score)

                # Format expertise level
                expertise_text = format_expertise_level(score)

                overall_table.add_row(author, str(score_bar), expertise_text)

            console.print(overall_table)

        # Print summary
        console.print()
        console.print(f"[bold]Total Files Analyzed:[/bold] {len(valid_files)}")
        console.print(f"[bold]Total Experts Shown:[/bold] {top}")

    return 0
