# Strawberry Elastic

[![CI](https://github.com/YOUR_USERNAME/strawberry-elastic/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/strawberry-elastic/actions/workflows/ci.yml)
[![Security](https://github.com/YOUR_USERNAME/strawberry-elastic/actions/workflows/security.yml/badge.svg)](https://github.com/YOUR_USERNAME/strawberry-elastic/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/strawberry-elastic/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/strawberry-elastic)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GraphQL integration for Elasticsearch and OpenSearch with Strawberry GraphQL.

**Status**: 🚧 Work in Progress - Phase 2.1 Complete (Type System Core Infrastructure)

## Features

- ✅ **Version-Agnostic Adapters**: Works with any Elasticsearch (7.x, 8.x) or OpenSearch (1.x, 2.x) version
- ✅ **Auto-Detection**: Automatically detects your client type and creates the appropriate adapter
- ✅ **Async-First**: Native async support with automatic sync client wrapping
- ✅ **Client Flexibility**: Users choose their own Elasticsearch/OpenSearch client version
- ✅ **Runtime Capability Detection**: Features detected at runtime (PIT, search_after, etc.)
- ✅ **Type System Core**: Universal DSL compatibility layer for Elasticsearch and OpenSearch
- ✅ **Document Support**: Works with elasticsearch-dsl and opensearchpy Document classes
- ✅ **Field Mapping**: Automatic mapping of 40+ field types to GraphQL types
- ✅ **Custom Scalars**: GeoPoint, GeoShape, IPAddress with validation
- 🚧 **Type Decorator**: @elastic.type decorator (Coming in Phase 2.2)
- 🚧 **Filtering**: Powerful query builder for complex searches (Coming Soon)
- 🚧 **Pagination**: Multiple strategies (offset, search_after, PIT) (Coming Soon)
- 🚧 **Mutations**: CRUD operations and bulk indexing (Coming Soon)

## Installation

```bash
# Base package (no client included)
pip install strawberry-elastic

# Choose your client
pip install strawberry-elastic[elasticsearch]  # For Elasticsearch 7.x/8.x
# OR
pip install strawberry-elastic[opensearch]     # For OpenSearch 1.x/2.x

# Or install client separately
pip install elasticsearch>=7.0      # Elasticsearch 7.x/8.x
pip install opensearch-py>=1.0      # OpenSearch 1.x/2.x

# For Document support (optional)
pip install elasticsearch-dsl       # Elasticsearch Document classes
# OR
pip install opensearch-py           # OpenSearch includes Document support
```

## Quick Start

### Basic Usage with Auto-Detection

```python
import asyncio
from elasticsearch import Elasticsearch
from strawberry_elastic import create_adapter

# Create your client
client = Elasticsearch(["http://localhost:9200"])

# Auto-detect and create adapter
adapter = create_adapter(client)

async def main():
    # Get cluster info
    info = await adapter.info()
    print(f"Connected to: {info['cluster_name']}")
    print(f"Version: {adapter.version}")

    # Search documents
    query = {"match": {"title": "python"}}
    results = await adapter.search(index="articles", query=query, size=10)

    for hit in results["hits"]["hits"]:
        print(f"- {hit['_source']['title']}")

asyncio.run(main())
```

### Using Async Clients

```python
from elasticsearch import AsyncElasticsearch
from strawberry_elastic import create_adapter

async def main():
    # Create async client
    client = AsyncElasticsearch(["http://localhost:9200"])
    adapter = create_adapter(client)

    # Use adapter (native async)
    results = await adapter.search(index="products", query={"match_all": {}})

    # Clean up
    await client.close()

asyncio.run(main())
```

### OpenSearch Support

```python
from opensearchpy import OpenSearch
from strawberry_elastic import create_adapter

# Works exactly the same with OpenSearch
client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_auth=("admin", "admin"),
    use_ssl=False,
)

adapter = create_adapter(client)
```

## Adapter API

The adapter provides a unified interface for both Elasticsearch and OpenSearch:

### Search Operations

```python
# Basic search
results = await adapter.search(
    index="products",
    query={"match": {"category": "electronics"}},
    size=10,
    from_=0,
)

# Advanced search with sorting and pagination
results = await adapter.search(
    index="products",
    query={"bool": {"must": [{"match": {"name": "laptop"}}]}},
    sort=[{"price": "asc"}],
    size=20,
    search_after=[999.99, "id123"],  # For deep pagination
    source=["name", "price"],  # Field filtering
)

# Get single document
doc = await adapter.get(index="products", id="12345")

# Get multiple documents (batch)
docs = await adapter.mget(index="products", ids=["1", "2", "3"])

# Count documents
count = await adapter.count(index="products", query={"match_all": {}})
```

### Index Operations

```python
# Index a document
result = await adapter.index(
    index="products",
    document={"name": "Widget", "price": 19.99},
    id="widget-001",
    refresh=True,
)

# Update a document
result = await adapter.update(
    index="products",
    id="widget-001",
    document={"price": 17.99},
    refresh=True,
)

# Delete a document
result = await adapter.delete(
    index="products",
    id="widget-001",
    refresh=True,
)

# Bulk operations
operations = [
    {"index": {"_index": "products", "_id": "1"}},
    {"name": "Product 1", "price": 10.00},
    {"index": {"_index": "products", "_id": "2"}},
    {"name": "Product 2", "price": 20.00},
]
result = await adapter.bulk(operations=operations, refresh=True)
```

### Mapping Operations

```python
# Get index mapping
mapping = await adapter.get_mapping(index="products")

# Update mapping
await adapter.put_mapping(
    index="products",
    properties={"new_field": {"type": "keyword"}},
)
```

### Index Management

```python
# Check if index exists
exists = await adapter.exists(index="products")

# Create index with mappings and settings
await adapter.create_index(
    index="products",
    mappings={
        "properties": {
            "name": {"type": "text"},
            "price": {"type": "float"},
            "category": {"type": "keyword"},
        }
    },
    settings={
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
)

# Delete index
await adapter.delete_index(index="products")

# Refresh index
await adapter.refresh(index="products")
```

## Capability Detection

The adapter automatically detects client capabilities at runtime using **lazy initialization**:

```python
import logging

logger = logging.getLogger(__name__)

adapter = create_adapter(client)

# Capabilities are detected on first operation (lazy initialization)
info = await adapter.info()

# Now you can check capabilities (they've been detected)
logger.info(f"Version: {adapter.version}")
logger.info(f"Supports PIT: {adapter.supports_pit}")
logger.info(f"Supports search_after: {adapter.supports_search_after}")
logger.info(f"Supports async search: {adapter.supports_async_search}")

# Or get all capabilities explicitly
capabilities = await adapter.get_capabilities()
# {
#     "supports_pit": True,
#     "supports_search_after": True,
#     "supports_async_search": True,
#     "version": "8.11.0",
#     "is_async": False,
# }
```

### How Lazy Detection Works

1. **No detection in `__init__`** - Creating an adapter doesn't make any network calls
2. **First operation triggers detection** - When you call any async method (search, get, info, etc.)
3. **Cached for future use** - Capabilities are stored and reused
4. **Property defaults** - Capability properties return safe defaults before detection:
   - `supports_pit` → False (before detection)
   - `supports_search_after` → True (before detection)
   - `version` → None (before detection)

```python
# Before any operations - properties return defaults
adapter = create_adapter(client)
print(adapter.version)  # None (not yet detected)

# After first operation - properties return detected values
await adapter.search(index="test", query={"match_all": {}})
print(adapter.version)  # "8.11.0" (now detected)
```

## Architecture

### Adapter Pattern

The library uses an adapter pattern to provide a unified interface across different client versions:

```text
┌─────────────────────────────────────┐
│     Strawberry Elastic Types        │
│  (GraphQL types, resolvers, etc.)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      BaseElasticAdapter (ABC)       │
│   (Unified async interface)         │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐   ┌──────────┐
│   ES   │   │OpenSearch│
│Adapter │   │ Adapter  │
└───┬────┘   └────┬─────┘
    │             │
    ▼             ▼
┌────────┐   ┌──────────┐
│  ES    │   │OpenSearch│
│7.x/8.x │   │ 1.x/2.x  │
└────────┘   └──────────┘
```

### Version Agnostic Design

Instead of creating separate adapters for each version (elasticsearch_v7, elasticsearch_v8, etc.), the adapters:

1. **Detect capabilities at runtime** - Features are detected by querying the cluster
2. **Normalize API differences** - Handle API changes between versions transparently
3. **Handle sync/async** - Automatically wrap sync clients in async executors
4. **Provide feature flags** - Expose capability detection for optional features

This approach means:

- ✅ Works with any client version
- ✅ No version-specific code paths
- ✅ Easy to maintain
- ✅ Users control their client version

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/strawberry-elastic
cd strawberry-elastic

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to automatically run checks before committing code. The hooks include:

- **Ruff**: Linting and formatting Python code
- **Type checking**: Static type analysis with ty
- **Bandit**: Security vulnerability scanning
- **detect-secrets**: Prevent committing secrets
- **Markdown linting**: Formatting for documentation
- **General checks**: Trailing whitespace, file endings, YAML/JSON validation

```bash
# Run all hooks manually on all files
pre-commit run --all-files

# Run hooks on specific files
pre-commit run --files src/strawberry_elastic/file.py

# Update hooks to latest versions
pre-commit autoupdate

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/clients/test_factory.py

# Run with coverage
pytest --cov=strawberry_elastic --cov-report=html

# Run tests with verbose output
pytest -v

# Type checking
ty check

# Linting
ruff check src/ tests/

# Security scan
bandit -r src/
```

### Project Structure

```text
strawberry-elastic/
├── src/strawberry_elastic/
│   ├── __init__.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract adapter interface
│   │   ├── factory.py           # Auto-detection factory
│   │   └── adapters/
│   │       ├── elasticsearch.py # ES adapter (all versions)
│   │       └── opensearch.py    # OpenSearch adapter (all versions)
│   ├── exceptions.py            # Custom exceptions
│   ├── type.py                  # GraphQL type decorators (coming soon)
│   ├── fields.py                # Field definitions (coming soon)
│   ├── filters.py               # Query filters (coming soon)
│   ├── pagination.py            # Pagination strategies (coming soon)
│   └── queries.py               # Query builder (coming soon)
├── examples/                    # Usage examples
├── tests/                       # Test suite
└── pyproject.toml
```

## Roadmap

### Phase 1: Adapter System ✅ (Current)

- [x] Base adapter interface
- [x] Elasticsearch adapter (version-agnostic)
- [x] OpenSearch adapter (version-agnostic)
- [x] Auto-detection factory
- [x] Capability detection
- [x] Sync/async client support

### Phase 2: Type System (In Progress - Phase 2.1 Complete ✅)

#### Phase 2.1: Core Infrastructure ✅

- [x] Universal DSL compatibility layer (elasticsearch.dsl, elasticsearch_dsl, opensearchpy)
- [x] Type inspector for detecting field sources
- [x] Field mapper for ES/OpenSearch → Python type conversion
- [x] Custom GraphQL scalars (GeoPoint, GeoShape, IPAddress, etc.)
- [x] Support for 40+ Elasticsearch/OpenSearch field types
- [x] Graceful handling of optional dependencies
- [x] 100+ comprehensive tests with real cluster integration

#### Phase 2.2: Document Support (Next)

- [ ] `@elastic.type` decorator
- [ ] Automatic field generation from Document classes
- [ ] Field extraction from mappings
- [ ] InnerDoc/nested type handling
- [ ] Index metadata extraction

#### Phase 2.3: Mapping Introspection

- [ ] Runtime mapping fetch
- [ ] Lazy field generation
- [ ] Mapping cache

#### Phase 2.4: Type Hints Support

- [ ] Pure type hint processing
- [ ] Integration with Strawberry's native type handling

#### Phase 2.5: Custom Scalars (Expanded)

- [ ] Date/DateTime handling improvements
- [ ] Range type support

#### Phase 2.6: Advanced Features

- [ ] Hybrid mode (Document + custom fields)
- [ ] Field overrides
- [ ] Custom resolvers with `@elastic.field`
- [ ] Multi-field handling
- [ ] Meta fields (score, highlights, etc.)

### Phase 3: Filtering & Search

- [ ] Filter system (`@elastic.filter`)
- [ ] Query builder
- [ ] Full-text search
- [ ] Range queries
- [ ] Geo queries
- [ ] Bool queries

### Phase 4: Pagination

- [ ] Offset pagination
- [ ] search_after pagination
- [ ] Point in Time (PIT)
- [ ] Relay connections
- [ ] Cursor encoding

### Phase 5: Mutations

- [ ] CRUD operations
- [ ] Bulk operations
- [ ] Optimistic concurrency
- [ ] Error handling

### Phase 6: Advanced Features

- [ ] Aggregations
- [ ] Suggestions/autocomplete
- [ ] Highlighting
- [ ] Nested queries
- [ ] Parent-child relationships
- [ ] Permissions/security

## Continuous Integration

This project uses GitHub Actions for CI/CD:

### Main CI Workflow

- ✅ **Lint & Format Check**: Ruff linter and formatter
- ✅ **Type Checking**: ty static type analysis
- ✅ **Unit Tests**: Python 3.11 and 3.12
- ✅ **Integration Tests**: Real Elasticsearch and OpenSearch clusters
- ✅ **Adapter Tests**: Multiple Elasticsearch versions (7.x, 8.x)

### Security Workflow

- 🔒 **Security Scan**: Bandit for security issues
- 🔒 **Dependency Audit**: pip-audit for vulnerable dependencies
- 🔒 **CodeQL Analysis**: Advanced code scanning
- 🔒 **License Check**: Verify dependency licenses
- 🔒 **Dependency Review**: Check for outdated packages

All PRs must pass CI checks before merging.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Development Setup

### Running Tests

```bash
# Unit tests (no dependencies)
pytest tests/

# Integration tests with real clusters (Elasticsearch)
./scripts/test-integration.sh all

# Integration tests with OpenSearch backend
BACKEND=opensearch ./scripts/test-integration.sh all
```

### Docker Test Environment

The project includes Docker Compose setup for integration testing:

```bash
# Start test clusters
docker compose up -d

# Services available:
# - Elasticsearch 8.x:  http://localhost:9200
# - Elasticsearch 7.x:  http://localhost:9201
# - OpenSearch 2.x:     http://localhost:9202

# Install DSL packages for testing
uv pip install elasticsearch-dsl opensearch-py httpx

# Run all tests (Elasticsearch backend)
pytest tests/types/ -v

# Run all tests (OpenSearch backend)
STRAWBERRY_ELASTIC_DSL=opensearch pytest tests/types/ -v

# Stop clusters
docker compose down -v
```

### Testing Different Backends

The universal DSL compatibility layer can be tested with different backends:

```bash
# Test with Elasticsearch DSL (default)
uv run pytest tests/types/ -v

# Test with OpenSearch DSL
STRAWBERRY_ELASTIC_DSL=opensearch uv run pytest tests/types/ -v

# Or use the test script
BACKEND=opensearch ./scripts/test-integration.sh all
```

See [scripts/README.md](scripts/README.md) for detailed testing documentation.

### Test Results

**Phase 2.1 Status**:

- ✅ **200/206 tests passing** (100/103 per backend)
- ✅ Full integration with **both** backends:
  - Elasticsearch DSL (elasticsearch-dsl 8.18.0+)
  - OpenSearch DSL (opensearchpy Document classes)
- ✅ 3 tests skipped per backend (backend-specific tests)
- ✅ Works without DSL (graceful degradation)
- ✅ Environment variable control: `STRAWBERRY_ELASTIC_DSL=opensearch`
- ✅ CI/CD: GitHub Actions with full test matrix
- ✅ Multiple Python versions tested (3.11, 3.12)
- ✅ Security scanning and dependency audits

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Inspired by:

- [strawberry-graphql-django](https://github.com/strawberry-graphql/strawberry-graphql-django)
- [strawberry-sqlalchemy](https://github.com/strawberry-graphql/strawberry-sqlalchemy)

---

**Note**: This library is under active development. The adapter system is complete and ready to use, but
higher-level GraphQL features are still being implemented. Check the roadmap for progress.
