"""Custom exceptions for the conversion toolkit"""

class ConversionError(Exception):
    """Base exception for conversion errors"""
    pass


class UnsupportedFormatError(ConversionError):
    """Raised when format is not supported"""
    pass


class ConversionFailedError(ConversionError):
    """Raised when conversion process fails"""
    pass


class ValidationError(ConversionError):
    """Raised when input validation fails"""
    pass


class DependencyMissingError(ConversionError):
    """Raised when required dependency is missing"""
    pass


class FileTooLargeError(ConversionError):
    """Raised when file exceeds size limit"""
    pass


class BatchProcessingError(Exception):
    """Raised when batch processing fails"""
    pass