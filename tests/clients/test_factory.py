"""Tests for adapter factory."""

from unittest.mock import Mock

import pytest

from strawberry_elastic.clients.adapters.elasticsearch import ElasticsearchAdapter
from strawberry_elastic.clients.adapters.opensearch import OpenSearchAdapter
from strawberry_elastic.clients.factory import (
    create_adapter,
    get_adapter_for_client_type,
)


class TestCreateAdapter:
    """Test create_adapter factory function."""

    def test_create_adapter_with_elasticsearch_client(self):
        """Test that create_adapter detects and creates Elasticsearch adapter."""
        # Create a mock Elasticsearch client
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.__class__.__name__ = "Elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        # Create adapter
        adapter = create_adapter(mock_client)

        # Should be ElasticsearchAdapter
        assert isinstance(adapter, ElasticsearchAdapter)
        assert adapter.client is mock_client

    def test_create_adapter_with_opensearch_client(self):
        """Test that create_adapter detects and creates OpenSearch adapter."""
        # Create a mock OpenSearch client
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.__class__.__name__ = "OpenSearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        # Create adapter
        adapter = create_adapter(mock_client)

        # Should be OpenSearchAdapter
        assert isinstance(adapter, OpenSearchAdapter)
        assert adapter.client is mock_client

    def test_create_adapter_detects_by_module_name(self):
        """Test that create_adapter detects client type by module name."""
        # Test with elasticsearch module
        mock_es_client = Mock()
        mock_es_client.__class__.__module__ = "elasticsearch.client"
        mock_es_client.__class__.__name__ = "SomeClient"
        mock_es_client.search = Mock()
        mock_es_client.get = Mock()
        mock_es_client.index = Mock()
        mock_es_client.delete = Mock()
        mock_es_client.info = Mock()

        adapter = create_adapter(mock_es_client)
        assert isinstance(adapter, ElasticsearchAdapter)

        # Test with opensearch module
        mock_os_client = Mock()
        mock_os_client.__class__.__module__ = "opensearchpy.client"
        mock_os_client.__class__.__name__ = "SomeClient"
        mock_os_client.search = Mock()
        mock_os_client.get = Mock()
        mock_os_client.index = Mock()
        mock_os_client.delete = Mock()
        mock_os_client.info = Mock()

        adapter = create_adapter(mock_os_client)
        assert isinstance(adapter, OpenSearchAdapter)

    def test_create_adapter_detects_by_class_name(self):
        """Test that create_adapter falls back to class name detection."""
        # Test with Elasticsearch in class name
        mock_es_client = Mock()
        mock_es_client.__class__.__module__ = "some.custom.module"
        mock_es_client.__class__.__name__ = "MyElasticsearchClient"
        mock_es_client.search = Mock()
        mock_es_client.get = Mock()
        mock_es_client.index = Mock()
        mock_es_client.delete = Mock()
        mock_es_client.info = Mock()

        adapter = create_adapter(mock_es_client)
        assert isinstance(adapter, ElasticsearchAdapter)

        # Test with OpenSearch in class name
        mock_os_client = Mock()
        mock_os_client.__class__.__module__ = "some.custom.module"
        mock_os_client.__class__.__name__ = "MyOpenSearchClient"
        mock_os_client.search = Mock()
        mock_os_client.get = Mock()
        mock_os_client.index = Mock()
        mock_os_client.delete = Mock()
        mock_os_client.info = Mock()

        adapter = create_adapter(mock_os_client)
        assert isinstance(adapter, OpenSearchAdapter)

    def test_create_adapter_raises_with_none_client(self):
        """Test that create_adapter raises ValueError with None client."""
        with pytest.raises(ValueError, match="Client cannot be None"):
            create_adapter(None)

    def test_create_adapter_raises_with_unknown_client(self):
        """Test that create_adapter raises ValueError with unknown client type."""
        # Create a mock client that doesn't match any known type
        mock_client = Mock()
        mock_client.__class__.__module__ = "some.unknown.module"
        mock_client.__class__.__name__ = "UnknownClient"

        with pytest.raises(ValueError, match="Unknown client type"):
            create_adapter(mock_client)

    def test_create_adapter_error_message_helpful(self):
        """Test that error message is helpful when client type is unknown."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "custom.database"
        mock_client.__class__.__name__ = "CustomClient"

        with pytest.raises(ValueError, match="Unknown client type") as exc_info:
            create_adapter(mock_client)

        error_message = str(exc_info.value)
        assert "Unknown client type" in error_message
        assert "elasticsearch" in error_message
        assert "opensearch-py" in error_message


class TestGetAdapterForClientType:
    """Test get_adapter_for_client_type function."""

    def test_get_elasticsearch_adapter_class(self):
        """Test getting Elasticsearch adapter class."""
        adapter_class = get_adapter_for_client_type("elasticsearch")
        assert adapter_class is ElasticsearchAdapter

    def test_get_opensearch_adapter_class(self):
        """Test getting OpenSearch adapter class."""
        adapter_class = get_adapter_for_client_type("opensearch")
        assert adapter_class is OpenSearchAdapter

    def test_get_adapter_case_insensitive(self):
        """Test that client_type parameter is case-insensitive."""
        # Test uppercase
        assert get_adapter_for_client_type("ELASTICSEARCH") is ElasticsearchAdapter
        assert get_adapter_for_client_type("OPENSEARCH") is OpenSearchAdapter

        # Test mixed case
        assert get_adapter_for_client_type("ElasticSearch") is ElasticsearchAdapter
        assert get_adapter_for_client_type("OpenSearch") is OpenSearchAdapter

    def test_get_adapter_raises_with_unknown_type(self):
        """Test that get_adapter_for_client_type raises with unknown type."""
        with pytest.raises(ValueError, match="Unknown client type"):
            get_adapter_for_client_type("unknown")

    def test_get_adapter_error_message_helpful(self):
        """Test that error message lists supported types."""
        with pytest.raises(ValueError, match="Unknown client type") as exc_info:
            get_adapter_for_client_type("mongodb")

        error_message = str(exc_info.value)
        assert "Unknown client type: mongodb" in error_message
        assert "elasticsearch" in error_message
        assert "opensearch" in error_message


class TestFactoryIntegration:
    """Integration tests for factory functions."""

    def test_created_adapter_works(self):
        """Test that created adapter is functional."""
        # Create a mock client
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        # Create adapter
        adapter = create_adapter(mock_client)

        # Verify it's the right type
        assert isinstance(adapter, ElasticsearchAdapter)

        # Verify it has access to the client
        assert hasattr(adapter, "client")
        assert adapter.client is mock_client

        # Verify it has expected methods
        assert hasattr(adapter, "search")
        assert hasattr(adapter, "get")
        assert hasattr(adapter, "index")
        assert hasattr(adapter, "delete")

    def test_factory_preserves_client_reference(self):
        """Test that factory preserves reference to original client."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        adapter = create_adapter(mock_client)

        # Should be the exact same object, not a copy
        assert adapter.client is mock_client
