"""Updated tests for web search providers using new config system."""

import pytest
from unittest.mock import Mock, patch

from web_search.providers.base import BaseSearchProvider
from web_search.providers.duckduckgo_provider import DuckDuckGoProvider
from web_search.providers.serpapi_provider import SerpAPIProvider
from web_search.providers.perplexity_provider import PerplexityProvider
from web_search.providers.tavily_provider import TavilyProvider
from web_search.providers.claude_provider import ClaudeProvider
from web_search.search_types import SearchProvider, SearchResult, SearchResponse
from web_search.config import (
    DuckDuckGoConfig,
    SerpAPIConfig,
    PerplexityConfig,
    TavilyConfig,
    ClaudeConfig,
)


class TestBaseSearchProvider:
    """Test the base search provider abstract class."""

    def test_base_provider_is_abstract(self):
        """Test that BaseSearchProvider cannot be instantiated directly."""
        config = DuckDuckGoConfig()
        with pytest.raises(TypeError):
            BaseSearchProvider(config)

    def test_base_provider_methods_are_abstract(self):
        """Test that abstract methods must be implemented."""
        config = DuckDuckGoConfig()

        class IncompleteProvider(BaseSearchProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider(config)


class TestDuckDuckGoProvider:
    """Test DuckDuckGo search provider."""

    @pytest.fixture
    def config(self):
        """Create a DuckDuckGo config."""
        return DuckDuckGoConfig(max_results=5, timeout=30)

    @pytest.fixture
    def provider(self, config):
        """Create a DuckDuckGo provider instance."""
        return DuckDuckGoProvider(config)

    def test_provider_initialization(self, provider, config):
        """Test provider initializes correctly."""
        assert isinstance(provider, DuckDuckGoProvider)
        assert provider.config == config
        assert provider.config.provider == SearchProvider.DUCKDUCKGO

    def test_provider_validation(self, provider):
        """Test provider validation."""
        assert provider._validate_config() is True

    @pytest.mark.asyncio
    async def test_search_method_exists(self, provider):
        """Test that search method exists and is callable."""
        assert hasattr(provider, "search")
        assert callable(provider.search)


class TestSerpAPIProvider:
    """Test SerpAPI search provider."""

    @pytest.fixture
    def config(self):
        """Create a SerpAPI config."""
        return SerpAPIConfig(api_key="test_key", max_results=5, timeout=30)

    @pytest.fixture
    def provider(self, config):
        """Create a SerpAPI provider instance."""
        return SerpAPIProvider(config)

    def test_provider_initialization(self, provider, config):
        """Test provider initializes correctly."""
        assert isinstance(provider, SerpAPIProvider)
        assert provider.config == config
        assert provider.config.provider == SearchProvider.SERPAPI

    def test_provider_validation_success(self, provider):
        """Test provider validation with API key."""
        assert provider._validate_config() is True

    def test_provider_validation_failure(self, monkeypatch):
        """Test provider validation without API key."""
        # Create config with explicitly empty API key
        config = SerpAPIConfig()
        config.api_key = ""  # Set to empty string to trigger validation failure
        provider = SerpAPIProvider(config)

        with pytest.raises(ValueError, match="SerpAPI requires an API key"):
            provider._validate_config()


class TestPerplexityProvider:
    """Test Perplexity search provider."""

    @pytest.fixture
    def config(self):
        """Create a Perplexity config."""
        return PerplexityConfig(api_key="test_key", max_results=5, timeout=30)

    @pytest.fixture
    def provider(self, config):
        """Create a Perplexity provider instance."""
        return PerplexityProvider(config)

    def test_provider_initialization(self, provider, config):
        """Test provider initializes correctly."""
        assert isinstance(provider, PerplexityProvider)
        assert provider.config == config
        assert provider.config.provider == SearchProvider.PERPLEXITY

    def test_provider_validation_success(self, provider):
        """Test provider validation with API key."""
        assert provider._validate_config() is True

    def test_provider_validation_failure(self, monkeypatch):
        """Test provider validation without API key."""
        # Create config with explicitly empty API key
        config = PerplexityConfig()
        config.api_key = ""  # Set to empty string to trigger validation failure
        provider = PerplexityProvider(config)

        with pytest.raises(ValueError, match="Perplexity API requires an API key"):
            provider._validate_config()


class TestTavilyProvider:
    """Test Tavily search provider."""

    @pytest.fixture
    def config(self):
        """Create a Tavily config."""
        return TavilyConfig(api_key="test_key", max_results=5, timeout=30)

    @pytest.fixture
    def provider(self, config):
        """Create a Tavily provider instance."""
        return TavilyProvider(config)

    def test_provider_initialization(self, provider, config):
        """Test provider initializes correctly."""
        assert isinstance(provider, TavilyProvider)
        assert provider.config == config
        assert provider.config.provider == SearchProvider.TAVILY

    def test_provider_validation_success(self, provider):
        """Test provider validation with API key."""
        assert provider._validate_config() is True

    def test_provider_validation_failure(self, monkeypatch):
        """Test provider validation without API key."""
        # Create config with explicitly empty API key
        config = TavilyConfig()
        config.api_key = ""  # Set to empty string to trigger validation failure
        provider = TavilyProvider(config)

        with pytest.raises(ValueError, match="Tavily API requires an API key"):
            provider._validate_config()


class TestClaudeProvider:
    """Test Claude search provider."""

    @pytest.fixture
    def config(self):
        """Create a Claude config."""
        return ClaudeConfig(api_key="test_key", max_results=5, timeout=30)

    @pytest.fixture
    def provider(self, config):
        """Create a Claude provider instance."""
        return ClaudeProvider(config)

    def test_provider_initialization(self, provider, config):
        """Test provider initializes correctly."""
        assert isinstance(provider, ClaudeProvider)
        assert provider.config == config
        assert provider.config.provider == SearchProvider.CLAUDE

    def test_provider_validation_success(self, provider):
        """Test provider validation with API key."""
        assert provider._validate_config() is True

    def test_provider_validation_failure(self, monkeypatch):
        """Test provider validation without API key."""
        # Create config with explicitly empty API key
        config = ClaudeConfig()
        config.api_key = ""  # Set to empty string to trigger validation failure
        provider = ClaudeProvider(config)

        with pytest.raises(ValueError, match="Claude API requires an API key"):
            provider._validate_config()


class TestProviderComparison:
    """Test comparison across different providers."""

    @pytest.fixture
    def all_providers(self):
        """Create instances of all providers with valid configs."""
        return {
            SearchProvider.DUCKDUCKGO: DuckDuckGoProvider(DuckDuckGoConfig()),
            SearchProvider.SERPAPI: SerpAPIProvider(SerpAPIConfig(api_key="test_key")),
            SearchProvider.PERPLEXITY: PerplexityProvider(
                PerplexityConfig(api_key="test_key")
            ),
            SearchProvider.TAVILY: TavilyProvider(TavilyConfig(api_key="test_key")),
            SearchProvider.CLAUDE: ClaudeProvider(ClaudeConfig(api_key="test_key")),
        }

    def test_all_providers_have_correct_provider_enum(self, all_providers):
        """Test that all providers have correct provider enum in their config."""
        for provider_type, provider in all_providers.items():
            assert provider.config.provider == provider_type

    def test_all_providers_implement_search(self, all_providers):
        """Test that all providers implement the search method."""
        for provider in all_providers.values():
            assert hasattr(provider, "search")
            assert callable(provider.search)

    def test_all_providers_implement_validate_config(self, all_providers):
        """Test that all providers implement the _validate_config method."""
        for provider in all_providers.values():
            assert hasattr(provider, "_validate_config")
            assert callable(provider._validate_config)

    def test_api_key_validation_behavior(self, all_providers):
        """Test API key validation behavior for each provider."""
        # DuckDuckGo should validate successfully without API key
        duckduckgo_provider = all_providers[SearchProvider.DUCKDUCKGO]
        assert duckduckgo_provider._validate_config() is True

        # Other providers should require API keys
        for provider_type, provider in all_providers.items():
            if provider_type != SearchProvider.DUCKDUCKGO:
                # These providers should validate successfully with API key
                assert provider._validate_config() is True
