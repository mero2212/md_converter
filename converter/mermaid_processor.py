"""
Mermaid diagram processor for md_converter.
Converts Mermaid code blocks to SVG/PNG images before Pandoc conversion.
"""

import hashlib
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from .errors import MermaidRenderError

logger = logging.getLogger(__name__)


# Regex pattern to find mermaid code blocks
MERMAID_PATTERN = re.compile(
    r'```mermaid\s*\n(.*?)\n```',
    re.DOTALL | re.IGNORECASE
)

DEFAULT_PNG_DPI = 300
DEFAULT_PNG_SCALE = DEFAULT_PNG_DPI / 96.0


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


def _hash_mermaid_code(diagram_code: str) -> str:
    """Create a stable hash based on Mermaid diagram content."""
    return hashlib.sha256(diagram_code.encode("utf-8")).hexdigest()


def _run_mermaid_cli(
    cmd: List[str],
    output_path: Path
) -> None:
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


def render_mermaid_to_svg_and_png(
    diagram_code: str,
    svg_path: Path,
    png_path: Path,
    mmdc_path: Optional[str] = None,
    width: int = 800,
    background: str = "white",
    png_scale: float = DEFAULT_PNG_SCALE
) -> None:
    """
    Render a Mermaid diagram to SVG and PNG.

    Args:
        diagram_code: Mermaid diagram code.
        svg_path: Path where to save the SVG.
        png_path: Path where to save the PNG.
        mmdc_path: Path to mmdc executable (auto-detected if None).
        width: Width of the output image.
        background: Background color.
        png_scale: Scale factor for PNG rendering.

    Raises:
        MermaidRenderError: If rendering fails or mmdc is not installed.
    """
    if mmdc_path is None:
        mmdc_path = find_mermaid_cli()

    if mmdc_path is None:
        raise MermaidRenderError(
            "Mermaid CLI (mmdc) not found – diagrams cannot be rendered."
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
        if not svg_path.exists():
            cmd = [
                mmdc_path,
                "-i", str(input_file),
                "-o", str(svg_path),
                "-w", str(width),
                "-b", background,
                "--quiet"
            ]
            logger.debug(f"Running Mermaid CLI (svg): {' '.join(cmd)}")
            _run_mermaid_cli(cmd, svg_path)

        if not png_path.exists():
            cmd = [
                mmdc_path,
                "-i", str(input_file),
                "-o", str(png_path),
                "-w", str(width),
                "-b", background,
                "--scale", str(png_scale),
                "--quiet"
            ]
            logger.debug(f"Running Mermaid CLI (png): {' '.join(cmd)}")
            _run_mermaid_cli(cmd, png_path)

    except subprocess.TimeoutExpired:
        raise MermaidRenderError("Mermaid rendering timed out after 30 seconds")
    except FileNotFoundError:
        raise MermaidRenderError(
            "Mermaid CLI (mmdc) not found – diagrams cannot be rendered."
        )
    finally:
        # Clean up temporary input file
        if input_file.exists():
            input_file.unlink()


def process_mermaid_in_markdown(
    content: str,
    base_dir: Path,
    output_format: str
) -> Tuple[str, List[Path]]:
    """
    Process all Mermaid blocks in Markdown content.

    Replaces Mermaid code blocks with image references.

    Args:
        content: Markdown content with Mermaid blocks.
        base_dir: Base directory used to resolve output paths.
        output_format: Output format ("docx" or "pdf").

    Returns:
        Tuple of (processed_content, list_of_generated_images).

    Raises:
        MermaidRenderError: If rendering fails or mmdc is not installed.
    """
    if not has_mermaid_diagrams(content):
        return content, []

    output_format = output_format.lower().strip()
    mmdc_path = find_mermaid_cli()
    if mmdc_path is None:
        raise MermaidRenderError(
            "Mermaid CLI (mmdc) not found - diagrams cannot be rendered."
        )

    output_dir = base_dir / "_assets" / "diagrams"
    output_dir.mkdir(parents=True, exist_ok=True)

    blocks = extract_mermaid_blocks(content)
    generated_images: List[Path] = []
    processed_content = content

    for i, (full_match, diagram_code) in enumerate(blocks, start=1):
        diagram_hash = _hash_mermaid_code(diagram_code)
        svg_path = output_dir / f"{diagram_hash}.svg"
        png_path = output_dir / f"{diagram_hash}.png"

        logger.info(f"Rendering Mermaid diagram {i}/{len(blocks)}: {diagram_hash}")
        render_mermaid_to_svg_and_png(
            diagram_code,
            svg_path,
            png_path,
            mmdc_path
        )
        generated_images.extend([svg_path, png_path])

        image_path = svg_path if output_format == "pdf" else png_path
        relative_path = image_path.relative_to(base_dir)
        image_ref = f"![]({relative_path.as_posix()})"
        processed_content = processed_content.replace(full_match, image_ref, 1)

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
