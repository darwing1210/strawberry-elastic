"""Decorators for Strawberry GraphQL integration with Elasticsearch/OpenSearch."""

from collections.abc import Callable
from typing import Any, TypeVar

from .types.field_mapper import FieldMapper
from .types.inspector import FieldSource


T = TypeVar("T")


class ElasticDecorators:
    """Namespace for elastic-related decorators."""

    @staticmethod
    def type(
        document: type | None = None,
        *,
        index: str | None = None,
        auto_fields: bool = True,
        exclude_fields: list[str] | None = None,
    ) -> Callable[[type[T]], type[T]]:
        """
        Decorator to mark a Strawberry type as backed by an Elasticsearch/OpenSearch Document.

        This decorator enables automatic field generation from Document classes and provides
        metadata for query execution.

        Args:
            document: The elasticsearch-dsl or opensearch-dsl Document class
            index: Optional index name override (uses Document._index.name if not provided)
            auto_fields: Whether to automatically generate fields from the Document
                mapping (default: True)
            exclude_fields: List of field names to exclude from auto-generation

        Returns:
            Decorated class with elastic metadata

        Example:
            ```python
            from elasticsearch_dsl import Document, Text, Keyword
            import strawberry
            from strawberry_elastic import elastic

            class ArticleDocument(Document):
                title = Text()
                author = Keyword()

                class Index:
                    name = "articles"

            @elastic.type(ArticleDocument)
            class Article:
                # Fields auto-generated from ArticleDocument
                pass

            # Or with custom fields
            @elastic.type(ArticleDocument, exclude_fields=["author"])
            class Article:
                title: str  # Auto-generated

                @strawberry.field
                def custom_author(self) -> str:
                    return f"By {self.author}"
            ```
        """

        def decorator(cls: type[T]) -> type[T]:
            # Store elastic metadata on the class
            elastic_meta = {
                "document_class": document,
                "index_name": index,
                "auto_fields": auto_fields,
                "exclude_fields": exclude_fields or [],
                "field_source": FieldSource.DOCUMENT if document else FieldSource.UNKNOWN,
            }

            # Mark the class with elastic metadata
            cls._elastic_type = elastic_meta  # type: ignore[attr-defined]

            # If auto_fields is True and we have a document, generate fields
            if auto_fields and document:
                cls = _generate_fields_from_document(cls, document, exclude_fields or [])

            return cls

        return decorator

    @staticmethod
    def field(
        resolver: Callable | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable | Any:
        """
        Decorator to mark a method or property as a custom GraphQL field.

        This allows you to add custom fields to an elastic type that don't come from
        the Document mapping.

        Args:
            resolver: The resolver function/method
            name: Optional field name override
            description: Optional field description

        Returns:
            Decorated method/property with elastic field marker

        Example:
            ```python
            @elastic.type(ArticleDocument)
            class Article:
                @elastic.field
                def full_title(self) -> str:
                    return f"{self.title} - {self.subtitle}"

                @elastic.field(description="Author's display name")
                def author_name(self) -> str:
                    return self.author.upper()
            ```
        """

        def decorator(func: Callable) -> Callable:
            # Mark the function as an elastic field
            func._elastic_field = True  # type: ignore[attr-defined]
            if name:
                func._elastic_field_name = name  # type: ignore[attr-defined]
            if description:
                func._elastic_field_description = description  # type: ignore[attr-defined]
            return func

        if resolver is not None:
            # Called as @elastic.field (without parentheses)
            return decorator(resolver)
        # Called as @elastic.field(...) (with arguments)
        return decorator


def _generate_fields_from_document(
    cls: type[T],
    document: type,
    exclude_fields: list[str],
) -> type[T]:
    """
    Generate Strawberry fields from a Document class mapping.

    This function:
    - Extracts fields from the Document's mapping
    - Uses FieldMapper to convert ES/OS field types to Python types
    - Adds type annotations to the class
    - Preserves existing annotations and custom fields

    Args:
        cls: The Strawberry type class
        document: The Document class
        exclude_fields: Fields to exclude from generation

    Returns:
        Class with generated field annotations
    """
    mapper = FieldMapper()

    # Generate field mappings from the Document class
    generated_fields = mapper.generate_fields_from_document(document, exclude_fields)

    # Get existing annotations (preserve user-defined fields)
    existing_annotations = getattr(cls, "__annotations__", {})

    # Merge generated fields with existing annotations
    # Existing annotations take precedence (user can override auto-generated fields)
    all_annotations = {**generated_fields, **existing_annotations}

    # Set the annotations on the class
    cls.__annotations__ = all_annotations

    return cls


# Create a singleton instance for use as a decorator namespace
elastic = ElasticDecorators()


__all__ = [
    "ElasticDecorators",
    "elastic",
]
