# Web Search MCP Server

A robust MCP (Model Context Protocol) server that provides web search functionality through multiple configurable search providers.

## Features

- **Multiple Search Providers**: SerpAPI, Perplexity, DuckDuckGo, Tavily, and Claude
- **Automatic Fallback**: Falls back to other providers if primary fails
- **Multi-Provider Search**: Compare results across multiple providers
- **Flexible Configuration**: Environment-based configuration for all providers
- **No API Key Required**: DuckDuckGo works without any API keys

## Supported Providers

### 🟢 DuckDuckGo (Free, No API Key)
- Uses unofficial DuckDuckGo API
- Includes instant answers and web results
- Safe search options

### 🔑 SerpAPI (API Key Required)
- Access to Google, Bing, Yahoo, and other search engines
- High-quality structured results
- Advanced search parameters

### 🔑 Perplexity (API Key Required)  
- AI-powered search with citations
- Real-time information with source attribution
- Multiple model options (sonar-pro, sonar-small, etc.)

### 🔑 Tavily (API Key Required)
- AI search API with advanced results
- Includes AI-generated answers
- Follow-up questions and deep search

### 🔑 Claude (API Key Required)
- Anthropic's web search capability
- AI-powered result synthesis
- Context-aware search

## Installation

```bash
# Install dependencies
cd servers/web_search
uv sync

# Copy environment template
cp .env.example .env

# Edit .env to add your API keys (optional for DuckDuckGo)
```

## Configuration

### Environment Variables

```env
# SerpAPI (optional)
SERPAPI_API_KEY=your_serpapi_key_here
SERPAPI_ENGINE=google

# Perplexity (optional)
PERPLEXITY_API_KEY=your_perplexity_key_here
PERPLEXITY_MODEL=sonar-pro

# DuckDuckGo (no key required)
DUCKDUCKGO_SAFESEARCH=moderate

# Tavily (optional)
TAVILY_API_KEY=your_tavily_key_here

# Claude/Anthropic (optional)
ANTHROPIC_API_KEY=your_anthropic_key_here

# General settings
SEARCH_TIMEOUT=30
```

### Claude Desktop Integration

Add to your Claude Desktop config (`~/.claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "web_search": {
      "command": "python",
      "args": ["/absolute/path/to/servers/web_search/src/web_search/server.py"]
    }
  }
}
```

## Usage

### Running the Server

```bash
# Run the MCP server
python servers/web_search/src/web_search/server.py
```

### Available Tools

#### 1. `search_web`
Basic web search with provider selection:
```python
search_web(
    query="artificial intelligence trends 2024",
    provider="duckduckgo",  # or serpapi, perplexity, tavily, claude
    max_results=10
)
```

#### 2. `search_with_fallback`
Search with automatic fallback to working providers:
```python
search_with_fallback(
    query="latest AI developments",
    max_results=10
)
```

#### 3. `multi_provider_search`
Compare results across multiple providers:
```python
multi_provider_search(
    query="machine learning news",
    providers=["duckduckgo", "perplexity"],
    max_results_per_provider=5
)
```

#### 4. `get_available_providers`
Check which providers are configured and available:
```python
get_available_providers()
```

## API Response Format

```json
{
  "query": "search query",
  "provider": "duckduckgo",
  "total_results": 10,
  "search_time": 1.234,
  "results": [
    {
      "title": "Result Title",
      "url": "https://example.com",
      "snippet": "Result description...",
      "source": "Source Name",
      "published_date": "2024-01-01",
      "metadata": {
        "type": "web_result",
        "score": 0.95
      }
    }
  ],
  "metadata": {
    "engine": "google",
    "search_parameters": {...}
  }
}
```

## Provider-Specific Features

### SerpAPI
- Multiple search engines (Google, Bing, Yahoo, etc.)
- Rich metadata and search parameters
- News results integration

### Perplexity
- AI-generated summaries with citations
- Real-time information
- Follow-up question suggestions

### DuckDuckGo
- Instant answers (Wikipedia, calculations, etc.)
- Related topics
- Privacy-focused (no tracking)

### Tavily
- AI-powered result analysis
- Content scoring and relevance
- Advanced search depth options

### Claude
- Context-aware search results
- AI synthesis of multiple sources
- Tool-based web access

## Error Handling

The server includes comprehensive error handling:
- Automatic fallback between providers
- Graceful degradation when APIs are unavailable
- Detailed error messages and metadata
- Timeout protection for all requests

## Development

### Project Structure
```
servers/web_search/
├── src/web_search/
│   ├── __init__.py
│   ├── server.py              # MCP server implementation  
│   ├── search_manager.py      # Provider coordination
│   ├── types.py              # Type definitions
│   └── providers/            # Search provider implementations
│       ├── __init__.py
│       ├── base.py           # Base provider class
│       ├── serpapi_provider.py
│       ├── perplexity_provider.py
│       ├── duckduckgo_provider.py
│       ├── tavily_provider.py
│       └── claude_provider.py
├── tests/
├── pyproject.toml
├── .env.example
└── README.md
```

### Adding New Providers

1. Create a new provider class inheriting from `BaseSearchProvider`
2. Implement required methods: `search()` and `_validate_config()`
3. Add provider to `SearchProvider` enum in `types.py`
4. Register in `SearchManager.PROVIDERS` mapping
5. Add configuration loading in `SearchManager._load_configs()`

## Testing

```bash
# Run tests
cd servers/web_search
python -m pytest tests/

# Test individual provider
python -c "
import asyncio
from src.web_search.search_manager import SearchManager
from src.web_search.types import SearchProvider

async def test():
    manager = SearchManager()
    result = await manager.search('test query', SearchProvider.DUCKDUCKGO)
    print(result)

asyncio.run(test())
"
```