"""Tests for SearchManager with centralized config system."""

import pytest

from web_search.search_manager import SearchManager
from web_search.search_types import SearchProvider


class TestSearchManager:
    """Test SearchManager with centralized configuration system."""

    def test_manager_initialization(self):
        """Should initialize SearchManager with default provider."""
        manager = SearchManager()
        assert manager.default_provider == SearchProvider.DUCKDUCKGO

    def test_manager_initialization_with_custom_provider(self):
        """Should initialize SearchManager with custom default provider."""
        manager = SearchManager(default_provider=SearchProvider.SERPAPI)
        assert manager.default_provider == SearchProvider.SERPAPI

    def test_manager_loads_all_provider_configs(self):
        """Should load configurations for all providers."""
        manager = SearchManager()

        # Should have loaded configs for all providers
        assert len(manager._configs) == 5
        assert SearchProvider.SERPAPI in manager._configs
        assert SearchProvider.PERPLEXITY in manager._configs
        assert SearchProvider.DUCKDUCKGO in manager._configs
        assert SearchProvider.TAVILY in manager._configs
        assert SearchProvider.CLAUDE in manager._configs

    def test_manager_uses_environment_variables(self, monkeypatch):
        """Should use configuration values from environment variables."""
        # Set environment variables
        monkeypatch.setenv("SERPAPI_API_KEY", "test-serpapi-key")
        monkeypatch.setenv("DUCKDUCKGO_MAX_RESULTS", "20")
        monkeypatch.setenv("SEARCH_TIMEOUT", "60")

        manager = SearchManager()

        # Should have correct config values from environment
        serpapi_config = manager._configs[SearchProvider.SERPAPI]
        duckduckgo_config = manager._configs[SearchProvider.DUCKDUCKGO]

        assert serpapi_config.api_key == "test-serpapi-key"
        assert duckduckgo_config.max_results == 20
        assert serpapi_config.timeout == 60
        assert duckduckgo_config.timeout == 60

    def test_get_available_providers(self, monkeypatch):
        """Should determine available providers based on API key presence."""
        # Set up environment with some providers having API keys
        monkeypatch.setenv("SERPAPI_API_KEY", "test-serpapi-key")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
        monkeypatch.setenv("TAVILY_API_KEY", "")  # Empty key
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")  # Empty key

        manager = SearchManager()
        available = manager.get_available_providers()

        # Should have all providers in the response
        assert len(available) == 5

        # DuckDuckGo should always be available (no API key required)
        assert available["duckduckgo"] is True

        # Providers with API keys should be available
        assert available["serpapi"] is True
        assert available["perplexity"] is True

        # Providers without API keys should be unavailable
        assert available["tavily"] is False
        assert available["claude"] is False

    def test_get_fallback_chain(self, monkeypatch):
        """Should create fallback chain based on available providers."""
        # Set up environment with some providers available
        monkeypatch.setenv("SERPAPI_API_KEY", "test-serpapi-key")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
        monkeypatch.setenv("TAVILY_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")

        manager = SearchManager()
        fallback_chain = manager.get_fallback_chain()

        # Should include available providers in priority order
        assert SearchProvider.DUCKDUCKGO in fallback_chain
        assert SearchProvider.SERPAPI in fallback_chain
        assert SearchProvider.PERPLEXITY in fallback_chain

        # Should not include unavailable providers
        assert SearchProvider.TAVILY not in fallback_chain
        assert SearchProvider.CLAUDE not in fallback_chain

    def test_get_fallback_chain_with_no_api_keys(self, monkeypatch):
        """Should still have DuckDuckGo in fallback chain when no API keys available."""
        # Clear all API keys
        monkeypatch.setenv("SERPAPI_API_KEY", "")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "")
        monkeypatch.setenv("TAVILY_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")

        manager = SearchManager()
        fallback_chain = manager.get_fallback_chain()

        # Should at least have DuckDuckGo
        assert SearchProvider.DUCKDUCKGO in fallback_chain
        assert len(fallback_chain) == 1
