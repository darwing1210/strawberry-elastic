"""
Tests for type inspector.

Tests the ability to detect field sources from:
- Document classes (Elasticsearch/OpenSearch)
- Python type hints
- Custom decorated fields
- Hybrid approaches
"""

import pytest

from strawberry_elastic.types._dsl_compat import has_dsl, universal_dsl
from strawberry_elastic.types.inspector import TypeInfo, TypeInspector


class TestTypeInspector:
    """Test basic TypeInspector functionality."""

    def test_inspector_creation(self):
        """Test creating a TypeInspector instance."""
        inspector = TypeInspector()
        assert inspector is not None

    def test_inspect_returns_type_info(self):
        """Test that inspect() returns a TypeInfo object."""
        inspector = TypeInspector()

        class TestClass:
            pass

        info = inspector.inspect(TestClass)
        assert isinstance(info, TypeInfo)
        assert info.source in ["document", "mapping", "hints", "hybrid"]


class TestTypeHintsDetection:
    """Test detection of type hints."""

    def test_class_with_type_hints(self):
        """Test that class with type hints is detected as 'hints' source."""
        inspector = TypeInspector()

        class UserType:
            username: str
            email: str
            age: int

        info = inspector.inspect(UserType)

        # Should be detected as hints (unless it's also a Document)
        if not has_dsl():
            assert info.source == "hints"
        assert info.has_type_hints is True

    def test_class_without_type_hints(self):
        """Test that class without type hints requires mapping."""
        inspector = TypeInspector()

        class PlainClass:
            pass

        info = inspector.inspect(PlainClass)

        # Should require mapping introspection
        if not has_dsl():
            assert info.source == "mapping"
            assert info.has_type_hints is False

    def test_class_with_only_private_annotations(self):
        """Test that private annotations are ignored."""
        inspector = TypeInspector()

        class PrivateAnnotations:
            _private: str
            __very_private: int

        info = inspector.inspect(PrivateAnnotations)

        # Should not count as having type hints
        assert info.has_type_hints is False

    def test_class_with_mixed_annotations(self):
        """Test class with both public and private annotations."""
        inspector = TypeInspector()

        class MixedAnnotations:
            public: str
            _private: int

        info = inspector.inspect(MixedAnnotations)

        # Should count as having type hints (has at least one public)
        assert info.has_type_hints is True


@pytest.mark.skipif(not has_dsl(), reason="DSL not available")
class TestDocumentDetection:
    """Test detection of Document classes."""

    def test_document_class_detected(self):
        """Test that Document subclass is detected."""
        inspector = TypeInspector()

        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class Article(Document):
            title = Text()

            class Index:
                name = "articles"

        info = inspector.inspect(Article)

        assert info.source in ["document", "hybrid"]
        assert info.document_class == Article
        assert info.index_name == "articles"

    def test_document_without_index_name(self):
        """Test Document without Index.name."""
        inspector = TypeInspector()

        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class SimpleDoc(Document):
            title = Text()

        info = inspector.inspect(SimpleDoc)

        assert info.source in ["document", "hybrid"]
        assert info.document_class == SimpleDoc
        assert info.index_name is None

    def test_document_with_type_hints_is_hybrid(self):
        """Test that Document with type hints is detected as hybrid."""
        inspector = TypeInspector()

        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class HybridDoc(Document):
            # Document field
            title = Text()

            # Type hint (custom field)
            computed_field: str

            class Index:
                name = "hybrid"

        info = inspector.inspect(HybridDoc)

        assert info.source == "hybrid"
        assert info.has_type_hints is True
        assert info.document_class == HybridDoc

    def test_non_document_class(self):
        """Test that regular class is not detected as Document."""
        inspector = TypeInspector()

        class NotADocument:
            title: str

        info = inspector.inspect(NotADocument)

        assert info.source == "hints"
        assert info.document_class is None


class TestCustomFieldDetection:
    """Test detection of custom fields marked with @elastic.field."""

    def test_detect_custom_field_marker(self):
        """Test detection of fields with _elastic_field marker."""
        inspector = TypeInspector()

        def custom_method(_self):
            return "value"

        # Mark as elastic field
        custom_method._elastic_field = True  # type: ignore[attr-defined]

        class CustomFieldClass:
            custom = custom_method

        info = inspector.inspect(CustomFieldClass)

        assert info.custom_fields is not None
        assert "custom" in info.custom_fields

    def test_no_custom_fields(self):
        """Test that custom_fields is None when no custom fields exist."""
        inspector = TypeInspector()

        class NoCustomFields:
            regular: str

        info = inspector.inspect(NoCustomFields)

        assert info.custom_fields is None

    def test_ignore_private_methods(self):
        """Test that private methods are ignored."""
        inspector = TypeInspector()

        class WithPrivate:
            def _private_method(self):
                pass

        # Even if marked, should be ignored
        WithPrivate._private_method._elastic_field = True  # type: ignore[attr-defined]

        info = inspector.inspect(WithPrivate)

        assert info.custom_fields is None or "_private_method" not in info.custom_fields


@pytest.mark.skipif(not has_dsl(), reason="DSL not available")
class TestHybridDetection:
    """Test detection of hybrid Document + custom fields."""

    def test_document_with_custom_fields(self):
        """Test Document with custom methods marked as fields."""
        inspector = TypeInspector()

        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class HybridDoc(Document):
            title = Text()

            def custom_method(self):
                return "custom"

            class Index:
                name = "hybrid"

        # Mark method as elastic field
        HybridDoc.custom_method._elastic_field = True  # type: ignore[attr-defined]

        info = inspector.inspect(HybridDoc)

        assert info.source == "hybrid"
        assert info.custom_fields is not None
        assert "custom_method" in info.custom_fields

    def test_document_with_hints_and_custom(self):
        """Test Document with both type hints and custom fields."""
        inspector = TypeInspector()

        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class ComplexHybrid(Document):
            # Document field
            title = Text()

            # Type hint
            extra: str

            def method_field(self):
                return "value"

            class Index:
                name = "complex"

        ComplexHybrid.method_field._elastic_field = True  # type: ignore[attr-defined]

        info = inspector.inspect(ComplexHybrid)

        assert info.source == "hybrid"
        assert info.has_type_hints is True
        assert info.custom_fields is not None
        assert "method_field" in info.custom_fields


class TestIndexNameExtraction:
    """Test extraction of index name from Document classes."""

    @pytest.mark.skipif(not has_dsl(), reason="DSL not available")
    def test_extract_simple_index_name(self):
        """Test extracting simple index name."""
        inspector = TypeInspector()

        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class TestDoc(Document):
            title = Text()

            class Index:
                name = "test-index"

        info = inspector.inspect(TestDoc)
        assert info.index_name == "test-index"

    @pytest.mark.skipif(not has_dsl(), reason="DSL not available")
    def test_no_index_class(self):
        """Test Document without Index class."""
        inspector = TypeInspector()

        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class NoIndex(Document):
            title = Text()

        info = inspector.inspect(NoIndex)
        assert info.index_name is None

    @pytest.mark.skipif(not has_dsl(), reason="DSL not available")
    def test_index_without_name(self):
        """Test Document with Index class but no name."""
        inspector = TypeInspector()

        Document = universal_dsl.Document
        Text = universal_dsl.Text

        class IndexNoName(Document):
            title = Text()

            class Index:
                using = "default"

        info = inspector.inspect(IndexNoName)
        assert info.index_name is None


class TestTypeInfoDataclass:
    """Test TypeInfo dataclass properties."""

    def test_type_info_creation(self):
        """Test creating TypeInfo instances."""
        info = TypeInfo(source="hints")

        assert info.source == "hints"
        assert info.document_class is None
        assert info.index_name is None
        assert info.has_type_hints is False
        assert info.custom_fields is None

    def test_type_info_with_all_fields(self):
        """Test TypeInfo with all fields populated."""

        class DummyDoc:
            pass

        custom = {"field": "value"}

        info = TypeInfo(
            source="hybrid",
            document_class=DummyDoc,
            index_name="test",
            has_type_hints=True,
            custom_fields=custom,
        )

        assert info.source == "hybrid"
        assert info.document_class == DummyDoc
        assert info.index_name == "test"
        assert info.has_type_hints is True
        assert info.custom_fields == custom


class TestEdgeCases:
    """Test edge cases and unusual class structures."""

    def test_empty_class(self):
        """Test completely empty class."""
        inspector = TypeInspector()

        class Empty:
            pass

        info = inspector.inspect(Empty)

        # Should require mapping introspection
        if not has_dsl():
            assert info.source == "mapping"

    def test_class_with_only_methods(self):
        """Test class with only methods (no fields)."""
        inspector = TypeInspector()

        class OnlyMethods:
            def method1(self):
                pass

            def method2(self):
                pass

        info = inspector.inspect(OnlyMethods)

        # Should require mapping unless methods are marked
        if not has_dsl():
            assert info.source == "mapping"

    def test_class_with_class_variables(self):
        """Test that class variables without annotations are ignored."""
        inspector = TypeInspector()

        class WithClassVars:
            class_var = "value"
            CONSTANT = 42

        info = inspector.inspect(WithClassVars)

        # No annotations, so requires mapping
        if not has_dsl():
            assert info.source == "mapping"
            assert info.has_type_hints is False


class TestInspectorStatelessness:
    """Test that inspector is stateless and reusable."""

    def test_multiple_inspections(self):
        """Test that inspector can be reused for multiple classes."""
        inspector = TypeInspector()

        class Class1:
            field1: str

        class Class2:
            field2: int

        info1 = inspector.inspect(Class1)
        info2 = inspector.inspect(Class2)

        # Should be independent results
        assert info1 is not info2
        if not has_dsl():
            assert info1.source == "hints"
            assert info2.source == "hints"

    def test_same_class_multiple_times(self):
        """Test inspecting the same class multiple times."""
        inspector = TypeInspector()

        class TestClass:
            field: str

        info1 = inspector.inspect(TestClass)
        info2 = inspector.inspect(TestClass)

        # Results should be equivalent (but not necessarily same object)
        assert info1.source == info2.source
        assert info1.has_type_hints == info2.has_type_hints
