"""
Configuration module for git-stats.

This module contains configuration classes and constants used throughout the application.
"""

from enum import Enum, auto
from typing import Dict, Any


class OutputFormat(Enum):
    """Enum representing the available output formats."""

    TEXT = auto()
    JSON = auto()


# Scoring weights for the contribution factors
# These weights are hardcoded based on the priority order specified in the requirements
SCORING_WEIGHTS = {
    "longevity": 0.4,  # How long someone has been contributing to a file/area
    "lines_of_code": 0.3,  # Amount of code contributed
    "commits": 0.2,  # Frequency of contributions
    "recency": 0.1,  # Recent contributions
}

# Default configuration values
DEFAULT_CONFIG = {
    "recency_period": 3,  # Default recency period in months
    "top_experts": 3,  # Default number of experts to recommend
    "min_score_threshold": 0.1,  # Minimum score to consider someone an expert
}

# UI/UX configuration
UI_CONFIG = {
    # Table styling
    "table_title_style": "bold cyan",
    "table_border_style": "dim",
    "table_header_style": "bold",
    # Message styling
    "info_style": "cyan",
    "success_style": "green",
    "warning_style": "yellow",
    "error_style": "bold red",
    # Progress indicators
    "show_progress": True,
    "progress_style": "cyan",
    # Terminal width
    "auto_width": True,  # Automatically adjust to terminal width
    "max_width": 120,  # Maximum width if auto_width is False
}

# Error messages
ERROR_MESSAGES = {
    "not_git_repo": "The specified path is not a Git repository.",
    "no_commits": "No commits found in the repository with the specified filters.",
    "invalid_date_format": "Invalid date format. Please use YYYY-MM-DD.",
    "file_not_found": "One or more specified files not found in the repository.",
    "permission_denied": "Permission denied when accessing the repository.",
}

# Success messages
SUCCESS_MESSAGES = {
    "stats_generated": "Contribution statistics generated successfully.",
    "experts_identified": "Code experts identified successfully.",
}


def get_ui_config() -> Dict[str, Any]:
    """
    Get the UI configuration.

    Returns:
        Dictionary containing UI configuration options
    """
    return UI_CONFIG.copy()
