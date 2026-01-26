"""Tests for PDF conversion."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch, MagicMock

from converter.errors import PDFEngineNotFoundError
from converter.pandoc_wrapper import PandocWrapper


@patch("converter.pandoc_wrapper.subprocess")
@patch("converter.pandoc_wrapper.shutil")
def test_convert_to_pdf(mock_shutil, mock_subprocess):
    """Test converting Markdown to PDF."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
        "xelatex": "/usr/bin/xelatex",
    }.get(cmd)

    mock_subprocess.run.return_value = MagicMock(
        returncode=0, stdout="", stderr=""
    )

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nContent")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".pdf")

        wrapper.convert(
            input_file=input_file,
            output_file=output_file,
            output_format="pdf",
        )

        # Verify pandoc was called with correct arguments
        mock_subprocess.run.assert_called_once()
        call_args = mock_subprocess.run.call_args[0][0]
        assert "--pdf-engine" in call_args
        assert "xelatex" in call_args
        assert "-t" in call_args
        assert "pdf" in call_args

    finally:
        input_file.unlink(missing_ok=True)


@patch("converter.pandoc_wrapper.shutil")
def test_convert_to_pdf_no_engine(mock_shutil):
    """Test PDF conversion fails when no engine is available."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
    }.get(cmd)

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".pdf")

        with pytest.raises(PDFEngineNotFoundError):
            wrapper.convert(
                input_file=input_file,
                output_file=output_file,
                output_format="pdf",
            )

    finally:
        input_file.unlink(missing_ok=True)


@patch("converter.pandoc_wrapper.subprocess")
@patch("converter.pandoc_wrapper.shutil")
def test_convert_to_pdf_with_metadata(mock_shutil, mock_subprocess):
    """Test PDF conversion with metadata."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
        "xelatex": "/usr/bin/xelatex",
    }.get(cmd)

    mock_subprocess.run.return_value = MagicMock(
        returncode=0, stdout="", stderr=""
    )

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".pdf")

        wrapper.convert(
            input_file=input_file,
            output_file=output_file,
            output_format="pdf",
            metadata={"title": "Test Document", "author": "Test Author"},
        )

        # Verify metadata was passed
        call_args = mock_subprocess.run.call_args[0][0]
        assert "-V" in call_args
        assert "title=Test Document" in call_args or any(
            "title=Test Document" in str(arg) for arg in call_args
        )

    finally:
        input_file.unlink(missing_ok=True)


@patch("converter.pandoc_wrapper.subprocess")
@patch("converter.pandoc_wrapper.shutil")
def test_convert_to_pdf_no_template(mock_shutil, mock_subprocess):
    """Test PDF conversion ignores template (templates not supported for PDF yet)."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
        "xelatex": "/usr/bin/xelatex",
    }.get(cmd)

    mock_subprocess.run.return_value = MagicMock(
        returncode=0, stdout="", stderr=""
    )

    wrapper = PandocWrapper()

    with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        f.flush()
        input_file = Path(f.name)

    try:
        output_file = Path(f.name).with_suffix(".pdf")
        template_file = Path("template.docx")

        wrapper.convert(
            input_file=input_file,
            output_file=output_file,
            output_format="pdf",
            template_file=template_file,
        )

        # Verify --reference-doc is NOT in call args for PDF
        call_args = mock_subprocess.run.call_args[0][0]
        assert "--reference-doc" not in call_args

        # Verify that template warning was logged (check via mock)
        # The actual logging happens, but we can't easily test it without
        # more complex logging setup. The important part is the behavior (no --reference-doc).

    finally:
        input_file.unlink(missing_ok=True)
