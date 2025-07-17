# Config.py Test Plan

## Test Strategy Overview
Following TDD principles, we'll write tests first, then implement the minimum code to make them pass. Each test will be focused, atomic, and clearly describe the expected behavior.

## Test Structure

### 1. Core Configuration Model Tests (`test_config.py`)

#### Basic Model Creation
```python
def test_config_basic_model_creation():
    """Should create a basic config model with default values."""
    
def test_config_model_with_valid_values():
    """Should accept valid configuration values."""
    
def test_config_model_rejects_invalid_values():
    """Should reject invalid configuration values with clear error messages."""
```

#### Provider-Specific Configuration Tests
```python
def test_serpapi_config_creation():
    """Should create SerpAPI config with provider-specific fields."""
    
def test_perplexity_config_creation():
    """Should create Perplexity config with model selection."""
    
def test_duckduckgo_config_creation():
    """Should create DuckDuckGo config without requiring API key."""
    
def test_tavily_config_creation():
    """Should create Tavily config with required API key."""
    
def test_claude_config_creation():
    """Should create Claude config with Anthropic API key."""
```

#### Validation Tests
```python
def test_max_results_validation():
    """Should validate max_results is within bounds (1-100)."""
    
def test_timeout_validation():
    """Should validate timeout is within bounds (1-300)."""
    
def test_api_key_validation():
    """Should validate API key format and presence for providers that require it."""
    
def test_provider_specific_field_validation():
    """Should validate provider-specific fields like serpapi_engine."""
```

### 2. Environment Loading Tests (`test_config_environment.py`)

#### Environment Variable Loading
```python
def test_load_config_from_environment():
    """Should load configuration from environment variables."""
    
def test_load_config_with_missing_optional_vars():
    """Should use defaults when optional environment variables are missing."""
    
def test_load_config_with_missing_required_vars():
    """Should raise appropriate error when required environment variables are missing."""
    
def test_load_config_with_invalid_env_values():
    """Should raise validation error for invalid environment variable values."""
```

#### Environment Variable Parsing
```python
def test_parse_integer_env_vars():
    """Should correctly parse integer environment variables."""
    
def test_parse_boolean_env_vars():
    """Should correctly parse boolean environment variables."""
    
def test_parse_string_env_vars():
    """Should correctly parse string environment variables."""
    
def test_handle_empty_string_env_vars():
    """Should handle empty string environment variables appropriately."""
```

#### Multi-Provider Environment Loading
```python
def test_load_all_provider_configs():
    """Should load configurations for all available providers."""
    
def test_load_selective_provider_configs():
    """Should load only requested provider configurations."""
    
def test_provider_availability_check():
    """Should correctly determine which providers are available based on config."""
```

### 3. Integration Tests (`test_config_integration.py`)

#### SearchManager Integration
```python
def test_search_manager_uses_config_system():
    """Should verify SearchManager uses config.py instead of direct env access."""
    
def test_search_manager_provider_instantiation():
    """Should verify providers receive correct configurations from config system."""
    
def test_search_manager_fallback_with_config():
    """Should verify fallback chain works with new config system."""
```

#### Configuration Override Tests
```python
def test_config_override_in_search_manager():
    """Should allow runtime configuration overrides in SearchManager."""
    
def test_max_results_override():
    """Should allow max_results override while preserving other config."""
    
def test_provider_specific_overrides():
    """Should allow provider-specific configuration overrides."""
```

### 4. Error Handling Tests (`test_config_errors.py`)

#### Configuration Error Scenarios
```python
def test_missing_required_api_key():
    """Should provide clear error when required API key is missing."""
    
def test_invalid_provider_configuration():
    """Should provide clear error for invalid provider configurations."""
    
def test_configuration_validation_errors():
    """Should provide helpful validation error messages."""
```

#### Environment Error Scenarios
```python
def test_malformed_environment_variables():
    """Should handle malformed environment variables gracefully."""
    
def test_environment_loading_failures():
    """Should handle environment loading failures appropriately."""
```

## Test Data and Fixtures

### Environment Variable Test Data
```python
# Valid environment configurations
VALID_SERPAPI_ENV = {
    "SERPAPI_API_KEY": "test-key-123",
    "SERPAPI_MAX_RESULTS": "20",
    "SERPAPI_ENGINE": "google",
    "SEARCH_TIMEOUT": "45"
}

VALID_PERPLEXITY_ENV = {
    "PERPLEXITY_API_KEY": "pplx-test-key",
    "PERPLEXITY_MAX_RESULTS": "15",
    "PERPLEXITY_MODEL": "sonar-small",
    "SEARCH_TIMEOUT": "30"
}

# Invalid environment configurations
INVALID_SERPAPI_ENV = {
    "SERPAPI_API_KEY": "",  # Empty key
    "SERPAPI_MAX_RESULTS": "invalid",  # Non-numeric
    "SEARCH_TIMEOUT": "500"  # Out of range
}
```

### Configuration Test Objects
```python
# Valid configuration objects for testing
VALID_SERPAPI_CONFIG = {
    "provider": "serpapi",
    "api_key": "test-key-123",
    "max_results": 20,
    "serpapi_engine": "google",
    "timeout": 45
}

VALID_DUCKDUCKGO_CONFIG = {
    "provider": "duckduckgo",
    "max_results": 10,
    "duckduckgo_safesearch": "moderate",
    "timeout": 30
}
```

## Test Execution Strategy

### Phase 1: Red Phase (Failing Tests)
1. Write all basic model tests - expect failures
2. Write environment loading tests - expect failures  
3. Write integration tests - expect failures

### Phase 2: Green Phase (Minimal Implementation)
1. Implement basic config models to pass model tests
2. Implement environment loading to pass environment tests
3. Implement SearchManager integration to pass integration tests

### Phase 3: Refactor Phase (Improve Design)
1. Refactor config models for better organization
2. Optimize environment loading performance
3. Clean up integration points

## Continuous Testing Requirements

### Test Commands
```bash
# Run all config tests
pytest tests/test_config*.py -v

# Run with coverage
pytest tests/test_config*.py --cov=src/web_search/config --cov-report=term-missing

# Run specific test categories
pytest tests/test_config.py::test_config_basic_model_creation -v
```

### Test Coverage Requirements
- 100% line coverage for config.py module
- 100% branch coverage for validation logic
- All error conditions must be tested
- All environment variable scenarios must be tested

## Success Criteria
- [ ] All tests pass consistently
- [ ] No regression in existing functionality
- [ ] Clear error messages for all failure scenarios
- [ ] Performance is equivalent or better than current implementation
- [ ] Code is more maintainable and type-safe than current implementation