"""Custom exceptions for sphinx-coverage-report."""


class CoverageReportError(Exception):
    """Base class for all sphinx-coverage-report errors."""


class CoverageReportFileNotFound(CoverageReportError):
    """Raised when a referenced coverage file does not exist."""


class CoverageReportFileInvalid(CoverageReportError):
    """Raised when a coverage file cannot be parsed."""


class CoverageReportInvalidOption(CoverageReportError):
    """Raised when a directive option has an invalid value."""
