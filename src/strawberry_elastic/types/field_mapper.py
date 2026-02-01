"""
Field mapper for converting Elasticsearch/OpenSearch field types to Python/GraphQL types.

Maps field type definitions from:
- Elasticsearch DSL field classes (Text, Keyword, etc.)
- Elasticsearch/OpenSearch mapping dictionaries (runtime introspection)
- To Python types that Strawberry can use for GraphQL schema generation
"""

from datetime import datetime
from typing import Any, ClassVar, get_args, get_origin

from ._dsl_compat import ensure_dsl, has_dsl, universal_dsl
from .scalars import Completion, GeoPoint, GeoShape, IPAddress, TokenCount


class FieldMapper:
    """
    Maps Elasticsearch/OpenSearch field types to Python/GraphQL types.

    Supports both:
    - Document field classes (Text, Keyword, Integer, etc.)
    - Mapping dictionaries from cluster introspection

    Example:
        >>> mapper = FieldMapper()
        >>> python_type = mapper.map_field("text", {"type": "text"})
        >>> print(python_type)  # <class 'str'>
    """

    # Elasticsearch/OpenSearch field type → Python type mapping
    # Works for both backends as they share the same type system
    ES_TO_PYTHON: ClassVar[dict[str, Any]] = {
        # Text fields
        "text": str,
        "keyword": str,
        "match_only_text": str,  # ES 7.10+
        "wildcard": str,  # ES 7.9+
        "constant_keyword": str,  # ES 7.7+
        # Numeric fields
        "long": int,
        "integer": int,
        "short": int,
        "byte": int,
        "double": float,
        "float": float,
        "half_float": float,
        "scaled_float": float,
        "unsigned_long": int,  # ES 7.10+
        # Date fields
        "date": datetime,
        "date_nanos": datetime,  # ES 7.0+
        # Boolean
        "boolean": bool,
        # Binary
        "binary": str,  # Base64 encoded
        # Range fields (represented as dict with gte/lte/gt/lt)
        "integer_range": dict,
        "float_range": dict,
        "long_range": dict,
        "double_range": dict,
        "date_range": dict,
        "ip_range": dict,
        # Special types requiring custom scalars
        "geo_point": GeoPoint,
        "geo_shape": GeoShape,
        "ip": IPAddress,
        "completion": Completion,
        "token_count": TokenCount,
        # Object/nested (handled separately)
        "object": dict,
        "nested": dict,
        "flattened": dict,  # ES 7.3+
        # Specialized types
        "percolator": str,
        "join": str,
        "rank_feature": float,
        "rank_features": dict,
        "dense_vector": list,
        "sparse_vector": dict,
        "search_as_you_type": str,  # ES 7.2+
        "alias": str,  # Field alias
        "histogram": dict,  # ES 7.6+
        "aggregate_metric_double": dict,  # ES 7.11+
    }

    def map_field(
        self,
        field_name: str,  # noqa: ARG002
        field_def: dict[str, Any],
        required: bool = False,
    ) -> type:
        """
        Map an Elasticsearch/OpenSearch field definition to a Python type.

        Used for runtime mapping introspection (when fetching mapping from cluster).

        Args:
            field_name: Name of the field
            field_def: Field definition dictionary from mapping
            required: Whether the field is required (affects Optional wrapping)

        Returns:
            Python type suitable for use with Strawberry GraphQL

        Example:
            >>> mapper = FieldMapper()
            >>> field_type = mapper.map_field("title", {"type": "text"})
            >>> print(field_type)  # <class 'str'>
        """
        field_type = field_def.get("type", "text")

        # Handle nested objects (will be processed separately)
        if field_type in ("nested", "object") or "properties" in field_def:
            # Will be handled by nested type generation
            return dict

        # Get base Python type
        python_type = self.ES_TO_PYTHON.get(field_type, str)

        # Handle arrays - check if field is an array type
        # Note: In Elasticsearch, all fields are potentially multi-valued
        # This would need to be determined from actual data or conventions
        # For now, we'll keep as single values unless explicitly marked

        # Make optional if not required
        if not required:
            return python_type | None

        return python_type

    def map_document_field(self, field: Any) -> Any:
        """
        Map an Elasticsearch/OpenSearch DSL Field instance to a Python type.

        Used when working with Document classes that have explicit field definitions.

        Works with:
        - elasticsearch.dsl fields (ES 8.18+)
        - elasticsearch_dsl fields (ES 7.x-8.17.x)
        - opensearchpy.helpers.field fields (OpenSearch)

        Args:
            field: Field instance from Document class

        Returns:
            Python type suitable for use with Strawberry GraphQL

        Raises:
            ImportError: If DSL is not available

        Example:
            >>> from elasticsearch.dsl import Text
            >>> mapper = FieldMapper()
            >>> field_type = mapper.map_document_field(Text())
            >>> print(field_type)  # <class 'str'>
        """
        ensure_dsl()

        # Get field classes from the compatibility layer
        field_type = type(field)
        field_class_name = field_type.__name__

        # Build type map using actual classes from the backend
        type_map = self._build_document_type_map()

        # Look up the type
        python_type = type_map.get(field_type)

        # If not found by class, try by class name (for compatibility)
        if python_type is None:
            python_type = self._get_type_by_class_name(field_class_name)

        # Default to str if we can't determine the type
        if python_type is None:
            python_type = str

        # Handle multi-valued fields (arrays)
        # elasticsearch-dsl 8.18+ uses private attributes _multi and _required
        is_multi = getattr(field, "multi", None)
        if is_multi is None:
            is_multi = getattr(field, "_multi", False)

        if is_multi:
            python_type = list[python_type]

        # Handle required/optional
        # In elasticsearch-dsl, required=True means the field must be present
        # If not required or if required is not explicitly set, make it optional
        required = getattr(field, "required", None)
        if required is None:
            required = getattr(field, "_required", False)
        if not required and not self._is_optional(python_type):
            python_type = python_type | None

        return python_type

    def _build_document_type_map(self) -> dict[type, Any]:
        """
        Build a mapping of DSL field classes to Python types.

        This is built dynamically based on which backend is available.

        Returns:
            Dictionary mapping field classes to Python types
        """
        if not has_dsl():
            return {}

        type_map = {}

        # Try to get each field class and map it
        field_mappings = {
            "Text": str,
            "Keyword": str,
            "Integer": int,
            "Long": int,
            "Short": int,
            "Byte": int,
            "Double": float,
            "Float": float,
            "HalfFloat": float,
            "ScaledFloat": float,
            "Boolean": bool,
            "Date": datetime,
            "Binary": str,
            "Ip": IPAddress,
            "Completion": Completion,
            "GeoPoint": GeoPoint,
            "GeoShape": GeoShape,
            "TokenCount": TokenCount,
            # Range types
            "IntegerRange": dict,
            "FloatRange": dict,
            "LongRange": dict,
            "DoubleRange": dict,
            "DateRange": dict,
            "IpRange": dict,
            # Special types
            "Percolator": str,
            "Join": str,
            "RankFeature": float,
            "RankFeatures": dict,
            "DenseVector": list,
            "SearchAsYouType": str,
            "ConstantKeyword": str,
            "Wildcard": str,
        }

        for class_name, python_type in field_mappings.items():
            try:
                field_class = getattr(universal_dsl, class_name)
                type_map[field_class] = python_type
            except AttributeError:
                # Field class doesn't exist in this backend version
                continue

        return type_map

    def _get_type_by_class_name(self, class_name: str) -> Any:
        """
        Get Python type by DSL field class name.

        Fallback method when we can't match by class instance.

        Args:
            class_name: Name of the field class (e.g., "Text", "Integer")

        Returns:
            Python type or None if not found
        """
        name_to_type = {
            "Text": str,
            "Keyword": str,
            "Integer": int,
            "Long": int,
            "Short": int,
            "Byte": int,
            "Double": float,
            "Float": float,
            "HalfFloat": float,
            "ScaledFloat": float,
            "Boolean": bool,
            "Date": datetime,
            "Binary": str,
            "Ip": IPAddress,
            "Completion": Completion,
            "GeoPoint": GeoPoint,
            "GeoShape": GeoShape,
            "TokenCount": TokenCount,
            "IntegerRange": dict,
            "FloatRange": dict,
            "LongRange": dict,
            "DoubleRange": dict,
            "DateRange": dict,
            "IpRange": dict,
            "Object": dict,
            "Nested": dict,
            "Percolator": str,
            "Join": str,
            "RankFeature": float,
            "RankFeatures": dict,
            "DenseVector": list,
            "SearchAsYouType": str,
            "ConstantKeyword": str,
            "Wildcard": str,
        }

        return name_to_type.get(class_name)

    def _is_optional(self, python_type: type) -> bool:
        """
        Check if a type is already optional (Union with None).

        Args:
            python_type: Type to check

        Returns:
            True if type includes None, False otherwise
        """
        # Check for Union types (Type | None or Union[Type, None])
        origin = get_origin(python_type)
        if origin is None:
            return False

        # For Python 3.10+ union syntax (Type | None)
        args = get_args(python_type)
        return type(None) in args

    def generate_fields_from_document(
        self,
        document_class: type,
        exclude_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate field definitions from a Document class.

        Extracts all fields from the Document's mapping and converts them
        to Python types suitable for Strawberry GraphQL.

        Args:
            document_class: The Document class to extract fields from
            exclude_fields: List of field names to exclude

        Returns:
            Dictionary mapping field names to Python types

        Example:
            >>> from elasticsearch.dsl import Document, Text, Integer
            >>> class MyDoc(Document):
            ...     title = Text()
            ...     count = Integer()
            >>> mapper = FieldMapper()
            >>> fields = mapper.generate_fields_from_document(MyDoc)
            >>> print(fields)  # {'title': str | None, 'count': int | None}
        """
        ensure_dsl()

        exclude = set(exclude_fields or [])
        fields = {}

        # Get the mapping from the document class
        # Document classes have a _doc_type attribute that contains the mapping
        if not hasattr(document_class, "_doc_type"):
            return fields

        doc_type = document_class._doc_type
        if not hasattr(doc_type, "mapping"):
            return fields

        mapping = doc_type.mapping

        # Iterate through all fields in the mapping
        for field_name in mapping:  # type: ignore[attr-defined]
            if field_name in exclude or field_name.startswith("_"):
                continue

            field = mapping[field_name]  # type: ignore[index]

            # Map the field to a Python type
            try:
                python_type = self.map_document_field(field)
                fields[field_name] = python_type
            except Exception:  # nosec B112
                # If we can't map the field, skip it
                # This allows the library to be resilient to unknown field types
                continue

        return fields

    def generate_nested_type(
        self,
        field_name: str,  # noqa: ARG002
        field: Any,
    ) -> dict[str, Any]:
        """
        Generate field definitions for a nested/object field.

        Recursively processes nested objects to create field mappings.

        Args:
            field_name: Name of the nested field
            field: The nested field instance

        Returns:
            Dictionary mapping nested field names to Python types

        Example:
            >>> from elasticsearch.dsl import Object, Text
            >>> class AuthorObject(InnerDoc):
            ...     name = Text()
            ...     email = Text()
            >>> nested_fields = mapper.generate_nested_type("author", AuthorObject)
        """
        ensure_dsl()

        nested_fields = {}

        # Check if this is an Object or Nested field with properties
        if hasattr(field, "properties"):
            for prop_name, prop_field in field.properties.to_dict().items():
                if prop_name.startswith("_"):
                    continue

                try:
                    python_type = self.map_document_field(prop_field)
                    nested_fields[prop_name] = python_type
                except Exception:  # nosec B112
                    continue

        return nested_fields


__all__ = [
    "FieldMapper",
]
