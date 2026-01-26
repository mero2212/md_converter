"""Custom exception classes for the converter."""


class ConverterError(Exception):
    """Base exception for all converter-related errors."""

    pass


class PandocNotFoundError(ConverterError):
    """Raised when Pandoc executable cannot be found."""

    pass


class InvalidFileError(ConverterError):
    """Raised when an input file is invalid or cannot be read."""

    pass


class ConversionError(ConverterError):
    """Raised when the conversion process fails."""

    pass


class FrontmatterError(ConverterError):
    """Raised when frontmatter parsing fails."""

    pass


class ProfileError(ConverterError):
    """Raised when a profile configuration is invalid."""

    pass


class PDFEngineNotFoundError(ConverterError):
    """Raised when PDF engine (LaTeX) cannot be found."""

    pass
