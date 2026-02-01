"""
Custom GraphQL scalars for Elasticsearch/OpenSearch special types.

Provides scalars for types that don't have direct GraphQL equivalents:
- GeoPoint: Geographic coordinates (latitude/longitude)
- GeoShape: Geographic shapes (polygons, etc.)
- IPAddress: IP address strings with validation
"""

from typing import Any, NewType

import strawberry


@strawberry.scalar(
    serialize=lambda v: _serialize_geo_point(v),
    parse_value=lambda v: _parse_geo_point(v),
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
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return {"lat": float(value[1]), "lon": float(value[0])}

    # String format "lat,lon"
    if isinstance(value, str):
        if "," in value:
            parts = value.split(",")
            if len(parts) == 2:
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
        raise ValueError(
            f"GeoPoint must be an object with lat and lon fields, got {type(value).__name__}"
        )

    if "lat" not in value or "lon" not in value:
        raise ValueError("GeoPoint must have both 'lat' and 'lon' fields")

    try:
        lat = float(value["lat"])
        lon = float(value["lon"])
    except (ValueError, TypeError) as e:
        raise ValueError(f"GeoPoint lat and lon must be numeric: {e}")

    # Validate ranges
    if not -90 <= lat <= 90:
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not -180 <= lon <= 180:
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

    return {"lat": lat, "lon": lon}


@strawberry.scalar(
    serialize=lambda v: v,
    parse_value=lambda v: v,
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
@strawberry.scalar(
    serialize=lambda v: str(v) if v is not None else None,
    parse_value=lambda v: _parse_ip_address(v),
    description="An IPv4 or IPv6 address",
)
class IPAddress:
    """
    Represents an IP address (IPv4 or IPv6).

    Basic validation is performed to ensure the format is correct.
    """

    __slots__ = ()


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
        raise ValueError(f"IP address must be a string, got {type(value).__name__}")

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
        if len(parts) != 4:
            raise ValueError(f"Invalid IPv4 address format: {value}")
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    raise ValueError(f"Invalid IPv4 octet: {part}")
        except ValueError:
            raise ValueError(f"Invalid IPv4 address: {value}")
    elif ":" in value:
        # IPv6-like - just check it has colons
        # Full IPv6 validation is complex, leave it to Elasticsearch
        pass
    else:
        raise ValueError(f"Invalid IP address format: {value}")

    return value


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
