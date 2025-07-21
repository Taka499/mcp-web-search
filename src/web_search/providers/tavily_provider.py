"""Tavily AI search provider implementation."""

import time

from web_search.search_types import SearchResponse, SearchResult

from .base import BaseSearchProvider


class TavilyProvider(BaseSearchProvider):
    """Tavily AI search provider for real-time search results."""

    BASE_URL = "https://api.tavily.com/search"

    def _validate_config(self) -> bool:
        """Validate Tavily API configuration."""
        if not self.config.api_key:
            raise ValueError("Tavily API requires an API key")
        return True

    async def search(self, query: str) -> SearchResponse:
        """Perform search using Tavily API."""
        self._validate_config()

        start_time = time.time()

        headers = {"Content-Type": "application/json"}

        payload = {
            "api_key": self.config.api_key,
            "query": query,
            "search_depth": "advanced",  # basic or advanced
            "include_answer": True,
            "include_raw_content": False,
            "max_results": self.config.max_results,
            "include_domains": [],
            "exclude_domains": [],
        }

        # Add language if specified
        if self.config.language:
            payload["language"] = self.config.language

        response = await self._make_post_request(
            self.BASE_URL,
            headers=headers,
            json=payload,
        )

        search_time = time.time() - start_time
        data = response.json()

        results = self._parse_results(data)

        metadata = {
            "answer": data.get("answer"),
            "follow_up_questions": data.get("follow_up_questions", []),
            "search_depth": "advanced",
            "response_time": data.get("response_time"),
        }

        return self._create_response(
            query=query,
            results=results,
            search_time=search_time,
            metadata=metadata,
        )

    def _parse_results(self, data: dict) -> list[SearchResult]:
        """Parse Tavily API response into SearchResult objects."""
        results = []

        # Add AI-generated answer as first result if available
        if data.get("answer"):
            answer_result = SearchResult(
                title="AI Answer",
                url="",
                snippet=data["answer"],
                source="Tavily AI",
                metadata={
                    "type": "ai_answer",
                    "follow_up_questions": data.get("follow_up_questions", []),
                },
            )
            results.append(answer_result)

        # Parse search results
        search_results = data.get("results", [])
        for result in search_results:
            search_result = SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                snippet=result.get("content", ""),
                source=result.get("source"),
                published_date=result.get("published_date"),
                metadata={
                    "score": result.get("score"),
                    "raw_content": result.get("raw_content"),
                    "type": "search_result",
                },
            )
            results.append(search_result)

        return results[: self.config.max_results]
