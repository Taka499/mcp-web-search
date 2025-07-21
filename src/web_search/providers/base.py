"""Base search provider interface."""

from abc import ABC, abstractmethod

import httpx

from web_search.config import ProviderConfig
from web_search.search_types import SearchResponse, SearchResult


class BaseSearchProvider(ABC):
    """Abstract base class for search providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    @abstractmethod
    async def search(self, query: str) -> SearchResponse:
        """Perform a search query and return results."""

    @abstractmethod
    def _validate_config(self) -> bool:
        """Validate provider-specific configuration."""

    def _create_response(
        self,
        query: str,
        results: list[SearchResult],
        total_results: int = None,
        search_time: float = None,
        metadata: dict = None,
    ) -> SearchResponse:
        """Create a standardized search response."""
        return SearchResponse(
            query=query,
            provider=self.config.provider,
            results=results,
            total_results=total_results or len(results),
            search_time=search_time,
            metadata=metadata or {},
        )

    async def _make_request(self, url: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with error handling."""
        try:
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.TimeoutException:
            raise Exception(f"Request timeout after {self.config.timeout} seconds")
        except Exception as e:
            raise Exception(f"Request failed: {e!s}")

    async def _make_post_request(self, url: str, **kwargs) -> httpx.Response:
        """Make an HTTP POST request with error handling."""
        try:
            response = await self.client.post(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.TimeoutException:
            raise Exception(f"Request timeout after {self.config.timeout} seconds")
        except Exception as e:
            raise Exception(f"Request failed: {e!s}")
