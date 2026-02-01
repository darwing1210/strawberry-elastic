# Development Guide

## Setup

### Prerequisites

- Python 3.12+
- uv (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/strawberry-elastic
cd strawberry-elastic

# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"

# Or with pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Installing with a Client

Choose one client to install for testing:

```bash
# Elasticsearch (supports 7.x and 8.x)
uv pip install elasticsearch>=7.0

# OpenSearch (supports 1.x and 2.x)
uv pip install opensearch-py>=1.0
```

## Code Quality

### Type Checking with ty

The project uses `ty` for type checking. All code is fully type-annotated.

```bash
# Run type checking (using venv)
source .venv/bin/activate
ty check src/

# Expected output:
# All checks passed!
```

**Status**: ✅ All type checks passing (0 errors)

### Linting with ruff

```bash
# Check for linting issues
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Check specific rules
ruff check --select E,F,I src/
```

**Status**: ✅ All checks passing

### Code Formatting with black

```bash
# Format code
black src/

# Check formatting without changes
black --check src/
```

**Configuration**: Line length 100, Python 3.12+

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=strawberry_elastic

# Run specific test file
pytest tests/test_adapters.py

# Run with verbose output
pytest -v
```

### Test Markers

```python
@pytest.mark.unit  # Unit tests (no external dependencies)
@pytest.mark.integration  # Requires running ES/OpenSearch
@pytest.mark.elasticsearch  # ES-specific tests
@pytest.mark.opensearch  # OpenSearch-specific tests
```

Run specific markers:

```bash
pytest -m unit  # Only unit tests
pytest -m integration  # Only integration tests
```

## Project Structure

```text
strawberry-elastic/
├── src/strawberry_elastic/
│   ├── __init__.py              (43 lines)
│   ├── clients/
│   │   ├── __init__.py          (10 lines)
│   │   ├── base.py              (414 lines) - Abstract adapter
│   │   ├── factory.py           (101 lines) - Auto-detection
│   │   └── adapters/
│   │       ├── __init__.py      (9 lines)
│   │       ├── elasticsearch.py (404 lines) - ES adapter
│   │       └── opensearch.py    (389 lines) - OpenSearch adapter
│   └── exceptions.py            (96 lines)
├── examples/
│   └── basic_adapter_usage.py   (418 lines) - Usage examples
├── tests/                        (Coming soon)
└── Total: 1,422 lines of Python code
```

## Code Quality Standards

### Type Annotations

- ✅ All functions must have type annotations
- ✅ Use modern type syntax (`dict` instead of `Dict`, `str | None` instead of `Optional[str]`)
- ✅ Use `Any` sparingly and document why
- ✅ Generic types properly annotated

Example:

```python
async def search(
    self,
    index: str | Sequence[str],
    query: dict[str, Any],
    source: bool | list[str] | None = None,
) -> dict[str, Any]:
    """Execute a search query."""
    ...
```

### Async-First

- ✅ All public methods are async
- ✅ Sync clients wrapped with `asyncio.run_in_executor`
- ✅ No blocking I/O in async context

### Documentation

- ✅ All public classes/functions have docstrings
- ✅ Complex logic explained with inline comments
- ✅ Examples in docstrings where helpful

### Error Handling

- ✅ Custom exceptions for specific errors
- ✅ Meaningful error messages
- ✅ Proper exception chaining

## Architecture Principles

### 1. Adapter Pattern

- Abstract base class defines the interface
- Concrete adapters implement for specific clients
- Factory auto-detects and creates appropriate adapter

### 2. Version Agnostic

- Runtime capability detection instead of version checks
- Feature flags for optional functionality
- Graceful degradation for missing features

### 3. Client Flexibility

- No client dependencies in base package
- Users install their preferred client version
- Support both sync and async clients

### 4. Type Safety

- Full type coverage with `ty`
- Strict type checking enabled
- Runtime type validation where needed

## Common Tasks

### Adding a New Method to Adapters

1. Add abstract method to `BaseElasticAdapter`
2. Implement in `ElasticsearchAdapter`
3. Implement in `OpenSearchAdapter`
4. Add type annotations (all methods must be async)
5. Write docstring
6. If method needs capabilities, call `await self._ensure_capabilities()` first
7. Run type checks: `ty check src/`
8. Run lints: `ruff check src/`
9. Add tests

### Adding a New Exception

1. Add to `exceptions.py`
2. Inherit from appropriate base exception
3. Add to `__init__.py` exports
4. Document when it's raised

### Running Examples

```bash
# Run basic adapter examples
python examples/basic_adapter_usage.py

# Note: Requires running ES/OpenSearch instance
```

## Continuous Integration

### Checks Run on CI

1. Type checking (`ty check`)
2. Linting (`ruff check`)
3. Formatting (`black --check`)
4. Tests (`pytest`)
5. Coverage report

### Pre-commit Checklist

Before committing:

```bash
# Format code
black src/

# Fix linting issues
ruff check --fix src/

# Type check
ty check src/

# Run tests
pytest

# Verify all checks pass
ty check src/ && ruff check src/ && black --check src/
```

## Lazy Capability Detection

The adapters use **lazy initialization** for capability detection:

- `__init__` does NOT call async methods (can't await in constructor)
- Capabilities are detected on first operation via `_ensure_capabilities()`
- All adapter operations call `await self._ensure_capabilities()` before execution
- Properties return safe defaults before detection completes

**Why lazy?**

- Can't call async methods from `__init__` (sync method)
- Avoids unnecessary network calls if adapter is created but never used
- Allows adapter creation to be instant and never fail

**Implementation pattern:**

```python
async def _execute(self, method_name: str, *args, **kwargs):
    # Ensure capabilities are detected before first operation
    await self._ensure_capabilities()

    method = getattr(self.client, method_name)
    # ... rest of execution
```

## Troubleshooting

### Type Checking Errors

If `ty` reports errors:

1. Check type annotations match actual types
2. Ensure modern type syntax (`dict` not `Dict`, `str | None` not `Optional[str]`)
3. Look for `Any` type leakage
4. Verify generic types are properly specified
5. Check for async/await consistency

### Async/Await Issues

Common mistakes:

- **Can't call async from sync**: Never call async methods from `__init__` or sync functions
- **Missing await**: All adapter methods are async and must be awaited
- **Sync client support**: Sync clients are wrapped with `run_in_executor` automatically

### Import Errors

Common issues:

- **Relative imports**: Adapters use relative imports (intentional for lazy loading)
- **Circular imports**: Use `TYPE_CHECKING` guard for type-only imports
- **Missing client**: Install `elasticsearch` or `opensearch-py`

### Linting Warnings

Suppressed rules (with justification):

- `PLR2004`: Magic value comparisons (version numbers in capability detection)
- `TID252`: Relative imports from parent (adapter pattern requires this)
- `PLC0415`: Import inside function (lazy loading for optional adapters)
- `RUF022`: `__all__` sorting (we group by category with comments)

## Release Process

1. Update version in `pyproject.toml`
2. Update `__version__` in `__init__.py`
3. Update `CHANGELOG.md`
4. Run all checks
5. Build: `python -m build`
6. Test install: `pip install dist/strawberry_elastic-*.whl`
7. Tag release: `git tag v0.1.0`
8. Push: `git push --tags`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.
