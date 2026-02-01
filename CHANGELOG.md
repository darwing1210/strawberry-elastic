# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-26

### Added

#### Simplified Dependencies

- **Single extras per client type** - No more version-specific extras
  - `[elasticsearch]` - Supports Elasticsearch 7.x and 8.x
  - `[opensearch]` - Supports OpenSearch 1.x and 2.x
  - Removes conflicting extras that made `uv run` fail

#### Adapter System

- **Version-agnostic adapters** for Elasticsearch and OpenSearch
  - `ElasticsearchAdapter` - Works with ES 7.x and 8.x
  - `OpenSearchAdapter` - Works with OpenSearch 1.x and 2.x
- **Auto-detection factory** (`create_adapter`) that automatically detects client type
- **Lazy capability detection** - No network calls during adapter initialization
  - Capabilities detected on first operation
  - Cached for subsequent operations
  - Safe default values before detection
- **Base adapter interface** (`BaseElasticAdapter`) defining unified API
- **Sync and async client support** - Sync clients automatically wrapped with `asyncio.run_in_executor`

#### Core Operations

- Search operations with full query DSL support
- CRUD operations (index, get, update, delete)
- Bulk operations
- Mapping operations (get, put)
- Index management (create, delete, exists, refresh)
- Document retrieval with batching (mget)
- Count operations

#### Developer Tools

- Full type annotations with modern Python 3.12+ syntax
- Type checking with `ty` (100% coverage)
- Linting with `ruff` (all checks passing)
- Code formatting with `black`
- Comprehensive test suite with pytest
- Pre-commit hooks configuration

#### Documentation

- Complete README with usage examples
- Development guide (DEVELOPMENT.md)
- Inline docstrings for all public APIs
- Example scripts demonstrating all features
- Architecture diagrams and design decisions

#### Exception System

- Custom exception hierarchy
- Specific exceptions for common errors:
  - `DocumentNotFoundError`
  - `IndexNotFoundError`
  - `BulkOperationError`
  - `CapabilityError`
  - `ValidationError`

### Fixed

- **Async initialization bug** - Removed async method call from `__init__`
  - Implemented lazy capability detection pattern
  - Capabilities now detected on first operation
  - Properties return safe defaults before detection
- **Type safety** - Fixed all type checking errors
  - Changed `_capabilities` type from `Dict[str, bool]` to `dict[str, Any]`
  - Added runtime type checking for version property
  - Fixed return type narrowing in `_normalize_index`
- **Modern type syntax** - Updated all type annotations
  - `Dict` → `dict`
  - `List` → `list`
  - `Optional[X]` → `X | None`
  - `Union[X, Y]` → `X | Y`

### Changed

- **Logging** - Replaced `print()` statements with Python `logging` module
  - Proper log levels (INFO, WARNING, ERROR)
  - Exception tracebacks with `exc_info=True`
  - Configurable logging format

### Technical Details

#### Architecture Decisions

1. **Lazy Initialization Pattern**
   - No async calls in `__init__` (prevents "coroutine never awaited" errors)
   - `_ensure_capabilities()` called before first operation
   - Properties return conservative defaults before detection
   - Network calls only when actually needed

2. **Version Agnostic Design**
   - Runtime capability detection instead of version checks
   - Feature flags for optional functionality
   - Single adapter per client type (not per version)

3. **Async-First API**
   - All operations are async
   - Sync clients automatically wrapped
   - No blocking operations in async context

4. **Type Safety**
   - 100% type coverage with `ty`
   - Modern Python 3.12+ type syntax
   - Strict type checking enabled

#### Quality Metrics

- **Lines of Code**: ~1,500 Python LOC
- **Type Coverage**: 100% (0 type errors)
- **Test Coverage**: 10 unit tests passing
- **Linting**: All ruff checks passing
- **Formatting**: Black formatted (line length 100)

### Dependencies

#### Required

- `strawberry-graphql>=0.200`
- `typing-extensions>=4.0`

#### Optional (User Choice)

- `elasticsearch>=7.0` (for Elasticsearch 7.x and 8.x)
- `opensearch-py>=1.0` (for OpenSearch 1.x and 2.x)

#### Development

- `pytest>=7.0`
- `pytest-asyncio>=0.21`
- `pytest-cov>=4.0`
- `black>=23.0`
- `ruff>=0.1`
- `ty>=0.0.14`
- `pre-commit>=3.0`

### Migration Guide

No migrations needed - this is the initial release.

### Known Issues

None at this time.

### Future Roadmap

See README.md for the complete roadmap. Next phases:

1. **Phase 2**: Type System (`@elastic.type` decorator)
2. **Phase 3**: Filtering & Search (query builder)
3. **Phase 4**: Pagination (connections, cursors)
4. **Phase 5**: Mutations (GraphQL mutations)
5. **Phase 6**: Advanced Features (aggregations, suggestions)

---

## Development Process

This changelog documents the development of Phase 1 (Adapter System):

### Session 1: Initial Implementation

- Created base adapter interface
- Implemented Elasticsearch adapter
- Implemented OpenSearch adapter
- Created auto-detection factory

### Session 2: Type Checking & Fixes

- Added `ty` for type checking
- Fixed async initialization bug (lazy detection)
- Updated to modern type syntax
- Fixed all type errors (0 errors)

### Session 3: Quality & Testing

- Replaced print with logging
- Added comprehensive test suite
- Verified lazy initialization with tests
- All quality checks passing

### Contributors

- Darwing Medina (@darwingjavier31)
