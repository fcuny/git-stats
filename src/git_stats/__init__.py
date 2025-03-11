"""
Git-Stats: A tool for analyzing Git repositories and identifying code experts.

This package provides functionality to generate statistics about contributions
and identify code experts for different parts of a Git repository.
"""

__version__ = "0.1.0"

from git_stats.cli import main

__all__ = ["main"]
