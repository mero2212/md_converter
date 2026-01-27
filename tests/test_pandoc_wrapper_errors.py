"""Tests for error handling in PandocWrapper."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch, MagicMock

from converter.errors import ConversionError, PandocNotFoundError
from converter.pandoc_wrapper import PandocWrapper


@patch("converter.pandoc_wrapper.subprocess.run")
@patch("converter.pandoc_wrapper.shutil")
def test_file_not_found_from_stat_race_condition(mock_shutil, mock_run):
    """Test that FileNotFoundError from stat() is handled correctly."""
    mock_shutil.which.return_value = "/usr/bin/pandoc"

    # Simulate race condition: file exists check passes, but stat() fails
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".docx")

        # Create output file so exists() returns True
        output_file.write_text("dummy")
        assert output_file.exists()

        # Create a custom Path subclass that simulates the race condition
        # File exists() returns True, but stat() raises FileNotFoundError
        class BrokenStatPath(type(output_file)):
            """Path that raises FileNotFoundError on stat() to simulate race condition."""
            def stat(self, *args, **kwargs):
                raise FileNotFoundError("File was deleted")

            def exists(self):
                return True  # Always return True to pass the first check

        # Create broken output path
        broken_output = BrokenStatPath(output_file)

        # Test that the exception is caught correctly
        with pytest.raises(ConversionError) as exc_info:
            wrapper.convert(
                input_file=input_file,
                output_file=broken_output,
                output_format="docx",
            )
        assert "deleted after creation" in str(exc_info.value).lower()
        assert "Pandoc executable not found" not in str(exc_info.value)

    finally:
        input_file.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)


@patch("converter.pandoc_wrapper.subprocess.run")
@patch("converter.pandoc_wrapper.shutil")
def test_file_not_found_from_subprocess(mock_shutil, mock_run):
    """Test that FileNotFoundError from subprocess.run() is handled correctly."""
    mock_shutil.which.return_value = "/usr/bin/pandoc"

    # Simulate FileNotFoundError from subprocess.run (Pandoc executable missing)
    mock_run.side_effect = FileNotFoundError("executable not found")

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".docx")

        with pytest.raises(PandocNotFoundError) as exc_info:
            wrapper.convert(
                input_file=input_file,
                output_file=output_file,
                output_format="docx",
            )
        assert "Pandoc executable not found" in str(exc_info.value)

    finally:
        input_file.unlink(missing_ok=True)
