"""Launcher for Streamlit UI."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """
    Launch the Streamlit UI.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    ui_app = Path(__file__).parent / "ui_app.py"
    result = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(ui_app)]
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
