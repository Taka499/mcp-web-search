"""Centralized configuration management for web search providers."""

from typing import Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings

from .search_types import SearchProvider


class Config(BaseModel):
    """Base configuration model for all search providers."""

    max_results: int = Field(default=10, ge=1, le=100)
    safe_search: bool = True
    timeout: int = Field(default=30, ge=1, le=300)
    region: str | None = None
    language: str | None = None


class ProviderConfig(BaseSettings):
    """Base settings class for provider-specific configuration."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables
    )


class SerpAPIConfig(ProviderConfig):
    """Configuration for SerpAPI provider."""

    provider: SearchProvider = SearchProvider.SERPAPI
    api_key: str | None = Field(default=None, alias="SERPAPI_API_KEY")
    serpapi_engine: str = Field(default="google", alias="SERPAPI_ENGINE")
    max_results: int = Field(default=10, ge=1, le=100, alias="SERPAPI_MAX_RESULTS")
    timeout: int = Field(default=30, ge=1, le=300, alias="SEARCH_TIMEOUT")
    safe_search: bool = Field(default=True, alias="SAFE_SEARCH")
    region: str | None = Field(default=None, alias="REGION")
    language: str | None = Field(default=None, alias="LANGUAGE")


class PerplexityConfig(ProviderConfig):
    """Configuration for Perplexity provider."""

    provider: SearchProvider = SearchProvider.PERPLEXITY
    api_key: str | None = Field(default=None, alias="PERPLEXITY_API_KEY")
    perplexity_model: str = Field(default="sonar-pro", alias="PERPLEXITY_MODEL")
    max_results: int = Field(default=10, ge=1, le=100, alias="PERPLEXITY_MAX_RESULTS")
    timeout: int = Field(default=30, ge=1, le=300, alias="SEARCH_TIMEOUT")
    safe_search: bool = Field(default=True, alias="SAFE_SEARCH")
    region: str | None = Field(default=None, alias="REGION")
    language: str | None = Field(default=None, alias="LANGUAGE")


class DuckDuckGoConfig(ProviderConfig):
    """Configuration for DuckDuckGo provider."""

    provider: SearchProvider = SearchProvider.DUCKDUCKGO
    api_key: str | None = None  # DuckDuckGo doesn't need API key
    duckduckgo_safesearch: str = Field(
        default="moderate", alias="DUCKDUCKGO_SAFESEARCH"
    )
    max_results: int = Field(default=10, ge=1, le=100, alias="DUCKDUCKGO_MAX_RESULTS")
    timeout: int = Field(default=30, ge=1, le=300, alias="SEARCH_TIMEOUT")
    safe_search: bool = Field(default=True, alias="SAFE_SEARCH")
    region: str | None = Field(default=None, alias="REGION")
    language: str | None = Field(default=None, alias="LANGUAGE")


class TavilyConfig(ProviderConfig):
    """Configuration for Tavily provider."""

    provider: SearchProvider = SearchProvider.TAVILY
    api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    max_results: int = Field(default=10, ge=1, le=100, alias="TAVILY_MAX_RESULTS")
    timeout: int = Field(default=30, ge=1, le=300, alias="SEARCH_TIMEOUT")
    safe_search: bool = Field(default=True, alias="SAFE_SEARCH")
    region: str | None = Field(default=None, alias="REGION")
    language: str | None = Field(default=None, alias="LANGUAGE")


class ClaudeConfig(ProviderConfig):
    """Configuration for Claude provider."""

    provider: SearchProvider = SearchProvider.CLAUDE
    api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    max_results: int = Field(default=10, ge=1, le=100, alias="CLAUDE_MAX_RESULTS")
    timeout: int = Field(default=30, ge=1, le=300, alias="SEARCH_TIMEOUT")
    safe_search: bool = Field(default=True, alias="SAFE_SEARCH")
    region: str | None = Field(default=None, alias="REGION")
    language: str | None = Field(default=None, alias="LANGUAGE")


# Factory functions for loading configurations
def load_config_from_environment(
    provider: SearchProvider,
) -> Union[ProviderConfig, None]:
    """Load configuration for a specific provider from environment variables."""
    config_classes = {
        SearchProvider.SERPAPI: SerpAPIConfig,
        SearchProvider.PERPLEXITY: PerplexityConfig,
        SearchProvider.DUCKDUCKGO: DuckDuckGoConfig,
        SearchProvider.TAVILY: TavilyConfig,
        SearchProvider.CLAUDE: ClaudeConfig,
    }

    config_class = config_classes.get(provider)
    if config_class is None:
        return None

    return config_class()


def load_all_provider_configs(
    providers: list[SearchProvider] = None,
) -> dict[SearchProvider, ProviderConfig]:
    """Load configurations for all or specified providers from environment variables."""
    if providers is None:
        providers = list(SearchProvider)

    configs = {}
    for provider in providers:
        config = load_config_from_environment(provider)
        if config is not None:
            configs[provider] = config

    return configs
