"""Tests for metadata sanitization."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch, MagicMock

from converter.pandoc_wrapper import PandocWrapper


@patch("converter.pandoc_wrapper.subprocess")
@patch("converter.pandoc_wrapper.shutil")
def test_metadata_newlines_removed(mock_shutil, mock_subprocess):
    """Test that newlines in metadata values are removed."""
    mock_shutil.which.return_value = "/usr/bin/pandoc"
    mock_subprocess.run.return_value = MagicMock(
        returncode=0, stdout="", stderr=""
    )

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".docx")

        metadata = {
            "title": "Test\nDocument",
            "author": "John\r\nDoe",
        }

        wrapper.convert(
            input_file=input_file,
            output_file=output_file,
            output_format="docx",
            metadata=metadata,
        )

        # Verify metadata was sanitized (no newlines in command)
        call_args = mock_subprocess.run.call_args[0][0]
        metadata_args = [
            arg for i, arg in enumerate(call_args) if i > 0 and call_args[i - 1] == "-V"
        ]

        # Check that newlines are replaced with spaces
        for arg in metadata_args:
            assert "\n" not in arg
            assert "\r" not in arg
            # Should contain sanitized values
            assert "Test Document" in " ".join(metadata_args) or "John Doe" in " ".join(
                metadata_args
            )

    finally:
        input_file.unlink(missing_ok=True)


@patch("converter.pandoc_wrapper.subprocess")
@patch("converter.pandoc_wrapper.shutil")
def test_metadata_empty_values_skipped(mock_shutil, mock_subprocess):
    """Test that empty metadata values are not passed to Pandoc."""
    mock_shutil.which.return_value = "/usr/bin/pandoc"
    mock_subprocess.run.return_value = MagicMock(
        returncode=0, stdout="", stderr=""
    )

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".docx")

        metadata = {
            "title": "Valid Title",
            "author": "",  # Empty
            "version": "   \n\r  ",  # Only whitespace/newlines
            "project": "Valid Project",
        }

        wrapper.convert(
            input_file=input_file,
            output_file=output_file,
            output_format="docx",
            metadata=metadata,
        )

        # Verify only non-empty metadata was passed
        call_args = mock_subprocess.run.call_args[0][0]
        metadata_pairs = []
        for i, arg in enumerate(call_args):
            if arg == "-V" and i + 1 < len(call_args):
                metadata_pairs.append(call_args[i + 1])

        # Should contain title and project, but not author or version
        metadata_str = " ".join(metadata_pairs)
        assert "title=Valid Title" in metadata_str
        assert "project=Valid Project" in metadata_str
        assert "author=" not in metadata_str
        assert "version=" not in metadata_str

    finally:
        input_file.unlink(missing_ok=True)


@patch("converter.pandoc_wrapper.subprocess")
@patch("converter.pandoc_wrapper.shutil")
def test_metadata_trimmed(mock_shutil, mock_subprocess):
    """Test that metadata values are trimmed."""
    mock_shutil.which.return_value = "/usr/bin/pandoc"
    mock_subprocess.run.return_value = MagicMock(
        returncode=0, stdout="", stderr=""
    )

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".docx")

        metadata = {
            "title": "  Padded Title  ",
        }

        wrapper.convert(
            input_file=input_file,
            output_file=output_file,
            output_format="docx",
            metadata=metadata,
        )

        # Verify metadata was trimmed
        call_args = mock_subprocess.run.call_args[0][0]
        metadata_pairs = []
        for i, arg in enumerate(call_args):
            if arg == "-V" and i + 1 < len(call_args):
                metadata_pairs.append(call_args[i + 1])

        metadata_str = " ".join(metadata_pairs)
        assert "title=Padded Title" in metadata_str
        assert "  " not in metadata_str  # No leading/trailing spaces

    finally:
        input_file.unlink(missing_ok=True)


def test_sanitize_metadata_value():
    """Test the _sanitize_metadata_value method directly."""
    wrapper = PandocWrapper()

    # Test newline removal
    assert wrapper._sanitize_metadata_value("Test\nDocument") == "Test Document"
    assert wrapper._sanitize_metadata_value("Test\r\nDocument") == "Test Document"

    # Test trimming
    assert wrapper._sanitize_metadata_value("  Test  ") == "Test"

    # Test empty values
    assert wrapper._sanitize_metadata_value("") is None
    assert wrapper._sanitize_metadata_value("   ") is None
    assert wrapper._sanitize_metadata_value("\n\r") is None

    # Test normal values
    assert wrapper._sanitize_metadata_value("Normal Value") == "Normal Value"
