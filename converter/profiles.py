"""Preset profiles for document conversion."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from converter.errors import ProfileError

logger = logging.getLogger(__name__)


class Profile:
    """Represents a conversion profile with default settings."""

    def __init__(
        self,
        name: str,
        default_template: Optional[str] = None,
        pandoc_args: Optional[List[str]] = None,
        output_naming: Optional[str] = None,
        default_formats: Optional[List[str]] = None,
    ):
        """
        Initialize a profile.

        Args:
            name: Profile name.
            default_template: Default template path (relative or absolute).
            pandoc_args: Additional Pandoc arguments (e.g., ["--toc", "--number-sections"]).
            output_naming: Output naming pattern (e.g., "{title}_{version}.docx").
            default_formats: Default output formats (e.g., ["docx", "pdf"]).
        """
        self.name = name
        self.default_template = default_template
        self.pandoc_args = pandoc_args or []
        self.output_naming = output_naming
        self.default_formats = default_formats or ["docx"]

    def get_template_path(self, base_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Resolve template path for this profile.

        Args:
            base_dir: Base directory for resolving relative paths.

        Returns:
            Resolved template path or None.
        """
        if not self.default_template:
            return None

        template = Path(self.default_template)
        if template.is_absolute():
            return template if template.exists() else None

        if base_dir:
            resolved = base_dir / template
            if resolved.exists():
                return resolved

        # Try relative to current working directory
        if template.exists():
            return template.resolve()

        return None


# Built-in profiles
PROFILES: Dict[str, Profile] = {
    "angebot": Profile(
        name="angebot",
        default_template=None,  # Can be set to "templates/angebot.docx"
        pandoc_args=["--toc", "--number-sections"],
        output_naming="{title}_Angebot.docx",
    ),
    "report": Profile(
        name="report",
        default_template=None,  # Can be set to "templates/report.docx"
        pandoc_args=["--toc", "--number-sections", "--standalone"],
        output_naming="{title}_Report.docx",
    ),
    "schulung": Profile(
        name="schulung",
        default_template=None,  # Can be set to "templates/schulung.docx"
        pandoc_args=["--toc"],
        output_naming="{title}_Schulung.docx",
    ),
}


def get_profile(name: str) -> Profile:
    """
    Get a profile by name.

    Args:
        name: Profile name.

    Returns:
        Profile object.

    Raises:
        ProfileError: If profile does not exist.
    """
    if name not in PROFILES:
        available = ", ".join(PROFILES.keys())
        raise ProfileError(
            f"Profile '{name}' not found. Available profiles: {available}"
        )

    return PROFILES[name]


def list_profiles() -> List[str]:
    """
    List all available profile names.

    Returns:
        List of profile names.
    """
    return list(PROFILES.keys())


def register_profile(profile: Profile) -> None:
    """
    Register a custom profile.

    Args:
        profile: Profile object to register.

    Raises:
        ProfileError: If profile name is invalid.
    """
    if not profile.name:
        raise ProfileError("Profile name cannot be empty")

    PROFILES[profile.name] = profile
    logger.info(f"Registered custom profile: {profile.name}")
