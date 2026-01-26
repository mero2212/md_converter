"""Path and filename utilities."""

import re
import unicodedata
from pathlib import Path
from typing import Optional


def slugify(text: str, max_length: int = 100) -> str:
    """
    Convert a string to a URL-safe slug.

    Args:
        text: Input text to slugify.
        max_length: Maximum length of the resulting slug.

    Returns:
        Slugified string (ASCII-safe, spaces replaced with hyphens).
    """
    if not text:
        return ""

    # Normalize unicode characters (e.g., é -> e)
    text = unicodedata.normalize("NFKD", text)

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)

    # Remove all non-alphanumeric characters except hyphens
    text = re.sub(r"[^\w\-]", "", text)

    # Replace multiple hyphens with single hyphen
    text = re.sub(r"-+", "-", text)

    # Remove leading/trailing hyphens
    text = text.strip("-")

    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length].rstrip("-")

    return text


def get_output_filename(
    input_file: Path,
    title: Optional[str] = None,
    output_naming_pattern: Optional[str] = None,
    output_format: str = "docx",
) -> str:
    """
    Generate output filename based on input file and optional metadata.

    Args:
        input_file: Input Markdown file path.
        title: Optional title from frontmatter.
        output_naming_pattern: Optional naming pattern (e.g., "{title}_{version}.docx").
        output_format: Output format extension (e.g., "docx", "pdf").

    Returns:
        Output filename (without path).
    """
    extension = f".{output_format}" if not output_format.startswith(".") else output_format

    if output_naming_pattern and title:
        # Simple pattern replacement (no full template engine)
        filename = output_naming_pattern.format(title=slugify(title))
        # Ensure correct extension
        if not filename.endswith(extension):
            # Remove any existing extension and add correct one
            base = filename.rsplit(".", 1)[0] if "." in filename else filename
            filename = base + extension
        return filename

    if title:
        # Use slugified title
        return f"{slugify(title)}{extension}"

    # Default: use input filename with correct extension
    return input_file.stem + extension


def resolve_template_path(
    template_path: Optional[str], base_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Resolve a template path (relative or absolute).

    Args:
        template_path: Template path (can be relative or absolute).
        base_dir: Base directory for resolving relative paths.

    Returns:
        Resolved Path object or None if template_path is None.
    """
    if not template_path:
        return None

    template = Path(template_path)
    if template.is_absolute():
        return template

    if base_dir:
        resolved = base_dir / template
        if resolved.exists():
            return resolved

    # Try relative to current working directory
    if template.exists():
        return template.resolve()

    return template  # Return unresolved path (will be checked later)
