"""
Custom GraphQL scalars for Elasticsearch/OpenSearch special types.

Provides scalars for types that don't have direct GraphQL equivalents:
- GeoPoint: Geographic coordinates (latitude/longitude)
- GeoShape: Geographic shapes (polygons, etc.)
- IPAddress: IP address strings with validation
"""

from typing import Any, NewType

import strawberry


# Constants for geo point validation
_GEO_POINT_ARRAY_LENGTH = 2
_MIN_LATITUDE = -90
_MAX_LATITUDE = 90
_MIN_LONGITUDE = -180
_MAX_LONGITUDE = 180
_IPV4_PARTS_COUNT = 4
_MAX_IPV4_OCTET = 255


def _serialize_geo_point(value: Any) -> dict[str, float] | None:
    """
    Serialize a geo_point value to GraphQL.

    Elasticsearch can store geo_point in multiple formats, we normalize to object.

    Args:
        value: Geo point in various formats from Elasticsearch

    Returns:
        Dictionary with lat and lon keys, or None if value is None
    """
    if value is None:
        return None

    # Already in object format
    if isinstance(value, dict):
        if "lat" in value and "lon" in value:
            return {"lat": float(value["lat"]), "lon": float(value["lon"])}
        # Handle alternative naming
        if "latitude" in value and "longitude" in value:
            return {"lat": float(value["latitude"]), "lon": float(value["longitude"])}

    # Array format [lon, lat] (GeoJSON convention)
    if isinstance(value, list | tuple) and len(value) == _GEO_POINT_ARRAY_LENGTH:
        return {"lat": float(value[1]), "lon": float(value[0])}

    # String format "lat,lon"
    if isinstance(value, str) and "," in value:
        parts = value.split(",")
        if len(parts) == _GEO_POINT_ARRAY_LENGTH:
            return {"lat": float(parts[0].strip()), "lon": float(parts[1].strip())}

    # Return as-is if we can't parse it
    return value


def _parse_geo_point(value: Any) -> dict[str, float]:
    """
    Parse a geo_point value from GraphQL input.

    Args:
        value: Input value from GraphQL (should be object with lat/lon)

    Returns:
        Dictionary with lat and lon keys

    Raises:
        ValueError: If the input format is invalid
    """
    if not isinstance(value, dict):
        raise TypeError(
            f"GeoPoint must be an object with lat and lon fields, got {type(value).__name__}"
        )

    if "lat" not in value or "lon" not in value:
        raise ValueError("GeoPoint must have both 'lat' and 'lon' fields")

    try:
        lat = float(value["lat"])
        lon = float(value["lon"])
    except (ValueError, TypeError) as e:
        raise ValueError(f"GeoPoint lat and lon must be numeric: {e}") from e

    # Validate ranges
    if not _MIN_LATITUDE <= lat <= _MAX_LATITUDE:
        raise ValueError(f"Latitude must be between {_MIN_LATITUDE} and {_MAX_LATITUDE}, got {lat}")
    if not _MIN_LONGITUDE <= lon <= _MAX_LONGITUDE:
        raise ValueError(
            f"Longitude must be between {_MIN_LONGITUDE} and {_MAX_LONGITUDE}, got {lon}"
        )

    return {"lat": lat, "lon": lon}


def _identity(v: Any) -> Any:
    """Identity function for GeoShape serialization."""
    return v


@strawberry.scalar(
    serialize=_serialize_geo_point,
    parse_value=_parse_geo_point,
    description="A geographic point with latitude and longitude coordinates",
)
class GeoPoint:
    """
    Represents a geographic point.

    Can be represented as:
    - Object: {"lat": 41.12, "lon": -71.34}
    - Array: [lon, lat] (note: longitude first, following GeoJSON convention)
    - String: "lat,lon" or WKT format

    GraphQL representation is always as an object with lat/lon fields.
    """

    __slots__ = ()


@strawberry.scalar(
    serialize=_identity,
    parse_value=_identity,
    description="A geographic shape (polygon, multipolygon, etc.) in GeoJSON format",
)
class GeoShape:
    """
    Represents a geographic shape in GeoJSON format.

    Used for geo_shape fields in Elasticsearch/OpenSearch.
    Supports various geometry types: Point, LineString, Polygon, MultiPoint, etc.

    The value is passed through as-is since GeoJSON is already JSON-compatible.
    """

    __slots__ = ()


# IP Address scalar with validation
def _serialize_ip_address(v: Any) -> str | None:
    """Serialize IP address to string."""
    return str(v) if v is not None else None


def _parse_ip_address(value: Any) -> str:
    """
    Parse and validate an IP address.

    Args:
        value: IP address string

    Returns:
        Validated IP address string

    Raises:
        ValueError: If the IP address format is invalid
    """
    if not isinstance(value, str):
        raise TypeError(f"IP address must be a string, got {type(value).__name__}")

    # Basic validation - check if it looks like an IP address
    # For more thorough validation, could use ipaddress module
    value = value.strip()

    if not value:
        raise ValueError("IP address cannot be empty")

    # Very basic check for IPv4 (contains dots and numbers)
    # or IPv6 (contains colons)
    if "." in value:
        # IPv4-like
        parts = value.split(".")
        if len(parts) != _IPV4_PARTS_COUNT:
            raise ValueError(f"Invalid IPv4 address format: {value}")
        try:
            _validate_ipv4_parts(parts)
        except ValueError as e:
            raise ValueError(f"Invalid IPv4 address: {value}") from e
    elif ":" in value:
        # IPv6-like - just check it has colons
        # Full IPv6 validation is complex, leave it to Elasticsearch
        pass
    else:
        raise ValueError(f"Invalid IP address format: {value}")

    return value


def _validate_ipv4_parts(parts: list[str]) -> None:
    """Validate IPv4 address parts."""
    for part in parts:
        num = int(part)
        if not 0 <= num <= _MAX_IPV4_OCTET:
            raise ValueError(f"Invalid IPv4 octet: {part}")


@strawberry.scalar(
    serialize=_serialize_ip_address,
    parse_value=_parse_ip_address,
    description="An IPv4 or IPv6 address",
)
class IPAddress:
    """
    Represents an IP address (IPv4 or IPv6).

    Basic validation is performed to ensure the format is correct.
    """

    __slots__ = ()


# Type aliases for fields that don't need custom scalars but benefit from semantic naming
CompletionType = NewType("CompletionType", str)
TokenCountType = NewType("TokenCountType", int)

Completion = strawberry.scalar(
    CompletionType,
    serialize=str,
    parse_value=str,
    description="A completion suggestion value",
)

TokenCount = strawberry.scalar(
    TokenCountType,
    serialize=int,
    parse_value=int,
    description="Number of tokens in analyzed text",
)


# Export all scalars
__all__ = [
    "Completion",
    "GeoPoint",
    "GeoShape",
    "IPAddress",
    "TokenCount",
]
