"""
Git log parser module.

This module provides functions for parsing Git log output and extracting
relevant information about commits, authors, and file changes.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Union


class Commit:
    """Class representing a Git commit."""

    def __init__(
        self,
        hash: str,
        author_name: str,
        author_email: str,
        date: datetime,
        subject: str,
        body: str,
        files: List[Dict[str, Union[str, int]]],
    ):
        """
        Initialize a Commit object.

        Args:
            hash: Commit hash
            author_name: Author name
            author_email: Author email
            date: Commit date
            subject: Commit subject
            body: Commit body
            files: List of files changed in the commit
        """
        self.hash = hash
        self.author_name = author_name
        self.author_email = author_email
        self.date = date
        self.subject = subject
        self.body = body
        self.files = files

    def __repr__(self) -> str:
        """Return a string representation of the commit."""
        return f"Commit({self.hash[:7]}, {self.author_name}, {self.date.isoformat()})"

    @property
    def author(self) -> str:
        """Return the author name and email."""
        return f"{self.author_name} <{self.author_email}>"

    @property
    def total_lines_added(self) -> int:
        """Return the total number of lines added in the commit."""
        return sum(file.get("lines_added", 0) for file in self.files)

    @property
    def total_lines_deleted(self) -> int:
        """Return the total number of lines deleted in the commit."""
        return sum(file.get("lines_deleted", 0) for file in self.files)

    @property
    def total_files_changed(self) -> int:
        """Return the total number of files changed in the commit."""
        return len(self.files)


def parse_git_log(log_output: str) -> List[Commit]:
    """
    Parse Git log output and convert it to a list of Commit objects.

    Args:
        log_output: Git log output from get_commit_history

    Returns:
        List of Commit objects
    """
    if not log_output.strip():
        return []

    commits = []

    # Split the log output by commit
    # Git log with --numstat format has a blank line followed by numstat output
    # between commits, so we need to find the commit boundaries
    commit_pattern = re.compile(r"^[0-9a-f]{40}$", re.MULTILINE)
    commit_positions = [m.start() for m in commit_pattern.finditer(log_output)]

    # Add the end of the string as the last position
    commit_positions.append(len(log_output))

    # Extract each commit
    for i in range(len(commit_positions) - 1):
        start = commit_positions[i]
        end = commit_positions[i + 1]
        commit_data = log_output[start:end].strip()

        commit = extract_commit_info(commit_data)
        if commit:
            commits.append(commit)

    return commits


def extract_commit_info(commit_data: str) -> Optional[Commit]:
    """
    Extract commit information from a Git log entry.

    Args:
        commit_data: Git log entry for a single commit

    Returns:
        Commit object or None if parsing fails
    """
    lines = commit_data.strip().split("\n")
    if len(lines) < 4:
        return None

    # Extract commit metadata
    hash_line = lines[0]
    if not hash_line:
        return None

    hash = hash_line.strip()

    # Parse author information
    author_line = None
    for line in lines[1:4]:  # Look in the first few lines
        if line.startswith("Author:"):
            author_line = line[7:].strip()  # Remove "Author: " prefix
            break

    if not author_line:
        # Fallback to old format or use placeholder
        author_name = lines[1] if len(lines) > 1 else "Unknown"
        author_email = lines[2] if len(lines) > 2 else "unknown@example.com"
    else:
        # Parse author line in format "Name <email>"
        match = re.match(r"^(.*?)\s*<([^>]+)>$", author_line)
        if match:
            author_name = match.group(1).strip()
            author_email = match.group(2).strip()
        else:
            # If format doesn't match, use the whole line as name
            author_name = author_line
            author_email = "unknown@example.com"

    # Parse date
    date_line = None
    for line in lines[1:6]:  # Look in the first few lines
        if line.startswith("Date:"):
            date_line = line[5:].strip()  # Remove "Date: " prefix
            break

    try:
        if date_line:
            # Try various date formats
            try:
                date = datetime.fromisoformat(date_line)
            except ValueError:
                try:
                    # Git's default format: "Thu Mar 7 12:34:56 2024 -0700"
                    date = datetime.strptime(date_line, "%a %b %d %H:%M:%S %Y %z")
                except ValueError:
                    try:
                        # Simple format
                        date = datetime.strptime(date_line, "%Y-%m-%d %H:%M:%S %z")
                    except ValueError:
                        date = datetime.now()
        else:
            # Fallback to old format or use current time
            try:
                date = (
                    datetime.fromisoformat(lines[3])
                    if len(lines) > 3
                    else datetime.now()
                )
            except ValueError:
                date = datetime.now()
    except Exception:
        # If all parsing fails, use current time
        date = datetime.now()

    # Find subject and body
    subject = ""
    body = ""
    body_start = 0

    # Find the first non-empty line after the metadata
    metadata_end = 0
    for i, line in enumerate(lines):
        if line.startswith("Author:") or line.startswith("Date:"):
            metadata_end = i + 1

    # Skip empty lines after metadata
    while metadata_end < len(lines) and not lines[metadata_end].strip():
        metadata_end += 1

    # The next non-empty line is the subject
    if metadata_end < len(lines):
        subject = lines[metadata_end].strip()
        body_start = metadata_end + 1

    # Find where the file stats begin
    body_end = body_start
    while body_end < len(lines):
        # Look for the start of numstat output (lines with format: <added> <deleted> <file>)
        if re.match(r"^\d+\s+\d+\s+\S", lines[body_end].strip()):
            break
        body_end += 1

    if body_start < body_end:
        body = "\n".join(lines[body_start:body_end]).strip()

    # Extract file changes
    files = extract_file_changes(lines[body_end:])

    return Commit(
        hash=hash,
        author_name=author_name,
        author_email=author_email,
        date=date,
        subject=subject,
        body=body,
        files=files,
    )


def extract_file_changes(file_lines: List[str]) -> List[Dict[str, Union[str, int]]]:
    """
    Extract file change information from Git log numstat output.

    Args:
        file_lines: Lines containing file change information

    Returns:
        List of dictionaries with file change information
    """
    files = []

    # Skip empty lines at the beginning
    start_idx = 0
    while start_idx < len(file_lines) and not file_lines[start_idx].strip():
        start_idx += 1

    for line in file_lines[start_idx:]:
        line = line.strip()
        if not line:
            continue

        # Parse numstat line: <added> <deleted> <file>
        match = re.match(r"^(\d+|-)\s+(\d+|-)\s+(.+)$", line)
        if not match:
            # Skip lines that don't match the numstat format
            continue

        added_str, deleted_str, file_path = match.groups()

        # Handle binary files (shown as "-" in numstat)
        lines_added = 0 if added_str == "-" else int(added_str)
        lines_deleted = 0 if deleted_str == "-" else int(deleted_str)

        # Handle renamed files
        if " => " in file_path:
            old_path, new_path = file_path.split(" => ")
            file_path = new_path.strip()
            old_path = old_path.strip()

            files.append(
                {
                    "path": file_path,
                    "old_path": old_path,
                    "lines_added": lines_added,
                    "lines_deleted": lines_deleted,
                    "is_renamed": True,
                    "is_binary": added_str == "-" and deleted_str == "-",
                }
            )
        else:
            files.append(
                {
                    "path": file_path,
                    "lines_added": lines_added,
                    "lines_deleted": lines_deleted,
                    "is_renamed": False,
                    "is_binary": added_str == "-" and deleted_str == "-",
                }
            )

    return files


def group_commits_by_author(commits: List[Commit]) -> Dict[str, List[Commit]]:
    """
    Group commits by author.

    Args:
        commits: List of Commit objects

    Returns:
        Dictionary mapping author strings to lists of commits
    """
    result = {}

    for commit in commits:
        author = commit.author
        if author not in result:
            result[author] = []
        result[author].append(commit)

    return result


def group_commits_by_file(commits: List[Commit]) -> Dict[str, List[Commit]]:
    """
    Group commits by file path.

    Args:
        commits: List of Commit objects

    Returns:
        Dictionary mapping file paths to lists of commits
    """
    result = {}

    for commit in commits:
        for file in commit.files:
            path = file["path"]
            if path not in result:
                result[path] = []
            result[path].append(commit)

    return result


def calculate_file_stats(
    commits: List[Commit], file_path: str
) -> Dict[str, Union[int, List[str]]]:
    """
    Calculate statistics for a specific file.

    Args:
        commits: List of Commit objects
        file_path: Path to the file

    Returns:
        Dictionary with file statistics
    """
    authors = set()
    total_commits = 0
    total_lines_added = 0
    total_lines_deleted = 0
    first_commit_date = None
    last_commit_date = None

    for commit in commits:
        for file in commit.files:
            if file["path"] == file_path:
                authors.add(commit.author)
                total_commits += 1
                total_lines_added += file.get("lines_added", 0)
                total_lines_deleted += file.get("lines_deleted", 0)

                if first_commit_date is None or commit.date < first_commit_date:
                    first_commit_date = commit.date

                if last_commit_date is None or commit.date > last_commit_date:
                    last_commit_date = commit.date

    return {
        "path": file_path,
        "authors": list(authors),
        "total_commits": total_commits,
        "total_lines_added": total_lines_added,
        "total_lines_deleted": total_lines_deleted,
        "first_commit_date": first_commit_date,
        "last_commit_date": last_commit_date,
    }


def calculate_author_stats(
    commits: List[Commit], author: str
) -> Dict[str, Union[int, List[str]]]:
    """
    Calculate statistics for a specific author.

    Args:
        commits: List of Commit objects
        author: Author string (name <email>)

    Returns:
        Dictionary with author statistics
    """
    files = set()
    total_commits = 0
    total_lines_added = 0
    total_lines_deleted = 0
    first_commit_date = None
    last_commit_date = None

    for commit in commits:
        if commit.author == author:
            total_commits += 1
            total_lines_added += commit.total_lines_added
            total_lines_deleted += commit.total_lines_deleted

            for file in commit.files:
                files.add(file["path"])

            if first_commit_date is None or commit.date < first_commit_date:
                first_commit_date = commit.date

            if last_commit_date is None or commit.date > last_commit_date:
                last_commit_date = commit.date

    return {
        "author": author,
        "files": list(files),
        "total_commits": total_commits,
        "total_lines_added": total_lines_added,
        "total_lines_deleted": total_lines_deleted,
        "first_commit_date": first_commit_date,
        "last_commit_date": last_commit_date,
    }
