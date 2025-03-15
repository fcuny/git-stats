"""
Tests for the Git log parser module.
"""

from pathlib import Path

import pytest

from git_stats.git.parser import (
    calculate_author_stats,
    calculate_file_stats,
    extract_commit_info,
    extract_file_changes,
    group_commits_by_author,
    group_commits_by_file,
    parse_git_log,
)


@pytest.fixture
def sample_log():
    """Load the sample Git log from the fixtures directory."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    with open(fixtures_dir / "git_log_sample.txt", "r") as f:
        return f.read()


class TestParseGitLog:
    """Tests for the parse_git_log function."""

    def test_parse_empty_log(self):
        """Test parsing an empty Git log."""
        commits = parse_git_log("")
        assert len(commits) == 0

    def test_parse_sample_log(self, sample_log):
        """Test parsing a sample Git log."""
        commits = parse_git_log(sample_log)
        assert len(commits) == 5

        # Check the first commit
        first_commit = commits[0]
        assert first_commit.hash == "abcdef1234567890abcdef1234567890abcdef12"
        assert first_commit.author_name == "Alice Developer"
        assert first_commit.author_email == "alice@example.com"
        assert first_commit.subject == "Add initial implementation of feature X"
        assert "Core functionality" in first_commit.body
        assert len(first_commit.files) == 3

        # Check the last commit
        last_commit = commits[-1]
        assert last_commit.hash == "ef1234567890abcdef1234567890abcdef123456"
        assert last_commit.author_name == "Bob Contributor"
        assert last_commit.author_email == "bob@example.com"
        assert last_commit.subject == "Refactor feature X for better maintainability"
        assert "Refactored the feature X implementation" in last_commit.body
        assert len(last_commit.files) == 4


class TestExtractCommitInfo:
    """Tests for the extract_commit_info function."""

    def test_extract_valid_commit(self):
        """Test extracting information from a valid commit."""
        commit_data = """abcdef1234567890abcdef1234567890abcdef12
Author: Alice Developer <alice@example.com>
Date: 2023-01-15T10:30:45+00:00

Add initial implementation of feature X

This commit adds the initial implementation of feature X,
which includes:
- Core functionality
- Basic tests
- Documentation

5\t0\tsrc/feature_x.py
10\t0\ttests/test_feature_x.py
3\t0\tdocs/feature_x.md"""

        commit = extract_commit_info(commit_data)
        assert commit is not None
        assert commit.hash == "abcdef1234567890abcdef1234567890abcdef12"
        assert commit.author_name == "Alice Developer"
        assert commit.author_email == "alice@example.com"
        assert commit.date.year == 2023
        assert commit.date.month == 1
        assert commit.date.day == 15
        assert commit.subject == "Add initial implementation of feature X"
        assert "Core functionality" in commit.body
        assert len(commit.files) == 3

    def test_extract_invalid_commit(self):
        """Test extracting information from an invalid commit."""
        # Not enough lines
        commit_data = """abcdef1234567890abcdef1234567890abcdef12
Author: Alice Developer <alice@example.com>"""

        commit = extract_commit_info(commit_data)
        assert commit is None


class TestExtractFileChanges:
    """Tests for the extract_file_changes function."""

    def test_extract_normal_files(self):
        """Test extracting normal file changes."""
        file_lines = [
            "5\t0\tsrc/feature_x.py",
            "10\t0\ttests/test_feature_x.py",
            "3\t0\tdocs/feature_x.md",
        ]

        files = extract_file_changes(file_lines)
        assert len(files) == 3

        assert files[0]["path"] == "src/feature_x.py"
        assert files[0]["lines_added"] == 5
        assert files[0]["lines_deleted"] == 0
        assert files[0]["is_renamed"] is False
        assert files[0]["is_binary"] is False

        assert files[1]["path"] == "tests/test_feature_x.py"
        assert files[1]["lines_added"] == 10
        assert files[1]["lines_deleted"] == 0
        assert files[1]["is_renamed"] is False
        assert files[1]["is_binary"] is False

        assert files[2]["path"] == "docs/feature_x.md"
        assert files[2]["lines_added"] == 3
        assert files[2]["lines_deleted"] == 0
        assert files[2]["is_renamed"] is False
        assert files[2]["is_binary"] is False

    def test_extract_renamed_files(self):
        """Test extracting renamed file changes."""
        file_lines = [
            "-\t-\tsrc/feature_x.py => src/features/feature_x.py",
        ]

        files = extract_file_changes(file_lines)
        assert len(files) == 1

        assert files[0]["path"] == "src/features/feature_x.py"
        assert files[0]["old_path"] == "src/feature_x.py"
        assert files[0]["lines_added"] == 0
        assert files[0]["lines_deleted"] == 0
        assert files[0]["is_renamed"] is True
        assert files[0]["is_binary"] is True

    def test_extract_binary_files(self):
        """Test extracting binary file changes."""
        file_lines = [
            "-\t-\tsrc/image.png",
        ]

        files = extract_file_changes(file_lines)
        assert len(files) == 1

        assert files[0]["path"] == "src/image.png"
        assert files[0]["lines_added"] == 0
        assert files[0]["lines_deleted"] == 0
        assert files[0]["is_renamed"] is False
        assert files[0]["is_binary"] is True


class TestGroupCommits:
    """Tests for the grouping functions."""

    def test_group_by_author(self, sample_log):
        """Test grouping commits by author."""
        commits = parse_git_log(sample_log)
        grouped = group_commits_by_author(commits)

        assert len(grouped) == 3
        assert "Alice Developer <alice@example.com>" in grouped
        assert "Bob Contributor <bob@example.com>" in grouped
        assert "Charlie Reviewer <charlie@example.com>" in grouped

        assert len(grouped["Alice Developer <alice@example.com>"]) == 2
        assert len(grouped["Bob Contributor <bob@example.com>"]) == 2
        assert len(grouped["Charlie Reviewer <charlie@example.com>"]) == 1

    def test_group_by_file(self, sample_log):
        """Test grouping commits by file."""
        commits = parse_git_log(sample_log)
        grouped = group_commits_by_file(commits)

        # The sample log contains 8 unique files:
        # 1. src/feature_x.py
        # 2. tests/test_feature_x.py
        # 3. docs/feature_x.md
        # 4. src/utils.py
        # 5. src/feature_x_extension.py
        # 6. tests/test_feature_x_extension.py
        # 7. src/features/feature_x.py (renamed from src/feature_x.py)
        # 8. src/features/feature_x_extension.py (renamed from src/feature_x_extension.py)
        assert len(grouped) == 8

        assert "src/feature_x.py" in grouped
        assert "tests/test_feature_x.py" in grouped
        assert "docs/feature_x.md" in grouped
        assert "src/utils.py" in grouped
        assert "src/feature_x_extension.py" in grouped
        assert "tests/test_feature_x_extension.py" in grouped
        assert "src/features/feature_x.py" in grouped
        assert "src/features/feature_x_extension.py" in grouped

        # src/feature_x.py appears in all 5 commits
        assert len(grouped["src/feature_x.py"]) == 5


class TestCalculateStats:
    """Tests for the statistics calculation functions."""

    def test_calculate_file_stats(self, sample_log):
        """Test calculating statistics for a file."""
        commits = parse_git_log(sample_log)
        stats = calculate_file_stats(commits, "src/feature_x.py")

        assert stats["path"] == "src/feature_x.py"
        assert len(stats["authors"]) == 3
        assert "Alice Developer <alice@example.com>" in stats["authors"]
        assert "Bob Contributor <bob@example.com>" in stats["authors"]
        assert "Charlie Reviewer <charlie@example.com>" in stats["authors"]
        assert (
            stats["total_commits"] == 5
        )  # Updated to match the actual number in the sample log

        # Calculate the total lines added from the sample log:
        # 1. First commit by Alice: 5 lines added
        # 2. Second commit by Bob: 15 lines added
        # 3. Third commit by Charlie: 20 lines added
        # 4. Fourth commit by Alice: 30 lines added
        # 5. Fifth commit by Bob: 25 lines added
        # Total: 5 + 15 + 20 + 30 + 25 = 95 lines added
        assert stats["total_lines_added"] == 95

        # Calculate the total lines deleted from the sample log:
        # 1. First commit by Alice: 0 lines deleted
        # 2. Second commit by Bob: 5 lines deleted
        # 3. Third commit by Charlie: 12 lines deleted
        # 4. Fourth commit by Alice: 8 lines deleted
        # 5. Fifth commit by Bob: 20 lines deleted
        # Total: 0 + 5 + 12 + 8 + 20 = 45 lines deleted
        assert stats["total_lines_deleted"] == 45

        assert stats["first_commit_date"] is not None
        assert stats["last_commit_date"] is not None

    def test_calculate_author_stats(self, sample_log):
        """Test calculating statistics for an author."""
        commits = parse_git_log(sample_log)
        stats = calculate_author_stats(commits, "Alice Developer <alice@example.com>")

        assert stats["author"] == "Alice Developer <alice@example.com>"
        assert len(stats["files"]) == 5
        assert "src/feature_x.py" in stats["files"]
        assert "tests/test_feature_x.py" in stats["files"]
        assert "docs/feature_x.md" in stats["files"]
        assert "src/feature_x_extension.py" in stats["files"]
        assert "tests/test_feature_x_extension.py" in stats["files"]
        assert stats["total_commits"] == 2
        assert stats["total_lines_added"] == 75
        assert stats["total_lines_deleted"] == 8
        assert stats["first_commit_date"] is not None
        assert stats["last_commit_date"] is not None
