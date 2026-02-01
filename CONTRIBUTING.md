# Contributing to Strawberry Elastic

Thank you for your interest in contributing to Strawberry Elastic! This document provides guidelines and
instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/strawberry-elastic.git`
3. Add upstream remote: `git remote add upstream https://github.com/ORIGINAL_OWNER/strawberry-elastic.git`

## Development Setup

### Prerequisites

- Python 3.11 or 3.12
- [uv](https://github.com/astral-sh/uv) package manager
- Docker (for integration tests)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/strawberry-elastic.git
cd strawberry-elastic

# Install dependencies
uv venv
uv pip install -e ".[dev]"

# Install DSL packages (optional, for Document support)
uv pip install elasticsearch-dsl opensearch-py httpx
```

### Project Structure

```text
strawberry-elastic/
├── src/strawberry_elastic/    # Source code
│   ├── clients/                # Adapter implementations
│   ├── types/                  # Type system (Phase 2)
│   └── exceptions.py           # Custom exceptions
├── tests/                      # Test suite
│   ├── clients/                # Adapter tests
│   ├── types/                  # Type system tests
│   └── conftest.py             # Test fixtures
├── scripts/                    # Helper scripts
├── .github/workflows/          # CI/CD workflows
└── docs/                       # Documentation
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

Example: `feature/add-aggregation-support`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:

```text
feat: add @elastic.type decorator for Document classes
fix: handle elasticsearch-dsl 8.18 private attributes
docs: update README with installation instructions
test: add integration tests for OpenSearch backend
```

### Code Style

We use **Ruff** for linting and formatting:

```bash
# Check linting
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/

# Fix auto-fixable issues
uv run ruff check --fix src/ tests/
```

**Style Guidelines:**

- Follow PEP 8
- Use type hints for all functions and methods
- Maximum line length: 100 characters
- Use docstrings for all public APIs (Google style)
- Import order: standard library, third-party, local

### Pre-commit Hooks

We use pre-commit hooks to automatically check code quality before commits:

```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Run all hooks manually
uv run pre-commit run --all-files

# Run hooks on staged files only
uv run pre-commit run

# Update hooks to latest versions
uv run pre-commit autoupdate
```

**Hooks included:**

- **Ruff**: Linting and formatting
- **ty**: Type checking
- **Bandit**: Security scanning
- **detect-secrets**: Prevent committing secrets
- **Markdown linting**: Documentation formatting
- **YAML/JSON validation**: Config file checks

**Important:** All hooks must pass before your code can be committed. If you need to bypass hooks temporarily
(not recommended), use:

```bash
git commit --no-verify
```

## Testing

### Running Tests

```bash
# Unit tests only (fast, no external dependencies)
uv run pytest tests/clients/ -v

# Type system tests (requires DSL)
uv run pytest tests/types/ -v

# Integration tests with Docker
./scripts/test-integration.sh all

# Test specific backend
BACKEND=opensearch ./scripts/test-integration.sh all

# Run with coverage
uv run pytest tests/ --cov=strawberry_elastic --cov-report=term-missing
```

### Writing Tests

- Place tests in `tests/` directory matching source structure
- Use descriptive test names: `test_<what>_<condition>_<expected>`
- Use pytest fixtures for common setup
- Mark tests appropriately:
  - `@pytest.mark.unit` - Unit tests
  - `@pytest.mark.integration` - Integration tests
  - `@pytest.mark.requires_dsl` - Requires Document support
  - `@pytest.mark.elasticsearch` - ES-specific
  - `@pytest.mark.opensearch` - OS-specific

Example test:

```python
import pytest
from strawberry_elastic import create_adapter

@pytest.mark.unit
def test_create_adapter_with_elasticsearch_client():
    """Test that create_adapter detects Elasticsearch client."""
    from elasticsearch import Elasticsearch

    client = Elasticsearch(["http://localhost:9200"])
    adapter = create_adapter(client)

    assert adapter is not None
    assert adapter.__class__.__name__ == "ElasticsearchAdapter"
```

### Test Coverage

- Aim for >90% code coverage
- All new features must include tests
- Bug fixes must include regression tests
- Integration tests for user-facing features

## Code Quality

### Type Checking

We use **ty** for static type analysis:

```bash
# Run ty
uv run ty check

# Check with verbose output
uv run ty check --verbose
```

**Type Checking Requirements:**

- All functions/methods must have type hints
- Use `typing` module for complex types
- Avoid `Any` when possible
- Use `TYPE_CHECKING` for circular imports

### Documentation

- Add docstrings to all public APIs
- Use Google-style docstrings
- Include examples in docstrings when helpful
- Update README.md for user-facing changes
- Add to CHANGELOG.md for releases

Example docstring:

```python
def map_field(
    self,
    field_name: str,
    field_def: dict[str, Any],
    required: bool = False,
) -> Type:
    """
    Map an Elasticsearch field definition to a Python type.

    Args:
        field_name: Name of the field
        field_def: Field definition dictionary from mapping
        required: Whether the field is required

    Returns:
        Python type suitable for use with Strawberry GraphQL

    Example:
        >>> mapper = FieldMapper()
        >>> field_type = mapper.map_field("title", {"type": "text"})
        >>> print(field_type)  # str | None
    """
```

### Pre-Commit Checklist

Before committing:

- [ ] Code is formatted: `uv run ruff format src/ tests/`
- [ ] No linting errors: `uv run ruff check src/ tests/`
- [ ] Type checking passes: `uv run ty check`
- [ ] Tests pass: `uv run pytest tests/`
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (if user-facing change)

## Pull Request Process

### Before Submitting

1. **Update from main:**

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run full test suite:**

   ```bash
   ./scripts/test-integration.sh all
   ```

3. **Ensure CI will pass:**
   - All tests pass locally
   - Code is linted and formatted
   - Type checking passes
   - Coverage is maintained/improved

### Submitting a PR

1. Push to your fork: `git push origin feature/your-feature`
2. Open a Pull Request on GitHub
3. Fill out the PR template completely
4. Link any related issues

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Dependent changes merged

## Related Issues
Closes #123
```

### CI Requirements

All PRs must pass:

- ✅ Ruff linting and formatting
- ✅ ty type checking
- ✅ Unit tests (Python 3.11 and 3.12)
- ✅ Integration tests (Elasticsearch)
- ✅ Integration tests (OpenSearch)
- ✅ Adapter tests (multiple ES versions)
- ✅ Security scans
- ✅ Dependency audits

### Review Process

1. At least one maintainer must approve
2. All CI checks must pass
3. All review comments must be addressed
4. Branch must be up to date with main

### After Approval

- Maintainers will merge using "Squash and merge"
- Delete your branch after merge
- Update your fork: `git pull upstream main`

## Release Process

Releases are managed by maintainers.

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- `MAJOR` - Breaking changes
- `MINOR` - New features (backwards compatible)
- `PATCH` - Bug fixes (backwards compatible)

### Release Steps

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Create release commit: `git commit -m "chore: release v1.2.3"`
4. Tag release: `git tag v1.2.3`
5. Push: `git push origin main --tags`
6. GitHub Actions will build and publish to PyPI

## Development Workflow Examples

### Adding a New Feature

```bash
# 1. Create branch
git checkout -b feature/add-aggregations

# 2. Make changes
# ... edit files ...

# 3. Test
uv run pytest tests/ -v
./scripts/test-integration.sh all

# 4. Format and lint
uv run ruff format src/ tests/
uv run ruff check src/ tests/

# 5. Type check
uv run ty check

# 6. Commit
git add .
git commit -m "feat: add aggregation support for GraphQL queries"

# 7. Push and create PR
git push origin feature/add-aggregations
```

### Fixing a Bug

```bash
# 1. Create branch
git checkout -b fix/field-mapper-optional-bug

# 2. Write failing test
# ... add test that reproduces bug ...

# 3. Verify test fails
uv run pytest tests/types/test_field_mapper.py::test_optional_fields -v

# 4. Fix bug
# ... edit source code ...

# 5. Verify test passes
uv run pytest tests/types/test_field_mapper.py::test_optional_fields -v

# 6. Run full test suite
uv run pytest tests/ -v

# 7. Commit and push
git add .
git commit -m "fix: correctly handle optional fields in field mapper"
git push origin fix/field-mapper-optional-bug
```

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email maintainers directly (see SECURITY.md)
- **Chat**: Join our Discord/Slack (if available)

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in documentation

Thank you for contributing to Strawberry Elastic! 🚀
