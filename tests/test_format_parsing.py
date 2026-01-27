"""Tests for format parsing and deduplication."""

import pytest
from cli import parse_formats, SUPPORTED_FORMATS


def test_parse_formats_single():
    """Test parsing a single format."""
    formats, error = parse_formats("docx", "docx")
    assert error is None
    assert formats == ["docx"]


def test_parse_formats_multiple():
    """Test parsing multiple formats."""
    formats, error = parse_formats("docx,pdf", "docx")
    assert error is None
    assert formats == ["docx", "pdf"]


def test_parse_formats_deduplication():
    """Test that duplicate formats are removed."""
    formats, error = parse_formats("docx,pdf,docx", "docx")
    assert error is None
    assert formats == ["docx", "pdf"]  # docx should appear only once


def test_parse_formats_multiple_duplicates():
    """Test deduplication with multiple duplicates."""
    formats, error = parse_formats("docx,pdf,docx,pdf,docx", "docx")
    assert error is None
    assert formats == ["docx", "pdf"]  # Each format should appear only once


def test_parse_formats_preserves_order():
    """Test that deduplication preserves first occurrence order."""
    formats, error = parse_formats("pdf,docx,pdf", "docx")
    assert error is None
    assert formats == ["pdf", "docx"]  # Order should be preserved


def test_parse_formats_invalid_filtered():
    """Test that invalid formats produce an error."""
    formats, error = parse_formats("docx,invalid,pdf,xyz", "docx")
    assert error is not None
    assert formats is None
    assert "invalid" in error


def test_parse_formats_all_invalid():
    """Test that all invalid formats result in error."""
    formats, error = parse_formats("invalid,xyz", "docx")
    assert error is not None
    assert "invalid value" in error


def test_parse_formats_none_uses_default():
    """Test that None formats_str uses default."""
    formats, error = parse_formats(None, "pdf")
    assert error is None
    assert formats == ["pdf"]


def test_parse_formats_empty_string():
    """Test that empty string is treated as None."""
    formats, error = parse_formats("", "docx")
    assert error is None
    assert formats == ["docx"]  # Should use default


def test_parse_formats_whitespace_handling():
    """Test that whitespace around formats is handled."""
    formats, error = parse_formats(" docx , pdf , docx ", "docx")
    assert error is None
    assert formats == ["docx", "pdf"]  # Whitespace should be stripped, duplicates removed
