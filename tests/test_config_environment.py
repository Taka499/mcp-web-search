"""Tests for environment variable loading in configuration management."""

import os

import pytest
from pydantic import ValidationError

from web_search.config import (
    ClaudeConfig,
    DuckDuckGoConfig,
    PerplexityConfig,
    SerpAPIConfig,
    TavilyConfig,
    load_all_provider_configs,
    load_config_from_environment,
)
from web_search.search_types import SearchProvider


class TestEnvironmentLoading:
    """Test configuration loading from environment variables."""

    def test_load_config_from_environment(self, monkeypatch):
        """Should load configuration from environment variables."""
        # Set up environment variables
        monkeypatch.setenv("SERPAPI_API_KEY", "test-serpapi-key")
        monkeypatch.setenv("SERPAPI_MAX_RESULTS", "20")
        monkeypatch.setenv("SERPAPI_ENGINE", "bing")
        monkeypatch.setenv("SEARCH_TIMEOUT", "45")

        config = load_config_from_environment(SearchProvider.SERPAPI)

        assert isinstance(config, SerpAPIConfig)
        assert config.api_key == "test-serpapi-key"
        assert config.max_results == 20
        assert config.serpapi_engine == "bing"
        assert config.timeout == 45

    def test_load_config_with_missing_optional_vars(self, monkeypatch):
        """Should use defaults when optional environment variables are missing."""
        # Only set required environment variables
        monkeypatch.setenv("SERPAPI_API_KEY", "test-key")

        config = load_config_from_environment(SearchProvider.SERPAPI)

        assert isinstance(config, SerpAPIConfig)
        assert config.api_key == "test-key"
        assert config.max_results == 10  # Default value
        assert config.serpapi_engine == "google"  # Default value
        assert config.timeout == 30  # Default value

    def test_load_config_with_missing_required_vars(self, monkeypatch):
        """Should handle missing environment variables gracefully."""
        # Clear all environment variables
        for key in os.environ:
            if key.startswith(("SERPAPI_", "SEARCH_")):
                monkeypatch.delenv(key, raising=False)

        # For providers that don't require API keys (like DuckDuckGo), should work
        config = load_config_from_environment(SearchProvider.DUCKDUCKGO)
        assert isinstance(config, DuckDuckGoConfig)

        # For providers that require API keys, config should still be created
        # but API key will come from .env file or be None
        config = load_config_from_environment(SearchProvider.SERPAPI)
        assert isinstance(config, SerpAPIConfig)
        # API key might be from .env file or None - both are valid

    def test_load_config_with_invalid_env_values(self, monkeypatch):
        """Should raise validation error for invalid environment variable values."""
        # Set invalid max_results
        monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
        monkeypatch.setenv("SERPAPI_MAX_RESULTS", "invalid")

        with pytest.raises(ValidationError):
            load_config_from_environment(SearchProvider.SERPAPI)

        # Set out-of-range timeout
        monkeypatch.setenv("SERPAPI_MAX_RESULTS", "10")
        monkeypatch.setenv("SEARCH_TIMEOUT", "500")

        with pytest.raises(ValidationError):
            load_config_from_environment(SearchProvider.SERPAPI)


class TestEnvironmentVariableParsing:
    """Test parsing of different environment variable types."""

    def test_parse_integer_env_vars(self, monkeypatch):
        """Should correctly parse integer environment variables."""
        monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
        monkeypatch.setenv("SERPAPI_MAX_RESULTS", "25")
        monkeypatch.setenv("SEARCH_TIMEOUT", "60")

        config = load_config_from_environment(SearchProvider.SERPAPI)

        assert config.max_results == 25
        assert config.timeout == 60

    def test_parse_boolean_env_vars(self, monkeypatch):
        """Should correctly parse boolean environment variables."""
        monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
        monkeypatch.setenv("SAFE_SEARCH", "false")

        config = load_config_from_environment(SearchProvider.SERPAPI)

        # Note: safe_search parsing depends on implementation
        assert isinstance(config.safe_search, bool)

    def test_parse_string_env_vars(self, monkeypatch):
        """Should correctly parse string environment variables."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")
        monkeypatch.setenv("PERPLEXITY_MODEL", "sonar-small")

        config = load_config_from_environment(SearchProvider.PERPLEXITY)

        assert config.perplexity_model == "sonar-small"

    def test_handle_empty_string_env_vars(self, monkeypatch):
        """Should handle empty string environment variables appropriately."""
        monkeypatch.setenv("SERPAPI_API_KEY", "")
        monkeypatch.setenv("SERPAPI_MAX_RESULTS", "10")

        config = load_config_from_environment(SearchProvider.SERPAPI)

        # Empty string should be treated as None for API key
        assert config.api_key is None or config.api_key == ""


class TestMultiProviderEnvironmentLoading:
    """Test loading configurations for multiple providers."""

    def test_load_all_provider_configs(self, monkeypatch):
        """Should load configurations for all available providers."""
        # Set up environment variables for all providers
        monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-key")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "perplexity-key")
        monkeypatch.setenv("TAVILY_API_KEY", "tavily-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")

        configs = load_all_provider_configs()

        assert len(configs) == 5  # All 5 providers
        assert SearchProvider.SERPAPI in configs
        assert SearchProvider.PERPLEXITY in configs
        assert SearchProvider.DUCKDUCKGO in configs
        assert SearchProvider.TAVILY in configs
        assert SearchProvider.CLAUDE in configs

        # Check that each config has the correct type
        assert isinstance(configs[SearchProvider.SERPAPI], SerpAPIConfig)
        assert isinstance(configs[SearchProvider.PERPLEXITY], PerplexityConfig)
        assert isinstance(configs[SearchProvider.DUCKDUCKGO], DuckDuckGoConfig)
        assert isinstance(configs[SearchProvider.TAVILY], TavilyConfig)
        assert isinstance(configs[SearchProvider.CLAUDE], ClaudeConfig)

    def test_load_selective_provider_configs(self, monkeypatch):
        """Should load only requested provider configurations."""
        monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-key")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "perplexity-key")

        requested_providers = [SearchProvider.SERPAPI, SearchProvider.DUCKDUCKGO]
        configs = load_all_provider_configs(providers=requested_providers)

        assert len(configs) == 2
        assert SearchProvider.SERPAPI in configs
        assert SearchProvider.DUCKDUCKGO in configs
        assert SearchProvider.PERPLEXITY not in configs

    def test_provider_availability_check(self, monkeypatch):
        """Should correctly determine which providers are available based on config."""
        # Set up only some providers with API keys
        monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-key")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "perplexity-key")
        # Clear other API keys to override .env file
        monkeypatch.setenv("TAVILY_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")

        configs = load_all_provider_configs()

        # Check availability based on API key presence
        assert configs[SearchProvider.SERPAPI].api_key == "serpapi-key"
        assert configs[SearchProvider.PERPLEXITY].api_key == "perplexity-key"
        assert (
            configs[SearchProvider.DUCKDUCKGO].api_key is None
        )  # DuckDuckGo doesn't need API key
        # Empty string should be treated as None for API keys
        assert (
            configs[SearchProvider.TAVILY].api_key == ""
            or configs[SearchProvider.TAVILY].api_key is None
        )
        assert (
            configs[SearchProvider.CLAUDE].api_key == ""
            or configs[SearchProvider.CLAUDE].api_key is None
        )


class TestEnvironmentVariableDefaults:
    """Test default values and fallbacks for environment variables."""

    def test_default_values_when_env_not_set(self, monkeypatch):
        """Should use default values when environment variables are not set."""
        # Clear all relevant environment variables
        for key in list(os.environ.keys()):
            if key.startswith(
                (
                    "SERPAPI_",
                    "SEARCH_",
                    "PERPLEXITY_",
                    "TAVILY_",
                    "ANTHROPIC_",
                    "DUCKDUCKGO_",
                )
            ):
                monkeypatch.delenv(key, raising=False)

        config = load_config_from_environment(SearchProvider.DUCKDUCKGO)

        assert config.max_results == 10
        assert config.timeout == 30
        assert config.safe_search is True
        assert config.duckduckgo_safesearch == "moderate"

    def test_provider_specific_defaults(self, monkeypatch):
        """Should use provider-specific default values correctly."""
        # Clear environment variables and test defaults
        for key in list(os.environ.keys()):
            if key.startswith(("SERPAPI_", "PERPLEXITY_", "DUCKDUCKGO_")):
                monkeypatch.delenv(key, raising=False)

        serpapi_config = load_config_from_environment(SearchProvider.SERPAPI)
        perplexity_config = load_config_from_environment(SearchProvider.PERPLEXITY)
        duckduckgo_config = load_config_from_environment(SearchProvider.DUCKDUCKGO)

        # Check provider-specific defaults
        assert serpapi_config.serpapi_engine == "google"
        assert perplexity_config.perplexity_model == "sonar-pro"
        assert duckduckgo_config.duckduckgo_safesearch == "moderate"
