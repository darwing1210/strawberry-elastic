"""Strawberry GraphQL integration for Elasticsearch and OpenSearch."""

from .clients import BaseElasticAdapter, create_adapter, get_adapter_for_client_type
from .exceptions import (
    AdapterError,
    BulkOperationError,
    CapabilityError,
    ClientNotFoundError,
    ConfigurationError,
    DocumentNotFoundError,
    IndexNotFoundError,
    MappingError,
    PaginationError,
    QueryError,
    StrawberryElasticError,
    UnsupportedClientError,
    ValidationError,
)


__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Client adapters
    "BaseElasticAdapter",
    "create_adapter",
    "get_adapter_for_client_type",
    # Exceptions
    "StrawberryElasticError",
    "AdapterError",
    "ClientNotFoundError",
    "UnsupportedClientError",
    "ConfigurationError",
    "MappingError",
    "QueryError",
    "DocumentNotFoundError",
    "IndexNotFoundError",
    "BulkOperationError",
    "ValidationError",
    "PaginationError",
    "CapabilityError",
]
