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
from .inspector import FieldSource, TypeInfo, TypeInspector, TypeSource
from .scalars import Completion, GeoPoint, GeoShape, IPAddress, TokenCount


__all__ = [
    "Backend",
    "Completion",
    "FieldMapper",
    "FieldSource",
    "GeoPoint",
    "GeoShape",
    "IPAddress",
    "TokenCount",
    "TypeInfo",
    "TypeInspector",
    "TypeSource",
    "get_backend",
    "has_dsl",
    "is_elasticsearch",
    "is_opensearch",
    "universal_dsl",
]
