"""
Basic adapter usage examples for strawberry-elastic.

This example demonstrates how to use the adapter system with both
Elasticsearch and OpenSearch clients, including sync and async variants.
"""

import asyncio
import logging
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Example 1: Auto-detection with Elasticsearch client
async def example_elasticsearch_sync():
    """Example using sync Elasticsearch client with auto-detection."""
    try:
        from elasticsearch import Elasticsearch

        from strawberry_elastic import create_adapter

        # Create Elasticsearch client
        client = Elasticsearch(
            ["http://localhost:9200"],
            basic_auth=("elastic", "password"),  # Optional
        )

        # Auto-detect and create adapter
        adapter = create_adapter(client)

        logger.info(f"Created adapter: {adapter}")

        # First operation will auto-detect capabilities (lazy initialization)
        info = await adapter.info()
        logger.info(f"Cluster info: {info['cluster_name']}")

        # Now capabilities are detected and available
        logger.info(f"Version: {adapter.version}")
        logger.info(f"Supports PIT: {adapter.supports_pit}")
        logger.info(f"Supports search_after: {adapter.supports_search_after}")

        # Search example
        query = {"match_all": {}}
        results = await adapter.search(index="products", query=query, size=10)
        logger.info(f"Found {results['hits']['total']['value']} documents")

        # Get single document
        doc = await adapter.get(index="products", id="1")
        logger.info(f"Document: {doc['_source']}")

    except ImportError:
        logger.warning("Elasticsearch not installed. Install with: pip install elasticsearch")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


async def example_elasticsearch_async():
    """Example using async Elasticsearch client."""
    try:
        from elasticsearch import AsyncElasticsearch

        from strawberry_elastic import create_adapter

        # Create async Elasticsearch client
        client = AsyncElasticsearch(
            ["http://localhost:9200"],
            basic_auth=("elastic", "password"),
        )

        # Auto-detect and create adapter
        adapter = create_adapter(client)

        logger.info(f"Created async adapter: {adapter}")

        # Use adapter (native async operations - capabilities detected on first use)
        info = await adapter.info()
        logger.info(f"Cluster: {info['cluster_name']}")

        # Get capabilities after detection
        capabilities = await adapter.get_capabilities()
        logger.info(f"Is async: {capabilities.get('is_async')}")

        # Clean up
        await client.close()

    except ImportError:
        logger.warning("Elasticsearch not installed. Install with: pip install elasticsearch")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


# Example 2: OpenSearch client
async def example_opensearch_sync():
    """Example using sync OpenSearch client."""
    try:
        from opensearchpy import OpenSearch

        from strawberry_elastic import create_adapter

        # Create OpenSearch client
        client = OpenSearch(
            hosts=[{"host": "localhost", "port": 9200}],
            http_auth=("admin", "admin"),
            use_ssl=False,
        )

        # Auto-detect and create adapter
        adapter = create_adapter(client)

        logger.info(f"Created adapter: {adapter}")

        # Use adapter (capabilities detected on first use)
        info = await adapter.info()
        logger.info(f"OpenSearch version: {info['version']['number']}")

        # Check capabilities after detection
        logger.info(f"Version: {adapter.version}")
        logger.info(f"Supports PIT: {adapter.supports_pit}")

    except ImportError:
        logger.warning("OpenSearch not installed. Install with: pip install opensearch-py")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


async def example_opensearch_async():
    """Example using async OpenSearch client."""
    try:
        from opensearchpy import AsyncOpenSearch

        from strawberry_elastic import create_adapter

        # Create async OpenSearch client
        client = AsyncOpenSearch(
            hosts=[{"host": "localhost", "port": 9200}],
            http_auth=("admin", "admin"),
            use_ssl=False,
        )

        # Auto-detect and create adapter
        adapter = create_adapter(client)

        logger.info(f"Created async adapter: {adapter}")

        # Use adapter
        info = await adapter.info()
        logger.info(f"OpenSearch: {info['version']['number']}")

        # Clean up
        await client.close()

    except ImportError:
        logger.warning("OpenSearch not installed. Install with: pip install opensearch-py")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


# Example 3: CRUD operations
async def example_crud_operations():
    """Example demonstrating CRUD operations with adapter."""
    try:
        from elasticsearch import Elasticsearch

        from strawberry_elastic import create_adapter

        client = Elasticsearch(["http://localhost:9200"])
        adapter = create_adapter(client)

        # Index a document
        document = {
            "name": "Wireless Mouse",
            "price": 29.99,
            "category": "Electronics",
            "in_stock": True,
        }

        result = await adapter.index(
            index="products", document=document, id="mouse-001", refresh=True
        )
        logger.info(f"Indexed document: {result['_id']}")

        # Get the document
        doc = await adapter.get(index="products", id="mouse-001")
        logger.info(f"Retrieved: {doc['_source']['name']}")

        # Update the document
        update_result = await adapter.update(
            index="products",
            id="mouse-001",
            document={"price": 24.99},
            refresh=True,
        )
        logger.info(f"Updated document: {update_result['result']}")

        # Search for documents
        query = {"match": {"category": "Electronics"}}
        search_results = await adapter.search(index="products", query=query)
        logger.info(f"Found {len(search_results['hits']['hits'])} electronics")

        # Delete the document
        delete_result = await adapter.delete(index="products", id="mouse-001", refresh=True)
        logger.info(f"Deleted document: {delete_result['result']}")

    except ImportError:
        logger.warning("Elasticsearch not installed")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


# Example 4: Bulk operations
async def example_bulk_operations():
    """Example demonstrating bulk operations."""
    try:
        from elasticsearch import Elasticsearch

        from strawberry_elastic import create_adapter

        client = Elasticsearch(["http://localhost:9200"])
        adapter = create_adapter(client)

        # Prepare bulk operations
        operations = [
            {"index": {"_index": "products", "_id": "1"}},
            {"name": "Product 1", "price": 10.00},
            {"index": {"_index": "products", "_id": "2"}},
            {"name": "Product 2", "price": 20.00},
            {"index": {"_index": "products", "_id": "3"}},
            {"name": "Product 3", "price": 30.00},
        ]

        # Execute bulk operation
        result = await adapter.bulk(operations=operations, refresh=True)

        logger.info(f"Bulk operation completed")
        logger.info(f"Errors: {result.get('errors', False)}")
        logger.info(f"Items processed: {len(result['items'])}")

        # Clean up
        for i in range(1, 4):
            await adapter.delete(index="products", id=str(i))

    except ImportError:
        logger.warning("Elasticsearch not installed")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


# Example 5: Advanced search with pagination
async def example_advanced_search():
    """Example demonstrating advanced search features."""
    try:
        from elasticsearch import Elasticsearch

        from strawberry_elastic import create_adapter

        client = Elasticsearch(["http://localhost:9200"])
        adapter = create_adapter(client)

        # Complex query with filters
        query = {
            "bool": {
                "must": [{"match": {"description": "wireless"}}],
                "filter": [
                    {"range": {"price": {"gte": 10, "lte": 100}}},
                    {"term": {"in_stock": True}},
                ],
            }
        }

        # Search with pagination using search_after
        results = await adapter.search(
            index="products",
            query=query,
            size=10,
            sort=[{"price": "asc"}, {"_id": "asc"}],
            track_total_hits=True,
        )

        logger.info(f"Total hits: {results['hits']['total']['value']}")
        logger.info(f"Results in page: {len(results['hits']['hits'])}")

        # Get last sort values for next page
        if results["hits"]["hits"]:
            last_hit = results["hits"]["hits"][-1]
            search_after_values = last_hit["sort"]
            logger.info(f"Search after values: {search_after_values}")

            # Get next page
            next_results = await adapter.search(
                index="products",
                query=query,
                size=10,
                sort=[{"price": "asc"}, {"_id": "asc"}],
                search_after=search_after_values,
            )
            logger.info(f"Next page results: {len(next_results['hits']['hits'])}")

    except ImportError:
        logger.warning("Elasticsearch not installed")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


# Example 6: Mapping operations
async def example_mapping_operations():
    """Example demonstrating mapping operations."""
    try:
        from elasticsearch import Elasticsearch

        from strawberry_elastic import create_adapter

        client = Elasticsearch(["http://localhost:9200"])
        adapter = create_adapter(client)

        index_name = "test_products"

        # Check if index exists
        exists = await adapter.exists(index=index_name)
        if exists:
            await adapter.delete_index(index=index_name)

        # Create index with mappings
        mappings = {
            "properties": {
                "name": {"type": "text"},
                "description": {"type": "text"},
                "price": {"type": "float"},
                "category": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "created_at": {"type": "date"},
                "in_stock": {"type": "boolean"},
            }
        }

        settings = {"number_of_shards": 1, "number_of_replicas": 0}

        create_result = await adapter.create_index(
            index=index_name, mappings=mappings, settings=settings
        )
        logger.info(f"Created index: {create_result['acknowledged']}")

        # Get mapping
        mapping = await adapter.get_mapping(index=index_name)
        logger.info(f"Index mappings: {list(mapping[index_name]['mappings']['properties'].keys())}")

        # Update mapping (add new field)
        new_properties = {"rating": {"type": "float"}}
        await adapter.put_mapping(index=index_name, properties=new_properties)
        logger.info("Added new field 'rating' to mapping")

        # Clean up
        await adapter.delete_index(index=index_name)

    except ImportError:
        logger.warning("Elasticsearch not installed")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


# Example 7: Capability detection
async def example_capability_detection():
    """Example showing how to detect and use client capabilities."""
    try:
        from elasticsearch import Elasticsearch

        from strawberry_elastic import create_adapter

        client = Elasticsearch(["http://localhost:9200"])
        adapter = create_adapter(client)

        # Trigger capability detection with first operation
        info = await adapter.info()

        # Get all capabilities (now detected)
        capabilities = await adapter.get_capabilities()
        logger.info("Client Capabilities:")
        logger.info(f"  Version: {adapter.version}")
        logger.info(f"  Supports PIT: {adapter.supports_pit}")
        logger.info(f"  Supports search_after: {adapter.supports_search_after}")
        logger.info(f"  Supports async search: {adapter.supports_async_search}")
        logger.info(f"  Is async client: {capabilities.get('is_async')}")

        # Use feature conditionally
        if adapter.supports_pit:
            logger.info("\nPoint in Time is supported - can use PIT for consistent pagination")
        else:
            logger.info("\nPoint in Time not supported - using search_after instead")

    except ImportError:
        logger.warning("Elasticsearch not installed")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


async def main():
    """Run all examples."""
    logger.info("=" * 80)
    logger.info("Strawberry Elastic - Basic Adapter Usage Examples")
    logger.info("=" * 80)

    examples = [
        ("Elasticsearch (Sync)", example_elasticsearch_sync),
        ("Elasticsearch (Async)", example_elasticsearch_async),
        ("OpenSearch (Sync)", example_opensearch_sync),
        ("OpenSearch (Async)", example_opensearch_async),
        ("CRUD Operations", example_crud_operations),
        ("Bulk Operations", example_bulk_operations),
        ("Advanced Search", example_advanced_search),
        ("Mapping Operations", example_mapping_operations),
        ("Capability Detection", example_capability_detection),
    ]

    for title, example_func in examples:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Example: {title}")
        logger.info("=" * 80)
        try:
            await example_func()
        except Exception as e:
            logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
