"""
Pytest configuration and fixtures for Strawberry Elastic tests.

Provides fixtures for:
- Elasticsearch clients (8.x and 7.x)
- OpenSearch clients
- Test adapters
- Test data setup/teardown
"""

import os

import pytest


# Environment variables for test cluster connections
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES7_PORT = int(os.getenv("ES7_PORT", "9201"))
OS_PORT = int(os.getenv("OS_PORT", "9202"))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test requiring real cluster",
    )
    config.addinivalue_line("markers", "elasticsearch: mark test as Elasticsearch-specific")
    config.addinivalue_line("markers", "opensearch: mark test as OpenSearch-specific")
    config.addinivalue_line("markers", "requires_dsl: mark test as requiring Document support")


# Check if clusters are available
def is_elasticsearch_available() -> bool:
    """Check if Elasticsearch is available."""
    try:
        import httpx  # type: ignore[import-untyped]

        response = httpx.get(f"http://{ES_HOST}:{ES_PORT}", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def is_elasticsearch_7_available() -> bool:
    """Check if Elasticsearch 7.x is available."""
    try:
        import httpx  # type: ignore[import-untyped]

        response = httpx.get(f"http://{ES_HOST}:{ES7_PORT}", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def is_opensearch_available() -> bool:
    """Check if OpenSearch is available."""
    try:
        import httpx  # type: ignore[import-untyped]

        response = httpx.get(f"http://{ES_HOST}:{OS_PORT}", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def is_dsl_available() -> bool:
    """Check if any DSL backend is available."""
    from strawberry_elastic.types._dsl_compat import has_dsl

    return has_dsl()


# Skip conditions
skip_if_no_elasticsearch = pytest.mark.skipif(
    not is_elasticsearch_available(),
    reason="Elasticsearch not available (run: docker-compose up elasticsearch)",
)

skip_if_no_elasticsearch_7 = pytest.mark.skipif(
    not is_elasticsearch_7_available(),
    reason="Elasticsearch 7.x not available (run: docker-compose up elasticsearch-7)",
)

skip_if_no_opensearch = pytest.mark.skipif(
    not is_opensearch_available(),
    reason="OpenSearch not available (run: docker-compose up opensearch)",
)

skip_if_no_dsl = pytest.mark.skipif(not is_dsl_available(), reason="DSL not available")


# Elasticsearch fixtures
@pytest.fixture(scope="session")
def elasticsearch_client():
    """
    Provide Elasticsearch 8.x client for testing.

    Requires Elasticsearch to be running on localhost:9200
    (use docker-compose up elasticsearch)
    """
    if not is_elasticsearch_available():
        pytest.skip("Elasticsearch not available")

    try:
        from elasticsearch import Elasticsearch  # type: ignore[import-untyped]

        # Configure client with compatibility mode for elasticsearch-py v9+
        client = Elasticsearch(
            [f"http://{ES_HOST}:{ES_PORT}"],
            # Set compatibility header for v8 (works with ES 7.x and 8.x)
            headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"},
        )
        # Verify connection
        info = client.info()
        print(f"\nConnected to Elasticsearch {info['version']['number']}")
        yield client
        client.close()
    except ImportError:
        pytest.skip("elasticsearch package not installed")


@pytest.fixture(scope="session")
def elasticsearch_7_client():
    """
    Provide Elasticsearch 7.x client for testing legacy support.

    Requires Elasticsearch 7.x to be running on localhost:9201
    (use docker-compose up elasticsearch-7)
    """
    if not is_elasticsearch_7_available():
        pytest.skip("Elasticsearch 7.x not available")

    try:
        from elasticsearch import Elasticsearch  # type: ignore[import-untyped]

        # Configure client with compatibility mode for elasticsearch-py v9+
        client = Elasticsearch(
            [f"http://{ES_HOST}:{ES7_PORT}"],
            # Set compatibility header for v7
            headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=7"},
        )
        # Verify connection
        info = client.info()
        print(f"\nConnected to Elasticsearch {info['version']['number']}")
        yield client
        client.close()
    except ImportError:
        pytest.skip("elasticsearch package not installed")


@pytest.fixture(scope="session")
async def async_elasticsearch_client():
    """
    Provide async Elasticsearch client for testing.

    Requires Elasticsearch to be running on localhost:9200
    """
    if not is_elasticsearch_available():
        pytest.skip("Elasticsearch not available")

    try:
        from elasticsearch import AsyncElasticsearch  # type: ignore[import-untyped]

        # Configure client with compatibility mode for elasticsearch-py v9+
        client = AsyncElasticsearch(
            [f"http://{ES_HOST}:{ES_PORT}"],
            # Set compatibility header for v8 (works with ES 7.x and 8.x)
            headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"},
        )
        # Verify connection
        info = await client.info()
        print(f"\nConnected to Elasticsearch {info['version']['number']} (async)")
        yield client
        await client.close()
    except ImportError:
        pytest.skip("elasticsearch package not installed")


# OpenSearch fixtures
@pytest.fixture(scope="session")
def opensearch_client():
    """
    Provide OpenSearch client for testing.

    Requires OpenSearch to be running on localhost:9202
    (use docker-compose up opensearch)
    """
    if not is_opensearch_available():
        pytest.skip("OpenSearch not available")

    try:
        from opensearchpy import OpenSearch  # type: ignore[import-untyped]

        client = OpenSearch(
            hosts=[{"host": ES_HOST, "port": OS_PORT}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        # Verify connection
        info = client.info()
        print(f"\nConnected to OpenSearch {info['version']['number']}")
        yield client
        client.close()
    except ImportError:
        pytest.skip("opensearch-py package not installed")


@pytest.fixture(scope="session")
async def async_opensearch_client():
    """
    Provide async OpenSearch client for testing.

    Requires OpenSearch to be running on localhost:9202
    """
    if not is_opensearch_available():
        pytest.skip("OpenSearch not available")

    try:
        from opensearchpy import AsyncOpenSearch  # type: ignore[import-untyped]

        client = AsyncOpenSearch(
            hosts=[{"host": ES_HOST, "port": OS_PORT}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        # Verify connection
        info = await client.info()
        print(f"\nConnected to OpenSearch {info['version']['number']} (async)")
        yield client
        await client.close()
    except ImportError:
        pytest.skip("opensearch-py package not installed")


# Adapter fixtures
@pytest.fixture
def elasticsearch_adapter(elasticsearch_client):
    """Provide Elasticsearch adapter for testing."""
    from strawberry_elastic import create_adapter

    return create_adapter(elasticsearch_client)


@pytest.fixture
def opensearch_adapter(opensearch_client):
    """Provide OpenSearch adapter for testing."""
    from strawberry_elastic import create_adapter

    return create_adapter(opensearch_client)


@pytest.fixture
async def async_elasticsearch_adapter(async_elasticsearch_client):
    """Provide async Elasticsearch adapter for testing."""
    from strawberry_elastic import create_adapter

    return create_adapter(async_elasticsearch_client)


@pytest.fixture
async def async_opensearch_adapter(async_opensearch_client):
    """Provide async OpenSearch adapter for testing."""
    from strawberry_elastic import create_adapter

    return create_adapter(async_opensearch_client)


# Test data fixtures
@pytest.fixture
def test_index_name() -> str:
    """Provide a unique test index name."""
    import uuid

    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def clean_test_index(elasticsearch_adapter, test_index_name):
    """
    Provide a clean test index and ensure cleanup after test.

    Yields the index name, then deletes it after the test.
    """
    # Ensure index doesn't exist before test
    try:
        await elasticsearch_adapter.delete_index(test_index_name)
    except Exception:
        pass

    yield test_index_name

    # Cleanup after test
    try:
        await elasticsearch_adapter.delete_index(test_index_name)
    except Exception:
        pass


# Document class fixtures (requires DSL)
@pytest.fixture
def sample_document_class():
    """
    Provide a sample Elasticsearch Document class for testing.

    Requires elasticsearch-dsl to be installed.
    """
    if not is_dsl_available():
        pytest.skip("DSL not available")

    from strawberry_elastic.types._dsl_compat import universal_dsl

    Document = universal_dsl.Document
    Text = universal_dsl.Text
    Keyword = universal_dsl.Keyword
    Integer = universal_dsl.Integer
    Date = universal_dsl.Date

    class Article(Document):
        """Sample article document for testing."""

        title = Text()
        slug = Keyword()
        content = Text()
        author = Keyword()
        view_count = Integer()
        published_at = Date()

        class Index:
            name = "test-articles"

    return Article


@pytest.fixture
def nested_document_class():
    """
    Provide a Document class with nested objects for testing.

    Requires elasticsearch-dsl to be installed.
    """
    if not is_dsl_available():
        pytest.skip("DSL not available")

    from strawberry_elastic.types._dsl_compat import universal_dsl

    Document = universal_dsl.Document
    InnerDoc = universal_dsl.get_inner_doc_class()
    Text = universal_dsl.Text
    Keyword = universal_dsl.Keyword
    Nested = universal_dsl.Nested

    class Author(InnerDoc):  # type: ignore[misc]
        """Nested author information."""

        name = Text()
        email = Keyword()

    class BlogPost(Document):
        """Blog post with nested author."""

        title = Text()
        content = Text()
        author = Nested(Author)

        class Index:
            name = "test-blog"

    return BlogPost


# Session-scoped cleanup
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_indices():
    """
    Clean up any test indices at the end of the session.

    Runs automatically after all tests complete.
    """
    yield

    # Cleanup phase - delete any indices starting with 'test-'
    if is_elasticsearch_available():
        try:
            from elasticsearch import Elasticsearch  # type: ignore[import-untyped]

            # Configure client with compatibility mode for elasticsearch-py v9+
            client = Elasticsearch(
                [f"http://{ES_HOST}:{ES_PORT}"],
                headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"},
            )
            indices = client.cat.indices(format="json")
            for index in indices:
                index_name = index["index"]
                if index_name.startswith("test-"):
                    try:
                        client.indices.delete(index=index_name)
                        print(f"\nCleaned up test index: {index_name}")
                    except Exception as e:
                        print(f"\nFailed to clean up {index_name}: {e}")
            client.close()
        except Exception:
            pass
