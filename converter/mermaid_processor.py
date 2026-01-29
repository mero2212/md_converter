"""
Mermaid diagram processor for md_converter.
Converts Mermaid code blocks to PNG images before Pandoc conversion.
"""

import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from .errors import MermaidNotFoundError, MermaidRenderError

logger = logging.getLogger(__name__)


# Regex pattern to find mermaid code blocks
MERMAID_PATTERN = re.compile(
    r'```mermaid\s*\n(.*?)\n```',
    re.DOTALL | re.IGNORECASE
)


def find_mermaid_cli() -> Optional[str]:
    """
    Find the Mermaid CLI executable (mmdc).

    Returns:
        Path to mmdc executable, or None if not found.
    """
    mmdc_path = shutil.which("mmdc")
    if mmdc_path:
        return mmdc_path

    # Try common locations on Windows
    common_paths = [
        Path.home() / "AppData" / "Roaming" / "npm" / "mmdc.cmd",
        Path.home() / "AppData" / "Roaming" / "npm" / "mmdc",
    ]

    for path in common_paths:
        if path.exists():
            return str(path)

    return None


def is_mermaid_available() -> bool:
    """Check if Mermaid CLI is available."""
    return find_mermaid_cli() is not None


def has_mermaid_diagrams(content: str) -> bool:
    """
    Check if the content contains Mermaid code blocks.

    Args:
        content: Markdown content to check.

    Returns:
        True if Mermaid blocks are found.
    """
    return bool(MERMAID_PATTERN.search(content))


def extract_mermaid_blocks(content: str) -> List[Tuple[str, str]]:
    """
    Extract all Mermaid code blocks from content.

    Args:
        content: Markdown content.

    Returns:
        List of tuples (full_match, diagram_code).
    """
    matches = []
    for match in MERMAID_PATTERN.finditer(content):
        full_match = match.group(0)
        diagram_code = match.group(1).strip()
        matches.append((full_match, diagram_code))
    return matches


def render_mermaid_to_png(
    diagram_code: str,
    output_path: Path,
    mmdc_path: Optional[str] = None,
    width: int = 800,
    background: str = "white"
) -> None:
    """
    Render a Mermaid diagram to PNG.

    Args:
        diagram_code: Mermaid diagram code.
        output_path: Path where to save the PNG.
        mmdc_path: Path to mmdc executable (auto-detected if None).
        width: Width of the output image.
        background: Background color.

    Raises:
        MermaidNotFoundError: If mmdc is not installed.
        MermaidRenderError: If rendering fails.
    """
    if mmdc_path is None:
        mmdc_path = find_mermaid_cli()

    if mmdc_path is None:
        raise MermaidNotFoundError(
            "Mermaid CLI (mmdc) not found. "
            "Install it with: npm install -g @mermaid-js/mermaid-cli"
        )

    # Create temporary input file for mermaid code
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.mmd',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(diagram_code)
        input_file = Path(f.name)

    try:
        # Build mmdc command
        cmd = [
            mmdc_path,
            "-i", str(input_file),
            "-o", str(output_path),
            "-w", str(width),
            "-b", background,
            "--quiet"
        ]

        logger.debug(f"Running Mermaid CLI: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise MermaidRenderError(f"Mermaid rendering failed: {error_msg}")

        if not output_path.exists():
            raise MermaidRenderError(
                f"Mermaid CLI completed but output file was not created: {output_path}"
            )

    except subprocess.TimeoutExpired:
        raise MermaidRenderError("Mermaid rendering timed out after 30 seconds")
    except FileNotFoundError:
        raise MermaidNotFoundError(
            f"Mermaid CLI not found at: {mmdc_path}. "
            "Install it with: npm install -g @mermaid-js/mermaid-cli"
        )
    finally:
        # Clean up temporary input file
        if input_file.exists():
            input_file.unlink()


def process_mermaid_in_markdown(
    content: str,
    output_dir: Path,
    base_name: str = "diagram"
) -> Tuple[str, List[Path]]:
    """
    Process all Mermaid blocks in Markdown content.

    Replaces Mermaid code blocks with image references.

    Args:
        content: Markdown content with Mermaid blocks.
        output_dir: Directory to save generated images.
        base_name: Base name for generated image files.

    Returns:
        Tuple of (processed_content, list_of_generated_images).

    Raises:
        MermaidNotFoundError: If mmdc is not installed.
        MermaidRenderError: If rendering fails.
    """
    if not has_mermaid_diagrams(content):
        return content, []

    # Check if Mermaid CLI is available
    mmdc_path = find_mermaid_cli()
    if mmdc_path is None:
        logger.warning(
            "Mermaid diagrams found but mmdc not installed. "
            "Diagrams will not be rendered. "
            "Install with: npm install -g @mermaid-js/mermaid-cli"
        )
        return content, []

    output_dir.mkdir(parents=True, exist_ok=True)

    blocks = extract_mermaid_blocks(content)
    generated_images: List[Path] = []
    processed_content = content

    for i, (full_match, diagram_code) in enumerate(blocks, start=1):
        image_name = f"{base_name}_{i}.png"
        image_path = output_dir / image_name

        try:
            logger.info(f"Rendering Mermaid diagram {i}/{len(blocks)}: {image_name}")
            render_mermaid_to_png(diagram_code, image_path, mmdc_path)
            generated_images.append(image_path)

            # Replace code block with image reference
            # Use relative path for portability
            image_ref = f"![Diagram {i}]({image_path.as_posix()})"
            processed_content = processed_content.replace(full_match, image_ref, 1)

        except MermaidRenderError as e:
            logger.error(f"Failed to render diagram {i}: {e}")
            # Keep original code block if rendering fails
            continue

    return processed_content, generated_images


def cleanup_generated_images(images: List[Path]) -> None:
    """
    Remove generated image files.

    Args:
        images: List of image paths to remove.
    """
    for image_path in images:
        try:
            if image_path.exists():
                image_path.unlink()
                logger.debug(f"Cleaned up: {image_path}")
        except OSError as e:
            logger.warning(f"Failed to clean up {image_path}: {e}")
