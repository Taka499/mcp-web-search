"""DuckDuckGo search provider implementation."""

import time
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from web_search.search_types import SearchResponse, SearchResult

from .base import BaseSearchProvider


class DuckDuckGoProvider(BaseSearchProvider):
    """DuckDuckGo search provider using unofficial API."""

    BASE_URL = "https://html.duckduckgo.com/html"
    INSTANT_ANSWER_URL = "https://api.duckduckgo.com/"

    def _validate_config(self) -> bool:
        """Validate DuckDuckGo configuration (no API key required)."""
        return True

    async def search(self, query: str) -> SearchResponse:
        """Perform search using DuckDuckGo."""
        start_time = time.time()

        # Try instant answers first
        instant_results = await self._get_instant_answers(query)

        # Get web search results
        web_results = await self._get_web_results(query)

        search_time = time.time() - start_time

        # Combine results
        all_results = instant_results + web_results
        results = all_results[: self.config.max_results]

        metadata = {
            "instant_answers_count": len(instant_results),
            "web_results_count": len(web_results),
            "safesearch": self.config.duckduckgo_safesearch,
        }

        return self._create_response(
            query=query,
            results=results,
            search_time=search_time,
            metadata=metadata,
        )

    async def _get_instant_answers(self, query: str) -> list[SearchResult]:
        """Get instant answers from DuckDuckGo API."""
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }

            url = f"{self.INSTANT_ANSWER_URL}?{urlencode(params)}"
            response = await self._make_request(url)
            data = response.json()

            results = []

            # Abstract (Wikipedia-style results)
            if data.get("Abstract"):
                result = SearchResult(
                    title=data.get("Heading", query),
                    url=data.get("AbstractURL", ""),
                    snippet=data.get("Abstract", ""),
                    source=data.get("AbstractSource", ""),
                    metadata={"type": "abstract", "image": data.get("Image")},
                )
                results.append(result)

            # Answer (direct answers)
            if data.get("Answer"):
                result = SearchResult(
                    title=f"Answer: {query}",
                    url="",
                    snippet=data.get("Answer", ""),
                    source=data.get("AnswerType", "DuckDuckGo"),
                    metadata={"type": "answer", "answer_type": data.get("AnswerType")},
                )
                results.append(result)

            # Related topics
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    result = SearchResult(
                        title=topic.get("Text", "").split(" - ")[0],
                        url=topic.get("FirstURL", ""),
                        snippet=topic.get("Text", ""),
                        source="DuckDuckGo",
                        metadata={
                            "type": "related_topic",
                            "icon": topic.get("Icon", {}).get("URL"),
                        },
                    )
                    results.append(result)

            return results

        except Exception:
            # If instant answers fail, continue with web search
            return []

    async def _get_web_results(self, query: str) -> list[SearchResult]:
        """Get web search results from DuckDuckGo HTML."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            }

            params = {"q": query, "safesearch": self.config.duckduckgo_safesearch}

            url = f"{self.BASE_URL}?{urlencode(params)}"
            response = await self._make_request(url, headers=headers)

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Parse search results
            result_divs = soup.find_all("div", class_="result")

            for div in result_divs[: self.config.max_results]:
                try:
                    # Extract title and URL
                    title_link = div.find("a", class_="result__a")
                    if not title_link:
                        continue

                    title = title_link.get_text(strip=True)
                    url = title_link.get("href", "")

                    # Extract snippet
                    snippet_div = div.find("a", class_="result__snippet")
                    snippet = snippet_div.get_text(strip=True) if snippet_div else ""

                    # Extract displayed URL
                    url_div = div.find("span", class_="result__url")
                    displayed_url = url_div.get_text(strip=True) if url_div else ""

                    result = SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source="DuckDuckGo",
                        metadata={"type": "web_result", "displayed_url": displayed_url},
                    )
                    results.append(result)

                except Exception:
                    # Skip malformed results
                    continue

            return results

        except Exception:
            # Return empty results if web search fails
            return []
