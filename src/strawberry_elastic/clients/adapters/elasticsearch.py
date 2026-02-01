"""Version-agnostic Elasticsearch adapter."""

import asyncio
import inspect
from collections.abc import Sequence
from typing import Any

from ..base import BaseElasticAdapter


class ElasticsearchAdapter(BaseElasticAdapter):
    """
    Version-agnostic adapter for Elasticsearch clients.

    Supports both sync and async Elasticsearch clients across versions 7.x and 8.x.
    Automatically detects capabilities at runtime.
    """

    def _validate_client(self) -> None:
        """Validate that the client is an Elasticsearch client."""
        client_module = self.client.__class__.__module__

        if "elasticsearch" not in client_module:
            raise TypeError(
                f"Expected Elasticsearch client, got {type(self.client)}. "
                "Install with: pip install elasticsearch"
            )

        # Check for required methods
        required_methods = ["search", "get", "index", "delete", "info"]
        missing_methods = [
            method for method in required_methods if not hasattr(self.client, method)
        ]

        if missing_methods:
            raise TypeError(f"Client missing required methods: {missing_methods}")

    async def _detect_capabilities(self) -> None:
        """Detect Elasticsearch capabilities at runtime."""
        self._capabilities = {
            "supports_pit": False,
            "supports_search_after": True,
            "supports_async_search": False,
            "version": None,
            "is_async": False,
        }

        try:
            # Get cluster info to detect version
            info = await self.info()
            version_info = info.get("version", {})
            version_number = version_info.get("number", "")

            self._capabilities["version"] = version_number

            # Parse major version
            major_version = int(version_number.split(".")[0]) if version_number else 0

            # Point in Time support (ES 7.10+)
            if major_version >= 8 or (
                major_version == 7 and self._parse_minor_version(version_number) >= 10
            ):
                self._capabilities["supports_pit"] = True

            # Async search support (ES 7.7+)
            if major_version >= 8 or (
                major_version == 7 and self._parse_minor_version(version_number) >= 7
            ):
                self._capabilities["supports_async_search"] = True

            # Detect if client is async
            self._capabilities["is_async"] = inspect.iscoroutinefunction(self.client.search)

        except Exception:
            # If info fails, use conservative defaults
            self._capabilities["is_async"] = inspect.iscoroutinefunction(self.client.search)

    def _parse_minor_version(self, version: str) -> int:
        """Parse minor version number from version string."""
        try:
            parts = version.split(".")
            if len(parts) >= 2:
                return int(parts[1])
        except (ValueError, IndexError):
            pass
        return 0

    async def _execute(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a client method, handling both sync and async clients.

        Args:
            method_name: Name of the client method to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Method result
        """
        # Ensure capabilities are detected before first operation
        await self._ensure_capabilities()

        method = getattr(self.client, method_name)

        if self._capabilities and self._capabilities.get("is_async"):
            # Async client
            return await method(*args, **kwargs)
        # Sync client - run in executor
        return await asyncio.get_event_loop().run_in_executor(None, lambda: method(*args, **kwargs))

    def _normalize_index(self, index: str | Sequence[str]) -> str:
        """Normalize index parameter to string."""
        if isinstance(index, str):
            return index
        return ",".join(index)

    # ========================================================================
    # Search Operations
    # ========================================================================

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
        """Execute a search query."""
        body: dict[str, Any] = {"query": query}

        if source is not None:
            body["_source"] = source
        if size is not None:
            body["size"] = size
        if from_ is not None:
            body["from"] = from_
        if sort is not None:
            body["sort"] = sort
        if search_after is not None:
            body["search_after"] = search_after
        if track_total_hits is not None:
            body["track_total_hits"] = track_total_hits

        # Merge additional body parameters from kwargs
        for key in list(kwargs.keys()):
            if key in ("aggs", "aggregations", "highlight", "suggest", "_source"):
                body[key] = kwargs.pop(key)

        return await self._execute(
            "search", index=self._normalize_index(index), body=body, **kwargs
        )

    async def get(
        self,
        index: str,
        id: str,
        source: bool | list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get a single document by ID."""
        params = {}
        if source is not None:
            params["_source"] = source

        return await self._execute("get", index=index, id=id, **params, **kwargs)

    async def mget(
        self,
        index: str,
        ids: list[str],
        source: bool | list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get multiple documents by IDs."""
        body: dict[str, Any] = {"ids": ids}
        if source is not None:
            body["_source"] = source

        return await self._execute("mget", index=index, body=body, **kwargs)

    async def count(
        self,
        index: str | Sequence[str],
        query: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> int:
        """Count documents matching a query."""
        body = {"query": query} if query else None
        result = await self._execute(
            "count", index=self._normalize_index(index), body=body, **kwargs
        )
        return result["count"]

    # ========================================================================
    # Index Operations
    # ========================================================================

    async def index(
        self,
        index: str,
        document: dict[str, Any],
        id: str | None = None,
        refresh: bool | str = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Index a document."""
        params: dict[str, Any] = {}
        if id is not None:
            params["id"] = id
        if refresh:
            params["refresh"] = refresh

        return await self._execute("index", index=index, body=document, **params, **kwargs)

    async def update(
        self,
        index: str,
        id: str,
        document: dict[str, Any] | None = None,
        script: dict[str, Any] | None = None,
        refresh: bool | str = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update a document."""
        body: dict[str, Any] = {}

        if document is not None:
            body["doc"] = document
        if script is not None:
            body["script"] = script

        params = {}
        if refresh:
            params["refresh"] = refresh

        return await self._execute("update", index=index, id=id, body=body, **params, **kwargs)

    async def delete(
        self,
        index: str,
        id: str,
        refresh: bool | str = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Delete a document."""
        params = {}
        if refresh:
            params["refresh"] = refresh

        return await self._execute("delete", index=index, id=id, **params, **kwargs)

    async def bulk(
        self,
        operations: list[dict[str, Any]],
        index: str | None = None,
        refresh: bool | str = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute bulk operations."""
        params: dict[str, Any] = {}
        if index is not None:
            params["index"] = index
        if refresh:
            params["refresh"] = refresh

        return await self._execute("bulk", body=operations, **params, **kwargs)

    # ========================================================================
    # Mapping Operations
    # ========================================================================

    async def get_mapping(
        self,
        index: str | Sequence[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get mapping for index(es)."""
        # Access indices namespace
        indices = self.client.indices
        method = indices.get_mapping

        if self._capabilities and self._capabilities.get("is_async"):
            result = await method(index=self._normalize_index(index), **kwargs)
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: method(index=self._normalize_index(index), **kwargs)
            )

        return result

    async def put_mapping(
        self,
        index: str,
        properties: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update mapping for an index."""
        body = {"properties": properties}

        indices = self.client.indices
        method = indices.put_mapping

        if self._capabilities and self._capabilities.get("is_async"):
            result = await method(index=index, body=body, **kwargs)
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: method(index=index, body=body, **kwargs)
            )

        return result

    # ========================================================================
    # Index Management
    # ========================================================================

    async def exists(self, index: str, **kwargs: Any) -> bool:
        """Check if index exists."""
        indices = self.client.indices
        method = indices.exists

        if self._capabilities and self._capabilities.get("is_async"):
            return await method(index=index, **kwargs)
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: method(index=index, **kwargs)
        )

    async def create_index(
        self,
        index: str,
        mappings: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create an index."""
        body: dict[str, Any] = {}
        if mappings is not None:
            body["mappings"] = mappings
        if settings is not None:
            body["settings"] = settings

        indices = self.client.indices
        method = indices.create

        if self._capabilities and self._capabilities.get("is_async"):
            result = await method(index=index, body=body, **kwargs)
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: method(index=index, body=body, **kwargs)
            )

        return result

    async def delete_index(self, index: str, **kwargs: Any) -> dict[str, Any]:
        """Delete an index."""
        indices = self.client.indices
        method = indices.delete

        if self._capabilities and self._capabilities.get("is_async"):
            result = await method(index=index, **kwargs)
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: method(index=index, **kwargs)
            )

        return result

    async def refresh(
        self,
        index: str | Sequence[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Refresh index(es)."""
        indices = self.client.indices
        method = indices.refresh

        params = {}
        if index is not None:
            params["index"] = self._normalize_index(index)

        if self._capabilities and self._capabilities.get("is_async"):
            result = await method(**params, **kwargs)
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: method(**params, **kwargs)
            )

        return result

    # ========================================================================
    # Info & Capabilities
    # ========================================================================

    async def info(self) -> dict[str, Any]:
        """Get cluster/client info."""
        return await self._execute("info")
