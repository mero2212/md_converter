# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool that converts Markdown files to Word (.docx) and PDF formats using Pandoc as the conversion engine. Features YAML frontmatter support, preset profiles, batch conversion, and a Streamlit web UI.

**External Dependencies**: Pandoc (required), LaTeX distribution (for PDF export)

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
pytest -v                           # verbose
pytest tests/test_frontmatter.py    # single test file

# CLI usage
python cli.py input.md output.docx
python cli.py input.md output.pdf --format pdf
python cli.py --batch input_folder output_folder --recursive

# Start Streamlit UI
streamlit run ui_app.py
```

## Architecture

### Core Components

- **cli.py** - Entry point, argument parsing, dispatches to single/batch handlers
- **converter/converter_service.py** - Main conversion orchestration: validates input, parses frontmatter, resolves profiles/templates, calls PandocWrapper
- **converter/pandoc_wrapper.py** - Executes Pandoc subprocess, handles PDF engine detection, sanitizes metadata
- **converter/batch_service.py** - Iterates directories, handles filename collisions, aggregates results
- **converter/frontmatter.py** - Parses YAML frontmatter from Markdown (custom parser, no PyYAML dependency)
- **converter/profiles.py** - Preset profiles (angebot, report, schulung) with default Pandoc args and naming patterns
- **converter/paths.py** - Slugify, output filename generation, template path resolution
- **converter/errors.py** - Exception hierarchy (ConverterError base, specific errors for Pandoc, PDF engine, frontmatter, etc.)

### Data Flow

1. CLI parses args → creates ConverterService
2. ConverterService reads input, parses frontmatter, resolves profile/template
3. Merges metadata (explicit overrides frontmatter)
4. PandocWrapper builds command and executes subprocess
5. For batch: BatchService iterates files, tracks collisions, returns BatchResult

### Key Design Patterns

- **Metadata precedence**: CLI args > frontmatter values
- **Profile system**: Profiles define default templates, Pandoc args (--toc, --number-sections), and output naming patterns
- **Collision handling**: Batch mode auto-generates unique names (name.docx, name_2.docx, etc.)
- **PDF engine detection**: Tries xelatex → lualatex → pdflatex in order

## Testing

Tests mock Pandoc calls - no actual Pandoc installation needed to run tests. Tests cover:
- Frontmatter parsing edge cases
- Profile defaults and overrides
- Batch collision handling
- CLI argument parsing
- PDF engine detection

## Configuration

Environment variables:
- `PANDOC_PATH` - Custom Pandoc executable path
- `MD_CONVERTER_TEMPLATE` - Default template path
