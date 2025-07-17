# Web Search MCP Server Tests

Comprehensive test suite for the web search MCP server, covering all providers, server tools, and search management functionality.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_providers.py           # Tests for individual search providers
├── test_server.py              # Tests for MCP server tools
├── test_search_manager.py      # Tests for SearchManager functionality
├── pytest.ini                 # Pytest configuration
└── README.md                   # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run only unit tests (fast, no external dependencies)
python run_tests.py --unit

# Run with coverage report
python run_tests.py --coverage
```

### Using pytest directly

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_providers.py

# Run tests for specific provider
python -m pytest tests/test_providers.py -k "duckduckgo"

# Run with coverage
python -m pytest tests/ --cov=src/web_search --cov-report=html
```

## Test Categories

### Unit Tests (Default)
- **Fast execution** - No external API calls
- **Mocked dependencies** - Uses mock objects and responses
- **High coverage** - Tests all code paths and error conditions
- **No API keys required** - Can run anywhere

Run with: `python run_tests.py --unit`

### Integration Tests
- **Real API calls** - Tests actual provider integrations
- **Requires API keys** - Set environment variables for providers
- **Network dependent** - May fail due to network issues
- **Slower execution** - Real HTTP requests take time

Run with: `python run_tests.py --integration`

### Provider-Specific Tests
Test individual search providers:

```bash
python run_tests.py --provider duckduckgo    # DuckDuckGo (no API key needed)
python run_tests.py --provider serpapi       # SerpAPI (requires SERPAPI_API_KEY)
python run_tests.py --provider perplexity    # Perplexity (requires PERPLEXITY_API_KEY)
python run_tests.py --provider tavily        # Tavily (requires TAVILY_API_KEY)
python run_tests.py --provider claude        # Claude (requires ANTHROPIC_API_KEY)
```

## Test Files Overview

### `test_providers.py`
Tests for individual search provider implementations:

- **BaseSearchProvider**: Abstract base class tests
- **DuckDuckGoProvider**: Privacy-focused search (no API key)
- **SerpAPIProvider**: Google/Bing search via SerpAPI
- **PerplexityProvider**: AI-powered search with citations
- **TavilyProvider**: AI search with content analysis
- **ClaudeProvider**: Anthropic's search integration
- **Provider Comparison**: Cross-provider functionality tests
- **Integration Tests**: Live API testing (requires API keys)

### `test_server.py`
Tests for MCP server tools and FastMCP integration:

- **search_web**: Basic search with provider selection
- **search_with_fallback**: Automatic provider fallback
- **multi_provider_search**: Compare results across providers
- **get_available_providers**: Check provider status
- **Error Handling**: Exception handling and validation
- **JSON Serialization**: Ensure all responses are serializable

### `test_search_manager.py`
Tests for SearchManager coordination and workflow:

- **Provider Management**: Loading and configuring providers
- **Search Coordination**: Managing search requests
- **Fallback Logic**: Automatic failover between providers
- **Concurrent Execution**: Multi-provider search performance
- **Configuration**: Environment variable handling
- **Error Recovery**: Graceful degradation

### `conftest.py`
Shared test fixtures and configuration:

- **Mock Objects**: SearchResult, SearchResponse, providers
- **Environment Variables**: API key mocking
- **HTTP Responses**: Mock API responses for each provider
- **Event Loop**: Async test support
- **Test Data**: Sample queries and configurations

## Environment Setup for Integration Tests

Create a `.env` file in the `servers/web_search/` directory:

```env
# Required for integration tests
SERPAPI_API_KEY=your_serpapi_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
TAVILY_API_KEY=your_tavily_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional provider settings
DUCKDUCKGO_SAFESEARCH=moderate
SEARCH_TIMEOUT=30
```

## Test Execution Options

### Parallel Execution
```bash
# Run tests in parallel (requires pytest-xdist)
python run_tests.py --parallel 4
```

### Coverage Reports
```bash
# Generate HTML coverage report
python run_tests.py --coverage

# View coverage report
open htmlcov/index.html
```

### Continuous Integration
```bash
# CI-friendly output with XML coverage
python -m pytest tests/ --cov=src/web_search --cov-report=xml --junitxml=test-results.xml
```

## Adding New Tests

### For New Providers
1. Add provider class to `test_providers.py`
2. Create mock response fixture in `conftest.py`
3. Add provider-specific test cases
4. Update integration tests

### For New Server Tools
1. Add tool function tests to `test_server.py`
2. Test parameter validation
3. Test error handling
4. Verify JSON serialization

### For New Manager Features
1. Add functionality tests to `test_search_manager.py`
2. Test configuration handling
3. Test concurrent execution
4. Test error recovery

## Test Dependencies

Required packages (install with `uv add --dev`):
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking utilities

Optional packages:
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel test execution
- `pytest-html` - HTML test reports

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'web_search'**
   - Ensure you're running from the correct directory
   - Check that `src/web_search/__init__.py` exists

2. **Integration tests failing**
   - Check API keys in `.env` file
   - Verify network connectivity
   - Some providers may have rate limits

3. **Async test errors**
   - Ensure `pytest-asyncio` is installed
   - Check that `asyncio_mode = auto` in pytest.ini

4. **Coverage not working**
   - Install `pytest-cov`: `uv add --dev pytest-cov`
   - Ensure correct path to source code

### Debug Mode

Run tests with maximum verbosity and debugging:
```bash
python -m pytest tests/ -vvv -s --tb=long --capture=no
```

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Add appropriate fixtures to `conftest.py`
3. Include both success and failure test cases
4. Document any new test markers or categories
5. Update this README if adding new test files