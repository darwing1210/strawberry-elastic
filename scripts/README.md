# Test Scripts

Helper scripts for development and testing.

## Integration Testing

### Quick Start

```bash
# Run complete integration test suite
./scripts/test-integration.sh all

# Start services and keep them running
KEEP_RUNNING=true ./scripts/test-integration.sh all
```

### Available Commands

#### `up` - Start Docker Containers

Starts Elasticsearch and OpenSearch containers for testing:

```bash
./scripts/test-integration.sh up
```

Services started:

- **Elasticsearch 8.x** on `http://localhost:9200`
- **Elasticsearch 7.x** on `http://localhost:9201`
- **OpenSearch 2.x** on `http://localhost:9202`

#### `down` - Stop Containers

Stops all containers and removes volumes:

```bash
./scripts/test-integration.sh down
```

#### `logs` - View Container Logs

Follow logs from all containers:

```bash
./scripts/test-integration.sh logs
```

#### `install-dsl` - Install DSL Packages

Installs Document support packages for testing:

```bash
./scripts/test-integration.sh install-dsl
```

Installs:

- `elasticsearch-dsl` (Elasticsearch Document support)
- `opensearch-py` (OpenSearch Document support)
- `httpx` (for health checks)

#### `test` - Run Integration Tests

Runs only tests that require DSL support:

```bash
./scripts/test-integration.sh test
```

#### `test-all` - Run All Tests

Runs both unit and integration tests:

```bash
./scripts/test-integration.sh test-all
```

#### `all` - Complete Test Run

Runs the full test cycle:

1. Starts Docker containers
2. Installs DSL packages
3. Runs complete test suite with coverage
4. Cleans up (unless `KEEP_RUNNING=true`)

```bash
./scripts/test-integration.sh all
```

### Environment Variables

#### `KEEP_RUNNING`

Keep containers running after tests complete:

```bash
KEEP_RUNNING=true ./scripts/test-integration.sh all
```

Useful for:

- Debugging test failures
- Running multiple test iterations
- Manual testing with live clusters

#### `BACKEND`

Choose which DSL backend to test with:

```bash
# Test with Elasticsearch DSL (default)
./scripts/test-integration.sh all

# Test with OpenSearch DSL
BACKEND=opensearch ./scripts/test-integration.sh all

# Combine with KEEP_RUNNING
BACKEND=opensearch KEEP_RUNNING=true ./scripts/test-integration.sh test
```

Valid values:

- `elasticsearch` (default) - Uses `elasticsearch.dsl` or `elasticsearch_dsl`
- `opensearch` - Uses `opensearchpy.helpers.document`

This tests that the universal DSL compatibility layer works correctly with both backends.

### Docker Compose Services

The `docker-compose.yml` defines three services:

#### Elasticsearch 8.x (`elasticsearch`)

- Port: `9200`
- Image: `docker.elastic.co/elasticsearch/elasticsearch:8.11.0`
- Security: Disabled for testing
- Memory: 512MB heap

#### Elasticsearch 7.x (`elasticsearch-7`)

- Port: `9201`
- Image: `docker.elastic.co/elasticsearch/elasticsearch:7.17.15`
- Security: Disabled for testing
- Memory: 512MB heap
- Purpose: Testing legacy version support

#### OpenSearch 2.x (`opensearch`)

- Port: `9202`
- Image: `opensearchproject/opensearch:2.11.0`
- Security: Disabled for testing
- Memory: 512MB heap

### Running Tests Manually

If you prefer to manage services yourself:

```bash
# 1. Start services
docker-compose up -d

# 2. Wait for health checks to pass (or check status)
docker-compose ps

# 3. Install DSL packages
uv pip install elasticsearch-dsl opensearch-py httpx

# 4. Run tests (default: Elasticsearch)
uv run pytest tests/types/ -v

# 5. Run tests with OpenSearch backend
STRAWBERRY_ELASTIC_DSL=opensearch uv run pytest tests/types/ -v

# 6. With specific markers
uv run pytest tests/types/ -m "requires_dsl" -v

# 7. With coverage
uv run pytest tests/types/ -v --cov=strawberry_elastic/types --cov-report=term-missing

# 8. Stop services
docker-compose down -v
```

### Test Markers

Tests use pytest markers to categorize functionality:

- `@pytest.mark.integration` - Requires real cluster
- `@pytest.mark.elasticsearch` - Elasticsearch-specific
- `@pytest.mark.opensearch` - OpenSearch-specific
- `@pytest.mark.requires_dsl` - Requires Document support
- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.slow` - Long-running tests

Run specific categories:

```bash
# Only integration tests
uv run pytest -m integration

# Only Elasticsearch tests
uv run pytest -m elasticsearch

# Only tests that require DSL
uv run pytest -m requires_dsl

# Exclude slow tests
uv run pytest -m "not slow"

# Test with specific backend
STRAWBERRY_ELASTIC_DSL=opensearch uv run pytest -m requires_dsl
```

### Troubleshooting

#### Containers won't start

Check Docker is running:

```bash
docker info
```

Check ports aren't in use:

```bash
lsof -i :9200
lsof -i :9201
lsof -i :9202
```

#### Tests timeout

Increase health check timeout in `docker-compose.yml` or wait longer for services to start:

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs elasticsearch
docker-compose logs opensearch
```

#### Out of memory

Increase Docker memory allocation or reduce heap sizes in `docker-compose.yml`:

```yaml
environment:
  - "ES_JAVA_OPTS=-Xms256m -Xmx256m"  # Reduce from 512m
```

#### Tests are skipped

If tests show as "skipped", check:

1. **Containers running?**

   ```bash
   docker-compose ps
   ```

2. **DSL installed?**

   ```bash
   uv pip list | grep -E "(elasticsearch-dsl|opensearch-py)"
   ```

3. **Services reachable?**

   ```bash
   curl http://localhost:9200
   curl http://localhost:9202
   ```

### CI/CD Integration

For GitHub Actions or other CI:

```yaml
- name: Start test services
  run: docker-compose up -d

- name: Wait for services
  run: |
    timeout 60 bash -c 'until curl -f http://localhost:9200/_cluster/health; do sleep 2; done'
    timeout 60 bash -c 'until curl -f http://localhost:9202/_cluster/health; do sleep 2; done'

- name: Install DSL packages
  run: uv pip install elasticsearch-dsl opensearch-py httpx

- name: Run tests
  run: uv run pytest tests/types/ -v --cov=strawberry_elastic/types

- name: Cleanup
  if: always()
  run: docker-compose down -v
```

## Development Workflow

### Typical workflow for DSL feature development

```bash
# 1. Start services in background
./scripts/test-integration.sh up

# 2. Install DSL packages (one time)
./scripts/test-integration.sh install-dsl

# 3. Develop and test iteratively
uv run pytest tests/types/test_dsl_compat.py -v
# ... make changes ...
uv run pytest tests/types/test_dsl_compat.py -v

# 4. Run full test suite when ready
uv run pytest tests/types/ -v

# 5. Stop services when done
./scripts/test-integration.sh down
```

### Testing Both Backends

```bash
# Test with Elasticsearch DSL
./scripts/test-integration.sh all

# Test with OpenSearch DSL
BACKEND=opensearch ./scripts/test-integration.sh all

# Or keep services running and switch backends
KEEP_RUNNING=true ./scripts/test-integration.sh up

# Test Elasticsearch
uv run pytest tests/types/ -v

# Test OpenSearch
STRAWBERRY_ELASTIC_DSL=opensearch uv run pytest tests/types/ -v

# Clean up
./scripts/test-integration.sh down
```

### Quick iteration loop

```bash
# Keep services running, just re-run tests
KEEP_RUNNING=true ./scripts/test-integration.sh all

# Services stay up after tests
# Run individual test files as needed
uv run pytest tests/types/test_inspector.py -v

# Test with OpenSearch backend
BACKEND=opensearch KEEP_RUNNING=true ./scripts/test-integration.sh all

# Clean up when done
./scripts/test-integration.sh down
```

## Test Results Summary

### Elasticsearch Backend

- **100/103 tests passing**
- 3 tests skipped (OpenSearch-specific)
- Backend: `elasticsearch.dsl` (ES 8.18+)
- Full Document class support

### OpenSearch Backend

- **100/103 tests passing**
- 3 tests skipped (Elasticsearch-specific)
- Backend: `opensearchpy`
- Full Document class support

**Both backends fully supported!** ✅
