"""
Integration tests for the git-stats package.
"""

import os
import subprocess
from unittest import mock

import pytest

from git_stats.git import (
    Commit,
    get_commit_history,
    parse_git_log,
    validate_repo,
)


class TestGitIntegration:
    """Integration tests for the Git repository and parser modules."""

    @mock.patch("git_stats.git.repository.validate_repo")
    @mock.patch("git_stats.git.repository.run_git_command")
    def test_get_and_parse_commit_history(
        self, mock_run_git_command, mock_validate_repo, fixtures_dir
    ):
        """Test getting and parsing commit history."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Load the sample Git log
        with open(os.path.join(fixtures_dir, "git_log_sample.txt"), "r") as f:
            sample_log = f.read()

        # Mock the run_git_command function to return the sample log
        mock_run_git_command.return_value = sample_log

        # Get the commit history
        log_output = get_commit_history("/path/to/repo")

        # Parse the commit history
        commits = parse_git_log(log_output)

        # Check that we got the expected number of commits
        assert len(commits) == 5

        # Check that the commits have the expected properties
        assert all(isinstance(commit, Commit) for commit in commits)
        assert all(commit.hash for commit in commits)
        assert all(commit.author_name for commit in commits)
        assert all(commit.author_email for commit in commits)
        assert all(commit.date for commit in commits)
        assert all(commit.subject for commit in commits)
        assert all(isinstance(commit.files, list) for commit in commits)

    def test_validate_repo_with_temp_repo(self, temp_repo):
        """Test validating a repository with a temporary repository."""
        # Check that the temporary repository is valid
        assert validate_repo(temp_repo) is True

        # Check that a subdirectory of the repository is not valid
        src_dir = os.path.join(temp_repo, "src")
        with mock.patch(
            "git_stats.git.repository.run_git_command",
            side_effect=Exception("Not a git repository"),
        ):
            assert validate_repo(src_dir) is False

        # Check that a non-existent directory is not valid
        non_existent_dir = os.path.join(temp_repo, "non_existent")
        assert validate_repo(non_existent_dir) is False
