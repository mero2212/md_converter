"""Batch conversion service for processing multiple Markdown files."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from converter.converter_service import ConverterService
from converter.errors import ConversionError
from converter.frontmatter import parse_frontmatter
from converter.paths import get_output_filename

logger = logging.getLogger(__name__)


class BatchResult:
    """Result of a batch conversion operation."""

    def __init__(self):
        """Initialize batch result counters."""
        self.successful: int = 0
        self.skipped: int = 0
        self.failed: int = 0
        self.errors: List[Tuple[Path, str]] = []

    def __str__(self) -> str:
        """String representation of batch result."""
        return (
            f"Batch conversion complete: {self.successful} successful, "
            f"{self.skipped} skipped, {self.failed} failed"
        )


class BatchService:
    """Service for batch converting multiple Markdown files."""

    def __init__(self, converter_service: ConverterService):
        """
        Initialize batch service.

        Args:
            converter_service: ConverterService instance to use for conversions.
        """
        self.converter = converter_service

    def convert_batch(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = False,
        overwrite: bool = False,
        template_path: Optional[str] = None,
        profile_name: Optional[str] = None,
        formats: Optional[List[str]] = None,
        pdf_engine: Optional[str] = None,
    ) -> BatchResult:
        """
        Convert all Markdown files in a directory.

        Args:
            input_dir: Input directory containing Markdown files.
            output_dir: Output directory for converted files.
            recursive: If True, process subdirectories recursively.
            overwrite: If True, overwrite existing files.
            template_path: Optional template path (only for docx).
            profile_name: Optional profile name.
            formats: List of output formats (e.g., ["docx", "pdf"]). Default: ["docx"].
            pdf_engine: Optional PDF engine (xelatex, lualatex, pdflatex).

        Returns:
            BatchResult with conversion statistics.
        """
        result = BatchResult()

        if not input_dir.exists():
            raise ConversionError(f"Input directory does not exist: {input_dir}")

        if not input_dir.is_dir():
            raise ConversionError(f"Input path is not a directory: {input_dir}")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find all Markdown files
        pattern = "**/*.md" if recursive else "*.md"
        md_files = list(input_dir.glob(pattern))

        if not md_files:
            logger.warning(f"No Markdown files found in {input_dir}")
            return result

        # Determine formats to use
        if formats is None or len(formats) == 0:
            formats = ["docx"]
        else:
            formats = [f.lower() for f in formats]

        logger.info(f"Found {len(md_files)} Markdown file(s) to process")
        logger.info(f"Output formats: {', '.join(formats)}")

        # Track used output filenames to handle collisions
        used_output_names: Dict[Path, int] = {}

        for md_file in md_files:
            # Determine relative path for output structure
            if recursive:
                relative_path = md_file.relative_to(input_dir)
                output_subdir = output_dir / relative_path.parent
            else:
                output_subdir = output_dir

            # Determine base output filename (without extension)
            frontmatter, _ = parse_frontmatter(md_file)
            title = frontmatter.title if frontmatter else None

            # Process each format
            for output_format in formats:
                try:
                    # Generate base output filename for this format
                    base_output_filename = get_output_filename(
                        md_file, title, output_format=output_format
                    )
                    base_output_file = output_subdir / base_output_filename

                    # Handle filename collisions
                    output_file = base_output_file
                    if base_output_file in used_output_names:
                        # Collision detected - generate unique name
                        # Start with base stem (without any existing counter)
                        base_stem = base_output_file.stem
                        # Remove existing counter suffix if present (e.g., "_2")
                        if "_" in base_stem and base_stem.split("_")[-1].isdigit():
                            base_stem = "_".join(base_stem.split("_")[:-1])
                        
                        # Start from 2 (first file uses base name, second uses _2, etc.)
                        counter = 2
                        while output_file in used_output_names or (
                            output_file.exists() and not overwrite
                        ):
                            output_file = output_subdir / f"{base_stem}_{counter}{base_output_file.suffix}"
                            counter += 1
                        used_output_names[output_file] = 0  # Mark this file as used
                        logger.debug(
                            f"Output filename collision resolved: "
                            f"{base_output_filename} -> {output_file.name}"
                        )
                    else:
                        # First use of this base filename
                        used_output_names[base_output_file] = 0
                        used_output_names[output_file] = 0  # Mark this file as used

                    # Check if output exists (per format)
                    if output_file.exists() and not overwrite:
                        logger.info(
                            f"Skipping {md_file.name} -> {output_format} "
                            f"(output exists: {output_file})"
                        )
                        result.skipped += 1
                        continue

                    # Ensure output subdirectory exists
                    output_subdir.mkdir(parents=True, exist_ok=True)

                    # Perform conversion
                    logger.info(f"Converting {md_file} -> {output_file} ({output_format})")
                    self.converter.convert(
                        input_path=str(md_file),
                        output_path=str(output_file),
                        template_path=template_path,
                        profile_name=profile_name,
                        output_format=output_format,
                        pdf_engine=pdf_engine,
                    )
                    result.successful += 1

                except Exception as e:
                    error_msg = str(e)
                    logger.error(
                        f"Failed to convert {md_file} to {output_format}: {error_msg}"
                    )
                    result.failed += 1
                    result.errors.append((md_file, f"{output_format}: {error_msg}"))

        logger.info(str(result))
        return result
