"""
Type inspector for determining how to generate GraphQL fields.

Inspects a class to determine whether fields should be generated from:
- Elasticsearch/OpenSearch Document classes
- Runtime mapping introspection
- Python type hints
- Hybrid approach (Document + custom fields)
"""

from dataclasses import dataclass
from typing import Any, Literal

from ._dsl_compat import has_dsl, universal_dsl


TypeSource = Literal["document", "mapping", "hints", "hybrid"]


@dataclass
class TypeInfo:
    """
    Information about a type's field sources.

    Attributes:
        source: Primary source of field definitions
        document_class: Document class if using Document mode
        index_name: Elasticsearch/OpenSearch index name
        has_type_hints: Whether the class has type annotations
        custom_fields: Custom field names (methods/properties decorated with @elastic.field)
    """

    source: TypeSource
    document_class: type | None = None
    index_name: str | None = None
    has_type_hints: bool = False
    custom_fields: dict[str, Any] | None = None


class TypeInspector:
    """
    Inspects a class to determine how to generate GraphQL fields.

    Detection order:
    1. Is it an Elasticsearch/OpenSearch Document class?
    2. Does it have Python type hints?
    3. Falls back to runtime mapping introspection

    Example:
        >>> inspector = TypeInspector()
        >>> info = inspector.inspect(MyClass)
        >>> print(info.source)  # "document", "hints", or "mapping"
    """

    def inspect(self, cls: type) -> TypeInfo:
        """
        Determine the type source and gather metadata.

        Args:
            cls: Class to inspect

        Returns:
            TypeInfo with detected source and metadata
        """
        # Check if it's a Document class (if DSL available)
        if has_dsl() and self._is_document(cls):
            has_hints = self._has_type_hints(cls)
            custom = self._get_custom_fields(cls)

            # Determine if it's pure Document or hybrid
            source: TypeSource = "document"
            if has_hints or custom:
                source = "hybrid"

            return TypeInfo(
                source=source,
                document_class=cls,
                index_name=self._get_index_name(cls),
                has_type_hints=has_hints,
                custom_fields=custom,
            )

        # Check for type hints
        if self._has_type_hints(cls):
            return TypeInfo(
                source="hints",
                has_type_hints=True,
                custom_fields=self._get_custom_fields(cls),
            )

        # Requires runtime mapping introspection
        return TypeInfo(
            source="mapping",
            custom_fields=self._get_custom_fields(cls),
        )

    def _is_document(self, cls: type) -> bool:
        """
        Check if class is an Elasticsearch/OpenSearch Document.

        Works with:
        - elasticsearch.dsl.Document (ES 8.18+)
        - elasticsearch_dsl.Document (ES 7.x-8.17.x)
        - opensearchpy.helpers.document.Document (OpenSearch)

        Args:
            cls: Class to check

        Returns:
            True if cls is a Document subclass, False otherwise
        """
        if not has_dsl():
            return False

        try:
            document = universal_dsl.get_document_class()
            return isinstance(cls, type) and issubclass(cls, document)
        except (TypeError, AttributeError):
            return False

    def _get_index_name(self, cls: type) -> str | None:
        """
        Extract index name from Document.Index.name.

        Args:
            cls: Document class to extract from

        Returns:
            Index name if defined, None otherwise
        """
        if hasattr(cls, "Index") and hasattr(cls.Index, "name"):
            name = cls.Index.name
            return str(name) if name is not None else None
        return None

    def _has_type_hints(self, cls: type) -> bool:
        """
        Check if class has type annotations.

        Args:
            cls: Class to check

        Returns:
            True if class has __annotations__, False otherwise
        """
        annotations = getattr(cls, "__annotations__", {})
        # Filter out class variables and private attributes
        return bool({k: v for k, v in annotations.items() if not k.startswith("_")})

    def _get_custom_fields(self, cls: type) -> dict[str, Any] | None:
        """
        Get custom fields marked with @elastic.field decorator.

        These are methods or properties that should be included as GraphQL fields
        in addition to or instead of auto-generated fields.

        Args:
            cls: Class to inspect

        Returns:
            Dictionary of custom field names to their definitions, or None if none found
        """
        custom_fields = {}

        for name in dir(cls):
            if name.startswith("_"):
                continue

            try:
                attr = getattr(cls, name)

                # Check if it's marked as an elastic field
                if hasattr(attr, "_elastic_field"):
                    custom_fields[name] = attr

            except AttributeError:
                # Some descriptors might not be accessible at class level
                continue

        return custom_fields if custom_fields else None
