"""Adapters for Elasticsearch and OpenSearch clients."""

from .elasticsearch import ElasticsearchAdapter
from .opensearch import OpenSearchAdapter


__all__ = [
    "ElasticsearchAdapter",
    "OpenSearchAdapter",
]
