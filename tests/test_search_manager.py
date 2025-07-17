"""Tests for the SearchManager class."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from web_search.search_manager import SearchManager
from web_search.search_types import SearchProvider, SearchResult, SearchResponse, SearchConfig
from web_search.providers.base import BaseSearchProvider


class MockProvider(BaseSearchProvider):
    """Mock provider for testing."""
    
    def __init__(self, name: str, requires_key: bool = False, should_fail: bool = False):
        self._name = name
        self._requires_key = requires_key
        self._should_fail = should_fail
    
    @property
    def name(self) -> str:
        return self._name
    
    def requires_api_key(self) -> bool:
        return self._requires_key
    
    async def search(self, query: str, config: SearchConfig) -> SearchResponse:
        if self._should_fail:
            raise Exception(f"{self._name} search failed")
        
        return SearchResponse(
            query=query,
            provider=config.provider,
            results=[
                SearchResult(
                    title=f"{self._name} Result",
                    url=f"https://{self._name.lower()}.com",
                    snippet=f"Test result from {self._name}",
                    source=f"{self._name.lower()}.com"
                )
            ],
            total_results=1,
            search_time=0.1,
            metadata={"provider": self._name}
        )


class TestSearchManager:
    """Test the SearchManager class."""
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock providers for testing."""
        return {
            SearchProvider.DUCKDUCKGO: MockProvider("DuckDuckGo", requires_key=False),
            SearchProvider.SERPAPI: MockProvider("SerpAPI", requires_key=True),
            SearchProvider.PERPLEXITY: MockProvider("Perplexity", requires_key=True)
        }
    
    @pytest.fixture
    def search_manager(self, mock_providers):
        """Create a SearchManager with mock providers."""
        manager = SearchManager(default_provider=SearchProvider.DUCKDUCKGO)
        manager.providers = mock_providers
        return manager
    
    def test_manager_initialization(self):
        """Test SearchManager initialization."""
        manager = SearchManager(default_provider=SearchProvider.DUCKDUCKGO)
        assert manager.default_provider == SearchProvider.DUCKDUCKGO
        assert isinstance(manager.providers, dict)
        assert len(manager.providers) == len(SearchProvider)
    
    def test_manager_initialization_with_invalid_default(self):
        """Test SearchManager initialization with invalid default provider."""
        # Should still work, will use first available provider
        manager = SearchManager(default_provider=None)
        assert manager.default_provider is not None
    
    @pytest.mark.asyncio
    async def test_search_with_valid_provider(self, search_manager):
        """Test search with a valid provider."""
        config = SearchConfig(
            provider=SearchProvider.DUCKDUCKGO,
            max_results=5
        )
        
        result = await search_manager.search("test query", SearchProvider.DUCKDUCKGO, 5)
        
        assert isinstance(result, SearchResponse)
        assert result.query == "test query"
        assert result.provider == SearchProvider.DUCKDUCKGO
        assert len(result.results) == 1
        assert result.results[0].title == "DuckDuckGo Result"
    
    @pytest.mark.asyncio
    async def test_search_with_provider_that_requires_api_key(self, search_manager):
        """Test search with provider that requires API key but none provided."""
        with pytest.raises(ValueError) as exc_info:
            await search_manager.search("test query", SearchProvider.SERPAPI, 5)
        
        assert "API key" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_with_api_key_provided(self, search_manager, mock_env_vars):
        """Test search with API key provided via environment."""
        with patch.dict('os.environ', mock_env_vars):
            result = await search_manager.search("test query", SearchProvider.SERPAPI, 5)
            
            assert isinstance(result, SearchResponse)
            assert result.provider == SearchProvider.SERPAPI
            assert result.results[0].title == "SerpAPI Result"
    
    @pytest.mark.asyncio
    async def test_search_with_failing_provider(self, search_manager):
        """Test search when provider fails."""
        # Replace with failing provider
        failing_provider = MockProvider("FailingProvider", should_fail=True)
        search_manager.providers[SearchProvider.DUCKDUCKGO] = failing_provider
        
        with pytest.raises(Exception) as exc_info:
            await search_manager.search("test query", SearchProvider.DUCKDUCKGO, 5)
        
        assert "search failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_with_fallback_success(self, search_manager):
        """Test search_with_fallback when first provider works."""
        result = await search_manager.search_with_fallback("test query", 5)
        
        assert isinstance(result, SearchResponse)
        assert result.query == "test query"
        # Should use default provider (DuckDuckGo)
        assert result.provider == SearchProvider.DUCKDUCKGO
    
    @pytest.mark.asyncio
    async def test_search_with_fallback_primary_fails(self, search_manager):
        """Test search_with_fallback when primary provider fails."""
        # Make DuckDuckGo fail, but SerpAPI should work with API key
        failing_provider = MockProvider("FailingDuckDuckGo", should_fail=True)
        search_manager.providers[SearchProvider.DUCKDUCKGO] = failing_provider
        
        with patch.dict('os.environ', {'SERPAPI_API_KEY': 'test_key'}):
            result = await search_manager.search_with_fallback("test query", 5)
            
            assert isinstance(result, SearchResponse)
            # Should fall back to next available provider
            assert result.provider != SearchProvider.DUCKDUCKGO
    
    @pytest.mark.asyncio
    async def test_search_with_fallback_all_fail(self, search_manager):
        """Test search_with_fallback when all providers fail."""
        # Make all providers fail
        for provider_type in search_manager.providers:
            search_manager.providers[provider_type] = MockProvider(
                f"Failing{provider_type.value}", should_fail=True
            )
        
        with pytest.raises(Exception) as exc_info:
            await search_manager.search_with_fallback("test query", 5)
        
        assert "All search providers failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_success(self, search_manager):
        """Test multi_provider_search with multiple providers."""
        providers = [SearchProvider.DUCKDUCKGO, SearchProvider.PERPLEXITY]
        
        with patch.dict('os.environ', {'PERPLEXITY_API_KEY': 'test_key'}):
            results = await search_manager.multi_provider_search(
                "test query", providers, 3
            )
            
            assert isinstance(results, dict)
            assert len(results) == 2
            assert "duckduckgo" in results
            assert "perplexity" in results
            
            # Verify each result is a SearchResponse
            for provider_name, response in results.items():
                assert isinstance(response, SearchResponse)
                assert response.query == "test query"
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_partial_failure(self, search_manager):
        """Test multi_provider_search when some providers fail."""
        # Make SerpAPI fail but keep DuckDuckGo working
        failing_provider = MockProvider("FailingSerpAPI", requires_key=True, should_fail=True)
        search_manager.providers[SearchProvider.SERPAPI] = failing_provider
        
        providers = [SearchProvider.DUCKDUCKGO, SearchProvider.SERPAPI]
        
        with patch.dict('os.environ', {'SERPAPI_API_KEY': 'test_key'}):
            results = await search_manager.multi_provider_search(
                "test query", providers, 3
            )
            
            # Should only contain successful results
            assert isinstance(results, dict)
            assert "duckduckgo" in results
            assert "serpapi" not in results  # Failed provider excluded
            assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_concurrent_execution(self, search_manager):
        """Test that multi_provider_search executes searches concurrently."""
        providers = [SearchProvider.DUCKDUCKGO, SearchProvider.PERPLEXITY]
        
        # Mock time tracking to verify concurrent execution
        start_times = []
        end_times = []
        
        async def track_search(original_search):
            async def wrapper(*args, **kwargs):
                start_times.append(asyncio.get_event_loop().time())
                result = await original_search(*args, **kwargs)
                end_times.append(asyncio.get_event_loop().time())
                return result
            return wrapper
        
        # Wrap provider search methods
        for provider in search_manager.providers.values():
            provider.search = await track_search(provider.search)
        
        with patch.dict('os.environ', {'PERPLEXITY_API_KEY': 'test_key'}):
            await search_manager.multi_provider_search("test query", providers, 3)
        
        # Verify searches started concurrently (within small time window)
        assert len(start_times) == 2
        time_diff = abs(start_times[1] - start_times[0])
        assert time_diff < 0.1  # Should start within 100ms of each other
    
    def test_get_available_providers(self, search_manager):
        """Test get_available_providers method."""
        with patch.dict('os.environ', {'SERPAPI_API_KEY': 'test_key'}):
            status = search_manager.get_available_providers()
            
            assert isinstance(status, dict)
            assert len(status) == len(SearchProvider)
            
            # DuckDuckGo should be available (no API key required)
            assert status["duckduckgo"] is True
            
            # SerpAPI should be available (API key in env)
            assert status["serpapi"] is True
            
            # Perplexity should not be available (no API key)
            assert status["perplexity"] is False
    
    def test_get_fallback_chain(self, search_manager):
        """Test get_fallback_chain method."""
        with patch.dict('os.environ', {'SERPAPI_API_KEY': 'test_key'}):
            chain = search_manager.get_fallback_chain()
            
            assert isinstance(chain, list)
            assert len(chain) > 0
            
            # Default provider should be first
            assert chain[0] == search_manager.default_provider
            
            # All providers in chain should be available
            available = search_manager.get_available_providers()
            for provider in chain:
                assert available[provider.value] is True
    
    def test_get_fallback_chain_no_available_providers(self, search_manager):
        """Test get_fallback_chain when no providers are available."""
        # Remove API keys to make all key-required providers unavailable
        with patch.dict('os.environ', {}, clear=True):
            # Make DuckDuckGo also require a key for this test
            search_manager.providers[SearchProvider.DUCKDUCKGO] = MockProvider(
                "DuckDuckGo", requires_key=True
            )
            
            chain = search_manager.get_fallback_chain()
            assert len(chain) == 0
    
    @pytest.mark.asyncio
    async def test_search_timeout_handling(self, search_manager):
        """Test search timeout handling."""
        # Create a provider that simulates timeout
        class TimeoutProvider(BaseSearchProvider):
            @property
            def name(self):
                return "TimeoutProvider"
            
            def requires_api_key(self):
                return False
            
            async def search(self, query, config):
                await asyncio.sleep(config.timeout + 1)  # Sleep longer than timeout
                return SearchResponse(query=query, provider=config.provider, results=[])
        
        search_manager.providers[SearchProvider.DUCKDUCKGO] = TimeoutProvider()
        
        config = SearchConfig(
            provider=SearchProvider.DUCKDUCKGO,
            timeout=1  # Very short timeout
        )
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                search_manager.search("test query", SearchProvider.DUCKDUCKGO, 5),
                timeout=2
            )
    
    def test_provider_configuration_from_env(self):
        """Test provider configuration from environment variables."""
        env_vars = {
            'SERPAPI_API_KEY': 'serpapi_key',
            'PERPLEXITY_API_KEY': 'perplexity_key',
            'TAVILY_API_KEY': 'tavily_key',
            'ANTHROPIC_API_KEY': 'anthropic_key',
            'DUCKDUCKGO_SAFESEARCH': 'strict',
            'SEARCH_TIMEOUT': '60'
        }
        
        with patch.dict('os.environ', env_vars):
            manager = SearchManager()
            
            # Check that environment variables are properly read
            available = manager.get_available_providers()
            
            # All providers with API keys should be available
            assert available["serpapi"] is True
            assert available["perplexity"] is True
            assert available["tavily"] is True
            assert available["claude"] is True
            assert available["duckduckgo"] is True  # No key required
    
    @pytest.mark.asyncio
    async def test_search_result_validation(self, search_manager):
        """Test that search results are properly validated."""
        # Create provider that returns invalid results
        class InvalidResultProvider(BaseSearchProvider):
            @property
            def name(self):
                return "InvalidProvider"
            
            def requires_api_key(self):
                return False
            
            async def search(self, query, config):
                # Return response with invalid result structure
                return SearchResponse(
                    query=query,
                    provider=config.provider,
                    results=[
                        SearchResult(
                            title="",  # Empty title should be handled
                            url="invalid-url",  # Invalid URL should be handled
                            snippet="Valid snippet"
                        )
                    ]
                )
        
        search_manager.providers[SearchProvider.DUCKDUCKGO] = InvalidResultProvider()
        
        # Should not raise exception, but handle invalid data gracefully
        result = await search_manager.search("test query", SearchProvider.DUCKDUCKGO, 5)
        assert isinstance(result, SearchResponse)
        assert len(result.results) == 1


class TestSearchManagerConfiguration:
    """Test SearchManager configuration and setup."""
    
    def test_manager_with_custom_providers(self):
        """Test SearchManager with custom provider configuration."""
        custom_providers = {
            SearchProvider.DUCKDUCKGO: MockProvider("CustomDuckDuckGo")
        }
        
        manager = SearchManager(default_provider=SearchProvider.DUCKDUCKGO)
        manager.providers = custom_providers
        
        assert len(manager.providers) == 1
        assert SearchProvider.DUCKDUCKGO in manager.providers
        assert manager.providers[SearchProvider.DUCKDUCKGO].name == "CustomDuckDuckGo"
    
    def test_manager_provider_priority(self, search_manager):
        """Test provider priority in fallback chain."""
        chain = search_manager.get_fallback_chain()
        
        # DuckDuckGo should be first (default and no API key required)
        assert chain[0] == SearchProvider.DUCKDUCKGO
        
        # Other providers should follow based on availability
        if len(chain) > 1:
            # Subsequent providers should be deterministically ordered
            provider_names = [p.value for p in chain[1:]]
            assert provider_names == sorted(provider_names)
    
    @pytest.mark.asyncio
    async def test_concurrent_search_safety(self, search_manager):
        """Test that concurrent searches don't interfere with each other."""
        # Start multiple searches concurrently
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                search_manager.search(f"query_{i}", SearchProvider.DUCKDUCKGO, 3)
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        # Verify each search got its own query
        for i, result in enumerate(results):
            assert result.query == f"query_{i}"
            assert isinstance(result, SearchResponse)
    
    def test_manager_memory_usage(self, search_manager):
        """Test that SearchManager doesn't leak memory."""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform multiple operations
        for _ in range(10):
            search_manager.get_available_providers()
            search_manager.get_fallback_chain()
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow significantly
        object_growth = final_objects - initial_objects
        assert object_growth < 100  # Allow for some normal object creation