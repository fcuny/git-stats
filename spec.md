# Git Repository Statistics Tool Specification

## Overview
A Python-based command-line tool that analyzes Git repositories to generate statistics about contributions and identify code experts for different parts of the codebase.

## Core Functionality
The tool provides two main subcommands:
1. `stats` - Generate contribution statistics for the entire repository
2. `dris` - Identify experts for specific files (especially useful for PR reviews)

## Technical Requirements

### Environment
- Python-based CLI tool
- Works with local Git repositories only
- No external API dependencies (GitHub, etc.)
- Uses the `rich` library for formatted terminal output

### Git Analysis Parameters
- Analyze only the current branch
- Ignore merge commits
- Consider only the main author for commits with multiple authors
- Treat each file path independently (don't track renames)
- Ignore binary files
- Primary focus on Go and Python files, but analyze all text files

## Scoring System

### Contribution Factors (in priority order)
1. **Longevity** - How long someone has been contributing to a file/area
2. **Lines of Code** - Amount of code contributed
3. **Number of Commits** - Frequency of contributions
4. **Recency** - Recent contributions (default: last 3 months)

### Weighting System
- Weights will be hardcoded based on the priority order
- No user-configurable weights

## Command-Line Interface

### Global Flags
- `--repo-path` - Path to the Git repository (default: current directory)
- `--recency-period` - Define recency period in months (default: 3)
- `--output-format` - Format for output (default: text, options: text, json)

### Stats Subcommand
```
git-stats stats [--path <path>] [--language <language>] [--since <date>] [--until <date>]
```

- `--path` - Filter by specific directory or file path
- `--language` - Filter by specific language (go, python, etc.)
- `--since` - Start date for the analysis
- `--until` - End date for the analysis

### dris Subcommand
```
git-stats dris [--files <file1,file2,...>] [--top <N>]
```

- `--files` - Comma-separated list of files to analyze (default: all files in current diff)
- `--top` - Number of experts to recommend (default: 3)

## Output Format

### Stats Output
- Leaderboard table showing:
  - Rank
  - Contributor name/email
  - Weighted score
  - Breakdown of individual metrics (commits, lines, etc.)
- Colorful output with clear formatting using `rich`
- Option for JSON output for integration with other tools

### Experts Output
- Table showing recommended reviewers for each file or file group
- Clear indication of expertise level
- Overall recommendations across all changed files
- Option for JSON output

## Implementation Details

### Git Interaction
- Use Git commands via subprocess or a Git Python library
- Parse Git log output to extract:
  - Commit information
  - Author details
  - File changes
  - Line additions/deletions

### Scoring Algorithm
1. Calculate raw metrics for each contributor per file/path:
   - Longevity: Time between first and last commit
   - Lines of code: Total lines added/modified
   - Commits: Total number of commits
   - Recency: Percentage of contributions in the recency period

2. Normalize each metric to a 0-1 scale

3. Apply weighted formula:
   ```
   Score = (Longevity * W1) + (LinesOfCode * W2) + (Commits * W3) + (Recency * W4)
   ```
   Where W1 > W2 > W3 > W4 are predefined weights

### Performance Considerations
- No caching mechanism in initial version
- Optimize Git queries to minimize subprocess calls
- Consider performance optimizations for large repositories

## Future Enhancements (Not in Initial Scope)
- Caching of analysis results
- Support for analyzing remote repositories
- Identity merging for contributors with multiple emails
- Custom weighting configuration
- Visualization features
- Support for submodules
