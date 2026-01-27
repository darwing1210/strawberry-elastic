"""Tests for OpenSearch adapter."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from strawberry_elastic.clients.adapters.opensearch import OpenSearchAdapter


class TestOpenSearchAdapterInit:
    """Test OpenSearch adapter initialization."""

    def test_adapter_init_does_not_detect_capabilities(self):
        """Test that creating OpenSearchAdapter doesn't detect capabilities."""
        # Create a mock client
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        # Create adapter - should not call info() yet
        adapter = OpenSearchAdapter(mock_client)

        # Verify capabilities not detected yet
        assert adapter._capabilities is None
        assert adapter._capabilities_detected is False

        # info() should not have been called during __init__
        mock_client.info.assert_not_called()

    def test_adapter_validates_client_on_init(self):
        """Test that adapter validates client type during initialization."""
        # Create a mock client with wrong module
        mock_client = Mock()
        mock_client.__class__.__module__ = "some_other_module"

        # Should raise TypeError
        with pytest.raises(TypeError, match="Expected OpenSearch client"):
            OpenSearchAdapter(mock_client)

    def test_adapter_requires_necessary_methods(self):
        """Test that adapter validates client has required methods."""
        # Create a mock client missing required methods
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        # Missing other required methods

        # Should raise TypeError about missing methods
        with pytest.raises(TypeError, match="missing required methods"):
            OpenSearchAdapter(mock_client)


class TestOpenSearchLazyCapabilityDetection:
    """Test lazy capability detection for OpenSearch adapter."""

    @pytest.mark.asyncio
    async def test_capabilities_detected_on_first_operation(self):
        """Test that capabilities are detected on first operation."""
        # Create a mock sync client
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "2.5.0"}, "cluster_name": "test"}
        )

        adapter = OpenSearchAdapter(mock_client)

        # Before first operation
        assert adapter._capabilities is None
        assert adapter._capabilities_detected is False

        # First operation should trigger capability detection
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"_id": "1", "_source": {"test": "data"}}
            )
            await adapter.get(index="test", id="1")

        # After first operation
        assert adapter._capabilities is not None
        assert adapter._capabilities_detected is True
        assert "version" in adapter._capabilities
        assert "supports_pit" in adapter._capabilities

    @pytest.mark.asyncio
    async def test_capabilities_detected_only_once(self):
        """Test that capabilities are only detected once, not on every operation."""
        # Create a mock sync client
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "2.5.0"}, "cluster_name": "test"}
        )

        adapter = OpenSearchAdapter(mock_client)

        # First operation
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"_id": "1", "_source": {"test": "data"}}
            )
            await adapter.get(index="test", id="1")

        # info() should have been called once
        info_call_count = mock_client.info.call_count

        # Second operation
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"_id": "2", "_source": {"test": "data2"}}
            )
            await adapter.get(index="test", id="2")

        # info() should not have been called again
        assert mock_client.info.call_count == info_call_count

    def test_capability_properties_return_defaults_before_detection(self):
        """Test that capability properties return safe defaults before detection."""
        # Create a mock client
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        adapter = OpenSearchAdapter(mock_client)

        # Before detection, properties should return safe defaults
        assert adapter.version is None
        assert adapter.supports_pit is False  # Conservative default
        assert adapter.supports_search_after is True  # Generally available
        assert adapter.supports_async_search is False  # Conservative default

    @pytest.mark.asyncio
    async def test_get_capabilities_triggers_detection(self):
        """Test that get_capabilities() explicitly triggers detection."""
        # Create a mock sync client
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "2.5.0"}, "cluster_name": "test"}
        )

        adapter = OpenSearchAdapter(mock_client)

        # Before calling get_capabilities
        assert adapter._capabilities is None

        # Call get_capabilities directly
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"version": {"number": "2.5.0"}, "cluster_name": "test"}
            )
            capabilities = await adapter.get_capabilities()

        # After calling get_capabilities
        assert adapter._capabilities is not None
        assert capabilities == adapter._capabilities
        assert "version" in capabilities
        assert capabilities["version"] == "2.5.0"

    @pytest.mark.asyncio
    async def test_detection_failure_doesnt_break_adapter(self):
        """Test that adapter still works if capability detection fails."""
        # Create a mock client that fails on info()
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(side_effect=Exception("Connection failed"))

        adapter = OpenSearchAdapter(mock_client)

        # Try to trigger detection - should not raise
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            # Detection should fail but be caught
            await adapter._detect_capabilities()

        # Capabilities should still be set with conservative defaults
        assert adapter._capabilities is not None
        assert "is_async" in adapter._capabilities


class TestOpenSearchCapabilityDetection:
    """Test OpenSearch-specific capability detection."""

    @pytest.mark.asyncio
    async def test_opensearch_2_capabilities(self):
        """Test capability detection for OpenSearch 2.x."""
        # Create a mock sync OpenSearch 2.x client
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "2.5.0"}, "cluster_name": "test"}
        )

        adapter = OpenSearchAdapter(mock_client)

        # Trigger detection
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"version": {"number": "2.5.0"}, "cluster_name": "test"}
            )
            await adapter.info()

        # OpenSearch 2.x capabilities
        assert adapter.version == "2.5.0"
        assert adapter.supports_pit is True  # OpenSearch 2.x supports PIT
        assert adapter.supports_async_search is True  # OpenSearch supports async search

    @pytest.mark.asyncio
    async def test_opensearch_1_capabilities(self):
        """Test capability detection for OpenSearch 1.x."""
        # Create a mock sync OpenSearch 1.x client
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "1.3.0"}, "cluster_name": "test"}
        )

        adapter = OpenSearchAdapter(mock_client)

        # Trigger detection
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"version": {"number": "1.3.0"}, "cluster_name": "test"}
            )
            await adapter.info()

        # OpenSearch 1.x capabilities
        assert adapter.version == "1.3.0"
        assert adapter.supports_pit is False  # PIT only in 2.x+
        assert adapter.supports_async_search is True  # OpenSearch 1.x+ has async search


class TestOpenSearchOperations:
    """Test OpenSearch adapter operations."""

    @pytest.mark.asyncio
    async def test_search_operation(self):
        """Test search operation."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock(return_value={"hits": {"total": {"value": 10}, "hits": []}})
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "2.0.0"}, "cluster_name": "test"}
        )

        adapter = OpenSearchAdapter(mock_client)

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=[
                    {"version": {"number": "2.0.0"}, "cluster_name": "test"},
                    {"hits": {"total": {"value": 10}, "hits": []}},
                ]
            )
            result = await adapter.search(index="test", query={"match_all": {}})

        assert "hits" in result
        assert result["hits"]["total"]["value"] == 10

    @pytest.mark.asyncio
    async def test_index_normalize_handles_list(self):
        """Test that _normalize_index handles list of indices."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        adapter = OpenSearchAdapter(mock_client)

        # Test with list of indices
        normalized = adapter._normalize_index(["index1", "index2", "index3"])
        assert normalized == "index1,index2,index3"

        # Test with single string
        normalized = adapter._normalize_index("single_index")
        assert normalized == "single_index"

    @pytest.mark.asyncio
    async def test_count_operation(self):
        """Test count operation."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.count = Mock(return_value={"count": 42})
        mock_client.info = Mock(
            return_value={"version": {"number": "2.0.0"}, "cluster_name": "test"}
        )

        adapter = OpenSearchAdapter(mock_client)

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=[
                    {"version": {"number": "2.0.0"}, "cluster_name": "test"},
                    {"count": 42},
                ]
            )
            count = await adapter.count(index="test", query={"match_all": {}})

        assert count == 42

    def test_capabilities_if_detected_property(self):
        """Test capabilities_if_detected property."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "opensearchpy"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        adapter = OpenSearchAdapter(mock_client)

        # Before detection
        assert adapter.capabilities_if_detected is None

        # After manually setting capabilities
        adapter._capabilities = {"test": True}
        assert adapter.capabilities_if_detected == {"test": True}
