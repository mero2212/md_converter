"""YAML Frontmatter parser for Markdown files."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from converter.errors import FrontmatterError

logger = logging.getLogger(__name__)

# Expected frontmatter fields
FRONTMATTER_FIELDS = {
    "title": str,
    "subtitle": str,
    "author": str,
    "version": str,
    "date": str,
    "customer": str,
    "project": str,
}


class FrontmatterData:
    """Container for parsed frontmatter data."""

    def __init__(self, data: Dict[str, str]):
        """
        Initialize frontmatter data.

        Args:
            data: Dictionary of frontmatter key-value pairs.
        """
        self.title: Optional[str] = data.get("title")
        self.subtitle: Optional[str] = data.get("subtitle")
        self.author: Optional[str] = data.get("author")
        self.version: Optional[str] = data.get("version")
        self.date: Optional[str] = data.get("date")
        self.customer: Optional[str] = data.get("customer")
        self.project: Optional[str] = data.get("project")

    def to_dict(self) -> Dict[str, str]:
        """
        Convert frontmatter data to dictionary.

        Returns:
            Dictionary of frontmatter fields (None values excluded).
        """
        result = {}
        for key in FRONTMATTER_FIELDS.keys():
            value = getattr(self, key, None)
            if value is not None:
                result[key] = value
        return result

    def to_pandoc_variables(self) -> Dict[str, str]:
        """
        Convert frontmatter data to Pandoc variables.

        Returns:
            Dictionary of Pandoc variable assignments.
        """
        variables = {}
        if self.title:
            variables["title"] = self.title
        if self.subtitle:
            variables["subtitle"] = self.subtitle
        if self.author:
            variables["author"] = self.author
        if self.version:
            variables["version"] = self.version
        if self.date:
            variables["date"] = self.date
        if self.customer:
            variables["customer"] = self.customer
        if self.project:
            variables["project"] = self.project
        return variables


def parse_frontmatter(file_path: Path) -> Tuple[Optional[FrontmatterData], str]:
    """
    Parse YAML frontmatter from a Markdown file.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        Tuple of (FrontmatterData or None, remaining markdown content).

    Raises:
        FrontmatterError: If frontmatter is malformed.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback to latin-1 for non-UTF8 files
        logger.warning(
            f"UTF-8 decoding failed for {file_path}, trying latin-1 encoding"
        )
        try:
            content = file_path.read_text(encoding="latin-1")
        except Exception as e:
            raise FrontmatterError(f"Cannot read file with any encoding: {e}") from e
    except Exception as e:
        raise FrontmatterError(f"Cannot read file: {e}") from e

    # Check for frontmatter delimiter at start
    if not content.startswith("---"):
        return None, content

    # Find the closing delimiter
    lines = content.split("\n")
    if len(lines) < 2:
        return None, content

    # Look for closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        # No closing delimiter found, treat as no frontmatter
        logger.debug("Frontmatter start found but no closing delimiter")
        return None, content

    # Extract frontmatter YAML
    frontmatter_lines = lines[1:end_idx]
    frontmatter_yaml = "\n".join(frontmatter_lines)

    # Extract remaining content
    remaining_content = "\n".join(lines[end_idx + 1 :])

    # Parse YAML (simple parser, no external dependency)
    try:
        data = _parse_simple_yaml(frontmatter_yaml)
    except Exception as e:
        raise FrontmatterError(f"Failed to parse YAML frontmatter: {e}") from e

    # Validate and normalize data
    validated_data = _validate_frontmatter(data)

    frontmatter = FrontmatterData(validated_data)
    logger.debug(f"Parsed frontmatter: {frontmatter.to_dict()}")

    return frontmatter, remaining_content


def _parse_simple_yaml(yaml_text: str) -> Dict[str, str]:
    """
    Simple YAML parser for key-value pairs (no nested structures).

    Args:
        yaml_text: YAML text to parse.

    Returns:
        Dictionary of key-value pairs.

    Raises:
        ValueError: If YAML is malformed.
    """
    result = {}
    for line in yaml_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match key: value pattern
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+)$", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()

            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]

            result[key] = value

    return result


def _validate_frontmatter(data: Dict[str, str]) -> Dict[str, str]:
    """
    Validate and normalize frontmatter data.

    Args:
        data: Raw frontmatter data dictionary.

    Returns:
        Validated and normalized data dictionary.

    Raises:
        FrontmatterError: If validation fails.
    """
    validated = {}

    for key, expected_type in FRONTMATTER_FIELDS.items():
        if key not in data:
            continue

        value = data[key]

        # Type validation
        if not isinstance(value, str):
            raise FrontmatterError(
                f"Frontmatter field '{key}' must be a string, got {type(value)}"
            )

        # Special handling for date field
        if key == "date":
            if value:
                # Try to parse and normalize date
                normalized_date = _normalize_date(value)
                if normalized_date:
                    validated[key] = normalized_date
                else:
                    logger.warning(
                        f"Could not parse date '{value}', using as-is"
                    )
                    validated[key] = value
            else:
                # Empty date -> use today
                validated[key] = datetime.now().strftime("%Y-%m-%d")
        else:
            validated[key] = value

    return validated


def _normalize_date(date_str: str) -> Optional[str]:
    """
    Normalize date string to YYYY-MM-DD format.

    Args:
        date_str: Date string in various formats.

    Returns:
        Normalized date string (YYYY-MM-DD) or None if parsing fails.
    """
    if not date_str:
        return None

    # Try common date formats
    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # If no format matches, return None
    return None
