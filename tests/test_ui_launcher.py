"""Tests for UI launcher."""

import pytest
import sys
from unittest.mock import patch, MagicMock

import ui_launcher


@patch("ui_launcher.subprocess.run")
def test_ui_launcher_success(mock_run):
    """Test successful UI launch."""
    mock_run.return_value = MagicMock(returncode=0)

    result = ui_launcher.main()
    assert result == 0
    mock_run.assert_called_once()


@patch("ui_launcher.subprocess.run")
def test_ui_launcher_failure(mock_run):
    """Test that UI launch failure is propagated."""
    mock_run.return_value = MagicMock(returncode=1)

    result = ui_launcher.main()
    assert result == 1
    mock_run.assert_called_once()


@patch("ui_launcher.subprocess.run")
def test_ui_launcher_exception(mock_run):
    """Test that exceptions are not caught (will propagate)."""
    mock_run.side_effect = FileNotFoundError("streamlit not found")

    with pytest.raises(FileNotFoundError):
        ui_launcher.main()
