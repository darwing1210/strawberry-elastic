#!/bin/bash
# Integration test script for Strawberry Elastic
# Manages Docker containers and runs tests with real clusters

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}Strawberry Elastic Integration Tests${NC}"
echo "======================================"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi
}

# Function to wait for service to be healthy
wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=0

    echo -n "Waiting for $service to be healthy..."

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep $service | grep -q "healthy"; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e " ${RED}✗${NC}"
    echo -e "${RED}Service $service failed to become healthy${NC}"
    return 1
}

# Parse command line arguments
COMMAND=${1:-"all"}
KEEP_RUNNING=${KEEP_RUNNING:-false}
BACKEND=${BACKEND:-"elasticsearch"}  # elasticsearch or opensearch

case $COMMAND in
    up)
        echo -e "${YELLOW}Starting Docker containers...${NC}"
        cd "$PROJECT_DIR"
        check_docker
        docker-compose up -d

        wait_for_service "strawberry-elastic-es" || exit 1
        wait_for_service "strawberry-elastic-es7" || exit 1
        wait_for_service "strawberry-elastic-os" || exit 1

        echo -e "${GREEN}All services are ready!${NC}"
        echo ""
        echo "Services:"
        echo "  - Elasticsearch 8.x:  http://localhost:9200"
        echo "  - Elasticsearch 7.x:  http://localhost:9201"
        echo "  - OpenSearch 2.x:     http://localhost:9202"
        ;;

    down)
        echo -e "${YELLOW}Stopping Docker containers...${NC}"
        cd "$PROJECT_DIR"
        docker-compose down -v
        echo -e "${GREEN}Containers stopped and volumes removed${NC}"
        ;;

    logs)
        cd "$PROJECT_DIR"
        docker-compose logs -f
        ;;

    test)
        echo -e "${YELLOW}Running integration tests...${NC}"
        cd "$PROJECT_DIR"

        # Check if containers are running, start if not
        if ! docker-compose ps | grep -q "Up"; then
            echo "Starting containers..."
            docker-compose up -d
            wait_for_service "strawberry-elastic-es" || exit 1
            wait_for_service "strawberry-elastic-es7" || exit 1
            wait_for_service "strawberry-elastic-os" || exit 1
        fi

        # Install DSL packages for testing
        echo -e "${YELLOW}Installing DSL packages...${NC}"
        uv pip install elasticsearch-dsl opensearch-py httpx

        # Run tests
        echo -e "${YELLOW}Running tests with backend: ${BACKEND}...${NC}"
        if [ "$BACKEND" = "opensearch" ]; then
            STRAWBERRY_ELASTIC_DSL=opensearch uv run pytest tests/types/ -m "requires_dsl" -v
        else
            uv run pytest tests/types/ -m "requires_dsl" -v
        fi

        if [ "$KEEP_RUNNING" != "true" ]; then
            echo -e "${YELLOW}Stopping containers...${NC}"
            docker-compose down -v
        fi
        ;;

    test-all)
        echo -e "${YELLOW}Running all tests (unit + integration)...${NC}"
        cd "$PROJECT_DIR"

        # Start containers
        docker-compose up -d
        wait_for_service "strawberry-elastic-es" || exit 1
        wait_for_service "strawberry-elastic-es7" || exit 1
        wait_for_service "strawberry-elastic-os" || exit 1

        # Install DSL packages
        echo -e "${YELLOW}Installing DSL packages...${NC}"
        uv pip install elasticsearch-dsl opensearch-py httpx

        # Run all tests
        echo -e "${YELLOW}Running all tests with backend: ${BACKEND}...${NC}"
        if [ "$BACKEND" = "opensearch" ]; then
            STRAWBERRY_ELASTIC_DSL=opensearch uv run pytest tests/types/ -v
        else
            uv run pytest tests/types/ -v
        fi

        if [ "$KEEP_RUNNING" != "true" ]; then
            echo -e "${YELLOW}Stopping containers...${NC}"
            docker-compose down -v
        fi
        ;;

    install-dsl)
        echo -e "${YELLOW}Installing DSL packages...${NC}"
        cd "$PROJECT_DIR"
        uv pip install elasticsearch-dsl opensearch-py httpx
        echo -e "${GREEN}DSL packages installed${NC}"
        ;;

    all)
        echo -e "${YELLOW}Running complete integration test suite...${NC}"
        cd "$PROJECT_DIR"
        check_docker

        # Start services
        docker-compose up -d
        wait_for_service "strawberry-elastic-es" || exit 1
        wait_for_service "strawberry-elastic-es7" || exit 1
        wait_for_service "strawberry-elastic-os" || exit 1

        # Install DSL
        echo -e "${YELLOW}Installing DSL packages...${NC}"
        uv pip install elasticsearch-dsl opensearch-py httpx

        # Run all tests
        echo -e "${YELLOW}Running complete test suite with backend: ${BACKEND}...${NC}"
        if [ "$BACKEND" = "opensearch" ]; then
            STRAWBERRY_ELASTIC_DSL=opensearch uv run pytest tests/types/ -v --cov=strawberry_elastic/types --cov-report=term-missing
        else
            uv run pytest tests/types/ -v --cov=strawberry_elastic/types --cov-report=term-missing
        fi

        TEST_EXIT_CODE=$?

        # Cleanup
        if [ "$KEEP_RUNNING" != "true" ]; then
            echo -e "${YELLOW}Cleaning up...${NC}"
            docker-compose down -v
        else
            echo -e "${YELLOW}Containers left running (use './scripts/test-integration.sh down' to stop)${NC}"
        fi

        if [ $TEST_EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}All tests passed!${NC}"
        else
            echo -e "${RED}Some tests failed${NC}"
            exit $TEST_EXIT_CODE
        fi
        ;;

    *)
        echo "Usage: $0 {up|down|logs|test|test-all|install-dsl|all}"
        echo ""
        echo "Commands:"
        echo "  up          - Start Docker containers"
        echo "  down        - Stop Docker containers and remove volumes"
        echo "  logs        - Show container logs"
        echo "  test        - Run DSL integration tests only"
        echo "  test-all    - Run all tests (unit + integration)"
        echo "  install-dsl - Install DSL packages (elasticsearch-dsl, opensearch-py)"
        echo "  all         - Complete test run (start, install, test, cleanup)"
        echo ""
        echo "Environment variables:"
        echo "  KEEP_RUNNING=true  - Keep containers running after tests"
        echo "  BACKEND=opensearch - Test with OpenSearch backend (default: elasticsearch)"
        echo ""
        echo "Examples:"
        echo "  ./scripts/test-integration.sh up"
        echo "  ./scripts/test-integration.sh test"
        echo "  KEEP_RUNNING=true ./scripts/test-integration.sh all"
        echo "  BACKEND=opensearch ./scripts/test-integration.sh all"
        echo "  BACKEND=opensearch KEEP_RUNNING=true ./scripts/test-integration.sh test"
        exit 1
        ;;
esac
