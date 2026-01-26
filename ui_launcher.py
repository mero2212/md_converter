"""Launcher for Streamlit UI."""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Streamlit UI."""
    ui_app = Path(__file__).parent / "ui_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(ui_app)])


if __name__ == "__main__":
    main()
