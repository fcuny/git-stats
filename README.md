# Git-Stats

A Python-based command-line tool that analyzes Git repositories to generate statistics about contributions and identify code experts for different parts of the codebase.

## Features

- Generate contribution statistics for the entire repository
- Identify experts for specific files (especially useful for PR reviews)
- Works with local Git repositories
- Comprehensive scoring system based on longevity, lines of code, commits, and recency
- Customizable filtering by path, language, and date range

## Installation

```bash
uv tool install git+https://github.com/fcuny/git-stats

# Development installation
git clone https://github.com/fcuny/git-stats.git
cd git-stats
uv install -e ".[dev]"
```

## Usage

### Global Options

```
--repo-path PATH       Path to the Git repository (default: current directory)
--recency-period INT   Define recency period in months (default: 3)
--output-format FORMAT Format for output (default: text, options: text, json)
```

### Stats Command

Generate contribution statistics for the repository:

```bash
git-stats stats [--path PATH] [--language LANGUAGE] [--since DATE] [--until DATE]
```

#### Examples

```bash
# Basic usage - analyze the current repository
git-stats stats

# Analyze a specific repository
git-stats stats --repo-path /path/to/repository

# Filter by directory
git-stats stats --path src/

# Filter by language
git-stats stats --language python

# Filter by date range
git-stats stats --since 2023-01-01 --until 2023-12-31

# Combine filters
git-stats stats --path src/ --language python --since 2023-01-01

# Output in JSON format
git-stats stats --output-format json > stats.json
```

### DRIs Command

Identify experts for specific files (Directly Responsible Individuals):

```bash
git-stats dris [--files FILE1,FILE2,...] [--top N]
```

#### Examples

```bash
# Analyze all files in the current diff
git-stats dris

# Analyze specific files
git-stats dris --files src/main.py,src/utils.py

# Show top 5 experts instead of default 3
git-stats dris --files src/main.py --top 5

# Analyze with a different recency period (6 months)
git-stats dris --files src/main.py --recency-period 6

# Output in JSON format
git-stats dris --files src/main.py --output-format json > experts.json
```

## Understanding the Output

### Stats Output

The stats command produces a table with the following columns:

- **Rank**: Position in the leaderboard
- **Contributor**: Name/email of the contributor
- **Score**: Weighted score based on all factors
- **Commits**: Number of commits
- **Lines**: Lines of code contributed
- **Longevity**: How long the contributor has been active
- **Recency**: Recent contribution activity

### DRIs Output

The dris command produces two tables:

1. **File Experts**: Shows the top experts for each file
   - File: Path to the file
   - Expert: Name/email of the expert
   - Score: Expertise score
   - Expertise Level: High, Medium, or Low with color coding

2. **Overall Experts**: Shows the top experts across all analyzed files
   - Expert: Name/email of the expert
   - Score: Overall expertise score
   - Expertise Level: High, Medium, or Low with color coding

## Scoring System

Git-Stats uses a weighted scoring system based on four factors:

1. **Longevity** (highest weight): How long someone has been contributing to a file/area
2. **Lines of Code** (high weight): Amount of code contributed
3. **Number of Commits** (medium weight): Frequency of contributions
4. **Recency** (lower weight): Recent contributions (default: last 3 months)

Scores are normalized to a 0-1 scale and color-coded:
- **High** (green): Score ≥ 0.7
- **Medium** (yellow): Score between 0.4 and 0.7
- **Low** (red): Score < 0.4
