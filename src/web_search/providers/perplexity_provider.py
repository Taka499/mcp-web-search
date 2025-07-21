"""Perplexity API search provider implementation."""

import time

from web_search.search_types import SearchResponse, SearchResult

from .base import BaseSearchProvider


class PerplexityProvider(BaseSearchProvider):
    """Perplexity API search provider with AI-powered search and citations."""

    BASE_URL = "https://api.perplexity.ai/chat/completions"

    def _validate_config(self) -> bool:
        """Validate Perplexity API configuration."""
        if not self.config.api_key:
            raise ValueError("Perplexity API requires an API key")
        return True

    async def search(self, query: str) -> SearchResponse:
        """Perform search using Perplexity API."""
        self._validate_config()

        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        # Use sonar model for web search capability
        payload = {
            "model": self.config.perplexity_model,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a helpful search assistant. Provide comprehensive search results for the given query. Return up to {self.config.max_results} relevant results with titles, URLs, and descriptions.",
                },
                {"role": "user", "content": f"Search for: {query}"},
            ],
            "max_tokens": 2000,
            "temperature": 0.1,
            "return_citations": True,
            "return_images": False,
        }

        response = await self._make_post_request(
            self.BASE_URL,
            headers=headers,
            json=payload,
        )

        search_time = time.time() - start_time
        data = response.json()

        results = self._parse_results(data, query)

        metadata = {
            "model": self.config.perplexity_model,
            "usage": data.get("usage", {}),
            "citations": data.get("citations", []),
        }

        return self._create_response(
            query=query,
            results=results,
            search_time=search_time,
            metadata=metadata,
        )

    def _parse_results(self, data: dict, query: str) -> list[SearchResult]:
        """Parse Perplexity API response into SearchResult objects."""
        results = []

        # Extract content and citations from response
        choices = data.get("choices", [])
        if not choices:
            return results

        content = choices[0].get("message", {}).get("content", "")
        citations = data.get("citations", [])

        # If we have citations, use them as search results
        if citations:
            for i, citation in enumerate(citations[: self.config.max_results]):
                search_result = SearchResult(
                    title=citation.get("title", f"Result {i + 1}"),
                    url=citation.get("url", ""),
                    snippet=citation.get("text", "")[:200] + "...",
                    source=citation.get("source"),
                    metadata={
                        "citation_index": i,
                        "relevance_score": citation.get("score"),
                        "type": "citation",
                    },
                )
                results.append(search_result)
        else:
            # Fallback: create a single result from the AI response
            search_result = SearchResult(
                title=f"AI Summary for: {query}",
                url="",
                snippet=content[:300] + "..." if len(content) > 300 else content,
                source="Perplexity AI",
                metadata={"type": "ai_summary", "full_content": content},
            )
            results.append(search_result)

        return results
