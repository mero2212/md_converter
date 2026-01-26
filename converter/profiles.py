"""Preset profiles for document conversion."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from converter.errors import ProfileError

logger = logging.getLogger(__name__)


class Profile:
    """Represents a conversion profile with default settings."""

    def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        default_template: Optional[str] = None,
        pandoc_args: Optional[List[str]] = None,
        output_naming: Optional[str] = None,
        default_formats: Optional[List[str]] = None,
        toc: bool = False,
        number_sections: bool = False,
    ):
        """
        Initialize a profile.

        Args:
            name: Profile identifier (lowercase, no spaces).
            display_name: Human-readable name for UI display.
            description: Short description of the profile's purpose.
            default_template: Default template path (relative or absolute).
            pandoc_args: Additional Pandoc arguments.
            output_naming: Output naming pattern (e.g., "{title}_{version}.docx").
            default_formats: Default output formats (e.g., ["docx", "pdf"]).
            toc: Whether to include table of contents.
            number_sections: Whether to number sections.
        """
        self.name = name
        self.display_name = display_name or name.capitalize()
        self.description = description or ""
        self.default_template = default_template
        self.output_naming = output_naming
        self.default_formats = default_formats or ["docx"]
        self.toc = toc
        self.number_sections = number_sections

        # Build pandoc_args from settings
        self.pandoc_args = list(pandoc_args or [])
        if toc and "--toc" not in self.pandoc_args:
            self.pandoc_args.append("--toc")
        if number_sections and "--number-sections" not in self.pandoc_args:
            self.pandoc_args.append("--number-sections")

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
        display_name="Angebot",
        description="Angebotsdokumente mit Inhaltsverzeichnis",
        default_template=None,  # Can be set to "templates/angebot.docx"
        output_naming="{title}_Angebot.docx",
        toc=True,
        number_sections=True,
    ),
    "bericht": Profile(
        name="bericht",
        display_name="Bericht",
        description="Berichte und Reports mit nummerierter Gliederung",
        default_template=None,  # Can be set to "templates/bericht.docx"
        pandoc_args=["--standalone"],
        output_naming="{title}_Bericht.docx",
        toc=True,
        number_sections=True,
    ),
    "analyse": Profile(
        name="analyse",
        display_name="Analyse",
        description="Analysedokumente mit detaillierter Struktur",
        default_template=None,  # Can be set to "templates/analyse.docx"
        output_naming="{title}_Analyse.docx",
        toc=True,
        number_sections=True,
    ),
    "script": Profile(
        name="script",
        display_name="Script",
        description="Schulungsunterlagen und Scripts",
        default_template=None,  # Can be set to "templates/script.docx"
        output_naming="{title}_Script.docx",
        toc=True,
        number_sections=False,
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


def list_profiles_for_ui() -> List[Dict[str, str]]:
    """
    List all profiles with display information for UI.

    Returns:
        List of dicts with name, display_name, and description.
    """
    return [
        {
            "name": p.name,
            "display_name": p.display_name,
            "description": p.description,
        }
        for p in PROFILES.values()
    ]


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
