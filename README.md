# Git-Stats

A Python-based command-line tool that analyzes Git repositories to generate statistics about contributions and identify code experts for different parts of the codebase.

## Features

- Generate contribution statistics for the entire repository
- Identify experts for specific files (especially useful for PR reviews)
- Works with local Git repositories
- Formatted terminal output using the `rich` library

## Installation

```bash
# Using pip
pip install git-stats

# Using uv
uv pip install git-stats

# Development installation
git clone https://github.com/yourusername/git-stats.git
cd git-stats
uv pip install -e ".[dev]"
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

### DRIs Command

Identify experts for specific files:

```bash
git-stats dris [--files FILE1,FILE2,...] [--top N]
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=git_stats
```

## License

MIT
