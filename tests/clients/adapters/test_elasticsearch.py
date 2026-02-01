"""Tests for Elasticsearch adapter."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from strawberry_elastic.clients.adapters.elasticsearch import ElasticsearchAdapter


class TestElasticsearchAdapterInit:
    """Test Elasticsearch adapter initialization."""

    def test_adapter_init_does_not_detect_capabilities(self):
        """Test that creating ElasticsearchAdapter doesn't detect capabilities."""
        # Create a mock client
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        # Create adapter - should not call info() yet
        adapter = ElasticsearchAdapter(mock_client)

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
        with pytest.raises(TypeError, match="Expected Elasticsearch client"):
            ElasticsearchAdapter(mock_client)

    def test_adapter_requires_necessary_methods(self):
        """Test that adapter validates client has required methods."""
        # Create a mock client missing required methods
        # Use spec_set to prevent Mock from auto-creating attributes
        mock_client = Mock(spec_set=["search"])
        mock_client.__class__.__module__ = "elasticsearch"
        # Missing other required methods (get, index, delete, info)

        # Should raise TypeError about missing methods
        with pytest.raises(TypeError, match="missing required methods"):
            ElasticsearchAdapter(mock_client)


class TestElasticsearchLazyCapabilityDetection:
    """Test lazy capability detection for Elasticsearch adapter."""

    @pytest.mark.asyncio
    async def test_capabilities_detected_on_first_operation(self):
        """Test that capabilities are detected on first operation."""
        # Create a mock sync client
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "8.11.0"}, "cluster_name": "test"}
        )

        adapter = ElasticsearchAdapter(mock_client)

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
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "8.11.0"}, "cluster_name": "test"}
        )

        adapter = ElasticsearchAdapter(mock_client)

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
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        adapter = ElasticsearchAdapter(mock_client)

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
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "8.11.0"}, "cluster_name": "test"}
        )

        adapter = ElasticsearchAdapter(mock_client)

        # Before calling get_capabilities
        assert adapter._capabilities is None

        # Call get_capabilities directly
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"version": {"number": "8.11.0"}, "cluster_name": "test"}
            )
            capabilities = await adapter.get_capabilities()

        # After calling get_capabilities
        assert adapter._capabilities is not None
        assert capabilities == adapter._capabilities
        assert "version" in capabilities
        assert capabilities["version"] == "8.11.0"

    @pytest.mark.asyncio
    async def test_detection_failure_doesnt_break_adapter(self):
        """Test that adapter still works if capability detection fails."""
        # Create a mock client that fails on info()
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(side_effect=Exception("Connection failed"))

        adapter = ElasticsearchAdapter(mock_client)

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


class TestElasticsearchCapabilityDetection:
    """Test Elasticsearch-specific capability detection."""

    @pytest.mark.asyncio
    async def test_elasticsearch_8_capabilities(self):
        """Test capability detection for Elasticsearch 8.x."""
        # Create a mock sync client with ES 8.11
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "8.11.0"}, "cluster_name": "test"}
        )

        adapter = ElasticsearchAdapter(mock_client)

        # Trigger detection with first operation
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"version": {"number": "8.11.0"}, "cluster_name": "test"}
            )
            await adapter.info()

        # After detection, properties should reflect ES 8.x capabilities
        assert adapter.version == "8.11.0"
        assert adapter.supports_pit is True  # ES 8.x supports PIT
        assert adapter.supports_search_after is True
        assert adapter.supports_async_search is True  # ES 8.x supports async search

    @pytest.mark.asyncio
    async def test_elasticsearch_7_10_capabilities(self):
        """Test capability detection for Elasticsearch 7.10+."""
        # Create a mock sync client with ES 7.10
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "7.10.2"}, "cluster_name": "test"}
        )

        adapter = ElasticsearchAdapter(mock_client)

        # Trigger detection
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"version": {"number": "7.10.2"}, "cluster_name": "test"}
            )
            await adapter.info()

        # ES 7.10+ capabilities
        assert adapter.version == "7.10.2"
        assert adapter.supports_pit is True  # ES 7.10+ supports PIT
        assert adapter.supports_async_search is True  # ES 7.7+ supports async search

    @pytest.mark.asyncio
    async def test_elasticsearch_7_0_capabilities(self):
        """Test capability detection for Elasticsearch 7.0-7.9."""
        # Create a mock sync client with ES 7.5
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "7.5.0"}, "cluster_name": "test"}
        )

        adapter = ElasticsearchAdapter(mock_client)

        # Trigger detection
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value={"version": {"number": "7.5.0"}, "cluster_name": "test"}
            )
            await adapter.info()

        # ES 7.0-7.9 capabilities
        assert adapter.version == "7.5.0"
        assert adapter.supports_pit is False  # PIT only in 7.10+
        assert adapter.supports_async_search is False  # Async search only in 7.7+


class TestElasticsearchOperations:
    """Test Elasticsearch adapter operations."""

    @pytest.mark.asyncio
    async def test_search_operation(self):
        """Test search operation."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock(return_value={"hits": {"total": {"value": 10}, "hits": []}})
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock(
            return_value={"version": {"number": "8.0.0"}, "cluster_name": "test"}
        )

        adapter = ElasticsearchAdapter(mock_client)

        with patch("asyncio.get_event_loop") as mock_loop:
            # Mock run_in_executor to return the search result directly
            async def mock_executor(_executor, func):
                # Call the lambda function to get the result
                return func()

            mock_loop.return_value.run_in_executor = mock_executor

            # Mock the search method to return expected result
            mock_client.search.return_value = {"hits": {"total": {"value": 10}, "hits": []}}

            result = await adapter.search(index="test", query={"match_all": {}})

        assert "hits" in result
        assert result["hits"]["total"]["value"] == 10

    @pytest.mark.asyncio
    async def test_index_normalize_handles_list(self):
        """Test that _normalize_index handles list of indices."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        adapter = ElasticsearchAdapter(mock_client)

        # Test with list of indices
        normalized = adapter._normalize_index(["index1", "index2", "index3"])
        assert normalized == "index1,index2,index3"

        # Test with single string
        normalized = adapter._normalize_index("single_index")
        assert normalized == "single_index"

    def test_capabilities_if_detected_property(self):
        """Test capabilities_if_detected property."""
        mock_client = Mock()
        mock_client.__class__.__module__ = "elasticsearch"
        mock_client.search = Mock()
        mock_client.get = Mock()
        mock_client.index = Mock()
        mock_client.delete = Mock()
        mock_client.info = Mock()

        adapter = ElasticsearchAdapter(mock_client)

        # Before detection
        assert adapter.capabilities_if_detected is None

        # After manually setting capabilities
        adapter._capabilities = {"test": True}
        assert adapter.capabilities_if_detected == {"test": True}
