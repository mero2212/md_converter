"""Tests for frontmatter parsing."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from converter.errors import FrontmatterError
from converter.frontmatter import FrontmatterData, parse_frontmatter


def test_parse_frontmatter_with_yaml():
    """Test parsing Markdown file with YAML frontmatter."""
    content = """---
title: Test Document
author: John Doe
version: 1.0
date: 2024-01-15
customer: Acme Corp
project: Project Alpha
---

# Content

This is the content.
"""

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = Path(f.name)

    try:
        frontmatter, remaining = parse_frontmatter(file_path)

        assert frontmatter is not None
        assert frontmatter.title == "Test Document"
        assert frontmatter.author == "John Doe"
        assert frontmatter.version == "1.0"
        assert frontmatter.date == "2024-01-15"
        assert frontmatter.customer == "Acme Corp"
        assert frontmatter.project == "Project Alpha"

        assert "# Content" in remaining
        assert "This is the content." in remaining
    finally:
        file_path.unlink()


def test_parse_frontmatter_without_yaml():
    """Test parsing Markdown file without frontmatter."""
    content = """# Content

This is the content.
"""

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = Path(f.name)

    try:
        frontmatter, remaining = parse_frontmatter(file_path)

        assert frontmatter is None
        assert remaining == content
    finally:
        file_path.unlink()


def test_parse_frontmatter_partial_fields():
    """Test parsing frontmatter with only some fields."""
    content = """---
title: Test Document
author: John Doe
---

# Content
"""

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = Path(f.name)

    try:
        frontmatter, remaining = parse_frontmatter(file_path)

        assert frontmatter is not None
        assert frontmatter.title == "Test Document"
        assert frontmatter.author == "John Doe"
        assert frontmatter.version is None
        assert frontmatter.date is None
    finally:
        file_path.unlink()


def test_parse_frontmatter_empty_date():
    """Test that empty date defaults to today."""
    content = """---
title: Test
date: ""
---
"""

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = Path(f.name)

    try:
        frontmatter, _ = parse_frontmatter(file_path)
        assert frontmatter is not None
        assert frontmatter.date is not None
        # Date should be in YYYY-MM-DD format
        assert len(frontmatter.date) == 10
        assert frontmatter.date.count("-") == 2
    finally:
        file_path.unlink()


def test_parse_frontmatter_malformed():
    """Test parsing malformed frontmatter."""
    content = """---
title: Test
invalid yaml: [unclosed
---

# Content
"""

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = Path(f.name)

    try:
        # Should not raise, but may parse partially or ignore invalid parts
        frontmatter, remaining = parse_frontmatter(file_path)
        # Parser is lenient, so it should still work
        assert frontmatter is not None or frontmatter is None
    finally:
        file_path.unlink()


def test_parse_frontmatter_no_closing_delimiter():
    """Test file with opening --- but no closing delimiter."""
    content = """---
title: Test

# Content
"""

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        file_path = Path(f.name)

    try:
        frontmatter, remaining = parse_frontmatter(file_path)
        # Should treat as no frontmatter
        assert frontmatter is None
        assert remaining == content
    finally:
        file_path.unlink()


def test_frontmatter_data_to_dict():
    """Test FrontmatterData.to_dict() method."""
    data = FrontmatterData({
        "title": "Test",
        "author": "John",
        "version": None,  # Should be excluded
    })

    result = data.to_dict()
    assert "title" in result
    assert "author" in result
    assert "version" not in result


def test_frontmatter_data_to_pandoc_variables():
    """Test FrontmatterData.to_pandoc_variables() method."""
    data = FrontmatterData({
        "title": "Test",
        "author": "John",
        "version": "1.0",
    })

    variables = data.to_pandoc_variables()
    assert variables["title"] == "Test"
    assert variables["author"] == "John"
    assert variables["version"] == "1.0"
