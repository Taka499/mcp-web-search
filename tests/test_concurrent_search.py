"""Test concurrent behavior in SearchManager.multi_provider_search."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from web_search.search_manager import SearchManager
from web_search.search_types import SearchProvider, SearchResponse


class TestConcurrentMultiProviderSearch:
    """Test concurrent execution in multi_provider_search."""

    @pytest.mark.asyncio
    async def test_multi_provider_search_executes_concurrently(self):
        """Test that multi_provider_search executes provider searches concurrently."""
        manager = SearchManager()

        # Mock the individual search calls to track timing
        async def mock_search(*args, **kwargs):
            provider = kwargs.get("provider")
            # Simulate delay - if concurrent, both should run simultaneously
            await asyncio.sleep(0.1)

            return SearchResponse(
                query=kwargs.get("query", "test"),
                provider=provider,
                results=[],
                search_time=0.1,
            )

        with patch.object(manager, "search", side_effect=mock_search):
            start_time = time.time()

            # Search with two providers
            results = await manager.multi_provider_search(
                query="test query",
                providers=[SearchProvider.DUCKDUCKGO, SearchProvider.SERPAPI],
                max_results_per_provider=5,
            )

            total_time = time.time() - start_time

            # CRITICAL: If concurrent, total time should be ~0.1s
            # If sequential, total time would be ~0.2s
            assert total_time < 0.15, (
                f"Expected concurrent execution (~0.1s), but took {total_time:.3f}s"
            )

    @pytest.mark.asyncio
    async def test_multi_provider_search_handles_concurrent_errors(self):
        """Test that concurrent execution properly handles errors from individual providers."""
        manager = SearchManager()

        async def mock_search(*args, **kwargs):
            provider = kwargs.get("provider")
            # Make one provider fail, one succeed
            if provider == SearchProvider.DUCKDUCKGO:
                raise Exception("DuckDuckGo search failed")
            else:
                await asyncio.sleep(0.1)  # Simulate delay
                return SearchResponse(
                    query=kwargs.get("query", "test"),
                    provider=provider,
                    results=[],
                    search_time=0.1,
                )

        with patch.object(manager, "search", side_effect=mock_search):
            results = await manager.multi_provider_search(
                query="test query",
                providers=[SearchProvider.DUCKDUCKGO, SearchProvider.SERPAPI],
                max_results_per_provider=5,
            )

            # Both providers should return results, even if one failed
            assert len(results) == 2
            assert SearchProvider.DUCKDUCKGO.value in results
            assert SearchProvider.SERPAPI.value in results

            # Failed provider should have error in metadata
            ddg_result = results[SearchProvider.DUCKDUCKGO.value]
            assert "error" in ddg_result.metadata
            assert "DuckDuckGo search failed" in ddg_result.metadata["error"]

            # Successful provider should have normal results
            serpapi_result = results[SearchProvider.SERPAPI.value]
            assert "error" not in serpapi_result.metadata
            assert serpapi_result.search_time == 0.1
