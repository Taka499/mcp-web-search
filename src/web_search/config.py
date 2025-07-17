"""Centralized configuration management for web search providers."""

from pydantic import BaseModel, Field

from .search_types import SearchProvider


class Config(BaseModel):
    """Base configuration model for all search providers."""

    max_results: int = Field(default=10, ge=1, le=100)
    safe_search: bool = True
    timeout: int = Field(default=30, ge=1, le=300)
    region: str | None = None
    language: str | None = None


class SerpAPIConfig(Config):
    """Configuration for SerpAPI provider."""

    provider: SearchProvider = SearchProvider.SERPAPI
    api_key: str | None = None
    serpapi_engine: str = "google"


class PerplexityConfig(Config):
    """Configuration for Perplexity provider."""

    provider: SearchProvider = SearchProvider.PERPLEXITY
    api_key: str | None = None
    perplexity_model: str = "sonar-pro"


class DuckDuckGoConfig(Config):
    """Configuration for DuckDuckGo provider."""

    provider: SearchProvider = SearchProvider.DUCKDUCKGO
    api_key: str | None = None
    duckduckgo_safesearch: str = "moderate"


class TavilyConfig(Config):
    """Configuration for Tavily provider."""

    provider: SearchProvider = SearchProvider.TAVILY
    api_key: str | None = None


class ClaudeConfig(Config):
    """Configuration for Claude provider."""

    provider: SearchProvider = SearchProvider.CLAUDE
    api_key: str | None = None
