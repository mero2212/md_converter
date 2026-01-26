"""Configuration settings for the converter."""

import os
from pathlib import Path
from typing import Optional

# Default Pandoc path (None means search in PATH)
PANDOC_PATH: Optional[str] = os.getenv("PANDOC_PATH", None)

# Default template path (None means no template)
DEFAULT_TEMPLATE: Optional[str] = os.getenv("MD_CONVERTER_TEMPLATE", None)

# If DEFAULT_TEMPLATE is set and relative, resolve it relative to project root
if DEFAULT_TEMPLATE:
    template_path = Path(DEFAULT_TEMPLATE)
    if not template_path.is_absolute():
        # Resolve relative to project root
        project_root = Path(__file__).parent
        DEFAULT_TEMPLATE = str(project_root / template_path)
