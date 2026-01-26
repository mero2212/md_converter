"""Tests for batch output filename collisions."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from converter.batch_service import BatchService
from converter.converter_service import ConverterService


@patch("converter.batch_service.parse_frontmatter")
@patch("converter.batch_service.ConverterService")
def test_batch_collision_same_title(mock_converter_class, mock_parse_frontmatter):
    """Test that batch conversion handles filename collisions from same title."""
    with TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()

        # Create two Markdown files with same title in frontmatter
        md_file1 = input_dir / "file1.md"
        md_file2 = input_dir / "file2.md"
        md_file1.write_text("# Content 1")
        md_file2.write_text("# Content 2")

        # Mock frontmatter parser to return same title for both
        from converter.frontmatter import FrontmatterData

        frontmatter = FrontmatterData({"title": "Same Title"})
        mock_parse_frontmatter.return_value = (frontmatter, "# Content")

        # Mock converter
        converter = MagicMock(spec=ConverterService)
        converter.convert.return_value = output_dir / "output.docx"

        batch_service = BatchService(converter)
        result = batch_service.convert_batch(
            input_dir, output_dir, overwrite=True, formats=["docx"]
        )

        # Both files should be converted
        assert result.successful == 2
        assert converter.convert.call_count == 2

        # Check that different output paths were used
        call_args_list = converter.convert.call_args_list
        output_paths = [str(call[1]["output_path"]) for call in call_args_list]

        # Should have two different paths (one with _2 suffix)
        assert len(set(output_paths)) == 2
        # One should be base name, one should have _2
        base_name = "same-title.docx"
        assert any(base_name in path for path in output_paths)
        assert any("_2.docx" in path for path in output_paths)


@patch("converter.batch_service.parse_frontmatter")
@patch("converter.batch_service.ConverterService")
def test_batch_collision_multiple_formats(mock_converter_class, mock_parse_frontmatter):
    """Test that collisions are handled per format."""
    with TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()

        md_file1 = input_dir / "file1.md"
        md_file2 = input_dir / "file2.md"
        md_file1.write_text("# Content 1")
        md_file2.write_text("# Content 2")

        from converter.frontmatter import FrontmatterData

        frontmatter = FrontmatterData({"title": "Same Title"})
        mock_parse_frontmatter.return_value = (frontmatter, "# Content")

        converter = MagicMock(spec=ConverterService)
        converter.convert.return_value = output_dir / "output.docx"

        batch_service = BatchService(converter)
        result = batch_service.convert_batch(
            input_dir, output_dir, overwrite=True, formats=["docx", "pdf"]
        )

        # Should convert 2 files × 2 formats = 4 conversions
        assert result.successful == 4
        assert converter.convert.call_count == 4

        # Check output paths
        call_args_list = converter.convert.call_args_list
        output_paths = [call[1]["output_path"] for call in call_args_list]

        # Should have unique paths for each file+format combination
        assert len(set(output_paths)) == 4
