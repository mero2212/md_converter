# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool that converts Markdown files to Word (.docx) and PDF formats using Pandoc as the conversion engine. Features YAML frontmatter support, preset profiles, batch conversion, and a Streamlit web UI.

**External Dependencies**: Pandoc (required), LaTeX distribution (for PDF export), Mermaid CLI (optional, for diagrams)

## Common Commands

```bash
# Install as editable package (recommended)
pip install -e .

# After installation, use short commands:
mdconv input.md output.docx
mdconv-ui

# Or without installation:
python cli.py input.md output.docx
streamlit run ui_app.py

# Windows batch files (no installation needed):
convert input.md output.docx
ui

# Run tests
pytest
pytest -v                           # verbose
pytest tests/test_frontmatter.py    # single test file
pytest tests/test_frontmatter.py::test_parse_valid_frontmatter  # single test
```

## Architecture

### Core Components

- **cli.py** - Entry point, argument parsing, dispatches to single/batch handlers. Contains `SUPPORTED_FORMATS` constant and `parse_formats()` helper.
- **converter/converter_service.py** - Main conversion orchestration: validates input, parses frontmatter, resolves profiles/templates, calls PandocWrapper
- **converter/pandoc_wrapper.py** - Executes Pandoc subprocess, handles PDF engine detection, sanitizes metadata, validates output file creation
- **converter/batch_service.py** - Iterates directories, handles filename collisions, aggregates results
- **converter/frontmatter.py** - Parses YAML frontmatter from Markdown (custom parser, no PyYAML dependency, with UTF-8/latin-1 fallback)
- **converter/mermaid_processor.py** - Converts Mermaid code blocks to PNG images using mmdc (Mermaid CLI)
- **converter/profiles.py** - Preset profiles (angebot, bericht, analyse, script) with default Pandoc args, templates, and naming patterns
- **converter/paths.py** - Slugify, output filename generation, template path resolution
- **converter/errors.py** - Exception hierarchy (ConverterError base, specific errors for Pandoc, PDF engine, frontmatter, profile, etc.)

### Data Flow

1. CLI parses args → creates ConverterService
2. ConverterService reads input, parses frontmatter, resolves profile/template
3. If Mermaid diagrams found and mmdc available: renders to PNG, creates temp file
4. Merges metadata (explicit overrides frontmatter)
5. PandocWrapper builds command and executes subprocess
6. Validates output file was created and has content
7. Cleans up Mermaid temp files
8. For batch: BatchService iterates files, tracks collisions, returns BatchResult

### Key Design Patterns

- **Metadata precedence**: CLI args > frontmatter values
- **Profile system**: Profiles define default templates, Pandoc args (--toc, --number-sections), and output naming patterns. Templates resolve from `local/templates/`.
- **Collision handling**: Batch mode auto-generates unique names (name.docx, name_2.docx, etc.)
- **PDF engine detection**: Tries xelatex → lualatex → pdflatex in order

## Local vs Public Data

Company-specific data is gitignored and stays local:

```
local/                         # Gitignored - company templates and logos
local_profiles.py              # Gitignored - custom profiles (see .example)
create_templates.py            # Gitignored - template generator with company address (see .example)
```

Custom profiles in `local_profiles.py` are auto-loaded by cli.py if present.

## Testing

Tests mock Pandoc calls - no actual Pandoc installation needed. Mock side effects must create output files for validation tests to pass.

```bash
pytest                                    # all tests
pytest tests/test_profiles.py -v          # specific file
pytest -k "test_parse"                    # pattern match
```

## Configuration

Environment variables:
- `PANDOC_PATH` - Custom Pandoc executable path
- `MD_CONVERTER_TEMPLATE` - Default template path
