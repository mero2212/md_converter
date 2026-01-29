"""Service layer for Markdown to DOCX conversion."""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from converter.errors import ConversionError, InvalidFileError
from converter.frontmatter import parse_frontmatter
from converter.mermaid_processor import (
    cleanup_generated_images,
    has_mermaid_diagrams,
    is_mermaid_available,
    process_mermaid_in_markdown,
)
from converter.pandoc_wrapper import PandocWrapper
from converter.paths import get_output_filename, resolve_template_path
from converter.profiles import Profile, get_profile

logger = logging.getLogger(__name__)


class ConverterService:
    """Service for converting Markdown files to DOCX format."""

    def __init__(self, pandoc_path: Optional[str] = None):
        """
        Initialize the converter service.

        Args:
            pandoc_path: Optional path to pandoc executable.
        """
        self.pandoc_wrapper = PandocWrapper(pandoc_path)

    def convert(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        template_path: Optional[str] = None,
        profile_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        additional_args: Optional[List[str]] = None,
        output_format: str = "docx",
        pdf_engine: Optional[str] = None,
    ) -> Path:
        """
        Convert a Markdown file to DOCX or PDF.

        Args:
            input_path: Path to the input Markdown file.
            output_path: Path to the output file. If None, generated from input.
            template_path: Optional path to a DOCX template file (overrides profile, only for docx).
            profile_name: Optional profile name (e.g., "report", "angebot").
            metadata: Optional metadata dictionary (overrides frontmatter).
            additional_args: Optional additional Pandoc arguments (appended to profile args).
            output_format: Output format ("docx" or "pdf").
            pdf_engine: Optional PDF engine (xelatex, lualatex, pdflatex). Auto-detected if None.

        Returns:
            Path to the output file.

        Raises:
            InvalidFileError: If the input file is invalid.
            ConversionError: If the conversion fails.
        """
        input_file = Path(input_path)

        # Validate input file
        if not input_file.exists():
            raise InvalidFileError(f"Input file does not exist: {input_file}")

        if not input_file.is_file():
            raise InvalidFileError(f"Input path is not a file: {input_file}")

        if not input_file.suffix.lower() == ".md":
            logger.warning(
                f"Input file does not have .md extension: {input_file.suffix}"
            )

        # Parse frontmatter
        frontmatter, content = parse_frontmatter(input_file)
        frontmatter_metadata = frontmatter.to_pandoc_variables() if frontmatter else {}

        # Process Mermaid diagrams if present
        mermaid_images: List[Path] = []
        processed_input_file = input_file
        temp_markdown_file: Optional[Path] = None

        if has_mermaid_diagrams(content):
            if is_mermaid_available():
                logger.info("Processing Mermaid diagrams...")
                # Create temp directory for images next to input file
                mermaid_output_dir = input_file.parent / ".mermaid_temp"
                try:
                    processed_content, mermaid_images = process_mermaid_in_markdown(
                        content,
                        mermaid_output_dir,
                        base_name=input_file.stem
                    )

                    if mermaid_images:
                        # Create temp file with processed content
                        temp_fd, temp_path = tempfile.mkstemp(
                            suffix='.md',
                            prefix='mermaid_',
                            dir=input_file.parent
                        )
                        temp_markdown_file = Path(temp_path)
                        with open(temp_fd, 'w', encoding='utf-8') as f:
                            f.write(processed_content)
                        processed_input_file = temp_markdown_file
                        logger.info(f"Rendered {len(mermaid_images)} Mermaid diagram(s)")
                except Exception as e:
                    logger.warning(f"Mermaid processing failed, using original content: {e}")
            else:
                logger.warning(
                    "Mermaid diagrams found but mmdc not installed. "
                    "Install with: npm install -g @mermaid-js/mermaid-cli"
                )

        # Merge metadata (explicit metadata overrides frontmatter)
        # Log overrides for transparency
        if metadata:
            for key in metadata.keys():
                if key in frontmatter_metadata:
                    logger.debug(
                        f"Metadata key '{key}' overridden by explicit metadata "
                        f"(frontmatter: '{frontmatter_metadata[key]}' -> explicit: '{metadata[key]}')"
                    )

        final_metadata = {**frontmatter_metadata, **(metadata or {})}

        # Get profile if specified
        profile: Optional[Profile] = None
        if profile_name:
            try:
                profile = get_profile(profile_name)
                logger.info(f"Using profile: {profile_name}")
            except Exception as e:
                logger.warning(f"Could not load profile '{profile_name}': {e}")

        # Determine template path (CLI arg > profile > None)
        resolved_template: Optional[Path] = None
        if template_path:
            resolved_template = resolve_template_path(template_path, input_file.parent)
        elif profile and profile.default_template:
            resolved_template = profile.get_template_path(input_file.parent)

        if resolved_template and not resolved_template.exists():
            logger.warning(f"Template not found: {resolved_template}")
            resolved_template = None

        # Determine output format (profile default > explicit > docx)
        if profile and profile.default_formats:
            # Use first format from profile if not explicitly set
            if output_format == "docx" and len(profile.default_formats) > 0:
                output_format = profile.default_formats[0]

        # Determine output path
        if output_path:
            output_file = Path(output_path)
            if output_file.exists() and output_file.is_dir():
                raise InvalidFileError(
                    f"Output path must be a file, not a directory: {output_file}"
                )
        elif profile and profile.output_naming and frontmatter and frontmatter.title:
            # Use profile naming pattern
            filename = get_output_filename(
                input_file, frontmatter.title, profile.output_naming, output_format
            )
            output_file = input_file.parent / filename
        else:
            # Default: same name with correct extension
            output_file = input_file.with_suffix(f".{output_format}")

        # Ensure output directory exists
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConversionError(
                f"Cannot create output directory '{output_file.parent}': {e}"
            ) from e

        # Collect Pandoc arguments
        pandoc_args = []
        if profile:
            pandoc_args.extend(profile.pandoc_args)
        if additional_args:
            pandoc_args.extend(additional_args)

        logger.info(
            f"Converting {input_file.name} to {output_file.name} "
            f"(format: {output_format})"
        )

        try:
            self.pandoc_wrapper.convert(
                input_file=processed_input_file,
                output_file=output_file,
                output_format=output_format,
                template_file=resolved_template,
                metadata=final_metadata if final_metadata else None,
                additional_args=pandoc_args if pandoc_args else None,
                pdf_engine=pdf_engine,
            )
            logger.info(
                f"Successfully converted {input_file.name} to {output_file.name}"
            )
            return output_file
        except ConversionError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error during conversion: {str(e)}"
            logger.error(error_msg)
            raise ConversionError(error_msg) from e
        finally:
            # Clean up Mermaid temporary files
            if temp_markdown_file and temp_markdown_file.exists():
                try:
                    temp_markdown_file.unlink()
                except OSError:
                    pass
            if mermaid_images:
                cleanup_generated_images(mermaid_images)
                # Try to remove temp directory if empty
                mermaid_temp_dir = input_file.parent / ".mermaid_temp"
                if mermaid_temp_dir.exists():
                    try:
                        mermaid_temp_dir.rmdir()
                    except OSError:
                        pass  # Directory not empty or other error
