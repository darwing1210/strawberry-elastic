"""Custom exceptions for strawberry-elastic."""


class StrawberryElasticError(Exception):
    """Base exception for all strawberry-elastic errors."""


class AdapterError(StrawberryElasticError):
    """Error related to client adapters."""


class ClientNotFoundError(AdapterError):
    """Raised when no client adapter could be created."""


class UnsupportedClientError(AdapterError):
    """Raised when the client type is not supported."""


class ConfigurationError(StrawberryElasticError):
    """Error in configuration or setup."""


class MappingError(StrawberryElasticError):
    """Error related to index mappings."""


class QueryError(StrawberryElasticError):
    """Error building or executing queries."""


class DocumentNotFoundError(StrawberryElasticError):
    """Raised when a document is not found."""

    def __init__(self, index: str, id: str, message: str | None = None):
        self.index = index
        self.id = id
        if message is None:
            message = f"Document with id '{id}' not found in index '{index}'"
        super().__init__(message)


class IndexNotFoundError(StrawberryElasticError):
    """Raised when an index is not found."""

    def __init__(self, index: str, message: str | None = None):
        self.index = index
        if message is None:
            message = f"Index '{index}' not found"
        super().__init__(message)


class BulkOperationError(StrawberryElasticError):
    """Raised when bulk operations fail."""

    def __init__(self, errors: list, message: str | None = None):
        self.errors = errors
        if message is None:
            message = f"Bulk operation failed with {len(errors)} errors"
        super().__init__(message)


class ValidationError(StrawberryElasticError):
    """Raised when data validation fails."""


class PaginationError(StrawberryElasticError):
    """Error related to pagination."""


class CapabilityError(StrawberryElasticError):
    """Raised when a feature is not supported by the client."""

    def __init__(self, capability: str, message: str | None = None):
        self.capability = capability
        if message is None:
            message = f"Feature '{capability}' is not supported by this client"
        super().__init__(message)
