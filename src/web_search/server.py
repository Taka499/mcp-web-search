"""Web Search MCP Server.

Provides web search functionality through multiple configurable providers.
"""

from mcp.server.fastmcp import FastMCP

from .search_manager import SearchManager
from .search_types import SearchProvider

# Initialize FastMCP server
mcp = FastMCP("web_search")

# Initialize search manager
search_manager = SearchManager(default_provider=SearchProvider.DUCKDUCKGO)


@mcp.tool()
async def search_web(
    query: str,
    provider: str = "duckduckgo",
    max_results: int = 10,
) -> dict:
    """Search the web using various search providers.

    Args:
        query: The search query string
        provider: Search provider to use (serpapi, perplexity, duckduckgo, tavily, claude)
        max_results: Maximum number of results to return (1-50)

    Returns:
        Dictionary containing search results with titles, URLs, snippets, and metadata

    """
    try:
        # Validate provider
        try:
            search_provider = SearchProvider(provider.lower())
        except ValueError:
            return {
                "error": f"Invalid provider '{provider}'. Available: {', '.join([p.value for p in SearchProvider])}",
            }

        # Validate max_results
        max_results = max(1, min(max_results, 50))

        # Perform search
        response = await search_manager.search(
            query=query,
            provider=search_provider,
            max_results=max_results,
        )

        # Convert to dictionary for JSON serialization
        return {
            "query": response.query,
            "provider": response.provider.value,
            "total_results": response.total_results,
            "search_time": response.search_time,
            "results": [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "source": result.source,
                    "published_date": result.published_date,
                    "metadata": result.metadata,
                }
                for result in response.results
            ],
            "metadata": response.metadata,
        }

    except Exception as e:
        return {
            "error": f"Search failed: {e!s}",
            "query": query,
            "provider": provider,
        }


@mcp.tool()
async def search_with_fallback(query: str, max_results: int = 10) -> dict:
    """Search the web with automatic fallback to other providers if primary fails.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (1-50)

    Returns:
        Dictionary containing search results from the first working provider

    """
    try:
        # Validate max_results
        max_results = max(1, min(max_results, 50))

        # Perform search with fallback
        response = await search_manager.search_with_fallback(
            query=query,
            max_results=max_results,
        )

        # Convert to dictionary for JSON serialization
        return {
            "query": response.query,
            "provider": response.provider.value,
            "total_results": response.total_results,
            "search_time": response.search_time,
            "results": [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "source": result.source,
                    "published_date": result.published_date,
                    "metadata": result.metadata,
                }
                for result in response.results
            ],
            "metadata": response.metadata,
        }

    except Exception as e:
        return {
            "error": f"Search with fallback failed: {e!s}",
            "query": query,
        }


@mcp.tool()
async def multi_provider_search(
    query: str,
    providers: list[str] = None,
    max_results_per_provider: int = 5,
) -> dict:
    """Search across multiple providers simultaneously for comparison.

    Args:
        query: The search query string
        providers: List of provider names to use. If None, uses all available providers
        max_results_per_provider: Maximum results per provider (1-20)

    Returns:
        Dictionary with results from each provider

    """
    try:
        # Default to all providers if none specified
        if providers is None:
            providers = [p.value for p in SearchProvider]

        # Validate providers
        search_providers = []
        for provider in providers:
            try:
                search_providers.append(SearchProvider(provider.lower()))
            except ValueError:
                continue  # Skip invalid providers

        if not search_providers:
            return {
                "error": f"No valid providers specified. Available: {', '.join([p.value for p in SearchProvider])}",
            }

        # Validate max_results
        max_results_per_provider = max(1, min(max_results_per_provider, 20))

        # Perform multi-provider search
        responses = await search_manager.multi_provider_search(
            query=query,
            providers=search_providers,
            max_results_per_provider=max_results_per_provider,
        )

        # Convert to dictionary for JSON serialization
        result = {
            "query": query,
            "providers": {},
        }

        for provider_name, response in responses.items():
            result["providers"][provider_name] = {
                "total_results": response.total_results,
                "search_time": response.search_time,
                "results": [
                    {
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.snippet,
                        "source": result.source,
                        "published_date": result.published_date,
                        "metadata": result.metadata,
                    }
                    for result in response.results
                ],
                "metadata": response.metadata,
            }

        return result

    except Exception as e:
        return {
            "error": f"Multi-provider search failed: {e!s}",
            "query": query,
        }


@mcp.tool()
async def get_available_providers() -> dict:
    """Get list of available search providers and their status.

    Returns:
        Dictionary showing which providers are available and configured

    """
    try:
        status = search_manager.get_available_providers()

        return {
            "providers": status,
            "default_provider": search_manager.default_provider.value,
            "fallback_chain": [p.value for p in search_manager.get_fallback_chain()],
            "total_available": sum(status.values()),
        }

    except Exception as e:
        return {
            "error": f"Failed to get provider status: {e!s}",
        }


if __name__ == "__main__":
    mcp.run()
