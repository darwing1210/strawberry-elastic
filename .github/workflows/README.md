# GitHub Actions Workflows

This directory contains CI/CD workflows for Strawberry Elastic.

## Workflows

### 1. CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Jobs:**

#### Lint & Format Check
- Runs Ruff linter and formatter
- Checks code style compliance
- Fast feedback (~30s)

#### Type Check
- Runs ty static type analysis
- Ensures type safety across the codebase
- Catches type errors before runtime

#### Unit Tests
- Tests Python 3.11 and 3.12
- No external dependencies required
- Tests adapter layer functionality
- Uploads coverage to Codecov

#### Integration Tests (Elasticsearch)
- Runs with real Elasticsearch 8.x cluster
- Tests Document support with elasticsearch-dsl
- Tests type system with ES backend
- Full integration validation

#### Integration Tests (OpenSearch)
- Runs with real OpenSearch 2.x cluster
- Tests Document support with opensearchpy
- Tests type system with OS backend
- Validates universal DSL compatibility

#### Adapter Tests
- Tests against multiple ES versions (7.x, 8.x)
- Validates version-agnostic adapter design
- Ensures backwards compatibility

#### Test Summary
- Aggregates all test results
- Creates summary report
- Fails if any job fails

**Total Runtime:** ~8-12 minutes

---

### 2. Security Workflow (`security.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Weekly schedule (Monday 00:00 UTC)
- Manual workflow dispatch

**Jobs:**

#### Security Scan (Bandit)
- Scans for common security issues
- Checks for hardcoded secrets
- Validates secure coding patterns

#### Dependency Audit
- Runs pip-audit to find vulnerable dependencies
- Checks against CVE databases
- Reports known security issues

#### CodeQL Analysis
- Advanced semantic code analysis
- Detects security vulnerabilities
- Finds code quality issues

#### License Check
- Verifies dependency licenses
- Ensures compliance with MIT license
- Flags incompatible licenses

#### Dependency Review
- Checks for outdated dependencies
- Reviews new dependencies in PRs
- Suggests updates

**Total Runtime:** ~5-8 minutes

---

## Environment Variables

### CI Workflow

| Variable | Description | Default |
|----------|-------------|---------|
| `PYTHON_VERSION` | Python version for tests | `3.12` |
| `UV_VERSION` | uv package manager version | `0.5.11` |
| `ES_HOST` | Elasticsearch host | `localhost` |
| `ES_PORT` | Elasticsearch port | `9200` |
| `STRAWBERRY_ELASTIC_DSL` | Force DSL backend | (auto-detect) |

### Using in Tests

```bash
# Force OpenSearch backend
STRAWBERRY_ELASTIC_DSL=opensearch pytest tests/types/ -v

# Use specific ES host
ES_HOST=es.example.com ES_PORT=9200 pytest tests/
```

---

## GitHub Services

Both workflows use GitHub Actions services to run test clusters:

### Elasticsearch Service

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    env:
      discovery.type: single-node
      xpack.security.enabled: false
    ports:
      - 9200:9200
    options: >-
      --health-cmd "curl -f http://localhost:9200/_cluster/health"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 10
```

### OpenSearch Service

```yaml
services:
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    env:
      discovery.type: single-node
      DISABLE_SECURITY_PLUGIN: true
    ports:
      - 9200:9200
    options: >-
      --health-cmd "curl -f http://localhost:9200/_cluster/health"
```

---

## Required Secrets

Configure in repository settings → Secrets and variables → Actions:

| Secret | Description | Required For |
|--------|-------------|--------------|
| `CODECOV_TOKEN` | Codecov upload token | Coverage reports |
| `PYPI_TOKEN` | PyPI publishing token | Release workflow (future) |

---

## Branch Protection Rules

Recommended settings for `main` branch:

- ✅ Require pull request reviews (1 approval)
- ✅ Require status checks to pass:
  - `lint`
  - `type-check`
  - `unit-tests`
  - `integration-tests-elasticsearch`
  - `integration-tests-opensearch`
  - `adapter-tests`
- ✅ Require branches to be up to date
- ✅ Require linear history
- ✅ Include administrators

---

## Workflow Badges

Add to README.md:

```markdown
[![CI](https://github.com/YOUR_USERNAME/strawberry-elastic/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/strawberry-elastic/actions/workflows/ci.yml)
[![Security](https://github.com/YOUR_USERNAME/strawberry-elastic/actions/workflows/security.yml/badge.svg)](https://github.com/YOUR_USERNAME/strawberry-elastic/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/strawberry-elastic/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/strawberry-elastic)
```

---

## Troubleshooting

### Service Container Timeouts

If services fail to start:

1. Check health check configuration
2. Increase `health-retries` or `health-start-period`
3. Verify image availability
4. Check memory limits

### Flaky Tests

If tests randomly fail:

1. Increase wait timeouts for services
2. Add retry logic for network operations
3. Use `pytest-rerunfailures` plugin
4. Check for race conditions

### Coverage Upload Failures

If Codecov upload fails:

1. Verify `CODECOV_TOKEN` is set
2. Check token has repository access
3. Ensure coverage.xml is generated
4. Try uploading manually for debugging

### Security Scan False Positives

To suppress false positives in Bandit:

```python
# nosec B101 - False positive, using assert in tests
assert some_condition
```

Or configure in `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests/"]
skips = ["B101"]  # Skip assert_used
```

---

## Local CI Testing

Test workflows locally before pushing:

### Using act

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflow
act push

# Run specific job
act -j lint

# Run with secrets
act --secret-file .secrets
```

### Manual Testing

```bash
# Run all checks locally
./scripts/test-integration.sh all

# Check formatting
uv run ruff format --check src/ tests/

# Run linter
uv run ruff check src/ tests/

# Type check
uv run ty check

# Run tests
uv run pytest tests/ -v
```

---

## Performance Optimization

### Caching

Workflows use caching for:
- uv cache directory
- pip cache
- ty cache

### Parallelization

Jobs run in parallel:
- Lint and type-check run independently
- Unit tests run across Python versions
- Integration tests run for each backend
- Adapter tests run for each ES version

**Total Parallelism:** Up to 8 jobs running concurrently

---

## Future Improvements

- [ ] Add performance benchmarking workflow
- [ ] Add documentation build workflow
- [ ] Add release automation workflow
- [ ] Add docker image publishing
- [ ] Add E2E tests workflow
- [ ] Add mutation testing
- [ ] Add dependency update automation (Dependabot/Renovate)

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Services](https://docs.github.com/en/actions/using-containerized-services)
- [Codecov GitHub Action](https://github.com/codecov/codecov-action)
- [CodeQL Documentation](https://codeql.github.com/docs/)