"""Client adapters for Elasticsearch and OpenSearch."""

from .base import BaseElasticAdapter
from .factory import create_adapter, get_adapter_for_client_type


__all__ = [
    "BaseElasticAdapter",
    "create_adapter",
    "get_adapter_for_client_type",
]
