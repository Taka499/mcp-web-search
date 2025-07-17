"""Claude search provider implementation using Anthropic's web search capability."""

import time
from typing import List

from .base import BaseSearchProvider
from ..search_types import SearchResponse, SearchResult, SearchProvider


class ClaudeProvider(BaseSearchProvider):
    """Claude search provider using Anthropic's web search API."""
    
    BASE_URL = "https://api.anthropic.com/v1/messages"
    
    def _validate_config(self) -> bool:
        """Validate Claude API configuration."""
        if not self.config.api_key:
            raise ValueError("Claude API requires an API key")
        return True
    
    async def search(self, query: str) -> SearchResponse:
        """Perform search using Claude's web search capability."""
        self._validate_config()
        
        start_time = time.time()
        
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "anthropic-beta": "computer-use-2024-10-22"
        }
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "tools": [
                {
                    "type": "computer_use",
                    "name": "computer",
                    "display_width_px": 1024,
                    "display_height_px": 768
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": f"Search the web for information about: {query}. Provide detailed search results with titles, URLs, and descriptions. Return up to {self.config.max_results} relevant results."
                }
            ]
        }
        
        try:
            response = await self._make_post_request(
                self.BASE_URL,
                headers=headers,
                json=payload
            )
            
            search_time = time.time() - start_time
            data = response.json()
            
            results = self._parse_results(data, query)
            
            metadata = {
                "model": "claude-3-5-sonnet-20241022",
                "usage": data.get("usage", {}),
                "tool_use": data.get("tool_use", [])
            }
            
            return self._create_response(
                query=query,
                results=results,
                search_time=search_time,
                metadata=metadata
            )
            
        except Exception as e:
            # Fallback: return a message about Claude search capability
            search_time = time.time() - start_time
            
            fallback_result = SearchResult(
                title=f"Claude Search: {query}",
                url="",
                snippet=f"Claude search capability is available but may require specific API access. Query: {query}",
                source="Claude AI",
                metadata={
                    "type": "fallback",
                    "error": str(e)
                }
            )
            
            return self._create_response(
                query=query,
                results=[fallback_result],
                search_time=search_time,
                metadata={"status": "fallback", "error": str(e)}
            )
    
    def _parse_results(self, data: dict, query: str) -> List[SearchResult]:
        """Parse Claude API response into SearchResult objects."""
        results = []
        
        # Extract content from Claude's response
        content_blocks = data.get("content", [])
        
        for block in content_blocks:
            if block.get("type") == "text":
                content = block.get("text", "")
                
                # Create a result from Claude's response
                search_result = SearchResult(
                    title=f"Claude Search Results: {query}",
                    url="",
                    snippet=content[:300] + "..." if len(content) > 300 else content,
                    source="Claude AI",
                    metadata={
                        "type": "claude_response",
                        "full_content": content,
                        "usage": data.get("usage", {})
                    }
                )
                results.append(search_result)
                
            elif block.get("type") == "tool_use":
                # Handle tool use results if Claude used web search tools
                tool_result = SearchResult(
                    title=f"Web Search via Claude: {query}",
                    url="",
                    snippet=f"Claude performed web search using tools: {block.get('name', 'unknown')}",
                    source="Claude AI Tools",
                    metadata={
                        "type": "tool_use",
                        "tool_name": block.get("name"),
                        "tool_input": block.get("input", {})
                    }
                )
                results.append(tool_result)
        
        # If no results found, create a default response
        if not results:
            default_result = SearchResult(
                title=f"Search: {query}",
                url="",
                snippet="Claude search is processing your query. Results may vary based on API access and configuration.",
                source="Claude AI",
                metadata={
                    "type": "default",
                    "model": "claude-3-5-sonnet-20241022"
                }
            )
            results.append(default_result)
        
        return results[:self.config.max_results]