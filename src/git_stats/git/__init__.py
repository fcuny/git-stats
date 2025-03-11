"""
Git interaction package for git-stats.

This package provides functionality for interacting with Git repositories,
including running Git commands and parsing Git output.
"""

from git_stats.git.parser import (
    Commit,
    calculate_author_stats,
    calculate_file_stats,
    extract_commit_info,
    extract_file_changes,
    group_commits_by_author,
    group_commits_by_file,
    parse_git_log,
)
from git_stats.git.repository import (
    get_commit_history,
    get_current_branch,
    get_file_blame,
    get_file_history,
    get_file_type,
    run_git_command,
    validate_repo,
)

__all__ = [
    # Repository module
    "get_commit_history",
    "get_current_branch",
    "get_file_blame",
    "get_file_history",
    "get_file_type",
    "run_git_command",
    "validate_repo",
    # Parser module
    "Commit",
    "calculate_author_stats",
    "calculate_file_stats",
    "extract_commit_info",
    "extract_file_changes",
    "group_commits_by_author",
    "group_commits_by_file",
    "parse_git_log",
]
