"""
Git-Stats: A tool for analyzing Git repositories and identifying code experts.

This package provides functionality to generate statistics about contributions
and identify code experts for different parts of a Git repository.
"""

__version__ = "0.1.0"
__author__ = "Franck Cuny"
__email__ = "59291+fcuny@users.noreply.github.com"
__license__ = "MIT"
__description__ = "A Python-based command-line tool that analyzes Git repositories to generate statistics about contributions and identify code experts"

from git_stats.cli import main

__all__ = ["main"]
