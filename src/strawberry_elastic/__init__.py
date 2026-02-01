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
from .types import (
    Completion,
    FieldMapper,
    GeoPoint,
    GeoShape,
    IPAddress,
    TokenCount,
    TypeInfo,
    TypeInspector,
    get_backend,
    has_dsl,
    is_elasticsearch,
    is_opensearch,
    universal_dsl,
)


__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Client adapters
    "BaseElasticAdapter",
    "create_adapter",
    "get_adapter_for_client_type",
    # Type system
    "universal_dsl",
    "has_dsl",
    "get_backend",
    "is_elasticsearch",
    "is_opensearch",
    "TypeInspector",
    "TypeInfo",
    "FieldMapper",
    "GeoPoint",
    "GeoShape",
    "IPAddress",
    "Completion",
    "TokenCount",
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
