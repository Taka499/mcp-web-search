"""Tests for web search providers."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from web_search.providers.base import BaseSearchProvider
from web_search.providers.duckduckgo_provider import DuckDuckGoProvider
from web_search.providers.serpapi_provider import SerpAPIProvider
from web_search.providers.perplexity_provider import PerplexityProvider
from web_search.providers.tavily_provider import TavilyProvider
from web_search.providers.claude_provider import ClaudeProvider
from web_search.search_types import SearchProvider, SearchResult, SearchResponse, SearchConfig


class TestBaseSearchProvider:
    """Test the base search provider abstract class."""
    
    def test_base_provider_is_abstract(self):
        """Test that BaseSearchProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSearchProvider()
    
    def test_base_provider_methods_are_abstract(self):
        """Test that abstract methods must be implemented."""
        class IncompleteProvider(BaseSearchProvider):
            pass
        
        with pytest.raises(TypeError):
            IncompleteProvider()


class TestDuckDuckGoProvider:
    """Test DuckDuckGo search provider."""
    
    @pytest.fixture
    def provider(self):
        """Create a DuckDuckGo provider instance."""
        return DuckDuckGoProvider()
    
    @pytest.fixture
    def config(self):
        """Create a search config for DuckDuckGo."""
        return SearchConfig(
            provider=SearchProvider.DUCKDUCKGO,
            max_results=5,
            timeout=30,
            duckduckgo_safesearch="moderate"
        )
    
    def test_provider_initialization(self, provider):
        """Test provider initializes correctly."""
        assert isinstance(provider, DuckDuckGoProvider)
        assert provider.name == "DuckDuckGo"
    
    def test_provider_requires_api_key(self, provider):
        """Test that DuckDuckGo doesn't require an API key."""
        assert not provider.requires_api_key()
    
    @pytest.mark.asyncio
    async def test_search_success(self, provider, config, duckduckgo_mock_response):
        """Test successful search with DuckDuckGo."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = duckduckgo_mock_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await provider.search("test query", config)
            
            assert isinstance(result, SearchResponse)
            assert result.query == "test query"
            assert result.provider == SearchProvider.DUCKDUCKGO
            assert len(result.results) == 2
            assert result.results[0].title == "Test Result 1"
            assert result.results[0].url == "https://example1.com"
    
    @pytest.mark.asyncio
    async def test_search_with_timeout(self, provider, config):
        """Test search with timeout."""
        config.timeout = 1
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            with pytest.raises(Exception) as exc_info:
                await provider.search("test query", config)
            
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_search_with_http_error(self, provider, config):
        """Test search with HTTP error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 429")
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await provider.search("test query", config)
            
            assert "HTTP 429" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_empty_results(self, provider, config):
        """Test search with empty results."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"results": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await provider.search("test query", config)
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 0


class TestSerpAPIProvider:
    """Test SerpAPI search provider."""
    
    @pytest.fixture
    def provider(self):
        """Create a SerpAPI provider instance."""
        return SerpAPIProvider()
    
    @pytest.fixture
    def config(self):
        """Create a search config for SerpAPI."""
        return SearchConfig(
            provider=SearchProvider.SERPAPI,
            api_key="test_api_key",
            max_results=5,
            timeout=30,
            serpapi_engine="google"
        )
    
    def test_provider_initialization(self, provider):
        """Test provider initializes correctly."""
        assert isinstance(provider, SerpAPIProvider)
        assert provider.name == "SerpAPI"
    
    def test_provider_requires_api_key(self, provider):
        """Test that SerpAPI requires an API key."""
        assert provider.requires_api_key()
    
    @pytest.mark.asyncio
    async def test_search_success(self, provider, config, serpapi_mock_response):
        """Test successful search with SerpAPI."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = serpapi_mock_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await provider.search("test query", config)
            
            assert isinstance(result, SearchResponse)
            assert result.query == "test query"
            assert result.provider == SearchProvider.SERPAPI
            assert len(result.results) == 2
            assert result.results[0].title == "SerpAPI Test Result 1"
            assert result.total_results == 2
    
    @pytest.mark.asyncio
    async def test_search_without_api_key(self, provider):
        """Test search without API key raises error."""
        config = SearchConfig(
            provider=SearchProvider.SERPAPI,
            api_key=None,
            max_results=5
        )
        
        with pytest.raises(ValueError) as exc_info:
            await provider.search("test query", config)
        
        assert "API key" in str(exc_info.value)


class TestPerplexityProvider:
    """Test Perplexity search provider."""
    
    @pytest.fixture
    def provider(self):
        """Create a Perplexity provider instance."""
        return PerplexityProvider()
    
    @pytest.fixture
    def config(self):
        """Create a search config for Perplexity."""
        return SearchConfig(
            provider=SearchProvider.PERPLEXITY,
            api_key="test_api_key",
            max_results=5,
            timeout=30,
            perplexity_model="sonar-pro"
        )
    
    def test_provider_initialization(self, provider):
        """Test provider initializes correctly."""
        assert isinstance(provider, PerplexityProvider)
        assert provider.name == "Perplexity"
    
    def test_provider_requires_api_key(self, provider):
        """Test that Perplexity requires an API key."""
        assert provider.requires_api_key()
    
    @pytest.mark.asyncio
    async def test_search_success(self, provider, config, perplexity_mock_response):
        """Test successful search with Perplexity."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = perplexity_mock_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.search("test query", config)
            
            assert isinstance(result, SearchResponse)
            assert result.query == "test query"
            assert result.provider == SearchProvider.PERPLEXITY
            assert len(result.results) >= 1
    
    @pytest.mark.asyncio
    async def test_search_without_api_key(self, provider):
        """Test search without API key raises error."""
        config = SearchConfig(
            provider=SearchProvider.PERPLEXITY,
            api_key=None,
            max_results=5
        )
        
        with pytest.raises(ValueError) as exc_info:
            await provider.search("test query", config)
        
        assert "API key" in str(exc_info.value)


class TestTavilyProvider:
    """Test Tavily search provider."""
    
    @pytest.fixture
    def provider(self):
        """Create a Tavily provider instance."""
        return TavilyProvider()
    
    @pytest.fixture
    def config(self):
        """Create a search config for Tavily."""
        return SearchConfig(
            provider=SearchProvider.TAVILY,
            api_key="test_api_key",
            max_results=5,
            timeout=30
        )
    
    def test_provider_initialization(self, provider):
        """Test provider initializes correctly."""
        assert isinstance(provider, TavilyProvider)
        assert provider.name == "Tavily"
    
    def test_provider_requires_api_key(self, provider):
        """Test that Tavily requires an API key."""
        assert provider.requires_api_key()
    
    @pytest.mark.asyncio
    async def test_search_success(self, provider, config, tavily_mock_response):
        """Test successful search with Tavily."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = tavily_mock_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.search("test query", config)
            
            assert isinstance(result, SearchResponse)
            assert result.query == "test query"
            assert result.provider == SearchProvider.TAVILY
            assert len(result.results) == 2
            assert result.results[0].title == "Tavily Test Result 1"
    
    @pytest.mark.asyncio
    async def test_search_without_api_key(self, provider):
        """Test search without API key raises error."""
        config = SearchConfig(
            provider=SearchProvider.TAVILY,
            api_key=None,
            max_results=5
        )
        
        with pytest.raises(ValueError) as exc_info:
            await provider.search("test query", config)
        
        assert "API key" in str(exc_info.value)


class TestClaudeProvider:
    """Test Claude search provider."""
    
    @pytest.fixture
    def provider(self):
        """Create a Claude provider instance."""
        return ClaudeProvider()
    
    @pytest.fixture
    def config(self):
        """Create a search config for Claude."""
        return SearchConfig(
            provider=SearchProvider.CLAUDE,
            api_key="test_api_key",
            max_results=5,
            timeout=30
        )
    
    def test_provider_initialization(self, provider):
        """Test provider initializes correctly."""
        assert isinstance(provider, ClaudeProvider)
        assert provider.name == "Claude"
    
    def test_provider_requires_api_key(self, provider):
        """Test that Claude requires an API key."""
        assert provider.requires_api_key()
    
    @pytest.mark.asyncio
    async def test_search_without_api_key(self, provider):
        """Test search without API key raises error."""
        config = SearchConfig(
            provider=SearchProvider.CLAUDE,
            api_key=None,
            max_results=5
        )
        
        with pytest.raises(ValueError) as exc_info:
            await provider.search("test query", config)
        
        assert "API key" in str(exc_info.value)


class TestProviderComparison:
    """Test comparison across different providers."""
    
    @pytest.fixture
    def all_providers(self):
        """Create instances of all providers."""
        return {
            SearchProvider.DUCKDUCKGO: DuckDuckGoProvider(),
            SearchProvider.SERPAPI: SerpAPIProvider(),
            SearchProvider.PERPLEXITY: PerplexityProvider(),
            SearchProvider.TAVILY: TavilyProvider(),
            SearchProvider.CLAUDE: ClaudeProvider()
        }
    
    def test_all_providers_have_unique_names(self, all_providers):
        """Test that all providers have unique names."""
        names = [provider.name for provider in all_providers.values()]
        assert len(names) == len(set(names))
    
    def test_api_key_requirements(self, all_providers):
        """Test API key requirements for each provider."""
        expected_requirements = {
            SearchProvider.DUCKDUCKGO: False,
            SearchProvider.SERPAPI: True,
            SearchProvider.PERPLEXITY: True,
            SearchProvider.TAVILY: True,
            SearchProvider.CLAUDE: True
        }
        
        for provider_type, provider in all_providers.items():
            assert provider.requires_api_key() == expected_requirements[provider_type]
    
    @pytest.mark.asyncio
    async def test_all_providers_implement_search(self, all_providers):
        """Test that all providers implement the search method."""
        for provider in all_providers.values():
            assert hasattr(provider, 'search')
            assert callable(provider.search)
    
    def test_provider_names_match_enum(self, all_providers):
        """Test that provider names are consistent with enum values."""
        for provider_type, provider in all_providers.items():
            # The provider name should contain the enum value in some form
            assert provider_type.value.lower() in provider.name.lower() or \
                   provider.name.lower() in provider_type.value.lower()


@pytest.mark.integration
class TestProviderIntegration:
    """Integration tests for providers (requires actual API keys)."""
    
    @pytest.mark.asyncio
    async def test_duckduckgo_live_search(self):
        """Test actual DuckDuckGo search (no API key required)."""
        provider = DuckDuckGoProvider()
        config = SearchConfig(
            provider=SearchProvider.DUCKDUCKGO,
            max_results=3,
            timeout=30
        )
        
        try:
            result = await provider.search("Python programming", config)
            assert isinstance(result, SearchResponse)
            assert len(result.results) > 0
            assert result.results[0].title
            assert result.results[0].url
        except Exception as e:
            pytest.skip(f"Live DuckDuckGo search failed: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_serpapi_live_search(self, mock_env_vars):
        """Test actual SerpAPI search (requires API key)."""
        if not mock_env_vars.get("SERPAPI_API_KEY"):
            pytest.skip("SERPAPI_API_KEY not provided")
        
        provider = SerpAPIProvider()
        config = SearchConfig(
            provider=SearchProvider.SERPAPI,
            api_key=mock_env_vars["SERPAPI_API_KEY"],
            max_results=3,
            timeout=30
        )
        
        result = await provider.search("Python programming", config)
        assert isinstance(result, SearchResponse)
        assert len(result.results) > 0