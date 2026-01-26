"""Tests for CLI argument parsing."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the CLI module
import cli


def test_cli_parser_single_mode():
    """Test CLI parser for single file mode."""
    parser = cli.create_parser()

    # Test backward compatible single file mode
    args = parser.parse_args(["input.md", "output.docx"])
    assert args.input == "input.md"
    assert args.output == "output.docx"
    assert args.batch is False


def test_cli_parser_batch_mode():
    """Test CLI parser for batch mode."""
    parser = cli.create_parser()

    args = parser.parse_args(["--batch", "input_dir", "output_dir"])
    assert args.batch is True
    assert args.input == "input_dir"
    assert args.output == "output_dir"


def test_cli_parser_with_profile():
    """Test CLI parser with profile option."""
    parser = cli.create_parser()

    args = parser.parse_args(["input.md", "output.docx", "--profile", "report"])
    assert args.profile == "report"


def test_cli_parser_with_template():
    """Test CLI parser with template option."""
    parser = cli.create_parser()

    args = parser.parse_args(
        ["input.md", "output.docx", "--template", "template.docx"]
    )
    assert args.template == "template.docx"


def test_cli_parser_batch_with_options():
    """Test CLI parser for batch mode with options."""
    parser = cli.create_parser()

    args = parser.parse_args([
        "--batch",
        "input_dir",
        "output_dir",
        "--recursive",
        "--overwrite",
        "--profile",
        "angebot",
    ])
    assert args.batch is True
    assert args.recursive is True
    assert args.overwrite is True
    assert args.profile == "angebot"


@patch("cli.ConverterService")
@patch("cli.handle_single_conversion")
def test_main_single_mode(mock_handle_single, mock_converter):
    """Test main() function in single mode."""
    mock_handle_single.return_value = 0

    with patch.object(sys, "argv", ["cli.py", "input.md", "output.docx"]):
        result = cli.main()
        assert result == 0
        mock_handle_single.assert_called_once()


@patch("cli.BatchService")
@patch("cli.handle_batch_conversion")
def test_main_batch_mode(mock_handle_batch, mock_batch):
    """Test main() function in batch mode."""
    mock_handle_batch.return_value = 0

    with patch.object(sys, "argv", ["cli.py", "--batch", "input_dir", "output_dir"]):
        result = cli.main()
        assert result == 0
        mock_handle_batch.assert_called_once()


@patch("cli.ConverterService")
def test_handle_single_conversion_success(mock_converter_class):
    """Test successful single conversion."""
    mock_converter = MagicMock()
    mock_converter_class.return_value = mock_converter
    mock_converter.convert.return_value = Path("output.docx")

    args = MagicMock()
    args.input = "input.md"
    args.output = "output.docx"
    args.template = None
    args.profile = None
    args.pandoc_path = None
    args.formats = None
    args.format = "docx"
    args.pdf_engine = None

    result = cli.handle_single_conversion(args)
    assert result == 0
    mock_converter.convert.assert_called_once()


@patch("cli.ConverterService")
def test_handle_single_conversion_missing_args(mock_converter_class):
    """Test single conversion with missing arguments."""
    args = MagicMock()
    args.input = None
    args.output = None

    result = cli.handle_single_conversion(args)
    assert result == 1


@patch("cli.ConverterService")
def test_handle_batch_conversion_missing_args(mock_converter_class):
    """Test batch conversion with missing arguments."""
    args = MagicMock()
    args.input = None
    args.output = None

    result = cli.handle_batch_conversion(args)
    assert result == 1
