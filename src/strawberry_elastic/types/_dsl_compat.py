"""
Universal compatibility layer for Document support across backends.

Supports:
- Elasticsearch 8.18+ (elasticsearch.dsl - built-in)
- Elasticsearch 7.x-8.17.x (elasticsearch_dsl - separate package)
- OpenSearch 1.x/2.x (opensearchpy.helpers.document)

This module provides a unified interface for working with Document classes
regardless of which backend is installed.
"""

import os
from dataclasses import dataclass
from typing import Any, Literal


Backend = Literal["elasticsearch.dsl", "elasticsearch_dsl", "opensearchpy"]


@dataclass
class DSLInfo:
    """Information about the available DSL backend."""

    available: bool
    backend: Backend | None
    module: Any | None
    version: str | None = None


class UniversalDSL:
    """
    Universal compatibility layer for Document support.

    Automatically detects and uses the appropriate backend:
    - Elasticsearch 8.18+ (built-in DSL)
    - Elasticsearch 7.x-8.17.x (separate DSL package)
    - OpenSearch (opensearchpy.helpers.document)

    Example:
        >>> from strawberry_elastic.types._dsl_compat import universal_dsl
        >>> if universal_dsl.available:
        ...     Document = universal_dsl.Document
        ...     Text = universal_dsl.Text
        ...     print(f"Using: {universal_dsl.backend}")
    """

    def __init__(self):
        self._info = self._detect_backend()
        self._field_module = None
        if self._info.available and self.is_opensearch:
            self._field_module = self._load_opensearch_fields()

    def _detect_backend(self) -> DSLInfo:
        """
        Detect which DSL backend is available.

        Can be forced using STRAWBERRY_ELASTIC_DSL environment variable:
        - "elasticsearch" or "elasticsearch.dsl" - Force Elasticsearch 8.18+
        - "elasticsearch_dsl" - Force Elasticsearch 7.x-8.17.x
        - "opensearch" or "opensearchpy" - Force OpenSearch
        """

        # Check for forced backend via environment variable
        forced_backend = os.getenv("STRAWBERRY_ELASTIC_DSL", "").lower()

        if forced_backend:
            if forced_backend in ("elasticsearch", "elasticsearch.dsl"):
                try:
                    from elasticsearch import dsl

                    if hasattr(dsl, "Document"):
                        return DSLInfo(
                            available=True,
                            backend="elasticsearch.dsl",
                            module=dsl,
                        )
                except (ImportError, AttributeError):
                    pass

            elif forced_backend == "elasticsearch_dsl":
                try:
                    import elasticsearch_dsl as dsl

                    if hasattr(dsl, "Document"):
                        return DSLInfo(
                            available=True,
                            backend="elasticsearch_dsl",
                            module=dsl,
                        )
                except (ImportError, AttributeError):
                    pass

            elif forced_backend in ("opensearch", "opensearchpy"):
                try:
                    from opensearchpy.helpers import document

                    if hasattr(document, "Document"):
                        return DSLInfo(
                            available=True,
                            backend="opensearchpy",
                            module=document,
                        )
                except (ImportError, AttributeError):
                    pass

        # Auto-detect: Try Elasticsearch 8.18+ (built-in DSL)
        try:
            from elasticsearch import dsl

            # Verify it has Document class
            if hasattr(dsl, "Document"):
                return DSLInfo(
                    available=True,
                    backend="elasticsearch.dsl",
                    module=dsl,
                )
        except (ImportError, AttributeError):
            pass

        # Try Elasticsearch 7.x-8.17.x (separate package)
        try:
            import elasticsearch_dsl as dsl

            if hasattr(dsl, "Document"):
                return DSLInfo(
                    available=True,
                    backend="elasticsearch_dsl",
                    module=dsl,
                )
        except (ImportError, AttributeError):
            pass

        # Try OpenSearch
        try:
            from opensearchpy.helpers import document

            if hasattr(document, "Document"):
                return DSLInfo(
                    available=True,
                    backend="opensearchpy",
                    module=document,
                )
        except (ImportError, AttributeError):
            pass

        # No DSL available
        return DSLInfo(available=False, backend=None, module=None)

    def _load_opensearch_fields(self) -> Any | None:
        """Load OpenSearch field module if available."""
        try:
            from opensearchpy.helpers import field

            return field
        except ImportError:
            return None

    @property
    def available(self) -> bool:
        """Whether any DSL backend is available."""
        return self._info.available

    @property
    def backend(self) -> Backend | None:
        """Which backend is being used."""
        return self._info.backend

    @property
    def is_elasticsearch(self) -> bool:
        """Whether using Elasticsearch DSL."""
        return self._info.backend in ["elasticsearch.dsl", "elasticsearch_dsl"]

    @property
    def is_opensearch(self) -> bool:
        """Whether using OpenSearch DSL."""
        return self._info.backend == "opensearchpy"

    def ensure_available(self) -> None:
        """Raise helpful error if no DSL backend is available."""
        if not self._info.available:
            raise ImportError(
                "Document support requires either Elasticsearch or OpenSearch DSL.\n\n"
                "For Elasticsearch 8.18+:\n"
                "  pip install 'strawberry-elastic[elasticsearch]'\n"
                "  (DSL included in elasticsearch>=8.18)\n\n"
                "For Elasticsearch 7.x to 8.17.x:\n"
                "  pip install 'strawberry-elastic[elasticsearch-legacy]'\n"
                "  (Requires: pip install elasticsearch-dsl)\n\n"
                "For OpenSearch:\n"
                "  pip install 'strawberry-elastic[opensearch]'\n"
                "  (Includes Document support via opensearchpy.helpers.document)\n"
            )

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to the DSL module.

        Handles backend-specific differences automatically.

        Args:
            name: Attribute name to access (e.g., 'Document', 'Text', 'Keyword')

        Returns:
            The requested class or attribute from the DSL module

        Raises:
            ImportError: If no DSL backend is available
            AttributeError: If the attribute doesn't exist in the backend
        """
        self.ensure_available()

        module = self._info.module

        # For OpenSearch, we might need to access attributes differently
        if self.is_opensearch:
            # Try document module first
            if hasattr(module, name):
                return getattr(module, name)

            # Try field module for field types
            if self._field_module and hasattr(self._field_module, name):
                return getattr(self._field_module, name)

        # For Elasticsearch, direct access
        if hasattr(module, name):
            return getattr(module, name)

        raise AttributeError(f"'{self._info.backend}' DSL backend does not have attribute '{name}'")

    def get_document_class(self) -> type:
        """
        Get the Document base class.

        Returns:
            Document class from the active backend

        Raises:
            ImportError: If no DSL backend is available
        """
        self.ensure_available()
        assert self._info.module is not None
        return self._info.module.Document

    def get_inner_doc_class(self) -> type:
        """
        Get the InnerDoc base class for nested objects.

        Returns:
            InnerDoc class from the active backend

        Raises:
            ImportError: If no DSL backend is available
        """
        self.ensure_available()

        if self.is_opensearch:
            # Check if OpenSearch has InnerDoc
            if hasattr(self._info.module, "InnerDoc"):
                return self._info.module.InnerDoc
            # OpenSearch might use InnerObject or similar
            if hasattr(self._info.module, "InnerObject"):
                return self._info.module.InnerObject

        assert self._info.module is not None
        return self._info.module.InnerDoc

    def normalize_field(self, field: Any) -> Any:
        """
        Normalize field differences between backends.

        OpenSearch and Elasticsearch fields should be mostly compatible,
        but this provides a hook for handling any differences.

        Args:
            field: Field instance from any backend

        Returns:
            Normalized field (currently returns as-is)
        """
        # Most fields should be compatible
        # Add normalization here if we discover differences
        return field


# Global instance for easy access
universal_dsl = UniversalDSL()


# Convenience functions for external use
def has_dsl() -> bool:
    """
    Check if any DSL backend is available.

    Returns:
        True if Document support is available, False otherwise
    """
    return universal_dsl.available


def get_backend() -> Backend | None:
    """
    Get the active DSL backend.

    Returns:
        Backend name or None if no backend available
    """
    return universal_dsl.backend


def is_elasticsearch() -> bool:
    """
    Check if using Elasticsearch DSL.

    Returns:
        True if using Elasticsearch (any version), False otherwise
    """
    return universal_dsl.is_elasticsearch


def is_opensearch() -> bool:
    """
    Check if using OpenSearch DSL.

    Returns:
        True if using OpenSearch, False otherwise
    """
    return universal_dsl.is_opensearch


def ensure_dsl() -> None:
    """
    Ensure DSL is available, raise helpful error if not.

    Raises:
        ImportError: If no DSL backend is available with installation instructions
    """
    universal_dsl.ensure_available()
