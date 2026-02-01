"""
Tests for universal DSL compatibility layer.

Tests the ability to detect and work with:
- Elasticsearch 8.18+ (built-in DSL)
- Elasticsearch 7.x-8.17.x (separate DSL package)
- OpenSearch (opensearchpy.helpers.document)
"""

import pytest

from strawberry_elastic.types._dsl_compat import (
    Backend,
    UniversalDSL,
    ensure_dsl,
    get_backend,
    has_dsl,
    is_elasticsearch,
    is_opensearch,
    universal_dsl,
)


class TestDSLDetection:
    """Test DSL backend detection."""

    def test_singleton_instance(self):
        """Test that universal_dsl is a singleton instance."""
        assert isinstance(universal_dsl, UniversalDSL)

    def test_has_dsl_function(self):
        """Test has_dsl() returns boolean."""
        result = has_dsl()
        assert isinstance(result, bool)

    def test_get_backend_function(self):
        """Test get_backend() returns Backend or None."""
        result = get_backend()
        if result is not None:
            assert result in ["elasticsearch.dsl", "elasticsearch_dsl", "opensearchpy"]

    def test_is_elasticsearch_function(self):
        """Test is_elasticsearch() returns boolean."""
        result = is_elasticsearch()
        assert isinstance(result, bool)

    def test_is_opensearch_function(self):
        """Test is_opensearch() returns boolean."""
        result = is_opensearch()
        assert isinstance(result, bool)

    def test_mutually_exclusive_backends(self):
        """Test that ES and OpenSearch detection are mutually exclusive."""
        if has_dsl():
            # Can't be both at the same time
            assert not (is_elasticsearch() and is_opensearch())


class TestDSLAvailability:
    """Test DSL availability checks."""

    def test_available_property(self):
        """Test available property."""
        assert isinstance(universal_dsl.available, bool)

    def test_backend_property(self):
        """Test backend property."""
        backend = universal_dsl.backend
        if backend is not None:
            assert backend in ["elasticsearch.dsl", "elasticsearch_dsl", "opensearchpy"]

    @pytest.mark.skipif(not has_dsl(), reason="DSL not available")
    def test_ensure_available_when_available(self):
        """Test ensure_dsl() doesn't raise when DSL is available."""
        # Should not raise
        ensure_dsl()
        universal_dsl.ensure_available()

    def test_ensure_available_error_message(self):
        """Test that ensure_available() provides helpful error message."""
        if not has_dsl():
            with pytest.raises(ImportError) as exc_info:
                ensure_dsl()

            error_msg = str(exc_info.value)
            # Should mention installation options
            assert "pip install" in error_msg
            assert "strawberry-elastic" in error_msg


@pytest.mark.skipif(not has_dsl(), reason="DSL not available")
class TestDSLWithBackend:
    """Tests that require a DSL backend to be available."""

    def test_backend_is_detected(self):
        """Test that a backend is detected when DSL is available."""
        assert universal_dsl.backend is not None
        assert universal_dsl.backend in [
            "elasticsearch.dsl",
            "elasticsearch_dsl",
            "opensearchpy",
        ]

    def test_get_document_class(self):
        """Test getting Document class."""
        Document = universal_dsl.get_document_class()
        assert Document is not None
        assert hasattr(Document, "__name__")
        assert "Document" in Document.__name__

    def test_get_inner_doc_class(self):
        """Test getting InnerDoc class."""
        InnerDoc = universal_dsl.get_inner_doc_class()
        assert InnerDoc is not None
        assert hasattr(InnerDoc, "__name__")

    def test_document_class_via_getattr(self):
        """Test accessing Document via __getattr__."""
        Document = universal_dsl.Document
        assert Document is not None
        assert hasattr(Document, "__name__")

    def test_field_classes_accessible(self):
        """Test that common field classes are accessible."""
        # These should be available in all backends
        Text = universal_dsl.Text
        Keyword = universal_dsl.Keyword
        Integer = universal_dsl.Integer
        Boolean = universal_dsl.Boolean
        Date = universal_dsl.Date

        assert all([Text, Keyword, Integer, Boolean, Date])

    def test_nonexistent_attribute_raises(self):
        """Test that accessing non-existent attributes raises AttributeError."""
        with pytest.raises(AttributeError) as exc_info:
            _ = universal_dsl.NonExistentFieldType

        assert "does not have attribute" in str(exc_info.value)

    def test_normalize_field(self):
        """Test field normalization (currently pass-through)."""
        # Create a simple field
        Text = universal_dsl.Text
        field = Text()

        # Normalize should return the same field (for now)
        normalized = universal_dsl.normalize_field(field)
        assert normalized is field


@pytest.mark.skipif(
    not has_dsl() or not is_elasticsearch(), reason="Elasticsearch DSL not available"
)
class TestElasticsearchBackend:
    """Tests specific to Elasticsearch backend."""

    def test_elasticsearch_detected(self):
        """Test that Elasticsearch is correctly detected."""
        assert is_elasticsearch()
        assert not is_opensearch()

    def test_backend_name(self):
        """Test backend name is one of the ES variants."""
        assert universal_dsl.backend in ["elasticsearch.dsl", "elasticsearch_dsl"]

    def test_elasticsearch_specific_fields(self):
        """Test Elasticsearch-specific field types."""
        # These might not be in OpenSearch
        try:
            Completion = universal_dsl.Completion
            assert Completion is not None
        except AttributeError:
            pytest.skip("Completion not available in this version")


@pytest.mark.skipif(not has_dsl() or not is_opensearch(), reason="OpenSearch DSL not available")
class TestOpenSearchBackend:
    """Tests specific to OpenSearch backend."""

    def test_opensearch_detected(self):
        """Test that OpenSearch is correctly detected."""
        assert is_opensearch()
        assert not is_elasticsearch()

    def test_backend_name(self):
        """Test backend name is opensearchpy."""
        assert universal_dsl.backend == "opensearchpy"

    def test_opensearch_document_accessible(self):
        """Test that OpenSearch Document is accessible."""
        Document = universal_dsl.Document
        assert Document is not None


class TestMultipleInstances:
    """Test that multiple UniversalDSL instances work correctly."""

    def test_multiple_instances_same_detection(self):
        """Test that multiple instances detect the same backend."""
        instance1 = UniversalDSL()
        instance2 = UniversalDSL()

        assert instance1.available == instance2.available
        assert instance1.backend == instance2.backend
        assert instance1.is_elasticsearch == instance2.is_elasticsearch
        assert instance1.is_opensearch == instance2.is_opensearch

    @pytest.mark.skipif(not has_dsl(), reason="DSL not available")
    def test_independent_instances(self):
        """Test that instances are independent."""
        instance1 = UniversalDSL()
        instance2 = UniversalDSL()

        # They should both work but be independent objects
        assert instance1 is not instance2

        # But should have the same backend info
        assert instance1._info.backend == instance2._info.backend


class TestErrorHandling:
    """Test error handling when DSL is not available."""

    def test_getattr_without_dsl(self):
        """Test that __getattr__ raises ImportError when DSL not available."""
        if not has_dsl():
            with pytest.raises(ImportError) as exc_info:
                _ = universal_dsl.Document

            error_msg = str(exc_info.value)
            assert "Document support requires" in error_msg

    def test_get_document_class_without_dsl(self):
        """Test get_document_class() raises ImportError when DSL not available."""
        if not has_dsl():
            with pytest.raises(ImportError):
                universal_dsl.get_document_class()

    def test_get_inner_doc_class_without_dsl(self):
        """Test get_inner_doc_class() raises ImportError when DSL not available."""
        if not has_dsl():
            with pytest.raises(ImportError):
                universal_dsl.get_inner_doc_class()


@pytest.mark.skipif(not has_dsl(), reason="DSL not available")
class TestDocumentCreation:
    """Test creating Document classes with detected backend."""

    def test_create_basic_document(self):
        """Test creating a basic Document class."""
        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class TestDoc(Document):
            title = Text()

            class Index:
                name = "test"

        # Should be a valid Document class
        assert issubclass(TestDoc, Document)
        # OpenSearch stores fields differently - check on instance
        doc = TestDoc()
        assert hasattr(doc, "title")

    def test_create_document_with_multiple_fields(self):
        """Test creating a Document with multiple field types."""
        Document = universal_dsl.Document
        Text = universal_dsl.Text
        Keyword = universal_dsl.Keyword
        Integer = universal_dsl.Integer
        Boolean = universal_dsl.Boolean

        class TestDoc(Document):
            title = Text()
            slug = Keyword()
            count = Integer()
            active = Boolean()

            class Index:
                name = "test"

        assert issubclass(TestDoc, Document)
        # OpenSearch stores fields differently - check on instance
        doc = TestDoc()
        assert hasattr(doc, "title")
        assert hasattr(doc, "slug")
        assert hasattr(doc, "count")
        assert hasattr(doc, "active")

    def test_create_nested_document(self):
        """Test creating nested documents with InnerDoc."""
        try:
            Document = universal_dsl.Document
            InnerDoc = universal_dsl.get_inner_doc_class()
            Text = universal_dsl.Text
            Nested = universal_dsl.Nested

            class Author(InnerDoc):
                name = Text()

            class Article(Document):
                title = Text()
                author = Nested(Author)

                class Index:
                    name = "articles"

            assert issubclass(Article, Document)
            assert issubclass(Author, InnerDoc)
        except AttributeError:
            pytest.skip("Nested/InnerDoc not available in this backend")


class TestBackendTypeHints:
    """Test type hints and typing support."""

    def test_backend_type_hint(self):
        """Test that Backend type is properly defined."""
        # This is a compile-time check, but we can verify the literal values
        from typing import get_args

        # Backend should be a Literal type
        backend_values = get_args(Backend)
        assert "elasticsearch.dsl" in backend_values
        assert "elasticsearch_dsl" in backend_values
        assert "opensearchpy" in backend_values
