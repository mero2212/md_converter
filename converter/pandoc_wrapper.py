"""Wrapper for Pandoc command-line tool."""

import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from converter.errors import (
    ConversionError,
    PandocNotFoundError,
    PDFEngineNotFoundError,
)

logger = logging.getLogger(__name__)


class PandocWrapper:
    """Wraps Pandoc command-line calls for Markdown to DOCX conversion."""

    def __init__(self, pandoc_path: Optional[str] = None):
        """
        Initialize the Pandoc wrapper.

        Args:
            pandoc_path: Optional path to pandoc executable.
                        If None, searches for 'pandoc' in PATH.
        """
        self.pandoc_path = self._find_pandoc(pandoc_path)
        logger.info(f"Using Pandoc at: {self.pandoc_path}")

    def _find_pandoc(self, pandoc_path: Optional[str]) -> str:
        """
        Find the Pandoc executable.

        Args:
            pandoc_path: Optional explicit path to pandoc.

        Returns:
            Path to pandoc executable.

        Raises:
            PandocNotFoundError: If pandoc cannot be found.
        """
        if pandoc_path:
            pandoc_path_obj = Path(pandoc_path)
            if pandoc_path_obj.exists() and pandoc_path_obj.is_file():
                return str(pandoc_path_obj.resolve())
            raise PandocNotFoundError(
                f"Pandoc not found at specified path: {pandoc_path}"
            )

        # Search in PATH
        pandoc_cmd = shutil.which("pandoc")
        if pandoc_cmd:
            return pandoc_cmd

        raise PandocNotFoundError(
            "Pandoc not found. Please install Pandoc or specify the path in config."
        )

    def _check_pdf_engine(self, engine: str = "xelatex") -> bool:
        """
        Check if a PDF engine (LaTeX) is available.

        Args:
            engine: PDF engine name (xelatex, lualatex, pdflatex).

        Returns:
            True if engine is available, False otherwise.
        """
        engine_cmd = shutil.which(engine)
        if engine_cmd:
            logger.debug(f"PDF engine '{engine}' found at: {engine_cmd}")
            return True
        logger.debug(f"PDF engine '{engine}' not found in PATH")
        return False

    def _sanitize_metadata_value(self, value: str) -> Optional[str]:
        """
        Sanitize a metadata value for Pandoc.

        Args:
            value: Raw metadata value.

        Returns:
            Sanitized value or None if value is empty after sanitization.
        """
        # Ensure value is a string
        value = str(value)

        # Replace newlines and carriage returns with spaces
        value = value.replace("\n", " ").replace("\r", " ")

        # Normalize multiple spaces to single space
        value = re.sub(r" +", " ", value)

        # Trim whitespace
        value = value.strip()

        # Return None if empty (will be skipped)
        if not value:
            logger.debug("Metadata value is empty after sanitization, will be skipped")
            return None

        return value

    def _find_pdf_engine(self, preferred_engine: Optional[str] = None) -> str:
        """
        Find an available PDF engine.

        Args:
            preferred_engine: Preferred engine (xelatex, lualatex, pdflatex).
                             If None, tries xelatex, lualatex, pdflatex in order.

        Returns:
            Name of available PDF engine.

        Raises:
            PDFEngineNotFoundError: If no PDF engine is available.
        """
        engines_to_try = []
        if preferred_engine:
            engines_to_try.append(preferred_engine)

        # Default order: xelatex, lualatex, pdflatex
        default_order = ["xelatex", "lualatex", "pdflatex"]
        for engine in default_order:
            if engine not in engines_to_try:
                engines_to_try.append(engine)

        for engine in engines_to_try:
            if self._check_pdf_engine(engine):
                logger.info(f"Using PDF engine: {engine}")
                return engine

        # No engine found
        error_msg = (
            "No PDF engine (LaTeX) found. Please install a LaTeX distribution:\n"
            "- Windows: MiKTeX (https://miktex.org/) or TeX Live (https://www.tug.org/texlive/)\n"
            "- Linux: texlive-xetex, texlive-luatex, or texlive-latex-base\n"
            "- macOS: MacTeX (https://www.tug.org/mactex/)"
        )
        raise PDFEngineNotFoundError(error_msg)

    def convert(
        self,
        input_file: Path,
        output_file: Path,
        output_format: str = "docx",
        template_file: Optional[Path] = None,
        metadata: Optional[Dict[str, str]] = None,
        additional_args: Optional[List[str]] = None,
        pdf_engine: Optional[str] = None,
    ) -> None:
        """
        Convert a Markdown file to DOCX or PDF using Pandoc.

        Args:
            input_file: Path to the input Markdown file.
            output_file: Path to the output file.
            output_format: Output format ("docx" or "pdf").
            template_file: Optional path to a DOCX template file (only for docx).
            metadata: Optional dictionary of metadata variables for Pandoc.
            additional_args: Optional list of additional Pandoc arguments.
            pdf_engine: Optional PDF engine (xelatex, lualatex, pdflatex).
                       If None, auto-detects available engine.

        Raises:
            ConversionError: If the conversion fails.
            PDFEngineNotFoundError: If PDF format requested but no engine available.
        """
        if not input_file.exists():
            raise ConversionError(f"Input file does not exist: {input_file}")

        if not input_file.is_file():
            raise ConversionError(f"Input path is not a file: {input_file}")

        output_format = output_format.lower()
        if output_format not in ["docx", "pdf"]:
            raise ConversionError(
                f"Unsupported output format: {output_format}. Supported: docx, pdf"
            )

        # Check PDF engine if needed
        if output_format == "pdf":
            engine = self._find_pdf_engine(pdf_engine)
        else:
            engine = None

        # Build Pandoc command
        cmd = [
            self.pandoc_path,
            str(input_file.resolve()),
            "-f",
            "markdown",
            "-t",
            output_format,
            "-o",
            str(output_file.resolve()),
        ]

        # Add PDF engine if converting to PDF
        if output_format == "pdf" and engine:
            cmd.extend(["--pdf-engine", engine])

        # Add template if provided (only for DOCX)
        if template_file and output_format == "docx":
            if not template_file.exists():
                logger.warning(
                    f"Template file does not exist: {template_file}. "
                    "Continuing without template."
                )
            else:
                cmd.extend(["--reference-doc", str(template_file.resolve())])
        elif template_file and output_format == "pdf":
            logger.info(
                "DOCX template ignored for PDF output. "
                "LaTeX template support will be added in a future version."
            )

        # Add metadata variables (with sanitization)
        if metadata:
            for key, value in metadata.items():
                sanitized_value = self._sanitize_metadata_value(value)
                if sanitized_value is not None:
                    cmd.extend(["-V", f"{key}={sanitized_value}"])
                # If sanitized_value is None, the key is skipped (already logged in _sanitize_metadata_value)

        # Add additional arguments (from profile, etc.)
        if additional_args:
            cmd.extend(additional_args)

        # Logging: INFO shows summary, DEBUG shows full command
        logger.info(
            f"Running Pandoc (format={output_format}, "
            f"input={input_file.name}, output={output_file.name})"
        )
        logger.debug(f"Full Pandoc command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            # Validate output file was created and has content
            if not output_file.exists():
                raise ConversionError(
                    f"Pandoc completed but output file was not created: {output_file}"
                )
            if output_file.stat().st_size == 0:
                raise ConversionError(
                    f"Pandoc completed but output file is empty: {output_file}"
                )

            logger.info("Conversion completed successfully")
            if result.stdout:
                logger.debug(f"Pandoc stdout: {result.stdout}")
        except subprocess.CalledProcessError as e:
            error_msg = f"Pandoc conversion failed: {e.stderr or str(e)}"
            logger.error(error_msg)
            raise ConversionError(error_msg) from e
        except FileNotFoundError as e:
            error_msg = f"Pandoc executable not found: {self.pandoc_path}"
            logger.error(error_msg)
            raise PandocNotFoundError(error_msg) from e

    def convert_md_to_docx(
        self,
        input_file: Path,
        output_file: Path,
        template_file: Optional[Path] = None,
        metadata: Optional[Dict[str, str]] = None,
        additional_args: Optional[List[str]] = None,
    ) -> None:
        """
        Convert a Markdown file to a DOCX file using Pandoc.

        This is a convenience method that calls convert() with format="docx".

        Args:
            input_file: Path to the input Markdown file.
            output_file: Path to the output DOCX file.
            template_file: Optional path to a DOCX template file.
            metadata: Optional dictionary of metadata variables for Pandoc.
            additional_args: Optional list of additional Pandoc arguments.

        Raises:
            ConversionError: If the conversion fails.
        """
        self.convert(
            input_file=input_file,
            output_file=output_file,
            output_format="docx",
            template_file=template_file,
            metadata=metadata,
            additional_args=additional_args,
        )
