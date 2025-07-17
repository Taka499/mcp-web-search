# Project Improvement Plan

## Todo List

### High Priority
- [ ] **Create pydantic-based config.py to centralize environment variable management**
  - Currently `src/web_search/search_manager.py` is loading environment variables before calling all the providers, which is ugly
  - We need to create `config.py` that uses pydantic model to provide re-usable environment variables

### Medium Priority
- [ ] **Implement concurrency in SearchManager.multi_provider_search method**
  - SearchManager.multi_provider_search performs provider searches sequentially and includes a TODO to implement concurrency, potentially slowing multi-provider queries

- [ ] **Refactor to use shared httpx.AsyncClient across providers and analyzers**
  - Each provider and analyzer creates its own httpx.AsyncClient per request (e.g., `HtmlAnalyzer.__init__`, `FeedAnalyzer.__init__`), leading to repeated client initialization and connection overhead