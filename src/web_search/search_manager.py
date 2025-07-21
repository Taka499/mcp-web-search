"""Search manager for coordinating different search providers."""

import asyncio

from .config import ProviderConfig, load_all_provider_configs
from .providers.base import BaseSearchProvider
from .providers.claude_provider import ClaudeProvider
from .providers.duckduckgo_provider import DuckDuckGoProvider
from .providers.perplexity_provider import PerplexityProvider
from .providers.serpapi_provider import SerpAPIProvider
from .providers.tavily_provider import TavilyProvider
from .search_types import SearchProvider, SearchResponse


class SearchManager:
    """Manages different search providers and routing."""

    # Provider class mapping
    PROVIDERS: dict[SearchProvider, type[BaseSearchProvider]] = {
        SearchProvider.SERPAPI: SerpAPIProvider,
        SearchProvider.PERPLEXITY: PerplexityProvider,
        SearchProvider.DUCKDUCKGO: DuckDuckGoProvider,
        SearchProvider.TAVILY: TavilyProvider,
        SearchProvider.CLAUDE: ClaudeProvider,
    }

    def __init__(
        self,
        default_provider: SearchProvider = SearchProvider.DUCKDUCKGO,
    ) -> None:
        self.default_provider = default_provider
        self._configs: dict[SearchProvider, ProviderConfig] = (
            load_all_provider_configs()
        )

    def get_available_providers(self) -> dict[str, bool]:
        """Get list of available providers and their status."""
        status = {}

        for provider in SearchProvider:
            config = self._configs[provider]

            # Check if provider is available
            if provider == SearchProvider.DUCKDUCKGO:
                # DuckDuckGo doesn't require API key
                status[provider.value] = True
            else:
                # Other providers require API keys
                status[provider.value] = bool(config.api_key)

        return status

    async def search(
        self,
        query: str,
        provider: SearchProvider | None = None,
        max_results: int | None = None,
    ) -> SearchResponse:
        """Perform search using specified or default provider."""
        # Use specified provider or fall back to default
        search_provider = provider or self.default_provider

        # Get provider configuration
        config = self._configs[search_provider].model_copy()

        # Override max_results if specified
        if max_results:
            config.max_results = max_results

        # Get provider class and perform search
        provider_class = self.PROVIDERS[search_provider]

        async with provider_class(config) as search_client:
            return await search_client.search(query)

    async def multi_provider_search(
        self,
        query: str,
        providers: list[SearchProvider],
        max_results_per_provider: int = 5,
    ) -> dict[str, SearchResponse]:
        """Perform search across multiple providers simultaneously."""

        async def search_single_provider(provider: SearchProvider):
            try:
                response = await self.search(
                    query=query,
                    provider=provider,
                    max_results=max_results_per_provider,
                )
                return provider.value, response
            except Exception as e:
                # Log error but continue with other providers
                return provider.value, SearchResponse(
                    query=query,
                    provider=provider,
                    results=[],
                    metadata={"error": str(e)},
                )

        # Execute all searches concurrently
        tasks = [search_single_provider(provider) for provider in providers]
        search_results = await asyncio.gather(*tasks)

        # Convert to dictionary
        results = dict(search_results)
        return results

    def get_fallback_chain(self) -> list[SearchProvider]:
        """Get fallback chain of providers to try in order."""
        available = self.get_available_providers()

        # Priority order: DuckDuckGo (free) -> SerpAPI -> Perplexity -> Tavily -> Claude
        fallback_order = [
            SearchProvider.DUCKDUCKGO,
            SearchProvider.SERPAPI,
            SearchProvider.PERPLEXITY,
            SearchProvider.TAVILY,
            SearchProvider.CLAUDE,
        ]

        return [p for p in fallback_order if available.get(p.value, False)]

    async def search_with_fallback(
        self,
        query: str,
        max_results: int = 10,
    ) -> SearchResponse:
        """Search with automatic fallback to other providers if primary fails."""
        fallback_chain = self.get_fallback_chain()

        last_error = None

        for provider in fallback_chain:
            try:
                return await self.search(query, provider, max_results)
            except Exception as e:
                last_error = e
                continue

        # If all providers failed, return error response
        return SearchResponse(
            query=query,
            provider=SearchProvider.DUCKDUCKGO,  # Default
            results=[],
            metadata={
                "error": f"All providers failed. Last error: {last_error!s}",
                "attempted_providers": [p.value for p in fallback_chain],
            },
        )
