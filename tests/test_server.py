"""Tests for the web search MCP server."""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from web_search.server import search_web, search_with_fallback, multi_provider_search, get_available_providers
from web_search.search_types import SearchProvider, SearchResult, SearchResponse, SearchConfig
from web_search.search_manager import SearchManager


class TestSearchWebTool:
    """Test the search_web MCP tool."""
    
    @pytest.mark.asyncio
    async def test_search_web_success(self, mock_search_response):
        """Test successful web search."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search = AsyncMock(return_value=mock_search_response)
            
            result = await search_web(
                query="test query",
                provider="duckduckgo",
                max_results=5
            )
            
            assert "error" not in result
            assert result["query"] == "test query"
            assert result["provider"] == "duckduckgo"
            assert result["total_results"] == 1
            assert len(result["results"]) == 1
            assert result["results"][0]["title"] == "Test Result"
            assert result["results"][0]["url"] == "https://example.com"
            
            mock_manager.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_web_invalid_provider(self):
        """Test search with invalid provider."""
        result = await search_web(
            query="test query",
            provider="invalid_provider",
            max_results=5
        )
        
        assert "error" in result
        assert "Invalid provider" in result["error"]
        assert "invalid_provider" in result["error"]
    
    @pytest.mark.asyncio
    async def test_search_web_max_results_validation(self, mock_search_response):
        """Test max_results parameter validation."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search = AsyncMock(return_value=mock_search_response)
            
            # Test negative value gets clamped to 1
            result = await search_web(
                query="test query",
                provider="duckduckgo",
                max_results=-5
            )
            
            assert "error" not in result
            # Verify search was called with clamped value
            call_args = mock_manager.search.call_args
            assert call_args[1]["max_results"] == 1
            
            # Test value > 50 gets clamped to 50
            await search_web(
                query="test query",
                provider="duckduckgo",
                max_results=100
            )
            
            call_args = mock_manager.search.call_args
            assert call_args[1]["max_results"] == 50
    
    @pytest.mark.asyncio
    async def test_search_web_exception_handling(self):
        """Test exception handling in search_web."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search = AsyncMock(side_effect=Exception("Search failed"))
            
            result = await search_web(
                query="test query",
                provider="duckduckgo",
                max_results=5
            )
            
            assert "error" in result
            assert "Search failed" in result["error"]
            assert result["query"] == "test query"
            assert result["provider"] == "duckduckgo"
    
    @pytest.mark.asyncio
    async def test_search_web_default_parameters(self, mock_search_response):
        """Test search_web with default parameters."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search = AsyncMock(return_value=mock_search_response)
            
            result = await search_web(query="test query")
            
            assert "error" not in result
            call_args = mock_manager.search.call_args
            assert call_args[1]["provider"] == SearchProvider.DUCKDUCKGO
            assert call_args[1]["max_results"] == 10


class TestSearchWithFallbackTool:
    """Test the search_with_fallback MCP tool."""
    
    @pytest.mark.asyncio
    async def test_search_with_fallback_success(self, mock_search_response):
        """Test successful search with fallback."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search_with_fallback = AsyncMock(return_value=mock_search_response)
            
            result = await search_with_fallback(
                query="test query",
                max_results=5
            )
            
            assert "error" not in result
            assert result["query"] == "test query"
            assert result["provider"] == "duckduckgo"
            assert len(result["results"]) == 1
            
            mock_manager.search_with_fallback.assert_called_once_with(
                query="test query",
                max_results=5
            )
    
    @pytest.mark.asyncio
    async def test_search_with_fallback_exception(self):
        """Test exception handling in search_with_fallback."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search_with_fallback = AsyncMock(
                side_effect=Exception("All providers failed")
            )
            
            result = await search_with_fallback(
                query="test query",
                max_results=5
            )
            
            assert "error" in result
            assert "All providers failed" in result["error"]
            assert result["query"] == "test query"
    
    @pytest.mark.asyncio
    async def test_search_with_fallback_max_results_validation(self, mock_search_response):
        """Test max_results validation in search_with_fallback."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search_with_fallback = AsyncMock(return_value=mock_search_response)
            
            # Test clamping
            await search_with_fallback(query="test", max_results=100)
            call_args = mock_manager.search_with_fallback.call_args
            assert call_args[1]["max_results"] == 50


class TestMultiProviderSearchTool:
    """Test the multi_provider_search MCP tool."""
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_success(self, mock_search_response):
        """Test successful multi-provider search."""
        mock_responses = {
            "duckduckgo": mock_search_response,
            "serpapi": mock_search_response
        }
        
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.multi_provider_search = AsyncMock(return_value=mock_responses)
            
            result = await multi_provider_search(
                query="test query",
                providers=["duckduckgo", "serpapi"],
                max_results_per_provider=3
            )
            
            assert "error" not in result
            assert result["query"] == "test query"
            assert "providers" in result
            assert "duckduckgo" in result["providers"]
            assert "serpapi" in result["providers"]
            
            # Check structure of provider results
            ddg_result = result["providers"]["duckduckgo"]
            assert ddg_result["total_results"] == 1
            assert len(ddg_result["results"]) == 1
            assert ddg_result["results"][0]["title"] == "Test Result"
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_default_providers(self, mock_search_response):
        """Test multi-provider search with default providers."""
        mock_responses = {provider.value: mock_search_response for provider in SearchProvider}
        
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.multi_provider_search = AsyncMock(return_value=mock_responses)
            
            result = await multi_provider_search(
                query="test query",
                providers=None,  # Should default to all providers
                max_results_per_provider=3
            )
            
            assert "error" not in result
            assert len(result["providers"]) == len(SearchProvider)
            
            # Verify all providers are included
            expected_providers = {p.value for p in SearchProvider}
            actual_providers = set(result["providers"].keys())
            assert actual_providers == expected_providers
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_invalid_providers(self):
        """Test multi-provider search with invalid providers."""
        result = await multi_provider_search(
            query="test query",
            providers=["invalid1", "invalid2"],
            max_results_per_provider=3
        )
        
        assert "error" in result
        assert "No valid providers" in result["error"]
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_mixed_valid_invalid(self, mock_search_response):
        """Test multi-provider search with mix of valid and invalid providers."""
        mock_responses = {"duckduckgo": mock_search_response}
        
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.multi_provider_search = AsyncMock(return_value=mock_responses)
            
            result = await multi_provider_search(
                query="test query",
                providers=["duckduckgo", "invalid_provider"],
                max_results_per_provider=3
            )
            
            assert "error" not in result
            assert "duckduckgo" in result["providers"]
            # Invalid provider should be filtered out silently
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_max_results_validation(self, mock_search_response):
        """Test max_results_per_provider validation."""
        mock_responses = {"duckduckgo": mock_search_response}
        
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.multi_provider_search = AsyncMock(return_value=mock_responses)
            
            # Test clamping to max value (20)
            await multi_provider_search(
                query="test query",
                providers=["duckduckgo"],
                max_results_per_provider=50
            )
            
            call_args = mock_manager.multi_provider_search.call_args
            assert call_args[1]["max_results_per_provider"] == 20
    
    @pytest.mark.asyncio
    async def test_multi_provider_search_exception(self):
        """Test exception handling in multi_provider_search."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.multi_provider_search = AsyncMock(
                side_effect=Exception("Multi-search failed")
            )
            
            result = await multi_provider_search(
                query="test query",
                providers=["duckduckgo"],
                max_results_per_provider=3
            )
            
            assert "error" in result
            assert "Multi-search failed" in result["error"]


class TestGetAvailableProvidersTool:
    """Test the get_available_providers MCP tool."""
    
    @pytest.mark.asyncio
    async def test_get_available_providers_success(self):
        """Test successful get_available_providers call."""
        mock_status = {
            "duckduckgo": True,
            "serpapi": False,
            "perplexity": True,
            "tavily": False,
            "claude": True
        }
        mock_fallback_chain = [SearchProvider.DUCKDUCKGO, SearchProvider.PERPLEXITY]
        
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.get_available_providers.return_value = mock_status
            mock_manager.get_fallback_chain.return_value = mock_fallback_chain
            mock_manager.default_provider = SearchProvider.DUCKDUCKGO
            
            result = await get_available_providers()
            
            assert "error" not in result
            assert result["providers"] == mock_status
            assert result["default_provider"] == "duckduckgo"
            assert result["fallback_chain"] == ["duckduckgo", "perplexity"]
            assert result["total_available"] == 3  # True values count
    
    @pytest.mark.asyncio
    async def test_get_available_providers_exception(self):
        """Test exception handling in get_available_providers."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.get_available_providers.side_effect = Exception("Status check failed")
            
            result = await get_available_providers()
            
            assert "error" in result
            assert "Status check failed" in result["error"]


class TestServerIntegration:
    """Integration tests for the MCP server tools."""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self, mock_search_response):
        """Test a complete search workflow using all tools."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search = AsyncMock(return_value=mock_search_response)
            mock_manager.search_with_fallback = AsyncMock(return_value=mock_search_response)
            mock_manager.multi_provider_search = AsyncMock(
                return_value={"duckduckgo": mock_search_response}
            )
            mock_manager.get_available_providers.return_value = {"duckduckgo": True}
            mock_manager.get_fallback_chain.return_value = [SearchProvider.DUCKDUCKGO]
            mock_manager.default_provider = SearchProvider.DUCKDUCKGO
            
            # Test getting provider status
            providers_result = await get_available_providers()
            assert providers_result["total_available"] == 1
            
            # Test basic search
            search_result = await search_web("test query", "duckduckgo", 5)
            assert search_result["query"] == "test query"
            
            # Test fallback search
            fallback_result = await search_with_fallback("test query", 5)
            assert fallback_result["query"] == "test query"
            
            # Test multi-provider search
            multi_result = await multi_provider_search("test query", ["duckduckgo"], 3)
            assert "duckduckgo" in multi_result["providers"]
    
    def test_server_tools_are_properly_defined(self):
        """Test that all server tools are properly defined."""
        # This test verifies that the tools exist and are callable
        tools = [search_web, search_with_fallback, multi_provider_search, get_available_providers]
        
        for tool in tools:
            assert callable(tool)
            assert hasattr(tool, '__name__')
            assert asyncio.iscoroutinefunction(tool)
    
    @pytest.mark.asyncio
    async def test_all_tools_return_json_serializable_data(self, mock_search_response):
        """Test that all tools return JSON-serializable data."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search = AsyncMock(return_value=mock_search_response)
            mock_manager.search_with_fallback = AsyncMock(return_value=mock_search_response)
            mock_manager.multi_provider_search = AsyncMock(
                return_value={"duckduckgo": mock_search_response}
            )
            mock_manager.get_available_providers.return_value = {"duckduckgo": True}
            mock_manager.get_fallback_chain.return_value = [SearchProvider.DUCKDUCKGO]
            mock_manager.default_provider = SearchProvider.DUCKDUCKGO
            
            # Test all tools return JSON-serializable data
            tools_and_args = [
                (search_web, ("test query", "duckduckgo", 5)),
                (search_with_fallback, ("test query", 5)),
                (multi_provider_search, ("test query", ["duckduckgo"], 3)),
                (get_available_providers, ())
            ]
            
            for tool, args in tools_and_args:
                result = await tool(*args)
                
                # Try to serialize to JSON to ensure it's serializable
                try:
                    json.dumps(result)
                except (TypeError, ValueError) as e:
                    pytest.fail(f"Tool {tool.__name__} returned non-JSON-serializable data: {e}")


class TestErrorHandling:
    """Test error handling across all server tools."""
    
    @pytest.mark.asyncio
    async def test_all_tools_handle_search_manager_none(self):
        """Test behavior when search_manager is None."""
        with patch('web_search.server.search_manager', None):
            # All tools should handle this gracefully
            result1 = await search_web("test", "duckduckgo", 5)
            result2 = await search_with_fallback("test", 5)
            result3 = await multi_provider_search("test", ["duckduckgo"], 3)
            result4 = await get_available_providers()
            
            # All should return error responses
            for result in [result1, result2, result3, result4]:
                assert "error" in result
    
    @pytest.mark.asyncio
    async def test_tools_handle_async_cancellation(self, mock_search_response):
        """Test that tools handle async cancellation gracefully."""
        with patch('web_search.server.search_manager') as mock_manager:
            mock_manager.search = AsyncMock(side_effect=asyncio.CancelledError())
            
            with pytest.raises(asyncio.CancelledError):
                await search_web("test", "duckduckgo", 5)
    
    @pytest.mark.asyncio
    async def test_parameter_validation_edge_cases(self):
        """Test edge cases in parameter validation."""
        # Test with empty query
        result = await search_web("", "duckduckgo", 5)
        # Should not error on empty query (provider will handle it)
        
        # Test with very long query
        long_query = "a" * 1000
        result = await search_web(long_query, "duckduckgo", 5)
        # Should handle long queries without errors