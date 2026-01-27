"""Base abstract adapter for Elasticsearch/OpenSearch clients."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


class BaseElasticAdapter(ABC):
    """
    Abstract adapter interface for Elasticsearch and OpenSearch clients.

    This adapter provides a unified interface for interacting with different
    Elasticsearch and OpenSearch client versions, handling both sync and async clients.
    """

    def __init__(self, client: Any):
        """
        Initialize the adapter with a client instance.

        Args:
            client: An Elasticsearch or OpenSearch client instance
        """
        self.client = client
        self._capabilities: dict[str, Any] | None = None
        self._capabilities_detected = False
        self._validate_client()

    @abstractmethod
    def _validate_client(self) -> None:
        """
        Validate that the client is of the correct type and version.

        Raises:
            TypeError: If client is not a valid Elasticsearch/OpenSearch client
            ValueError: If client version is not supported
        """

    @abstractmethod
    async def _detect_capabilities(self) -> None:
        """
        Detect client capabilities at runtime.

        This method should populate self._capabilities with feature flags like:
        - supports_pit: Point in Time API support
        - supports_search_after: search_after pagination support
        - supports_async_search: Async search API support
        - version: Client version string
        - is_async: Whether the client is async
        """

    async def _ensure_capabilities(self) -> None:
        """
        Ensure capabilities have been detected (lazy initialization).

        This is called automatically before any operation that needs capabilities.
        """
        if not self._capabilities_detected:
            await self._detect_capabilities()
            self._capabilities_detected = True

    # ========================================================================
    # Search Operations
    # ========================================================================

    @abstractmethod
    async def search(
        self,
        index: str | Sequence[str],
        query: dict[str, Any],
        source: bool | list[str] | None = None,
        size: int | None = None,
        from_: int | None = None,
        sort: list[dict[str, Any]] | None = None,
        search_after: list[Any] | None = None,
        track_total_hits: bool | int = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a search query.

        Args:
            index: Index name(s) to search
            query: Query DSL dictionary
            source: Fields to include in _source
            size: Number of hits to return
            from_: Starting offset
            sort: Sort configuration
            search_after: Values to search after (for pagination)
            track_total_hits: Whether to track total hits accurately
            **kwargs: Additional parameters to pass to the client

        Returns:
            Search response dictionary
        """

    @abstractmethod
    async def get(
        self,
        index: str,
        id: str,
        source: bool | list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Get a single document by ID.

        Args:
            index: Index name
            id: Document ID
            source: Fields to include in _source
            **kwargs: Additional parameters

        Returns:
            Document dictionary with _source, _id, _index, etc.

        Raises:
            NotFoundError: If document doesn't exist
        """

    @abstractmethod
    async def mget(
        self,
        index: str,
        ids: list[str],
        source: bool | list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Get multiple documents by IDs (batch retrieval).

        Args:
            index: Index name
            ids: List of document IDs
            source: Fields to include in _source
            **kwargs: Additional parameters

        Returns:
            Response dictionary with 'docs' list
        """

    @abstractmethod
    async def count(
        self,
        index: str | Sequence[str],
        query: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> int:
        """
        Count documents matching a query.

        Args:
            index: Index name(s)
            query: Query DSL dictionary (optional)
            **kwargs: Additional parameters

        Returns:
            Number of matching documents
        """

    # ========================================================================
    # Index Operations
    # ========================================================================

    @abstractmethod
    async def index(
        self,
        index: str,
        document: dict[str, Any],
        id: str | None = None,
        refresh: bool | str = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Index a document.

        Args:
            index: Index name
            document: Document to index
            id: Document ID (auto-generated if not provided)
            refresh: Whether to refresh the index (true, false, 'wait_for')
            **kwargs: Additional parameters

        Returns:
            Index response with _id, _index, result, etc.
        """

    @abstractmethod
    async def update(
        self,
        index: str,
        id: str,
        document: dict[str, Any] | None = None,
        script: dict[str, Any] | None = None,
        refresh: bool | str = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Update a document.

        Args:
            index: Index name
            id: Document ID
            document: Partial document to merge (use 'doc' wrapper)
            script: Update script
            refresh: Whether to refresh the index
            **kwargs: Additional parameters

        Returns:
            Update response
        """

    @abstractmethod
    async def delete(
        self,
        index: str,
        id: str,
        refresh: bool | str = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Delete a document.

        Args:
            index: Index name
            id: Document ID
            refresh: Whether to refresh the index
            **kwargs: Additional parameters

        Returns:
            Delete response
        """

    @abstractmethod
    async def bulk(
        self,
        operations: list[dict[str, Any]],
        index: str | None = None,
        refresh: bool | str = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute bulk operations.

        Args:
            operations: List of bulk operations (action + optional document)
            index: Default index name (can be overridden per operation)
            refresh: Whether to refresh after bulk
            **kwargs: Additional parameters

        Returns:
            Bulk response with 'items' list
        """

    # ========================================================================
    # Mapping Operations
    # ========================================================================

    @abstractmethod
    async def get_mapping(
        self,
        index: str | Sequence[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Get mapping for index(es).

        Args:
            index: Index name(s)
            **kwargs: Additional parameters

        Returns:
            Mapping dictionary
        """

    @abstractmethod
    async def put_mapping(
        self,
        index: str,
        properties: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Update mapping for an index.

        Args:
            index: Index name
            properties: Mapping properties
            **kwargs: Additional parameters

        Returns:
            Acknowledgement response
        """

    # ========================================================================
    # Index Management
    # ========================================================================

    @abstractmethod
    async def exists(self, index: str, **kwargs: Any) -> bool:
        """
        Check if index exists.

        Args:
            index: Index name
            **kwargs: Additional parameters

        Returns:
            True if index exists, False otherwise
        """

    @abstractmethod
    async def create_index(
        self,
        index: str,
        mappings: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create an index.

        Args:
            index: Index name
            mappings: Index mappings
            settings: Index settings
            **kwargs: Additional parameters

        Returns:
            Acknowledgement response
        """

    @abstractmethod
    async def delete_index(self, index: str, **kwargs: Any) -> dict[str, Any]:
        """
        Delete an index.

        Args:
            index: Index name
            **kwargs: Additional parameters

        Returns:
            Acknowledgement response
        """

    @abstractmethod
    async def refresh(
        self,
        index: str | Sequence[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Refresh index(es).

        Args:
            index: Index name(s), or None for all indices
            **kwargs: Additional parameters

        Returns:
            Refresh response
        """

    # ========================================================================
    # Info & Capabilities
    # ========================================================================

    @abstractmethod
    async def info(self) -> dict[str, Any]:
        """
        Get cluster/client info.

        Returns:
            Info dictionary with version, cluster name, etc.
        """

    async def get_capabilities(self) -> dict[str, Any]:
        """
        Get detected capabilities.

        Returns:
            Dictionary of capability flags

        Note:
            This method will detect capabilities on first call (lazy initialization).
        """
        await self._ensure_capabilities()
        if self._capabilities is None:
            raise RuntimeError("Capabilities detection failed")
        return self._capabilities

    @property
    def capabilities_if_detected(self) -> dict[str, Any] | None:
        """
        Get capabilities if already detected, otherwise None.

        Use this for synchronous access after capabilities have been detected.
        For first access, use `await adapter.get_capabilities()` instead.
        """
        return self._capabilities

    @property
    def supports_pit(self) -> bool:
        """
        Whether Point in Time API is supported.

        Note: Returns False if capabilities haven't been detected yet.
        Call `await adapter.get_capabilities()` first for accurate detection.
        """
        if self._capabilities is None:
            return False
        return self._capabilities.get("supports_pit", False)

    @property
    def supports_search_after(self) -> bool:
        """
        Whether search_after pagination is supported.

        Note: Returns True if capabilities haven't been detected yet.
        Call `await adapter.get_capabilities()` first for accurate detection.
        """
        if self._capabilities is None:
            return True
        return self._capabilities.get("supports_search_after", True)

    @property
    def supports_async_search(self) -> bool:
        """
        Whether async search API is supported.

        Note: Returns False if capabilities haven't been detected yet.
        Call `await adapter.get_capabilities()` first for accurate detection.
        """
        if self._capabilities is None:
            return False
        return self._capabilities.get("supports_async_search", False)

    @property
    def version(self) -> str | None:
        """
        Client/cluster version string.

        Note: Returns None if capabilities haven't been detected yet.
        Call `await adapter.get_capabilities()` first for accurate detection.
        """
        if self._capabilities is None:
            return None
        version = self._capabilities.get("version")
        return version if isinstance(version, str) else None

    def __repr__(self) -> str:
        """String representation of the adapter."""
        return f"<{self.__class__.__name__} version={self.version}>"
