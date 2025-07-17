"""Tests for SearchManager integration with centralized config system."""

import pytest

from web_search.config import load_all_provider_configs
from web_search.search_manager import SearchManager
from web_search.search_types import SearchProvider


class TestSearchManagerConfigIntegration:
    """Test SearchManager integration with centralized config system."""

    def test_search_manager_uses_config_system(self, monkeypatch):
        """Should use config.py instead of direct environment access."""
        # Set environment variables
        monkeypatch.setenv("SERPAPI_API_KEY", "test-serpapi-key")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
        monkeypatch.setenv("DUCKDUCKGO_MAX_RESULTS", "15")
        monkeypatch.setenv("SEARCH_TIMEOUT", "45")

        # Create SearchManager
        manager = SearchManager()

        # Should use config system internally
        # The internal configs should come from our config.py system
        configs = manager._configs

        # Verify it has the correct configs loaded
        assert len(configs) == 5  # All providers
        assert SearchProvider.SERPAPI in configs
        assert SearchProvider.PERPLEXITY in configs
        assert SearchProvider.DUCKDUCKGO in configs
        assert SearchProvider.TAVILY in configs
        assert SearchProvider.CLAUDE in configs

        # Verify the configs have correct values from environment
        assert configs[SearchProvider.SERPAPI].api_key == "test-serpapi-key"
        assert configs[SearchProvider.PERPLEXITY].api_key == "test-perplexity-key"
        assert configs[SearchProvider.DUCKDUCKGO].max_results == 15
        assert configs[SearchProvider.DUCKDUCKGO].timeout == 45

    def test_search_manager_config_matches_load_all_provider_configs(self, monkeypatch):
        """Should produce same configs as load_all_provider_configs function."""
        # Set environment variables
        monkeypatch.setenv("SERPAPI_API_KEY", "test-serpapi-key")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
        monkeypatch.setenv("SERPAPI_MAX_RESULTS", "20")
        monkeypatch.setenv("PERPLEXITY_MODEL", "sonar-small")
        monkeypatch.setenv("SEARCH_TIMEOUT", "60")

        # Load configs using config.py function
        expected_configs = load_all_provider_configs()

        # Create SearchManager
        manager = SearchManager()

        # The configs should match what load_all_provider_configs produces
        for provider in SearchProvider:
            manager_config = manager._configs[provider]
            expected_config = expected_configs[provider]

            # Compare key fields
            assert manager_config.provider == expected_config.provider
            assert manager_config.api_key == expected_config.api_key
            assert manager_config.max_results == expected_config.max_results
            assert manager_config.timeout == expected_config.timeout

            # Compare provider-specific fields
            if provider == SearchProvider.SERPAPI:
                assert manager_config.serpapi_engine == expected_config.serpapi_engine
            elif provider == SearchProvider.PERPLEXITY:
                assert (
                    manager_config.perplexity_model == expected_config.perplexity_model
                )
            elif provider == SearchProvider.DUCKDUCKGO:
                assert (
                    manager_config.duckduckgo_safesearch
                    == expected_config.duckduckgo_safesearch
                )

    def test_search_manager_provider_instantiation_with_config(self, monkeypatch):
        """Should pass correct configurations to provider instances."""
        # Set environment variables
        monkeypatch.setenv("SERPAPI_API_KEY", "test-serpapi-key")
        monkeypatch.setenv("SERPAPI_ENGINE", "bing")
        monkeypatch.setenv("SERPAPI_MAX_RESULTS", "25")
        monkeypatch.setenv("SEARCH_TIMEOUT", "30")

        # Create SearchManager
        manager = SearchManager()

        # Get the config that would be passed to SerpAPI provider
        serpapi_config = manager._configs[SearchProvider.SERPAPI]

        # Verify the config has the correct values
        assert serpapi_config.api_key == "test-serpapi-key"
        assert serpapi_config.serpapi_engine == "bing"
        assert serpapi_config.max_results == 25
        assert serpapi_config.timeout == 30

    def test_search_manager_no_direct_os_getenv_usage(self):
        """Should not use os.getenv() directly in SearchManager implementation."""
        # This test verifies that SearchManager uses config.py instead of direct os.getenv()
        # We'll check the implementation by inspecting the source code
        import inspect

        # Get the source code of SearchManager class
        source = inspect.getsource(SearchManager)

        # The class should not contain os.getenv() calls
        assert "os.getenv" not in source, (
            "SearchManager should not use os.getenv() directly"
        )

        # The class should use config.py functions
        assert "load_all_provider_configs" in source, (
            "SearchManager should use load_all_provider_configs function"
        )

    def test_search_manager_fallback_chain_with_config(self, monkeypatch):
        """Should create correct fallback chain based on config availability."""
        # Set up partial environment (some providers available, some not)
        monkeypatch.setenv("SERPAPI_API_KEY", "test-serpapi-key")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
        # Don't set TAVILY_API_KEY or ANTHROPIC_API_KEY
        monkeypatch.setenv("TAVILY_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")

        # Create SearchManager
        manager = SearchManager()

        # Get fallback chain
        fallback_chain = manager.get_fallback_chain()

        # Should include providers with valid configs
        assert SearchProvider.DUCKDUCKGO in fallback_chain  # Always available
        assert SearchProvider.SERPAPI in fallback_chain  # Has API key
        assert SearchProvider.PERPLEXITY in fallback_chain  # Has API key

        # Should not include providers without API keys (or handle appropriately)
        # This depends on implementation - empty string might be treated as unavailable
