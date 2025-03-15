"""
Formatting module for git-stats.

This module provides utilities for formatting output using the rich library.
It includes console setup, table generation, color and style definitions.
"""

from enum import Enum
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# Color and style definitions
class ExpertiseLevel(Enum):
    """Enum representing expertise levels with associated colors."""

    HIGH = ("High", "bold green")
    MEDIUM = ("Medium", "yellow")
    LOW = ("Low", "dim red")

    def __init__(self, label: str, style: str):
        self.label = label
        self.style = style


# Score thresholds for expertise levels
EXPERTISE_THRESHOLDS = {
    0.7: ExpertiseLevel.HIGH,
    0.4: ExpertiseLevel.MEDIUM,
    0.0: ExpertiseLevel.LOW,
}

# Rank styles for different positions
RANK_STYLES = {
    1: "bold gold1",  # Gold for 1st place
    2: "bold grey70",  # Silver for 2nd place
    3: "bold orange3",  # Bronze for 3rd place
}

# Default style for other ranks
DEFAULT_RANK_STYLE = "dim"

# Column styles
COLUMN_STYLES = {
    "rank": "dim",
    "contributor": "cyan",
    "score": "magenta",
    "file": "cyan",
    "expert": "magenta",
    "expertise_level": "bold",
}


def create_console(width: Optional[int] = None) -> Console:
    """
    Create a rich console with the specified width.

    Args:
        width: Optional width for the console (defaults to auto-detection)

    Returns:
        Configured Console instance
    """
    return Console(width=width, highlight=True)


def get_expertise_level(score: float) -> ExpertiseLevel:
    """
    Get the expertise level based on a score.

    Args:
        score: The score value (0.0 to 1.0)

    Returns:
        The corresponding ExpertiseLevel
    """
    for threshold, level in sorted(EXPERTISE_THRESHOLDS.items(), reverse=True):
        if score >= threshold:
            return level
    return ExpertiseLevel.LOW


def format_expertise_level(score: float) -> Text:
    """
    Format an expertise level as rich Text with appropriate styling.

    Args:
        score: The score value (0.0 to 1.0)

    Returns:
        Styled Text object
    """
    level = get_expertise_level(score)
    return Text(level.label, style=level.style)


def get_rank_style(rank: int) -> str:
    """
    Get the style for a specific rank.

    Args:
        rank: The rank position (1-based)

    Returns:
        Style string for the rank
    """
    return RANK_STYLES.get(rank, DEFAULT_RANK_STYLE)


def create_score_bar(score: float, width: int = 10) -> Text:
    """
    Create a visual bar representation of a score.

    Args:
        score: The score value (0.0 to 1.0)
        width: The width of the bar in characters

    Returns:
        Text object with the bar visualization
    """
    filled = int(score * width)
    empty = width - filled

    level = get_expertise_level(score)

    bar = Text("█" * filled, style=level.style)
    bar.append("░" * empty, style="dim")
    bar.append(f" {score:.2f}", style="bold")

    return bar


def create_stats_table(
    title: str = "Contribution Statistics",
    sortable: bool = True,
) -> Table:
    """
    Create a table for contribution statistics.

    Args:
        title: The title of the table
        sortable: Whether to make the table sortable

    Returns:
        Configured Table instance
    """
    table = Table(title=title, title_style="bold", expand=True)

    table.add_column("Rank", style=COLUMN_STYLES["rank"], width=6)
    table.add_column("Contributor", style=COLUMN_STYLES["contributor"])
    table.add_column("Score", style=COLUMN_STYLES["score"], justify="right", width=16)
    table.add_column("Commits", justify="right")
    table.add_column("Lines", justify="right")
    table.add_column("Longevity", justify="right")
    table.add_column("Recency", justify="right")

    if sortable:
        table.caption = "Click column headers to sort"
        table.caption_style = "dim italic"

    return table


def create_experts_table(title: str = "File Experts") -> Table:
    """
    Create a table for file experts.

    Args:
        title: The title of the table

    Returns:
        Configured Table instance
    """
    table = Table(title=title, title_style="bold", expand=True)

    table.add_column("File", style=COLUMN_STYLES["file"])
    table.add_column("Expert", style=COLUMN_STYLES["expert"])
    table.add_column("Score", justify="right", width=16)
    table.add_column("Expertise Level", justify="center")

    return table


def create_overall_experts_table(title: str = "Overall Experts") -> Table:
    """
    Create a table for overall experts.

    Args:
        title: The title of the table

    Returns:
        Configured Table instance
    """
    table = Table(title=title, title_style="bold", expand=True)

    table.add_column("Expert", style=COLUMN_STYLES["expert"])
    table.add_column("Score", justify="right", width=16)
    table.add_column("Expertise Level", justify="center")

    return table


def create_command_panel(
    title: str, command_name: str, parameters: Dict[str, Any]
) -> Panel:
    """
    Create a panel displaying command parameters.

    Args:
        title: The panel title
        command_name: The name of the command
        parameters: Dictionary of parameter names and values

    Returns:
        Configured Panel instance
    """
    content = f"[bold]{command_name}[/bold]\n\n"

    for key, value in parameters.items():
        if value is not None:
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)

            content += f"{key.replace('_', ' ').title()}: [cyan]{value_str}[/cyan]\n"

    return Panel(content, title=title, expand=False)


def format_longevity(days: int) -> str:
    """
    Format longevity in a human-readable format.

    Args:
        days: Number of days

    Returns:
        Formatted string (e.g., "2y 3m" or "5m")
    """
    years = days // 365
    months = (days % 365) // 30

    if years > 0:
        return f"{years}y {months}m"
    else:
        return f"{months}m"
