"""Tests for @elastic.type decorator."""

import pytest

from strawberry_elastic import elastic
from strawberry_elastic.types import FieldSource, TypeInspector


# Skip if DSL is not available
pytest.importorskip("elasticsearch.dsl", reason="elasticsearch-dsl not installed")

from elasticsearch.dsl import Document, Integer, Keyword, Text


class ArticleDocument(Document):
    """Sample Document for testing."""

    title = Text()
    author = Keyword()
    views = Integer()

    class Index:
        name = "articles"


class TestElasticTypeDecorator:
    """Test @elastic.type decorator functionality."""

    def test_basic_decorator_usage(self):
        """Test basic @elastic.type decorator usage."""

        @elastic.type(ArticleDocument)
        class Article:
            pass

        # Check that elastic metadata is set
        assert hasattr(Article, "_elastic_type")
        elastic_meta = Article._elastic_type  # type: ignore[attr-defined]

        assert elastic_meta["document_class"] == ArticleDocument
        assert elastic_meta["auto_fields"] is True
        assert elastic_meta["exclude_fields"] == []
        assert elastic_meta["field_source"] == FieldSource.DOCUMENT

    def test_decorator_with_index_override(self):
        """Test decorator with custom index name."""

        @elastic.type(ArticleDocument, index="custom-index")
        class Article:
            pass

        elastic_meta = Article._elastic_type  # type: ignore[attr-defined]
        assert elastic_meta["index_name"] == "custom-index"

    def test_decorator_with_auto_fields_disabled(self):
        """Test decorator with auto_fields=False."""

        @elastic.type(ArticleDocument, auto_fields=False)
        class Article:
            pass

        elastic_meta = Article._elastic_type  # type: ignore[attr-defined]
        assert elastic_meta["auto_fields"] is False

    def test_decorator_with_exclude_fields(self):
        """Test decorator with excluded fields."""

        @elastic.type(ArticleDocument, exclude_fields=["views"])
        class Article:
            pass

        elastic_meta = Article._elastic_type  # type: ignore[attr-defined]
        assert "views" in elastic_meta["exclude_fields"]

    def test_auto_field_generation(self):
        """Test that fields are automatically generated from Document."""

        @elastic.type(ArticleDocument)
        class Article:
            pass

        # Check that annotations were added
        assert hasattr(Article, "__annotations__")
        annotations = Article.__annotations__

        # Should have fields from the Document
        assert "title" in annotations
        assert "author" in annotations
        assert "views" in annotations

    def test_auto_field_generation_with_exclusions(self):
        """Test auto field generation respects exclusions."""

        @elastic.type(ArticleDocument, exclude_fields=["views"])
        class Article:
            pass

        annotations = Article.__annotations__

        # Should have title and author, but not views
        assert "title" in annotations
        assert "author" in annotations
        assert "views" not in annotations

    def test_preserves_existing_annotations(self):
        """Test that existing annotations are preserved."""

        @elastic.type(ArticleDocument)
        class Article:
            custom_field: str

        annotations = Article.__annotations__

        # Should have both auto-generated and custom fields
        assert "title" in annotations
        assert "author" in annotations
        assert "views" in annotations
        assert "custom_field" in annotations

    def test_existing_annotations_override_generated(self):
        """Test that existing annotations take precedence."""

        @elastic.type(ArticleDocument)
        class Article:
            # Override the generated type
            title: int

        annotations = Article.__annotations__

        # Title should be int (user override), not str (auto-generated)
        assert annotations["title"] is int

    def test_decorator_without_document(self):
        """Test decorator without a Document class."""

        @elastic.type()
        class Article:
            title: str

        elastic_meta = Article._elastic_type  # type: ignore[attr-defined]
        assert elastic_meta["document_class"] is None
        assert elastic_meta["field_source"] == FieldSource.UNKNOWN

    def test_type_inspector_recognizes_decorated_class(self):
        """Test that TypeInspector recognizes @elastic.type decorated classes."""

        @elastic.type(ArticleDocument)
        class Article:
            pass

        inspector = TypeInspector()
        info = inspector.inspect(Article)

        # When auto_fields=True, fields are generated which creates annotations
        # This makes it hybrid mode (Document + type hints)
        assert info.source == "hybrid"
        assert info.document_class == ArticleDocument
        assert info.index_name == "articles"
        assert info.auto_fields is True
        assert info.exclude_fields == []

    def test_type_inspector_recognizes_hybrid_mode(self):
        """Test that TypeInspector recognizes hybrid mode (Document + custom fields)."""

        @elastic.type(ArticleDocument)
        class Article:
            custom_field: str

            @elastic.field
            def computed_field(self) -> str:
                return "computed"

        inspector = TypeInspector()
        info = inspector.inspect(Article)

        # Should be hybrid because it has both Document and custom annotations/fields
        assert info.source == "hybrid"
        assert info.has_type_hints is True
        assert info.custom_fields is not None
        assert "computed_field" in info.custom_fields

    def test_decorator_with_index_from_document(self):
        """Test that index name is extracted from Document if not overridden."""

        @elastic.type(ArticleDocument)
        class Article:
            pass

        inspector = TypeInspector()
        info = inspector.inspect(Article)

        # Should use index name from Document.Index.name
        assert info.index_name == "articles"

    def test_decorator_index_override_takes_precedence(self):
        """Test that explicit index parameter overrides Document index."""

        @elastic.type(ArticleDocument, index="override-index")
        class Article:
            pass

        inspector = TypeInspector()
        info = inspector.inspect(Article)

        assert info.index_name == "override-index"


class TestElasticFieldDecorator:
    """Test @elastic.field decorator functionality."""

    def test_basic_field_decorator(self):
        """Test basic @elastic.field decorator usage."""

        @elastic.type(ArticleDocument)
        class Article:
            @elastic.field
            def full_title(self) -> str:
                return f"{self.title} - Full"

        # Check that the method is marked
        assert hasattr(Article.full_title, "_elastic_field")
        assert Article.full_title._elastic_field is True

    def test_field_decorator_with_name(self):
        """Test @elastic.field decorator with custom name."""

        @elastic.type(ArticleDocument)
        class Article:
            @elastic.field(name="customName")
            def full_title(self) -> str:
                return f"{self.title} - Full"

        assert hasattr(Article.full_title, "_elastic_field_name")
        assert Article.full_title._elastic_field_name == "customName"

    def test_field_decorator_with_description(self):
        """Test @elastic.field decorator with description."""

        @elastic.type(ArticleDocument)
        class Article:
            @elastic.field(description="The full title of the article")
            def full_title(self) -> str:
                return f"{self.title} - Full"

        assert hasattr(Article.full_title, "_elastic_field_description")
        assert Article.full_title._elastic_field_description == "The full title of the article"

    def test_field_decorator_without_parentheses(self):
        """Test @elastic.field decorator usage without parentheses."""

        @elastic.type(ArticleDocument)
        class Article:
            @elastic.field
            def full_title(self) -> str:
                return f"{self.title} - Full"

        assert hasattr(Article.full_title, "_elastic_field")

    def test_field_decorator_with_parentheses(self):
        """Test @elastic.field decorator usage with parentheses."""

        @elastic.type(ArticleDocument)
        class Article:
            @elastic.field()
            def full_title(self) -> str:
                return f"{self.title} - Full"

        assert hasattr(Article.full_title, "_elastic_field")

    def test_type_inspector_detects_custom_fields(self):
        """Test that TypeInspector detects custom fields."""

        @elastic.type(ArticleDocument)
        class Article:
            @elastic.field
            def full_title(self) -> str:
                return f"{self.title} - Full"

            @elastic.field
            def author_upper(self) -> str:
                return self.author.upper()

        inspector = TypeInspector()
        info = inspector.inspect(Article)

        assert info.custom_fields is not None
        assert "full_title" in info.custom_fields
        assert "author_upper" in info.custom_fields


class TestDecoratorEdgeCases:
    """Test edge cases and error handling."""

    def test_decorator_on_class_without_document(self):
        """Test decorator works on a class without a Document."""

        @elastic.type(auto_fields=False)
        class Article:
            title: str
            author: str

        elastic_meta = Article._elastic_type
        assert elastic_meta["document_class"] is None

    def test_multiple_decorations(self):
        """Test that @elastic.type can be used with other decorators."""
        import strawberry

        @strawberry.type
        @elastic.type(ArticleDocument)
        class Article:
            pass

        # Should have both strawberry type info and elastic metadata
        assert hasattr(Article, "_elastic_type")
        assert hasattr(Article, "__strawberry_definition__")

    def test_auto_fields_false_doesnt_generate(self):
        """Test that auto_fields=False prevents field generation."""

        @elastic.type(ArticleDocument, auto_fields=False)
        class Article:
            pass

        # Should not have annotations from the Document
        annotations = getattr(Article, "__annotations__", {})
        assert "title" not in annotations
        assert "author" not in annotations
        assert "views" not in annotations
