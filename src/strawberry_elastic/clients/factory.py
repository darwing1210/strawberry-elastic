"""Factory for auto-detecting and creating appropriate adapters."""

from typing import Any

from .base import BaseElasticAdapter


def create_adapter(client: Any) -> BaseElasticAdapter:
    """
    Auto-detect client type and create the appropriate adapter.

    This factory inspects the client instance and creates the correct adapter
    (Elasticsearch or OpenSearch) based on the client's module and type.

    Args:
        client: An Elasticsearch or OpenSearch client instance (sync or async)

    Returns:
        An appropriate adapter instance (ElasticsearchAdapter or OpenSearchAdapter)

    Raises:
        ValueError: If the client type cannot be determined or is not supported

    Examples:
        >>> from elasticsearch import Elasticsearch
        >>> es_client = Elasticsearch(["http://localhost:9200"])
        >>> adapter = create_adapter(es_client)
        >>> # Returns ElasticsearchAdapter instance

        >>> from opensearchpy import OpenSearch
        >>> os_client = OpenSearch(["http://localhost:9200"])
        >>> adapter = create_adapter(os_client)
        >>> # Returns OpenSearchAdapter instance
    """
    if client is None:
        raise ValueError("Client cannot be None")

    # Get the module name of the client class
    client_module = client.__class__.__module__.lower()
    client_class = client.__class__.__name__

    # Try to detect Elasticsearch client
    if "elasticsearch" in client_module:
        from .adapters.elasticsearch import ElasticsearchAdapter

        return ElasticsearchAdapter(client)

    # Try to detect OpenSearch client
    if "opensearch" in client_module:
        from .adapters.opensearch import OpenSearchAdapter

        return OpenSearchAdapter(client)

    # Try to detect by class name as fallback
    if "elasticsearch" in client_class.lower():
        from .adapters.elasticsearch import ElasticsearchAdapter

        return ElasticsearchAdapter(client)

    if "opensearch" in client_class.lower():
        from .adapters.opensearch import OpenSearchAdapter

        return OpenSearchAdapter(client)

    raise ValueError(
        f"Unknown client type: {type(client)} (module: {client_module}). "
        "Supported clients:\n"
        "  - elasticsearch (pip install elasticsearch)\n"
        "  - opensearch-py (pip install opensearch-py)\n"
        f"Client class: {client_class}, Module: {client.__class__.__module__}"
    )


def get_adapter_for_client_type(client_type: str) -> type[BaseElasticAdapter]:
    """
    Get the adapter class for a specific client type.

    Args:
        client_type: Either 'elasticsearch' or 'opensearch'

    Returns:
        The adapter class

    Raises:
        ValueError: If client_type is not supported
    """
    client_type = client_type.lower()

    if client_type == "elasticsearch":
        from .adapters.elasticsearch import ElasticsearchAdapter

        return ElasticsearchAdapter

    if client_type == "opensearch":
        from .adapters.opensearch import OpenSearchAdapter

        return OpenSearchAdapter

    raise ValueError(
        f"Unknown client type: {client_type}. Supported types: 'elasticsearch', 'opensearch'"
    )
