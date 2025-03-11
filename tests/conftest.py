"""
Common fixtures for the git-stats tests.
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_repo():
    """Create a temporary directory for a mock Git repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a .git directory to make it look like a Git repository
        git_dir = os.path.join(temp_dir, ".git")
        os.makedirs(git_dir)

        # Create some sample files
        src_dir = os.path.join(temp_dir, "src")
        os.makedirs(src_dir)

        with open(os.path.join(src_dir, "main.py"), "w") as f:
            f.write("print('Hello, world!')\n")

        with open(os.path.join(src_dir, "utils.py"), "w") as f:
            f.write("def add(a, b):\n    return a + b\n")

        tests_dir = os.path.join(temp_dir, "tests")
        os.makedirs(tests_dir)

        with open(os.path.join(tests_dir, "test_utils.py"), "w") as f:
            f.write("def test_add():\n    assert add(1, 2) == 3\n")

        yield temp_dir
