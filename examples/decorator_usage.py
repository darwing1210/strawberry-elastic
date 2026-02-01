"""
Example demonstrating the @elastic.type decorator for automatic field generation.

This example shows how to use the @elastic.type decorator to create Strawberry
GraphQL types from Elasticsearch/OpenSearch Document classes with automatic
field generation.
"""

import strawberry
from elasticsearch.dsl import Document, Integer, Keyword, Text

from strawberry_elastic import elastic


# ============================================================================
# Define Elasticsearch Document classes
# ============================================================================


class ArticleDocument(Document):
    """Elasticsearch Document for articles."""

    title = Text(required=True)
    author = Keyword()
    content = Text()
    views = Integer()
    tags = Keyword(multi=True)

    class Index:
        name = "articles"


class UserDocument(Document):
    """Elasticsearch Document for users."""

    username = Keyword(required=True)
    email = Keyword()
    full_name = Text()
    bio = Text()

    class Index:
        name = "users"


# ============================================================================
# Example 1: Basic usage with automatic field generation
# ============================================================================


@elastic.type(ArticleDocument)
class Article:
    """
    GraphQL type with fields automatically generated from ArticleDocument.

    Fields generated:
    - title: str | None
    - author: str | None
    - content: str | None
    - views: int | None
    - tags: list[str] | None
    """


# ============================================================================
# Example 2: Hybrid mode - Document fields + custom fields
# ============================================================================


@elastic.type(ArticleDocument)
class ArticleWithCustomFields:
    """
    Combines auto-generated fields from Document with custom fields.

    Auto-generated: title, author, content, views, tags
    Custom: summary, display_name
    """

    # Custom field using @elastic.field decorator
    @elastic.field
    def summary(self) -> str:
        """Generate a summary from the content."""
        if hasattr(self, "content") and self.content:
            return self.content[:100] + "..."  # type: ignore[index]
        return "No content"

    @elastic.field(description="Formatted display name with view count")
    def display_name(self) -> str:
        """Display name with view count."""
        views = getattr(self, "views", 0) or 0
        return f"{self.title} ({views} views)"  # type: ignore[attr-defined]


# ============================================================================
# Example 3: Override auto-generated field types
# ============================================================================


@elastic.type(ArticleDocument)
class ArticleWithOverrides:
    """
    Override some auto-generated field types.

    The title field will be int instead of str (user override).
    """

    # This overrides the auto-generated str type
    title: int


# ============================================================================
# Example 4: Exclude specific fields
# ============================================================================


@elastic.type(ArticleDocument, exclude_fields=["views", "tags"])
class ArticlePublic:
    """
    Public article type with sensitive fields excluded.

    Only includes: title, author, content
    Excludes: views, tags
    """


# ============================================================================
# Example 5: Custom index name override
# ============================================================================


@elastic.type(ArticleDocument, index="custom-articles-index")
class ArticleCustomIndex:
    """
    Use a custom index name instead of the one defined in Document.

    This is useful for multi-tenant scenarios or environment-specific indices.
    """


# ============================================================================
# Example 6: Disable auto-field generation
# ============================================================================


@elastic.type(ArticleDocument, auto_fields=False)
class ArticleManual:
    """
    Disable automatic field generation and define fields manually.

    This gives you full control over which fields to expose in GraphQL.
    """

    title: str
    author: str

    @elastic.field
    def short_title(self) -> str:
        """Get a shortened version of the title."""
        return self.title[:50]


# ============================================================================
# Example 7: Multiple custom methods
# ============================================================================


@elastic.type(UserDocument)
class User:
    """
    User type with multiple custom computed fields.
    """

    @elastic.field
    def display_name(self) -> str:
        """Return full name or username."""
        if hasattr(self, "full_name") and self.full_name:
            return self.full_name  # type: ignore[return-value]
        return self.username  # type: ignore[attr-defined]

    @elastic.field
    def initials(self) -> str:
        """Get user initials from full name."""
        if not hasattr(self, "full_name") or not self.full_name:
            return ""

        parts = self.full_name.split()  # type: ignore[union-attr]
        min_parts_for_initials = 2
        if len(parts) >= min_parts_for_initials:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return ""

    @elastic.field(name="emailDomain")
    def email_domain(self) -> str | None:
        """Extract domain from email address."""
        if hasattr(self, "email") and self.email and "@" in self.email:  # type: ignore[operator]
            return self.email.split("@")[1]  # type: ignore[union-attr]
        return None


# ============================================================================
# Example 8: Using with Strawberry schema
# ============================================================================


@strawberry.type
@elastic.type(ArticleDocument)
class ArticleForSchema:
    """
    Combine @strawberry.type with @elastic.type for use in GraphQL schema.

    This allows you to use the type directly in your GraphQL queries.
    """

    @elastic.field
    def url(self) -> str:
        """Generate a URL for this article."""
        # Assuming title is slug-friendly
        slug = getattr(self, "title", "").lower().replace(" ", "-")
        return f"/articles/{slug}"


@strawberry.type
class Query:
    """GraphQL Query root."""

    @strawberry.field
    def article(self, id: str) -> ArticleForSchema | None:  # noqa: ARG002
        """
        Get an article by ID.

        In a real application, this would query Elasticsearch and return
        an instance of ArticleForSchema with data from the document.
        """
        # This is a placeholder - real implementation would query ES
        return None

    @strawberry.field
    def articles(self, limit: int = 10) -> list[ArticleForSchema]:  # noqa: ARG002
        """
        Get a list of articles.

        In a real application, this would query Elasticsearch and return
        a list of ArticleForSchema instances.
        """
        # This is a placeholder - real implementation would query ES
        return []


# Create the schema
schema = strawberry.Schema(query=Query)


# ============================================================================
# Example 9: Type inspection
# ============================================================================


def inspect_types():
    """Demonstrate type inspection of decorated classes."""
    from strawberry_elastic.types import TypeInspector

    inspector = TypeInspector()

    # Inspect basic Article type
    info = inspector.inspect(Article)
    print(f"Article source: {info.source}")
    print(f"Article document: {info.document_class}")
    print(f"Article index: {info.index_name}")
    print(f"Article auto_fields: {info.auto_fields}")

    # Inspect hybrid type
    info = inspector.inspect(ArticleWithCustomFields)
    print(f"\nArticleWithCustomFields source: {info.source}")
    print(f"ArticleWithCustomFields custom fields: {info.custom_fields}")

    # Inspect type with exclusions
    info = inspector.inspect(ArticlePublic)
    print(f"\nArticlePublic exclude_fields: {info.exclude_fields}")


# ============================================================================
# Example 10: Field generation inspection
# ============================================================================


def inspect_generated_fields():
    """Show what fields were generated from Documents."""

    print("Article fields:")
    for name, type_hint in Article.__annotations__.items():
        print(f"  {name}: {type_hint}")

    print("\nArticlePublic fields (with exclusions):")
    for name, type_hint in ArticlePublic.__annotations__.items():
        print(f"  {name}: {type_hint}")

    print("\nArticleManual fields (manual only):")
    for name, type_hint in ArticleManual.__annotations__.items():
        print(f"  {name}: {type_hint}")


if __name__ == "__main__":
    print("=== Type Inspection ===")
    inspect_types()

    print("\n=== Generated Fields ===")
    inspect_generated_fields()

    print("\n=== GraphQL Schema ===")
    print(schema)
