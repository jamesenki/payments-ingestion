"""
Storage components for raw events, metrics, and aggregates.
"""

from .raw_event import RawEvent, BufferError, StorageError
from .parquet_serializer import ParquetSerializer
from .raw_event_store import RawEventStore

# Conditionally import BlobRawEventStore if Azure SDK is available
try:
    from .blob_raw_event_store import BlobRawEventStore
    BLOB_STORAGE_AVAILABLE = True
except ImportError:
    BlobRawEventStore = None
    BLOB_STORAGE_AVAILABLE = False

__all__ = [
    'RawEvent',
    'BufferError',
    'StorageError',
    'ParquetSerializer',
    'RawEventStore',
]

if BLOB_STORAGE_AVAILABLE:
    __all__.append('BlobRawEventStore')

