"""Command-line interface for Markdown to DOCX converter."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from config import DEFAULT_TEMPLATE, PANDOC_PATH
from converter.batch_service import BatchService
from converter.converter_service import ConverterService
from converter.errors import (
    ConversionError,
    FrontmatterError,
    InvalidFileError,
    MermaidRenderError,
    PandocNotFoundError,
    PDFEngineNotFoundError,
    ProfileError,
)
from converter.profiles import list_profiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Load local profiles if available (not tracked by git)
try:
    import local_profiles  # noqa: F401
    logger.debug("Local profiles loaded successfully")
except ImportError:
    pass  # No local profiles defined - this is fine

# Supported output formats
SUPPORTED_FORMATS = ["docx", "pdf"]


def parse_formats(
    formats_str: Optional[str], default_format: str
) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Parse and validate format string.

    Args:
        formats_str: Comma-separated format string (e.g., "docx,pdf") or None.
        default_format: Default format to use if formats_str is None.

    Returns:
        Tuple of (list of valid formats, error message or None).
        If error_message is not None, the formats list should be ignored.
    """
    if formats_str is not None and formats_str.strip() != "":
        raw_formats = [f.strip().lower() for f in formats_str.split(",")]
        # Filter out empty entries from extra commas/whitespace
        raw_formats = [f for f in raw_formats if f]

        invalid_formats = [f for f in raw_formats if f not in SUPPORTED_FORMATS]
        if invalid_formats:
            return (
                None,
                f"--formats contains invalid value(s): {', '.join(invalid_formats)}. "
                f"Valid formats: {', '.join(SUPPORTED_FORMATS)}",
            )

        formats = [f for f in raw_formats if f in SUPPORTED_FORMATS]
        if not formats:
            return (
                None,
                f"--formats must contain at least one valid format "
                f"({', '.join(SUPPORTED_FORMATS)})",
            )
        # Deduplicate while preserving order (first occurrence wins)
        seen = set()
        deduplicated = []
        for f in formats:
            if f not in seen:
                seen.add(f)
                deduplicated.append(f)
        return deduplicated, None
    return [default_format], None


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Convert Markdown files to Word documents (.docx) or PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file conversion (backward compatible)
  python cli.py input.md output.docx
  python cli.py input.md output.docx --template template.docx

  # Single file with profile
  python cli.py input.md output.docx --profile report

  # Batch conversion
  python cli.py --batch input_folder output_folder
  python cli.py --batch input_folder output_folder --recursive --overwrite
  python cli.py --batch input_folder output_folder --profile angebot --template template.docx

  # PDF export
  python cli.py input.md output.pdf --format pdf
  python cli.py --batch input_folder output_folder --formats docx,pdf
  python cli.py input.md output.pdf --format pdf --pdf-engine xelatex
        """,
    )

    # Mode selection
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Enable batch mode (convert all .md files in a directory)",
    )

    # Single file mode arguments (positional, backward compatible)
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        help="Path to the input Markdown file (.md) or input directory (in batch mode)",
    )

    parser.add_argument(
        "output",
        type=str,
        nargs="?",
        help="Path to the output document (.docx/.pdf) or output directory (in batch mode)",
    )

    # Common options
    parser.add_argument(
        "--template",
        type=str,
        default=DEFAULT_TEMPLATE,
        help="Path to a DOCX template file (optional)",
    )

    parser.add_argument(
        "--profile",
        type=str,
        choices=list_profiles(),
        help=f"Preset profile to use (available: {', '.join(list_profiles())})",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=SUPPORTED_FORMATS,
        default="docx",
        help="Output format (default: docx)",
    )

    parser.add_argument(
        "--formats",
        type=str,
        help="Comma-separated list of output formats (e.g., 'docx,pdf'). "
        "Useful for batch mode to generate multiple formats.",
    )

    parser.add_argument(
        "--pdf-engine",
        type=str,
        choices=["xelatex", "lualatex", "pdflatex"],
        help="PDF engine to use (xelatex, lualatex, pdflatex). "
        "Auto-detected if not specified.",
    )

    parser.add_argument(
        "--pandoc-path",
        type=str,
        default=PANDOC_PATH,
        help="Path to pandoc executable (optional, searches PATH by default)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    # Batch mode specific options
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Process subdirectories recursively (batch mode only)",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing DOCX files (batch mode only)",
    )

    return parser


def handle_single_conversion(args: argparse.Namespace) -> int:
    """
    Handle single file conversion mode.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    if not args.input or not args.output:
        print("✗ Error: Both input and output paths are required in single mode", file=sys.stderr)
        return 1

    # Parse and validate formats
    formats, error = parse_formats(args.formats, args.format)
    if error:
        print(f"✗ Error: {error}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    if output_path.exists() and output_path.is_dir():
        print("✗ Error: Output path must be a file, not a directory", file=sys.stderr)
        return 1

    try:
        converter = ConverterService(pandoc_path=args.pandoc_path)

        # Convert to each format
        output_files = []
        for output_format in formats:
            # Determine output path for this format
            if len(formats) > 1:
                # Multiple formats: adjust extension
                output_path = Path(args.output)
                output_path = output_path.with_suffix(f".{output_format}")
            else:
                output_path = args.output

            output_file = converter.convert(
                input_path=args.input,
                output_path=str(output_path),
                template_path=args.template if args.template else None,
                profile_name=args.profile,
                output_format=output_format,
                pdf_engine=args.pdf_engine,
            )
            output_files.append(output_file)

        if len(output_files) == 1:
            print(f"✓ Successfully converted {args.input} to {output_files[0]}")
        else:
            print(f"✓ Successfully converted {args.input} to {len(output_files)} format(s):")
            for of in output_files:
                print(f"  - {of}")
        return 0

    except PandocNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        print(
            "\nPlease install Pandoc or specify the path using --pandoc-path",
            file=sys.stderr,
        )
        return 1

    except InvalidFileError as e:
        print(f"✗ Error: Invalid input file - {e}", file=sys.stderr)
        return 1

    except FrontmatterError as e:
        print(f"✗ Error: Frontmatter parsing failed - {e}", file=sys.stderr)
        return 1

    except ProfileError as e:
        print(f"✗ Error: Profile error - {e}", file=sys.stderr)
        return 1

    except PDFEngineNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1

    except MermaidRenderError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1

    except ConversionError as e:
        print(f"✗ Error: Conversion failed - {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n✗ Conversion cancelled by user", file=sys.stderr)
        return 130

    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def handle_batch_conversion(args: argparse.Namespace) -> int:
    """
    Handle batch conversion mode.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    if not args.input or not args.output:
        print(
            "✗ Error: Both input and output directories are required in batch mode",
            file=sys.stderr,
        )
        return 1

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    # Parse and validate formats
    formats, error = parse_formats(args.formats, args.format)
    if error:
        print(f"✗ Error: {error}", file=sys.stderr)
        return 1

    if not input_dir.exists():
        print(f"✗ Error: Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1

    if not input_dir.is_dir():
        print(f"✗ Error: Input path is not a directory: {input_dir}", file=sys.stderr)
        return 1

    if output_dir.exists() and not output_dir.is_dir():
        print(f"✗ Error: Output path is not a directory: {output_dir}", file=sys.stderr)
        return 1

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"✗ Error: Cannot create output directory: {e}", file=sys.stderr)
        return 1

    try:
        converter = ConverterService(pandoc_path=args.pandoc_path)
        batch_service = BatchService(converter)

        result = batch_service.convert_batch(
            input_dir=input_dir,
            output_dir=output_dir,
            recursive=args.recursive,
            overwrite=args.overwrite,
            template_path=args.template if args.template else None,
            profile_name=args.profile,
            formats=formats,
            pdf_engine=args.pdf_engine,
        )

        print(f"\n{result}")
        if result.errors:
            print("\nErrors:")
            for file_path, error_msg in result.errors:
                print(f"  - {file_path}: {error_msg}")

        return 0 if result.failed == 0 else 1

    except PandocNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        print(
            "\nPlease install Pandoc or specify the path using --pandoc-path",
            file=sys.stderr,
        )
        return 1

    except ConversionError as e:
        print(f"✗ Error: Batch conversion failed - {e}", file=sys.stderr)
        return 1

    except ProfileError as e:
        print(f"✗ Error: Profile error - {e}", file=sys.stderr)
        return 1

    except PDFEngineNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1

    except MermaidRenderError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n✗ Batch conversion cancelled by user", file=sys.stderr)
        return 130

    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine mode
    if args.batch:
        return handle_batch_conversion(args)
    else:
        return handle_single_conversion(args)


if __name__ == "__main__":
    sys.exit(main())
