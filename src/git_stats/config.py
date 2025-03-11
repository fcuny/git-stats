"""
Configuration module for git-stats.

This module contains configuration classes and constants used throughout the application.
"""

from enum import Enum, auto


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
