# Web Search Failure Analysis in Hybrid RAG System

## Issue Description
The Hybrid RAG system is experiencing failures in its web search functionality, specifically with DuckDuckGo searches. This manifests as error messages in the logs: "ERROR:hybrid_rag_system:DuckDuckGo search failed: Expecting value: line 1 column 1 (char 0)". 

This error occurs when attempting to parse the response from DuckDuckGo as JSON, but the response is either empty or not valid JSON. As a result, queries that rely on web search (like "How far is Voyager 1 from Earth?") fail to retrieve information, leading to responses indicating inability to determine the answer from provided context.

In contrast, queries with sufficient local results (like "What is the Big Bang Theory?") succeed using local knowledge.

## Affected Queries
- Queries not covered by local knowledge base trigger web search.
- Example: Voyager 1 distance - No local info, web search fails, no answer provided.
- Example: Big Bang Theory - Local results available, successful response with sources.

## Root Cause Analysis
The error is a JSONDecodeError from `response.json()` in the DuckDuckGo search implementation. Possible reasons:
1. **Empty Response:** DuckDuckGo API returns empty content.
2. **Invalid JSON:** Response is not properly formatted JSON (e.g., HTML error page).
3. **Network/Rate Limiting:** IP or User-Agent blocked, or rate-limited.
4. **API Changes:** DuckDuckGo API endpoint or format has changed.
5. **Timeout/Connection Issues:** Request times out or fails silently.

From terminal logs, this happens repeatedly, suggesting a consistent issue with the API call.

## Code Walkthrough
The web search is handled in `WebSearchManager` class within `hybrid_rag_system.py`.

Key method: `search_duckduckgo(query, num_results)`
- Checks cache.
- Calls `_try_ddg_instant_api` which sends GET to `https://api.duckduckgo.com/` with params.
- Then `data = response.json()` - This is where the error occurs if response.text is invalid.
- If few results, falls back to scraping `https://duckduckgo.com/html/`.

The error is logged in the except block: `logger.error(f"DuckDuckGo search failed: {e}")`

In `HybridRAGSystem.query_knowledge_base` (likely in lines >750):
- Evaluates local results.
- If confidence low, triggers web search via `self.web_search_manager.search_and_extract`.
- If web search fails, system falls back to local or indicates no info.

## Proposed Fixes
1. **Handle JSON Errors Gracefully:**
   - Wrap `response.json()` in try-except and log response.status_code and response.text for debugging.
   - If fails, immediately try the web scraping fallback.

2. **Improve Fallback:**
   - Make web scraping the primary method if API fails consistently.
   - Or integrate another search engine like Bing or Google Custom Search (requires API key).

3. **Update User-Agent Rotation:**
   - Implement rotating User-Agents to avoid blocking.

4. **Add Retry Mechanism:**
   - Retry failed requests 2-3 times with exponential backoff.

5. **Caching Enhancement:**
   - Cache failures briefly to avoid repeated errors.

6. **Test and Debug:**
   - Add debug mode to print response before parsing.

Implement these step-by-step, testing after each change. Start by adding logging to see the actual response from DuckDuckGo. 