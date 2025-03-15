"""
Tests for the Git repository module.
"""

import os
import subprocess
from unittest import mock

import pytest

from git_stats.git.repository import (
    get_commit_history,
    get_file_type,
    run_git_command,
    validate_repo,
)


class TestValidateRepo:
    """Tests for the validate_repo function."""

    def test_valid_repo_with_git_dir(self, tmp_path):
        """Test validation of a valid repository with a .git directory."""
        # Create a mock repository with a .git directory
        repo_path = tmp_path / "repo"
        git_dir = repo_path / ".git"
        os.makedirs(git_dir)

        assert validate_repo(str(repo_path)) is True

    def test_valid_repo_with_git_file(self, tmp_path):
        """Test validation of a valid repository with a .git file (submodule)."""
        # Create a mock repository with a .git file
        repo_path = tmp_path / "repo"
        os.makedirs(repo_path)
        git_file = repo_path / ".git"
        git_file.write_text("gitdir: ../.git/modules/repo")

        assert validate_repo(str(repo_path)) is True

    def test_invalid_repo_no_git(self, tmp_path):
        """Test validation of an invalid repository with no .git directory or file."""
        # Create a directory without a .git directory or file
        repo_path = tmp_path / "not_a_repo"
        os.makedirs(repo_path)

        # Mock run_git_command to simulate a failed git command
        with mock.patch(
            "git_stats.git.repository.run_git_command",
            side_effect=Exception("Not a git repository"),
        ):
            assert validate_repo(str(repo_path)) is False

    def test_invalid_repo_not_a_directory(self, tmp_path):
        """Test validation of an invalid repository that is not a directory."""
        # Create a file instead of a directory
        repo_path = tmp_path / "not_a_repo"
        repo_path.write_text("This is not a repository")

        assert validate_repo(str(repo_path)) is False


class TestRunGitCommand:
    """Tests for the run_git_command function."""

    @mock.patch("subprocess.run")
    def test_successful_command(self, mock_run, tmp_path):
        """Test running a successful Git command."""
        # Mock the subprocess.run function to return a successful result
        mock_process = mock.Mock()
        mock_process.stdout = "Command output"
        mock_run.return_value = mock_process

        result = run_git_command("/path/to/repo", "status")

        # Check that subprocess.run was called with the correct arguments
        mock_run.assert_called_once_with(
            ["git", "-C", "/path/to/repo", "status"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Check that the function returns the command output
        assert result == "Command output"

    @mock.patch("subprocess.run")
    def test_failed_command(self, mock_run, tmp_path):
        """Test running a failed Git command."""
        # Mock the subprocess.run function to raise a CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["git", "-C", "/path/to/repo", "status"],
            output="Error output",
        )

        # Check that the function raises the CalledProcessError
        with pytest.raises(subprocess.CalledProcessError):
            run_git_command("/path/to/repo", "status")

    @mock.patch("subprocess.run")
    def test_command_with_capture_stderr(self, mock_run, tmp_path):
        """Test running a Git command with stderr capture."""
        # Mock the subprocess.run function to return a successful result
        mock_process = mock.Mock()
        mock_process.stdout = "Command output"
        mock_run.return_value = mock_process

        result = run_git_command("/path/to/repo", "status", capture_stderr=True)

        # Check that subprocess.run was called with the correct arguments
        mock_run.assert_called_once_with(
            ["git", "-C", "/path/to/repo", "status"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Check that the function returns the command output
        assert result == "Command output"


class TestGetCommitHistory:
    """Tests for the get_commit_history function."""

    @mock.patch("git_stats.git.repository.validate_repo")
    @mock.patch("git_stats.git.repository.run_git_command")
    def test_basic_history(self, mock_run_git_command, mock_validate_repo):
        """Test getting basic commit history."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Mock the run_git_command function to return a sample log
        mock_run_git_command.return_value = "Sample log output"

        result = get_commit_history("/path/to/repo")

        # Check that validate_repo was called with the correct arguments
        mock_validate_repo.assert_called_once_with("/path/to/repo")

        # Check that run_git_command was called with the correct arguments
        mock_run_git_command.assert_called_once_with(
            "/path/to/repo",
            "log",
            "--numstat",
            "--date=iso-strict",
            "--pretty=format:%H%nAuthor: %an <%ae>%nDate: %ad%n%n%s%n%b%n",
            "--no-merges",
        )

        # Check that the function returns the command output
        assert result == "Sample log output"

    @mock.patch("git_stats.git.repository.validate_repo")
    def test_invalid_repo(self, mock_validate_repo):
        """Test getting commit history for an invalid repository."""
        # Mock the validate_repo function to return False
        mock_validate_repo.return_value = False

        # Check that the function raises a ValueError
        with pytest.raises(ValueError, match="Invalid Git repository"):
            get_commit_history("/path/to/repo")

    @mock.patch("git_stats.git.repository.validate_repo")
    @mock.patch("git_stats.git.repository.run_git_command")
    def test_with_path_filter(self, mock_run_git_command, mock_validate_repo):
        """Test getting commit history with a path filter."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Mock the run_git_command function to return a sample log
        mock_run_git_command.return_value = "Sample log output"

        result = get_commit_history("/path/to/repo", path="src/feature_x.py")

        # Check that validate_repo was called with the correct arguments
        mock_validate_repo.assert_called_once_with("/path/to/repo")

        # Check that run_git_command was called with the correct arguments
        mock_run_git_command.assert_called_once_with(
            "/path/to/repo",
            "log",
            "--numstat",
            "--date=iso-strict",
            "--pretty=format:%H%nAuthor: %an <%ae>%nDate: %ad%n%n%s%n%b%n",
            "--no-merges",
            "--",
            "src/feature_x.py",
        )

        # Check that the function returns the command output
        assert result == "Sample log output"

    @mock.patch("git_stats.git.repository.validate_repo")
    @mock.patch("git_stats.git.repository.run_git_command")
    def test_with_date_range(self, mock_run_git_command, mock_validate_repo):
        """Test getting commit history with a date range."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Mock the run_git_command function to return a sample log
        mock_run_git_command.return_value = "Sample log output"

        result = get_commit_history(
            "/path/to/repo",
            since="2023-01-01",
            until="2023-12-31",
        )

        # Check that validate_repo was called with the correct arguments
        mock_validate_repo.assert_called_once_with("/path/to/repo")

        # Check that run_git_command was called with the correct arguments
        mock_run_git_command.assert_called_once_with(
            "/path/to/repo",
            "log",
            "--numstat",
            "--date=iso-strict",
            "--pretty=format:%H%nAuthor: %an <%ae>%nDate: %ad%n%n%s%n%b%n",
            "--since",
            "2023-01-01",
            "--until",
            "2023-12-31",
            "--no-merges",
        )

        # Check that the function returns the command output
        assert result == "Sample log output"


class TestGetFileType:
    """Tests for the get_file_type function."""

    @mock.patch("git_stats.git.repository.validate_repo")
    def test_python_file(self, mock_validate_repo, tmp_path):
        """Test getting the type of a Python file."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Create a Python file
        repo_path = tmp_path / "repo"
        os.makedirs(repo_path)
        file_path = repo_path / "file.py"
        file_path.write_text("print('Hello, world!')")

        result = get_file_type(str(repo_path), "file.py")

        # Check that the function returns the correct file type
        assert result == "python"

    @mock.patch("git_stats.git.repository.validate_repo")
    def test_go_file(self, mock_validate_repo, tmp_path):
        """Test getting the type of a Go file."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Create a Go file
        repo_path = tmp_path / "repo"
        os.makedirs(repo_path)
        file_path = repo_path / "file.go"
        file_path.write_text("package main")

        result = get_file_type(str(repo_path), "file.go")

        # Check that the function returns the correct file type
        assert result == "go"

    @mock.patch("git_stats.git.repository.validate_repo")
    def test_text_file(self, mock_validate_repo, tmp_path):
        """Test getting the type of a text file."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Create a text file
        repo_path = tmp_path / "repo"
        os.makedirs(repo_path)
        file_path = repo_path / "file.txt"
        file_path.write_text("Hello, world!")

        result = get_file_type(str(repo_path), "file.txt")

        # Check that the function returns the correct file type
        assert result == "text"

    @mock.patch("git_stats.git.repository.validate_repo")
    def test_binary_file(self, mock_validate_repo, tmp_path):
        """Test getting the type of a binary file."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Create a binary file
        repo_path = tmp_path / "repo"
        os.makedirs(repo_path)
        file_path = repo_path / "file.bin"
        file_path.write_bytes(b"Hello\x00world!")

        result = get_file_type(str(repo_path), "file.bin")

        # Check that the function returns the correct file type
        assert result == "binary"

    @mock.patch("git_stats.git.repository.validate_repo")
    def test_invalid_file(self, mock_validate_repo, tmp_path):
        """Test getting the type of a file that doesn't exist."""
        # Mock the validate_repo function to return True
        mock_validate_repo.return_value = True

        # Create a repository without the file
        repo_path = tmp_path / "repo"
        os.makedirs(repo_path)

        # Check that the function raises a ValueError
        with pytest.raises(ValueError, match="does not exist in repository"):
            get_file_type(str(repo_path), "nonexistent.py")
