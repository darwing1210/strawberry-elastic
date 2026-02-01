"""
Tests for field mapper.

Tests the ability to map field types from:
- Elasticsearch/OpenSearch mapping dictionaries
- Document field classes (Text, Keyword, etc.)
- To Python types for GraphQL
"""

from datetime import datetime
from typing import get_args

import pytest

from strawberry_elastic.types._dsl_compat import has_dsl, universal_dsl
from strawberry_elastic.types.field_mapper import FieldMapper
from strawberry_elastic.types.scalars import (
    Completion,
    GeoPoint,
    GeoShape,
    IPAddress,
    TokenCount,
)


def is_type_or_optional(field_type, expected_type):
    """Check if field_type is expected_type or Optional[expected_type]."""
    # Direct match
    if field_type == expected_type:
        return True

    # Check if it's a Union type
    args = get_args(field_type)
    if args:
        # Check if expected_type is in the union
        return expected_type in args

    return False


class TestFieldMapperCreation:
    """Test basic FieldMapper functionality."""

    def test_mapper_creation(self):
        """Test creating a FieldMapper instance."""
        mapper = FieldMapper()
        assert mapper is not None

    def test_es_to_python_mapping_exists(self):
        """Test that ES_TO_PYTHON mapping is defined."""
        mapper = FieldMapper()
        assert hasattr(mapper, "ES_TO_PYTHON")
        assert isinstance(mapper.ES_TO_PYTHON, dict)


class TestMappingDictionaryFields:
    """Test mapping from Elasticsearch/OpenSearch mapping dictionaries."""

    def test_text_field_mapping(self):
        """Test mapping text field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("title", {"type": "text"})
        # Should be optional str by default
        assert is_type_or_optional(field_type, str)

    def test_keyword_field_mapping(self):
        """Test mapping keyword field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("slug", {"type": "keyword"})
        assert is_type_or_optional(field_type, str)

    def test_integer_field_mapping(self):
        """Test mapping integer field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("count", {"type": "integer"})
        assert is_type_or_optional(field_type, int)

    def test_long_field_mapping(self):
        """Test mapping long field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("big_number", {"type": "long"})
        assert is_type_or_optional(field_type, int)

    def test_float_field_mapping(self):
        """Test mapping float field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("price", {"type": "float"})
        assert is_type_or_optional(field_type, float)

    def test_double_field_mapping(self):
        """Test mapping double field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("value", {"type": "double"})
        assert is_type_or_optional(field_type, float)

    def test_boolean_field_mapping(self):
        """Test mapping boolean field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("active", {"type": "boolean"})
        assert is_type_or_optional(field_type, bool)

    def test_date_field_mapping(self):
        """Test mapping date field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("created_at", {"type": "date"})
        assert is_type_or_optional(field_type, datetime)

    def test_binary_field_mapping(self):
        """Test mapping binary field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("data", {"type": "binary"})
        assert is_type_or_optional(field_type, str)


class TestSpecialFieldTypes:
    """Test mapping of special field types with custom scalars."""

    def test_geo_point_field_mapping(self):
        """Test mapping geo_point field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("location", {"type": "geo_point"})
        # Should be GeoPoint or Optional[GeoPoint]
        assert is_type_or_optional(field_type, GeoPoint)

    def test_geo_shape_field_mapping(self):
        """Test mapping geo_shape field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("area", {"type": "geo_shape"})
        assert is_type_or_optional(field_type, GeoShape)

    def test_ip_field_mapping(self):
        """Test mapping ip field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("ip_address", {"type": "ip"})
        assert is_type_or_optional(field_type, IPAddress)

    def test_completion_field_mapping(self):
        """Test mapping completion field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("suggest", {"type": "completion"})
        assert is_type_or_optional(field_type, Completion)

    def test_token_count_field_mapping(self):
        """Test mapping token_count field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("tokens", {"type": "token_count"})
        assert is_type_or_optional(field_type, TokenCount)


class TestRequiredOptionalFields:
    """Test required vs optional field handling."""

    def test_optional_field_by_default(self):
        """Test that fields are optional by default."""
        mapper = FieldMapper()
        field_type = mapper.map_field("title", {"type": "text"}, required=False)

        # Should be Union[str, None] or str | None
        args = getattr(field_type, "__args__", ())
        assert type(None) in args or field_type is type(None)

    def test_required_field(self):
        """Test that required=True produces non-optional type."""
        mapper = FieldMapper()
        field_type = mapper.map_field("title", {"type": "text"}, required=True)

        # Should be str (not optional)
        assert field_type is str

    def test_required_integer_field(self):
        """Test required integer field."""
        mapper = FieldMapper()
        field_type = mapper.map_field("count", {"type": "integer"}, required=True)
        assert field_type is int


class TestObjectNestedFields:
    """Test object and nested field handling."""

    def test_object_field_returns_dict(self):
        """Test that object fields return dict type."""
        mapper = FieldMapper()
        field_type = mapper.map_field("metadata", {"type": "object"})
        assert is_type_or_optional(field_type, dict)

    def test_nested_field_returns_dict(self):
        """Test that nested fields return dict type."""
        mapper = FieldMapper()
        field_type = mapper.map_field("items", {"type": "nested"})
        assert is_type_or_optional(field_type, dict)

    def test_field_with_properties_returns_dict(self):
        """Test that fields with properties are treated as objects."""
        mapper = FieldMapper()
        field_type = mapper.map_field(
            "author",
            {
                "properties": {
                    "name": {"type": "text"},
                    "email": {"type": "keyword"},
                }
            },
        )
        assert is_type_or_optional(field_type, dict)


class TestUnknownFieldTypes:
    """Test handling of unknown or new field types."""

    def test_unknown_field_type_defaults_to_str(self):
        """Test that unknown field types default to str."""
        mapper = FieldMapper()
        field_type = mapper.map_field("unknown", {"type": "future_type"})
        assert is_type_or_optional(field_type, str)

    def test_missing_type_defaults_to_text(self):
        """Test that missing type defaults to text (str)."""
        mapper = FieldMapper()
        field_type = mapper.map_field("no_type", {})
        assert is_type_or_optional(field_type, str)


@pytest.mark.skipif(not has_dsl(), reason="DSL not available")
class TestDocumentFieldMapping:
    """Test mapping from Document field classes."""

    def test_text_field_class(self):
        """Test mapping Text field class."""
        mapper = FieldMapper()
        Text = universal_dsl.Text

        field = Text()
        field_type = mapper.map_document_field(field)

        # Should be optional str by default
        assert is_type_or_optional(field_type, str)

    def test_keyword_field_class(self):
        """Test mapping Keyword field class."""
        mapper = FieldMapper()
        Keyword = universal_dsl.Keyword

        field = Keyword()
        field_type = mapper.map_document_field(field)

        assert is_type_or_optional(field_type, str)

    def test_integer_field_class(self):
        """Test mapping Integer field class."""
        mapper = FieldMapper()
        Integer = universal_dsl.Integer

        field = Integer()
        field_type = mapper.map_document_field(field)

        assert is_type_or_optional(field_type, int)

    def test_boolean_field_class(self):
        """Test mapping Boolean field class."""
        mapper = FieldMapper()
        Boolean = universal_dsl.Boolean

        field = Boolean()
        field_type = mapper.map_document_field(field)

        assert is_type_or_optional(field_type, bool)

    def test_date_field_class(self):
        """Test mapping Date field class."""
        mapper = FieldMapper()
        Date = universal_dsl.Date

        field = Date()
        field_type = mapper.map_document_field(field)

        assert is_type_or_optional(field_type, datetime)


@pytest.mark.skipif(not has_dsl(), reason="DSL not available")
class TestDocumentFieldOptions:
    """Test Document field options (required, multi, etc.)."""

    def test_required_document_field(self):
        """Test required Document field."""
        mapper = FieldMapper()
        Text = universal_dsl.Text

        field = Text(required=True)
        field_type = mapper.map_document_field(field)

        # Should not be optional
        assert field_type is str

    def test_optional_document_field(self):
        """Test optional Document field."""
        mapper = FieldMapper()
        Text = universal_dsl.Text

        field = Text(required=False)
        field_type = mapper.map_document_field(field)

        # Should be optional
        args = getattr(field_type, "__args__", ())
        assert type(None) in args

    def test_multi_valued_field(self):
        """Test multi-valued field becomes list."""
        mapper = FieldMapper()
        Text = universal_dsl.Text

        field = Text(multi=True)
        field_type = mapper.map_document_field(field)

        # Should be list[str] or Optional[list[str]]
        origin = getattr(field_type, "__origin__", None)
        if origin is not None:
            # Check if it's a list or Union containing list
            args = getattr(field_type, "__args__", ())
            # Look for list in the union or check if origin is list
            found_list = origin is list or any(
                getattr(arg, "__origin__", None) is list for arg in args
            )
            assert found_list
        else:
            # Might be list directly
            assert field_type is list or str(field_type).startswith("list")

    def test_required_multi_valued_field(self):
        """Test required multi-valued field."""
        mapper = FieldMapper()
        Text = universal_dsl.Text

        field = Text(multi=True, required=True)
        field_type = mapper.map_document_field(field)

        # Should be list[str] (not optional)
        origin = getattr(field_type, "__origin__", None)
        assert origin is list


@pytest.mark.skipif(not has_dsl(), reason="DSL not available")
class TestSpecialDocumentFields:
    """Test special Document field types."""

    def test_geo_point_document_field(self):
        """Test GeoPoint Document field."""
        mapper = FieldMapper()

        try:
            GeoPointField = universal_dsl.GeoPoint
            field = GeoPointField()
            field_type = mapper.map_document_field(field)

            assert is_type_or_optional(field_type, GeoPoint)
        except AttributeError:
            pytest.skip("GeoPoint not available in this backend")

    def test_ip_document_field(self):
        """Test Ip Document field."""
        mapper = FieldMapper()

        try:
            IpField = universal_dsl.Ip
            field = IpField()
            field_type = mapper.map_document_field(field)

            assert is_type_or_optional(field_type, IPAddress)
        except AttributeError:
            pytest.skip("Ip not available in this backend")


class TestRangeFields:
    """Test range field types."""

    def test_integer_range_mapping(self):
        """Test integer_range field mapping."""
        mapper = FieldMapper()
        field_type = mapper.map_field("age_range", {"type": "integer_range"})
        assert is_type_or_optional(field_type, dict)

    def test_date_range_mapping(self):
        """Test date_range field mapping."""
        mapper = FieldMapper()
        field_type = mapper.map_field("period", {"type": "date_range"})
        assert is_type_or_optional(field_type, dict)

    def test_float_range_mapping(self):
        """Test float_range field mapping."""
        mapper = FieldMapper()
        field_type = mapper.map_field("price_range", {"type": "float_range"})
        assert is_type_or_optional(field_type, dict)


class TestAdvancedFieldTypes:
    """Test advanced/specialized field types."""

    def test_dense_vector_mapping(self):
        """Test dense_vector field mapping."""
        mapper = FieldMapper()
        field_type = mapper.map_field("vector", {"type": "dense_vector"})
        assert is_type_or_optional(field_type, list)

    def test_rank_feature_mapping(self):
        """Test rank_feature field mapping."""
        mapper = FieldMapper()
        field_type = mapper.map_field("rank", {"type": "rank_feature"})
        assert is_type_or_optional(field_type, float)

    def test_flattened_mapping(self):
        """Test flattened field mapping."""
        mapper = FieldMapper()
        field_type = mapper.map_field("dynamic", {"type": "flattened"})
        assert is_type_or_optional(field_type, dict)


class TestFieldMapperStatelessness:
    """Test that field mapper is stateless and reusable."""

    def test_multiple_mappings(self):
        """Test that mapper can be reused."""
        mapper = FieldMapper()

        type1 = mapper.map_field("field1", {"type": "text"})
        type2 = mapper.map_field("field2", {"type": "integer"})
        type3 = mapper.map_field("field3", {"type": "boolean"})

        # All should work independently
        assert is_type_or_optional(type1, str)
        assert is_type_or_optional(type2, int)
        assert is_type_or_optional(type3, bool)

    def test_same_field_multiple_times(self):
        """Test mapping same field type multiple times."""
        mapper = FieldMapper()

        type1 = mapper.map_field("title1", {"type": "text"})
        type2 = mapper.map_field("title2", {"type": "text"})

        # Should produce equivalent types
        assert type1 == type2


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_empty_field_definition(self):
        """Test empty field definition."""
        mapper = FieldMapper()
        field_type = mapper.map_field("empty", {})

        # Should default to text (str)
        assert is_type_or_optional(field_type, str)

    def test_field_with_extra_properties(self):
        """Test field with extra metadata properties."""
        mapper = FieldMapper()
        field_type = mapper.map_field(
            "title",
            {
                "type": "text",
                "analyzer": "standard",
                "fields": {"keyword": {"type": "keyword"}},
            },
        )

        # Should still map to str
        assert is_type_or_optional(field_type, str)

    @pytest.mark.skipif(not has_dsl(), reason="DSL not available")
    def test_document_field_without_options(self):
        """Test Document field with no special options."""
        mapper = FieldMapper()
        Text = universal_dsl.Text

        # Create field with no parameters
        field = Text()
        field_type = mapper.map_document_field(field)

        # Should be optional str
        args = getattr(field_type, "__args__", ())
        assert type(None) in args
