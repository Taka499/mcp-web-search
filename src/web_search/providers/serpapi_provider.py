"""SerpAPI search provider implementation."""

import time
from urllib.parse import urlencode

from web_search.search_types import SearchResponse, SearchResult

from .base import BaseSearchProvider


class SerpAPIProvider(BaseSearchProvider):
    """SerpAPI search provider for Google, Bing, DuckDuckGo and other engines."""

    BASE_URL = "https://serpapi.com/search"

    def _validate_config(self) -> bool:
        """Validate SerpAPI configuration."""
        if not self.config.api_key:
            raise ValueError("SerpAPI requires an API key")
        return True

    async def search(self, query: str) -> SearchResponse:
        """Perform search using SerpAPI."""
        self._validate_config()

        start_time = time.time()

        params = {
            "q": query,
            "api_key": self.config.api_key,
            "engine": self.config.serpapi_engine,
            "num": str(self.config.max_results),
            "safe": "active" if self.config.safe_search else "off",
        }

        if self.config.region:
            params["gl"] = self.config.region
        if self.config.language:
            params["hl"] = self.config.language

        url = f"{self.BASE_URL}?{urlencode(params)}"
        response = await self._make_request(url)

        search_time = time.time() - start_time
        data = response.json()

        results = self._parse_results(data)
        total_results = data.get("search_information", {}).get("total_results")

        metadata = {
            "engine": self.config.serpapi_engine,
            "search_parameters": data.get("search_parameters", {}),
            "search_information": data.get("search_information", {}),
        }

        return self._create_response(
            query=query,
            results=results,
            total_results=total_results,
            search_time=search_time,
            metadata=metadata,
        )

    def _parse_results(self, data: dict) -> list[SearchResult]:
        """Parse SerpAPI response into SearchResult objects."""
        results = []

        # Parse organic results
        organic_results = data.get("organic_results", [])
        for result in organic_results:
            search_result = SearchResult(
                title=result.get("title", ""),
                url=result.get("link", ""),
                snippet=result.get("snippet", ""),
                source=result.get("source"),
                published_date=result.get("date"),
                metadata={
                    "position": result.get("position"),
                    "displayed_link": result.get("displayed_link"),
                    "cached_page_link": result.get("cached_page_link"),
                },
            )
            results.append(search_result)

        # Parse news results if available
        news_results = data.get("news_results", [])
        for result in news_results:
            search_result = SearchResult(
                title=result.get("title", ""),
                url=result.get("link", ""),
                snippet=result.get("snippet", ""),
                source=result.get("source"),
                published_date=result.get("date"),
                metadata={
                    "position": result.get("position"),
                    "thumbnail": result.get("thumbnail"),
                    "type": "news",
                },
            )
            results.append(search_result)

        return results[: self.config.max_results]
