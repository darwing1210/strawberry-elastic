"""
Type system for Strawberry Elastic.

Provides decorators and utilities for creating GraphQL types from
Elasticsearch/OpenSearch documents and mappings.
"""

from ._dsl_compat import (
    Backend,
    get_backend,
    has_dsl,
    is_elasticsearch,
    is_opensearch,
    universal_dsl,
)
from .field_mapper import FieldMapper
from .inspector import TypeInfo, TypeInspector, TypeSource
from .scalars import Completion, GeoPoint, GeoShape, IPAddress, TokenCount


__all__ = [
    # DSL compatibility
    "universal_dsl",
    "has_dsl",
    "get_backend",
    "is_elasticsearch",
    "is_opensearch",
    "Backend",
    # Type inspection
    "TypeInspector",
    "TypeInfo",
    "TypeSource",
    # Field mapping
    "FieldMapper",
    # Custom scalars
    "GeoPoint",
    "GeoShape",
    "IPAddress",
    "Completion",
    "TokenCount",
]
