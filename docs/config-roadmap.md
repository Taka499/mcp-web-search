# Config.py Implementation Roadmap

## Overview
Create a centralized pydantic-based configuration system to replace the current environment variable loading scattered across the codebase.

## Current State Analysis
- **Problem**: Environment variables are loaded in `src/web_search/search_manager.py` using `os.getenv()` calls mixed with business logic
- **Location**: Lines 42-82 in `search_manager.py._load_configs()`
- **Issues**: 
  - No validation of environment variables
  - No centralized defaults
  - No type safety
  - Environment loading happens in business logic class

## Solution Design
Create `src/web_search/config.py` with pydantic models for:
- Base configuration settings
- Provider-specific configurations
- Environment variable validation and defaults

## TDD Implementation Plan

### Phase 1: Structural Changes (Tidy First)
1. **Create config.py structure** - Define pydantic models without changing behavior
2. **Add configuration loading** - Create factory functions for config instantiation
3. **Add validation** - Implement proper type checking and validation rules

### Phase 2: Behavioral Changes
1. **Integrate with SearchManager** - Replace `_load_configs()` with config.py usage
2. **Update imports** - Change environment variable access patterns
3. **Remove old code** - Clean up deprecated environment loading

### Phase 3: Testing Strategy
1. **Unit tests for config models** - Test validation, defaults, and error handling
2. **Integration tests** - Test SearchManager with new config system
3. **Environment variable tests** - Test different environment scenarios

## Test Plan

### Test Categories

#### 1. Configuration Model Tests
- **Validation Tests**: Invalid values, missing required fields
- **Default Value Tests**: Ensure proper defaults when env vars missing
- **Type Conversion Tests**: String to int conversion, boolean parsing
- **Provider-specific Tests**: Each provider's unique configuration

#### 2. Environment Loading Tests
- **Missing Environment Variables**: Test graceful handling of missing vars
- **Invalid Environment Variables**: Test error handling for invalid values
- **Override Tests**: Test configuration override capabilities

#### 3. Integration Tests
- **SearchManager Integration**: Test SearchManager with new config system
- **Provider Instantiation**: Test that providers receive correct configurations
- **Backward Compatibility**: Ensure existing functionality works unchanged

#### 4. Edge Cases
- **Empty String Handling**: Test behavior with empty string env vars
- **Numeric Boundary Tests**: Test min/max values for numeric settings
- **Provider Availability**: Test availability checks with new config

### Test Files Structure
```
tests/
├── test_config.py              # Main config model tests
├── test_config_integration.py  # Integration with SearchManager
└── test_config_environment.py  # Environment variable scenarios
```

## Implementation Order (Following TDD Red-Green-Refactor)

### Step 1: Write failing test for basic config model
- Test: `test_config_basic_model_creation`
- Expected: Basic config model can be instantiated

### Step 2: Implement basic config model
- Create `Config` base class with common fields
- Make the test pass

### Step 3: Write failing test for provider configs
- Test: `test_provider_specific_configs`
- Expected: Each provider has its own config model

### Step 4: Implement provider-specific config models
- Create individual provider config classes
- Make the test pass

### Step 5: Write failing test for environment loading
- Test: `test_load_config_from_environment`
- Expected: Config can be loaded from environment variables

### Step 6: Implement environment loading
- Create factory functions for loading from env
- Make the test pass

### Step 7: Write failing test for SearchManager integration
- Test: `test_search_manager_uses_config`
- Expected: SearchManager uses config.py instead of direct env access

### Step 8: Refactor SearchManager to use config.py
- Replace `_load_configs()` with config.py usage
- Make the test pass

### Step 9: Refactor and cleanup
- Remove old environment loading code
- Ensure all tests still pass
- Commit structural and behavioral changes separately

## Definition of Done
- [ ] All existing tests pass
- [ ] New config tests have 100% coverage
- [ ] No direct `os.getenv()` calls in business logic
- [ ] Pydantic validation for all environment variables
- [ ] Proper error messages for invalid configurations
- [ ] Documentation updated
- [ ] Type hints throughout