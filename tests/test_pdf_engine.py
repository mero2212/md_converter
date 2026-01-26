"""Tests for PDF engine detection."""

import pytest
from unittest.mock import patch, MagicMock

from converter.errors import PDFEngineNotFoundError
from converter.pandoc_wrapper import PandocWrapper


@patch("converter.pandoc_wrapper.shutil")
def test_find_pdf_engine_xelatex_available(mock_shutil):
    """Test finding xelatex when available."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
        "xelatex": "/usr/bin/xelatex",
    }.get(cmd)

    wrapper = PandocWrapper()
    engine = wrapper._find_pdf_engine()
    assert engine == "xelatex"


@patch("converter.pandoc_wrapper.shutil")
def test_find_pdf_engine_lualatex_fallback(mock_shutil):
    """Test falling back to lualatex when xelatex not available."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
        "lualatex": "/usr/bin/lualatex",
    }.get(cmd)

    wrapper = PandocWrapper()
    engine = wrapper._find_pdf_engine()
    assert engine == "lualatex"


@patch("converter.pandoc_wrapper.shutil")
def test_find_pdf_engine_pdflatex_fallback(mock_shutil):
    """Test falling back to pdflatex when xelatex and lualatex not available."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
        "pdflatex": "/usr/bin/pdflatex",
    }.get(cmd)

    wrapper = PandocWrapper()
    engine = wrapper._find_pdf_engine()
    assert engine == "pdflatex"


@patch("converter.pandoc_wrapper.shutil")
def test_find_pdf_engine_none_available(mock_shutil):
    """Test error when no PDF engine is available."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
    }.get(cmd)

    wrapper = PandocWrapper()
    with pytest.raises(PDFEngineNotFoundError, match="No PDF engine"):
        wrapper._find_pdf_engine()


@patch("converter.pandoc_wrapper.shutil")
def test_find_pdf_engine_preferred(mock_shutil):
    """Test using preferred PDF engine."""
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
        "lualatex": "/usr/bin/lualatex",
    }.get(cmd)

    wrapper = PandocWrapper()
    engine = wrapper._find_pdf_engine("lualatex")
    assert engine == "lualatex"


@patch("converter.pandoc_wrapper.shutil")
def test_check_pdf_engine_available(mock_shutil):
    """Test checking if PDF engine is available."""
    mock_shutil.which.return_value = "/usr/bin/xelatex"

    wrapper = PandocWrapper()
    result = wrapper._check_pdf_engine("xelatex")
    assert result is True


@patch("converter.pandoc_wrapper.shutil")
def test_check_pdf_engine_not_available(mock_shutil):
    """Test checking if PDF engine is not available."""
    # Mock pandoc found, but xelatex not found
    mock_shutil.which.side_effect = lambda cmd: {
        "pandoc": "/usr/bin/pandoc",
        "xelatex": None,
    }.get(cmd)

    wrapper = PandocWrapper()
    result = wrapper._check_pdf_engine("xelatex")
    assert result is False
