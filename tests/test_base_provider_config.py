"""Test BaseSearchProvider with new ProviderConfig system."""

import pytest
from unittest.mock import Mock, patch
from src.web_search.providers.base import BaseSearchProvider
from src.web_search.config import DuckDuckGoConfig, TavilyConfig
from src.web_search.search_types import SearchProvider


class TestBaseProviderConfig:
    """Test BaseSearchProvider uses new ProviderConfig system."""

    def test_base_provider_accepts_provider_config(self):
        """BaseSearchProvider should accept ProviderConfig instead of SearchConfig."""

        # Create a concrete implementation for testing
        class TestProvider(BaseSearchProvider):
            async def search(self, query: str):
                pass

            def _validate_config(self) -> bool:
                return True

        config = DuckDuckGoConfig(timeout=30, max_results=10)

        provider = TestProvider(config)

        assert provider.config == config
        assert provider.config.provider == SearchProvider.DUCKDUCKGO
        assert provider.config.timeout == 30
        assert provider.config.max_results == 10

    def test_base_provider_creates_http_client_with_config_timeout(self):
        """BaseSearchProvider should create HTTP client with config timeout."""

        class TestProvider(BaseSearchProvider):
            async def search(self, query: str):
                pass

            def _validate_config(self) -> bool:
                return True

        config = DuckDuckGoConfig()

        with patch("src.web_search.providers.base.httpx.AsyncClient") as mock_client:
            provider = TestProvider(config)

            mock_client.assert_called_once_with(timeout=config.timeout)

    def test_create_response_uses_config_provider(self):
        """_create_response should use provider from config."""

        class TestProvider(BaseSearchProvider):
            async def search(self, query: str):
                pass

            def _validate_config(self) -> bool:
                return True

        config = TavilyConfig(timeout=30)

        provider = TestProvider(config)

        response = provider._create_response(query="test query", results=[])

        assert response.provider == SearchProvider.TAVILY
        assert response.query == "test query"
        assert response.results == []

    @pytest.mark.asyncio
    async def test_make_request_uses_config_timeout_in_error_message(self):
        """_make_request should use config timeout in error messages."""

        class TestProvider(BaseSearchProvider):
            async def search(self, query: str):
                pass

            def _validate_config(self) -> bool:
                return True

        config = DuckDuckGoConfig()

        provider = TestProvider(config)

        # Mock httpx.TimeoutException
        with patch.object(provider.client, "get") as mock_get:
            import httpx

            mock_get.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(Exception) as exc_info:
                await provider._make_request("http://example.com")

            assert f"Request timeout after {config.timeout} seconds" in str(
                exc_info.value
            )
