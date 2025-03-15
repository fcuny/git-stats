"""
Git repository interaction module.

This module provides functions for interacting with Git repositories,
including validating repositories, running Git commands, and retrieving commit history.
"""

import os
import subprocess
from datetime import datetime
from typing import Optional, Union


def validate_repo(repo_path: str) -> bool:
    """
    Check if the given path is a valid Git repository.

    Args:
        repo_path: Path to the Git repository

    Returns:
        True if the path is a valid Git repository, False otherwise
    """
    if not os.path.isdir(repo_path):
        return False

    try:
        # Check if .git directory exists
        git_dir = os.path.join(repo_path, ".git")
        if os.path.isdir(git_dir):
            return True

        # If .git is not a directory, check if it's a file (submodule case)
        if os.path.isfile(git_dir):
            return True

        # As a final check, run git rev-parse --is-inside-work-tree
        result = run_git_command(repo_path, "rev-parse", "--is-inside-work-tree")
        return result.strip().lower() == "true"
    except Exception:
        return False


def run_git_command(repo_path: str, *args: str, capture_stderr: bool = False) -> str:
    """
    Execute a Git command in the specified repository.

    Args:
        repo_path: Path to the Git repository
        *args: Git command arguments
        capture_stderr: Whether to capture stderr output

    Returns:
        Command output as a string

    Raises:
        subprocess.CalledProcessError: If the Git command fails
        FileNotFoundError: If Git is not installed or not in PATH
    """
    cmd = ["git", "-C", repo_path] + list(args)

    stderr = subprocess.PIPE if capture_stderr else subprocess.STDOUT

    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_message = e.stderr if capture_stderr and e.stderr else e.stdout
        raise subprocess.CalledProcessError(
            e.returncode,
            e.cmd,
            output=e.output,
            stderr=f"Git command failed: {error_message}",
        )


def get_commit_history(
    repo_path: str,
    path: Optional[str] = None,
    since: Optional[Union[str, datetime]] = None,
    until: Optional[Union[str, datetime]] = None,
    ignore_merges: bool = True,
    max_count: Optional[int] = None,
) -> str:
    """
    Get the commit history for a Git repository.

    Args:
        repo_path: Path to the Git repository
        path: Filter by specific directory or file path
        since: Start date for the analysis (ISO format string or datetime)
        until: End date for the analysis (ISO format string or datetime)
        ignore_merges: Whether to ignore merge commits
        max_count: Maximum number of commits to retrieve

    Returns:
        Git log output as a string

    Raises:
        subprocess.CalledProcessError: If the Git command fails
        FileNotFoundError: If Git is not installed or not in PATH
    """
    # Validate repository
    if not validate_repo(repo_path):
        raise ValueError(f"Invalid Git repository: {repo_path}")

    # Build the git log command
    cmd_args = [
        "log",
        "--numstat",
        "--date=iso-strict",
        "--pretty=format:%H%nAuthor: %an <%ae>%nDate: %ad%n%n%s%n%b%n",
    ]

    # Add date range filters
    if since:
        if isinstance(since, datetime):
            since = since.isoformat()
        cmd_args.extend(["--since", since])

    if until:
        if isinstance(until, datetime):
            until = until.isoformat()
        cmd_args.extend(["--until", until])

    # Ignore merge commits if requested
    if ignore_merges:
        cmd_args.append("--no-merges")

    # Limit the number of commits if requested
    if max_count:
        cmd_args.extend(["--max-count", str(max_count)])

    # Add path filter if specified
    if path:
        # Make sure path is relative to repo_path
        if os.path.isabs(path):
            if not path.startswith(repo_path):
                raise ValueError(f"Path {path} is not within repository {repo_path}")
            path = os.path.relpath(path, repo_path)

        cmd_args.append("--")
        cmd_args.append(path)

    # Run the git log command
    return run_git_command(repo_path, *cmd_args)


def get_current_branch(repo_path: str) -> str:
    """
    Get the name of the current branch in the Git repository.

    Args:
        repo_path: Path to the Git repository

    Returns:
        Name of the current branch

    Raises:
        subprocess.CalledProcessError: If the Git command fails
        FileNotFoundError: If Git is not installed or not in PATH
    """
    # Validate repository
    if not validate_repo(repo_path):
        raise ValueError(f"Invalid Git repository: {repo_path}")

    # Run git branch --show-current
    return run_git_command(repo_path, "branch", "--show-current").strip()


def get_file_history(
    repo_path: str,
    file_path: str,
    since: Optional[Union[str, datetime]] = None,
    until: Optional[Union[str, datetime]] = None,
    ignore_merges: bool = True,
) -> str:
    """
    Get the commit history for a specific file in a Git repository.

    Args:
        repo_path: Path to the Git repository
        file_path: Path to the file, relative to the repository root
        since: Start date for the analysis (ISO format string or datetime)
        until: End date for the analysis (ISO format string or datetime)
        ignore_merges: Whether to ignore merge commits

    Returns:
        Git log output as a string

    Raises:
        subprocess.CalledProcessError: If the Git command fails
        FileNotFoundError: If Git is not installed or not in PATH
        ValueError: If the file is not in the repository
    """
    # Validate repository
    if not validate_repo(repo_path):
        raise ValueError(f"Invalid Git repository: {repo_path}")

    # Make sure file_path is relative to repo_path
    if os.path.isabs(file_path):
        if not file_path.startswith(repo_path):
            raise ValueError(f"File {file_path} is not within repository {repo_path}")
        file_path = os.path.relpath(file_path, repo_path)

    # Check if the file exists in the repository
    full_path = os.path.join(repo_path, file_path)
    if not os.path.exists(full_path):
        raise ValueError(f"File {file_path} does not exist in repository {repo_path}")

    # Get the commit history for the file
    return get_commit_history(
        repo_path=repo_path,
        path=file_path,
        since=since,
        until=until,
        ignore_merges=ignore_merges,
    )


def get_file_blame(repo_path: str, file_path: str) -> str:
    """
    Get the blame information for a specific file in a Git repository.

    Args:
        repo_path: Path to the Git repository
        file_path: Path to the file, relative to the repository root

    Returns:
        Git blame output as a string

    Raises:
        subprocess.CalledProcessError: If the Git command fails
        FileNotFoundError: If Git is not installed or not in PATH
        ValueError: If the file is not in the repository
    """
    # Validate repository
    if not validate_repo(repo_path):
        raise ValueError(f"Invalid Git repository: {repo_path}")

    # Make sure file_path is relative to repo_path
    if os.path.isabs(file_path):
        if not file_path.startswith(repo_path):
            raise ValueError(f"File {file_path} is not within repository {repo_path}")
        file_path = os.path.relpath(file_path, repo_path)

    # Check if the file exists in the repository
    full_path = os.path.join(repo_path, file_path)
    if not os.path.exists(full_path):
        raise ValueError(f"File {file_path} does not exist in repository {repo_path}")

    # Run git blame
    return run_git_command(repo_path, "blame", "--line-porcelain", file_path)


def get_file_type(repo_path: str, file_path: str) -> str:
    """
    Determine the type of a file in a Git repository.

    Args:
        repo_path: Path to the Git repository
        file_path: Path to the file, relative to the repository root

    Returns:
        File type as a string (e.g., "python", "go", "text", "binary")

    Raises:
        ValueError: If the file is not in the repository
    """
    # Validate repository
    if not validate_repo(repo_path):
        raise ValueError(f"Invalid Git repository: {repo_path}")

    # Make sure file_path is relative to repo_path
    if os.path.isabs(file_path):
        if not file_path.startswith(repo_path):
            raise ValueError(f"File {file_path} is not within repository {repo_path}")
        file_path = os.path.relpath(file_path, repo_path)

    # Check if the file exists in the repository
    full_path = os.path.join(repo_path, file_path)
    if not os.path.exists(full_path):
        raise ValueError(f"File {file_path} does not exist in repository {repo_path}")

    # Get the file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Map extensions to file types
    if ext in (".py", ".pyi", ".pyx"):
        return "python"
    elif ext in (".go", ".mod"):
        return "go"
    elif ext in (".c", ".cpp", ".h", ".hpp"):
        return "c"
    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        return "javascript"
    elif ext in (".java", ".kt", ".scala"):
        return "java"
    elif ext in (".rb", ".rake"):
        return "ruby"
    elif ext in (".rs",):
        return "rust"
    elif ext in (".sh", ".bash", ".zsh", ".fish"):
        return "shell"
    elif ext in (".md", ".rst", ".txt"):
        return "text"
    elif ext in (".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"):
        return "config"
    elif ext in (".html", ".htm", ".css", ".scss", ".sass"):
        return "web"
    elif ext in (".sql",):
        return "sql"
    elif ext in (".xml",):
        return "xml"

    # Check if the file is binary
    try:
        with open(full_path, "rb") as f:
            chunk = f.read(1024)
            if b"\0" in chunk:
                return "binary"
    except Exception:
        pass

    # Default to text
    return "text"
