"""Tests for centralized configuration management."""

import pytest
from pydantic import ValidationError

from web_search.config import (
    ClaudeConfig,
    Config,
    DuckDuckGoConfig,
    PerplexityConfig,
    SerpAPIConfig,
    TavilyConfig,
)
from web_search.search_types import SearchProvider


class TestBasicConfigModel:
    """Test basic configuration model functionality."""

    def test_config_basic_model_creation(self):
        """Should create a basic config model with default values."""
        config = Config()

        assert config.max_results == 10
        assert config.safe_search is True
        assert config.timeout == 30
        assert config.region is None
        assert config.language is None

    def test_config_model_with_valid_values(self):
        """Should accept valid configuration values."""
        config = Config(
            max_results=20,
            safe_search=False,
            timeout=45,
            region="us",
            language="en",
        )

        assert config.max_results == 20
        assert config.safe_search is False
        assert config.timeout == 45
        assert config.region == "us"
        assert config.language == "en"

    def test_config_model_rejects_invalid_values(self):
        """Should reject invalid configuration values with clear error messages."""
        # Test invalid max_results (out of range)
        with pytest.raises(ValidationError) as exc_info:
            Config(max_results=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            Config(max_results=101)
        assert "less than or equal to 100" in str(exc_info.value)

        # Test invalid timeout (out of range)
        with pytest.raises(ValidationError) as exc_info:
            Config(timeout=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            Config(timeout=301)
        assert "less than or equal to 300" in str(exc_info.value)


class TestProviderSpecificConfigs:
    """Test provider-specific configuration models."""

    def test_serpapi_config_creation(self):
        """Should create SerpAPI config with provider-specific fields."""
        config = SerpAPIConfig(api_key="test-key")

        assert config.provider == SearchProvider.SERPAPI
        assert config.api_key == "test-key"
        assert config.serpapi_engine == "google"
        assert config.max_results == 10
        assert config.timeout == 30

    def test_perplexity_config_creation(self):
        """Should create Perplexity config with model selection."""
        config = PerplexityConfig(api_key="test-key")

        assert config.provider == SearchProvider.PERPLEXITY
        assert config.api_key == "test-key"
        assert config.perplexity_model == "sonar-pro"
        assert config.max_results == 10
        assert config.timeout == 30

    def test_duckduckgo_config_creation(self):
        """Should create DuckDuckGo config without requiring API key."""
        config = DuckDuckGoConfig()

        assert config.provider == SearchProvider.DUCKDUCKGO
        assert config.api_key is None
        assert config.duckduckgo_safesearch == "moderate"
        assert config.max_results == 10
        assert config.timeout == 30

    def test_tavily_config_creation(self):
        """Should create Tavily config with required API key."""
        config = TavilyConfig(api_key="test-key")

        assert config.provider == SearchProvider.TAVILY
        assert config.api_key == "test-key"
        assert config.max_results == 10
        assert config.timeout == 30

    def test_claude_config_creation(self):
        """Should create Claude config with Anthropic API key."""
        config = ClaudeConfig(api_key="test-key")

        assert config.provider == SearchProvider.CLAUDE
        assert config.api_key == "test-key"
        assert config.max_results == 10
        assert config.timeout == 30


class TestConfigValidation:
    """Test configuration validation rules."""

    def test_max_results_validation(self):
        """Should validate max_results is within bounds (1-100)."""
        # Valid values
        Config(max_results=1)
        Config(max_results=50)
        Config(max_results=100)

        # Invalid values
        with pytest.raises(ValidationError):
            Config(max_results=0)
        with pytest.raises(ValidationError):
            Config(max_results=101)

    def test_timeout_validation(self):
        """Should validate timeout is within bounds (1-300)."""
        # Valid values
        Config(timeout=1)
        Config(timeout=150)
        Config(timeout=300)

        # Invalid values
        with pytest.raises(ValidationError):
            Config(timeout=0)
        with pytest.raises(ValidationError):
            Config(timeout=301)

    def test_provider_specific_field_validation(self):
        """Should validate provider-specific fields like serpapi_engine."""
        # Valid SerpAPI engine
        SerpAPIConfig(api_key="test", serpapi_engine="google")
        SerpAPIConfig(api_key="test", serpapi_engine="bing")

        # Valid Perplexity model
        PerplexityConfig(api_key="test", perplexity_model="sonar-pro")
        PerplexityConfig(api_key="test", perplexity_model="sonar-small")

        # Valid DuckDuckGo safesearch
        DuckDuckGoConfig(duckduckgo_safesearch="strict")
        DuckDuckGoConfig(duckduckgo_safesearch="moderate")
        DuckDuckGoConfig(duckduckgo_safesearch="off")
