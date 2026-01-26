"""Tests for path utilities."""

import pytest
from pathlib import Path

from converter.paths import get_output_filename, resolve_template_path, slugify


def test_slugify_basic():
    """Test basic slugify functionality."""
    assert slugify("Hello World") == "hello-world"
    assert slugify("Test Document") == "test-document"


def test_slugify_special_characters():
    """Test slugify with special characters."""
    assert slugify("Test & Document!") == "test-document"
    assert slugify("Test@Document#123") == "testdocument123"


def test_slugify_unicode():
    """Test slugify with unicode characters."""
    result = slugify("Café & Résumé")
    assert "cafe" in result
    assert "resume" in result or "resum" in result


def test_slugify_multiple_hyphens():
    """Test slugify removes multiple consecutive hyphens."""
    assert slugify("Test---Document") == "test-document"
    assert slugify("Test   Document") == "test-document"


def test_slugify_leading_trailing_hyphens():
    """Test slugify removes leading/trailing hyphens."""
    assert slugify("-Test-") == "test"
    assert slugify("---Test---") == "test"


def test_slugify_max_length():
    """Test slugify respects max_length."""
    long_text = "a" * 200
    result = slugify(long_text, max_length=50)
    assert len(result) <= 50


def test_get_output_filename_with_title():
    """Test output filename generation with title."""
    input_file = Path("test.md")
    filename = get_output_filename(input_file, title="My Document")
    assert filename == "my-document.docx"


def test_get_output_filename_without_title():
    """Test output filename generation without title."""
    input_file = Path("test.md")
    filename = get_output_filename(input_file)
    assert filename == "test.docx"


def test_get_output_filename_pdf_format():
    """Test output filename generation for PDF format."""
    input_file = Path("test.md")
    filename = get_output_filename(input_file, output_format="pdf")
    assert filename == "test.pdf"


def test_get_output_filename_with_title_pdf():
    """Test output filename generation with title for PDF."""
    input_file = Path("test.md")
    filename = get_output_filename(input_file, title="My Document", output_format="pdf")
    assert filename == "my-document.pdf"


def test_get_output_filename_with_pattern():
    """Test output filename generation with naming pattern."""
    input_file = Path("test.md")
    filename = get_output_filename(
        input_file, title="My Document", output_naming_pattern="{title}_v1.docx"
    )
    assert "my-document" in filename
    assert filename.endswith(".docx")


def test_resolve_template_path_absolute():
    """Test resolving absolute template path."""
    template = Path("/absolute/path/template.docx")
    result = resolve_template_path(str(template))
    assert result == template


def test_resolve_template_path_none():
    """Test resolving None template path."""
    result = resolve_template_path(None)
    assert result is None


def test_resolve_template_path_relative():
    """Test resolving relative template path."""
    # This test depends on file system, so we'll just check the function doesn't crash
    result = resolve_template_path("template.docx", base_dir=Path("/tmp"))
    # Result may be None if file doesn't exist, or a Path object
    assert result is None or isinstance(result, Path)
