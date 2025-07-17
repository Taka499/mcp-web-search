"""Test configuration and fixtures for web search server tests."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from web_search.search_manager import SearchManager
from web_search.search_types import (
    SearchConfig,
    SearchProvider,
    SearchResponse,
    SearchResult,
)


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests",
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark tests as integration tests")
    config.addinivalue_line("markers", "asyncio: mark tests as async tests")


@pytest.fixture(scope="session")
def integration_enabled(pytestconfig):
    """Fixture to check if integration tests are enabled."""
    return pytestconfig.getoption("--run-integration")


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_search_result():
    """Create a mock search result for testing."""
    return SearchResult(
        title="Test Result",
        url="https://example.com",
        snippet="This is a test snippet",
        source="example.com",
        published_date="2024-01-01",
        metadata={"test": "data"},
    )


@pytest.fixture
def mock_search_response(mock_search_result):
    """Create a mock search response for testing."""
    return SearchResponse(
        query="test query",
        provider=SearchProvider.DUCKDUCKGO,
        results=[mock_search_result],
        total_results=1,
        search_time=0.5,
        metadata={"test": "response"},
    )


@pytest.fixture
def search_config():
    """Create a search configuration for testing."""
    return SearchConfig(
        provider=SearchProvider.DUCKDUCKGO,
        max_results=10,
        safe_search=True,
        timeout=30,
    )


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        "SERPAPI_API_KEY": "test_serpapi_key",
        "PERPLEXITY_API_KEY": "test_perplexity_key",
        "TAVILY_API_KEY": "test_tavily_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "DUCKDUCKGO_SAFESEARCH": "moderate",
        "SEARCH_TIMEOUT": "30",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    return test_env


@pytest.fixture
def mock_search_manager():
    """Create a mock search manager for testing."""
    manager = Mock(spec=SearchManager)
    manager.search = AsyncMock()
    manager.search_with_fallback = AsyncMock()
    manager.multi_provider_search = AsyncMock()
    manager.get_available_providers = Mock()
    manager.get_fallback_chain = Mock()
    manager.default_provider = SearchProvider.DUCKDUCKGO
    return manager


@pytest.fixture
def sample_search_queries():
    """Sample search queries for testing."""
    return [
        "artificial intelligence",
        "machine learning tutorials",
        "Python programming",
        "web development 2024",
        "data science trends",
    ]


@pytest.fixture
def provider_configs():
    """Configurations for different providers."""
    return {
        SearchProvider.DUCKDUCKGO: SearchConfig(
            provider=SearchProvider.DUCKDUCKGO,
            max_results=10,
            timeout=30,
        ),
        SearchProvider.SERPAPI: SearchConfig(
            provider=SearchProvider.SERPAPI,
            api_key="test_key",
            max_results=10,
            timeout=30,
            serpapi_engine="google",
        ),
        SearchProvider.PERPLEXITY: SearchConfig(
            provider=SearchProvider.PERPLEXITY,
            api_key="test_key",
            max_results=10,
            timeout=30,
            perplexity_model="sonar-pro",
        ),
        SearchProvider.TAVILY: SearchConfig(
            provider=SearchProvider.TAVILY,
            api_key="test_key",
            max_results=10,
            timeout=30,
        ),
        SearchProvider.CLAUDE: SearchConfig(
            provider=SearchProvider.CLAUDE,
            api_key="test_key",
            max_results=10,
            timeout=30,
        ),
    }


@pytest.fixture
def mock_http_response():
    """Mock HTTP response for testing."""

    class MockResponse:
        def __init__(self, json_data: dict[str, Any], status_code: int = 200):
            self.json_data = json_data
            self.status_code = status_code
            self.ok = status_code < 400

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if not self.ok:
                raise Exception(f"HTTP {self.status_code}")

    return MockResponse


@pytest.fixture
def duckduckgo_mock_response():
    """Mock DuckDuckGo API response."""
    return {
        "results": [
            {
                "title": "Test Result 1",
                "href": "https://example1.com",
                "body": "This is the first test result snippet",
            },
            {
                "title": "Test Result 2",
                "href": "https://example2.com",
                "body": "This is the second test result snippet",
            },
        ],
    }


@pytest.fixture
def serpapi_mock_response():
    """Mock SerpAPI response."""
    return {
        "organic_results": [
            {
                "title": "SerpAPI Test Result 1",
                "link": "https://serpapi-example1.com",
                "snippet": "This is a SerpAPI test snippet 1",
                "source": "serpapi-example1.com",
            },
            {
                "title": "SerpAPI Test Result 2",
                "link": "https://serpapi-example2.com",
                "snippet": "This is a SerpAPI test snippet 2",
                "source": "serpapi-example2.com",
            },
        ],
        "search_information": {
            "total_results": 2,
            "time_taken": 0.3,
        },
    }


@pytest.fixture
def perplexity_mock_response():
    """Mock Perplexity API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Here are the search results for your query...",
                    "role": "assistant",
                },
                "citations": [
                    "https://perplexity-example1.com",
                    "https://perplexity-example2.com",
                ],
            },
        ],
        "usage": {
            "total_tokens": 150,
        },
    }


@pytest.fixture
def tavily_mock_response():
    """Mock Tavily API response."""
    return {
        "results": [
            {
                "title": "Tavily Test Result 1",
                "url": "https://tavily-example1.com",
                "snippet": "This is a Tavily test snippet 1",
                "published_date": "2024-01-01",
                "score": 0.9,
            },
            {
                "title": "Tavily Test Result 2",
                "url": "https://tavily-example2.com",
                "snippet": "This is a Tavily test snippet 2",
                "published_date": "2024-01-02",
                "score": 0.8,
            },
        ],
        "query": "test query",
        "response_time": 0.4,
    }
