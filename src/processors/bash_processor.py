"""Compatibility alias for users requesting 'bash processor'."""

from .batch_processor import BatchProcessor


class BashProcessor(BatchProcessor):
    """Alias of BatchProcessor to keep naming compatibility."""

    pass
