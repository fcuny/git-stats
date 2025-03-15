"""
Tests for the formatting module.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from git_stats.formatting import (
    ExpertiseLevel,
    create_command_panel,
    create_console,
    create_experts_table,
    create_overall_experts_table,
    create_score_bar,
    create_stats_table,
    format_expertise_level,
    format_longevity,
    get_expertise_level,
    get_rank_style,
)


def test_create_console():
    """Test creating a console."""
    console = create_console()
    assert isinstance(console, Console)

    # Test with custom width
    console = create_console(width=80)
    assert isinstance(console, Console)
    assert console.width == 80


def test_get_expertise_level():
    """Test getting expertise level based on score."""
    # Test high expertise level
    assert get_expertise_level(0.8) == ExpertiseLevel.HIGH
    assert get_expertise_level(0.7) == ExpertiseLevel.HIGH

    # Test medium expertise level
    assert get_expertise_level(0.6) == ExpertiseLevel.MEDIUM
    assert get_expertise_level(0.4) == ExpertiseLevel.MEDIUM

    # Test low expertise level
    assert get_expertise_level(0.3) == ExpertiseLevel.LOW
    assert get_expertise_level(0.0) == ExpertiseLevel.LOW


def test_format_expertise_level():
    """Test formatting expertise level."""
    # Test high expertise level
    high_text = format_expertise_level(0.8)
    assert isinstance(high_text, Text)
    assert high_text.plain == "High"

    # Test medium expertise level
    medium_text = format_expertise_level(0.5)
    assert isinstance(medium_text, Text)
    assert medium_text.plain == "Medium"

    # Test low expertise level
    low_text = format_expertise_level(0.2)
    assert isinstance(low_text, Text)
    assert low_text.plain == "Low"


def test_get_rank_style():
    """Test getting rank style."""
    # Test top 3 ranks
    assert get_rank_style(1) == "bold gold1"
    assert get_rank_style(2) == "bold grey70"
    assert get_rank_style(3) == "bold orange3"

    # Test other ranks
    assert get_rank_style(4) == "dim"
    assert get_rank_style(10) == "dim"


def test_create_score_bar():
    """Test creating a score bar."""
    # Test with different scores
    high_bar = create_score_bar(0.8)
    assert isinstance(high_bar, Text)

    medium_bar = create_score_bar(0.5)
    assert isinstance(medium_bar, Text)

    low_bar = create_score_bar(0.2)
    assert isinstance(low_bar, Text)

    # Test with custom width
    custom_bar = create_score_bar(0.5, width=20)
    assert isinstance(custom_bar, Text)


def test_create_stats_table():
    """Test creating a stats table."""
    # Test default table
    table = create_stats_table()
    assert isinstance(table, Table)
    assert table.title == "Contribution Statistics"
    assert len(table.columns) == 7

    # Test with custom title
    custom_table = create_stats_table(title="Custom Stats")
    assert custom_table.title == "Custom Stats"

    # Test with sortable=False
    non_sortable_table = create_stats_table(sortable=False)
    assert non_sortable_table.caption is None


def test_create_experts_table():
    """Test creating an experts table."""
    # Test default table
    table = create_experts_table()
    assert isinstance(table, Table)
    assert table.title == "File Experts"
    assert len(table.columns) == 4

    # Test with custom title
    custom_table = create_experts_table(title="Custom Experts")
    assert custom_table.title == "Custom Experts"


def test_create_overall_experts_table():
    """Test creating an overall experts table."""
    # Test default table
    table = create_overall_experts_table()
    assert isinstance(table, Table)
    assert table.title == "Overall Experts"
    assert len(table.columns) == 3

    # Test with custom title
    custom_table = create_overall_experts_table(title="Custom Overall")
    assert custom_table.title == "Custom Overall"


def test_create_command_panel():
    """Test creating a command panel."""
    # Test with simple parameters
    parameters = {
        "repository": "/path/to/repo",
        "recency_period": "3 months",
        "output_format": "text",
    }
    panel = create_command_panel("Test Command", "Git Test", parameters)
    assert isinstance(panel, Panel)
    assert panel.title == "Test Command"

    # Test with None values
    parameters_with_none = {
        "repository": "/path/to/repo",
        "recency_period": "3 months",
        "path_filter": None,
    }
    panel_with_none = create_command_panel(
        "Test Command", "Git Test", parameters_with_none
    )
    assert isinstance(panel_with_none, Panel)

    # Test with list values
    parameters_with_list = {
        "repository": "/path/to/repo",
        "files": ["file1.py", "file2.py"],
    }
    panel_with_list = create_command_panel(
        "Test Command", "Git Test", parameters_with_list
    )
    assert isinstance(panel_with_list, Panel)


def test_format_longevity():
    """Test formatting longevity."""
    # Test with years and months
    assert format_longevity(400) == "1y 1m"
    assert format_longevity(730) == "2y 0m"

    # Test with only months
    assert format_longevity(30) == "1m"
    assert format_longevity(60) == "2m"
    assert format_longevity(0) == "0m"
