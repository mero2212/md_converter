"""Tests for batch conversion service."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from converter.batch_service import BatchResult, BatchService
from converter.converter_service import ConverterService
from converter.errors import ConversionError


def test_batch_result_initialization():
    """Test BatchResult initialization."""
    result = BatchResult()
    assert result.successful == 0
    assert result.skipped == 0
    assert result.failed == 0
    assert result.errors == []


def test_batch_result_string():
    """Test BatchResult string representation."""
    result = BatchResult()
    result.successful = 5
    result.skipped = 2
    result.failed = 1

    str_repr = str(result)
    assert "5" in str_repr
    assert "2" in str_repr
    assert "1" in str_repr


@patch("converter.batch_service.ConverterService")
def test_batch_service_convert_batch_no_files(mock_converter_class):
    """Test batch conversion with no Markdown files."""
    with TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()

        converter = ConverterService()
        batch_service = BatchService(converter)

        result = batch_service.convert_batch(input_dir, output_dir)

        assert result.successful == 0
        assert result.skipped == 0
        assert result.failed == 0


@patch("converter.batch_service.ConverterService")
def test_batch_service_convert_batch_nonexistent_dir(mock_converter_class):
    """Test batch conversion with non-existent input directory."""
    converter = ConverterService()
    batch_service = BatchService(converter)

    with pytest.raises(ConversionError, match="does not exist"):
        batch_service.convert_batch(
            Path("/nonexistent/input"), Path("/nonexistent/output")
        )


@patch("converter.batch_service.parse_frontmatter")
@patch("converter.batch_service.ConverterService")
def test_batch_service_convert_batch_single_file(
    mock_converter_class, mock_parse_frontmatter
):
    """Test batch conversion with a single file."""
    with TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()

        # Create a test Markdown file
        md_file = input_dir / "test.md"
        md_file.write_text("# Test\n\nContent")

        # Mock frontmatter parser
        from converter.frontmatter import FrontmatterData
        mock_parse_frontmatter.return_value = (None, "# Test\n\nContent")

        # Mock converter
        converter = MagicMock(spec=ConverterService)
        converter.convert.return_value = output_dir / "test.docx"

        batch_service = BatchService(converter)
        result = batch_service.convert_batch(input_dir, output_dir, overwrite=True)

        assert result.successful == 1
        assert result.failed == 0
        converter.convert.assert_called_once()


@patch("converter.batch_service.parse_frontmatter")
@patch("converter.batch_service.ConverterService")
def test_batch_service_skip_existing(
    mock_converter_class, mock_parse_frontmatter
):
    """Test that existing files are skipped when overwrite=False."""
    with TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Create a test Markdown file
        md_file = input_dir / "test.md"
        md_file.write_text("# Test\n\nContent")

        # Create existing output file
        existing_output = output_dir / "test.docx"
        existing_output.write_text("existing")

        # Mock frontmatter parser
        mock_parse_frontmatter.return_value = (None, "# Test\n\nContent")

        converter = MagicMock(spec=ConverterService)
        batch_service = BatchService(converter)

        result = batch_service.convert_batch(input_dir, output_dir, overwrite=False)

        assert result.skipped == 1
        assert result.successful == 0
        converter.convert.assert_not_called()
