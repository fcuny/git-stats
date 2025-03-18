#!/usr/bin/env python3
"""
Command-line interface for git-stats.

This module provides the main entry point for the git-stats command-line tool,
which analyzes Git repositories to generate statistics about contributions
and identify code experts for different parts of the codebase.
"""

import argparse
import os
import sys
from typing import List, Optional

from git_stats import __version__
from git_stats.commands import dris, stats
from git_stats.config import OutputFormat
from git_stats.formatting import create_console


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for git-stats."""
    parser = argparse.ArgumentParser(
        prog="git-stats",
        description="Analyze Git repositories to generate statistics and identify code experts",
        epilog="For more information and examples, visit: https://github.com/fcuny/git-stats",
    )

    # Add version information
    parser.add_argument(
        "--version", action="version", version=f"git-stats {__version__}"
    )

    # Global options
    parser.add_argument(
        "--repo-path",
        default=os.getcwd(),
        help="Path to the Git repository (default: current directory)",
    )
    parser.add_argument(
        "--recency-period",
        type=int,
        default=3,
        help="Define recency period in months (default: 3)",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Format for output (default: text, options: text, json)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Generate contribution statistics for the repository",
        description="Generate detailed contribution statistics for the repository, with options to filter by path, language, and date range.",
    )
    stats_parser.add_argument(
        "--path", help="Filter by specific directory or file path"
    )
    stats_parser.add_argument(
        "--language", help="Filter by specific language (go, python, etc.)"
    )
    stats_parser.add_argument(
        "--since", help="Start date for the analysis (YYYY-MM-DD)"
    )
    stats_parser.add_argument("--until", help="End date for the analysis (YYYY-MM-DD)")

    # DRIs command
    dris_parser = subparsers.add_parser(
        "dris",
        help="Identify experts for specific files",
        description="Identify Directly Responsible Individuals (experts) for specific files, useful for code reviews and knowledge sharing.",
    )
    dris_parser.add_argument("--files", help="Comma-separated list of files to analyze")
    dris_parser.add_argument(
        "--top", type=int, default=3, help="Number of experts to recommend (default: 3)"
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the git-stats command-line tool.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:] if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # Create console with rich formatting
    console = create_console()

    # Display welcome message
    console.print(
        f"[bold]Git-Stats v{__version__}[/bold] - Analyzing Git repositories",
        style="cyan",
    )
    console.print()

    # Convert output format string to enum
    output_format = OutputFormat.TEXT
    if args.output_format == "json":
        output_format = OutputFormat.JSON

    # Execute the appropriate command
    try:
        if args.command == "stats":
            console.print(
                "[bold]Generating contribution statistics...[/bold]", style="cyan"
            )
            return stats.execute(
                repo_path=args.repo_path,
                recency_period=args.recency_period,
                output_format=output_format,
                path=args.path,
                language=args.language,
                since=args.since,
                until=args.until,
                console=console,
            )
        elif args.command == "dris":
            console.print("[bold]Identifying code experts...[/bold]", style="cyan")
            return dris.execute(
                repo_path=args.repo_path,
                recency_period=args.recency_period,
                output_format=output_format,
                files=args.files.split(",") if args.files else None,
                top=args.top,
                console=console,
            )
        else:
            parser.print_help()
            return 0
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        console.print("[dim]For more help, run: git-stats --help[/dim]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
