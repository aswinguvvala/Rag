# Detailed System Flow Analysis for Hybrid RAG System

## Overview
This document provides a step-by-step breakdown of how the Hybrid RAG System processes a user query from input to final response. The system is designed for space exploration queries but handles general questions via hybrid local/web search. Key components include semantic search, confidence evaluation, web fallback, and LLM-based response generation.

## High-Level Flow
1. **Query Input**: User submits a query (e.g., via Streamlit app in `app.py`).
2. **Basic Facts Check**: Quick lookup in hardcoded facts (e.g., planet moons).
3. **Domain Detection**: Check if query is space-related using keyword matching.
4. **Local Search**: Semantic search on indexed documents.
5. **Confidence Evaluation**: Decide if web search is needed.
6. **Web Search (if needed)**: Fetch and extract from web via DuckDuckGo.
7. **Result Combination**: Rank and filter local + web results.
8. **Response Generation**: Use LLM to synthesize answer.
9. **Output**: Display response with sources and metrics.

## Detailed Step-by-Step Process
### 1. Query Reception (`app.py` - `query_api` function, lines ~195-235)
- Input: User query string (e.g., "How far is Voyager 1 from Earth?") and expertise level (general/student/expert).
- First, check `BASIC_SPACE_FACTS` dictionary for exact matches (e.g., if query contains 'jupiter' and 'moons', return hardcoded fact).
- If no match, proceed to RAG system.
- Enhance query based on expertise (e.g., prepend "Explain in simple terms for students:").

### 2. RAG Initialization (`hybrid_rag_system.py` - `HybridRAGSystem` class, lines ~371-400)
- Load SentenceTransformer model ('all-MiniLM-L6-v2') for embeddings.
- Load or create FAISS index from scraped documents (NASA, arXiv, etc.).

### 3. Semantic Local Search (`hybrid_rag_system.py` - `semantic_search`, lines ~826-865)
- Embed the query.
- Search FAISS index for top matches.
- Filter results: Require semantic score >0.5, then combine with keyword relevance (e.g., check for query terms in content).
- Special filters: Reject exoplanet content for solar system queries; ensure moon/planet terms match.
- Output: List of relevant local documents with scores.

### 4. Confidence Evaluation (`confidence_evaluator.py` - full file, and `HybridRAGSystem.query`, lines ~972-1044)
- Calculate domain relevance: Match query against space keywords (primary: 'space', 'nasa'; secondary: 'orbit', 'comet'). Score based on matches (0-1).
- Evaluate local results: Weighted score from domain relevance (40%), result quality (40%), count (20%).
- Decision:
  - If domain <0.3: Use web ("outside space domain").
  - If person/recent query and low local: Use web.
  - If confidence <0.6: Use web.
  - If >0.8: Use local only.
  - Else: Hybrid.
- For non-space (e.g., Wimbledon): Later in response gen, detect domain via Ollama and generate polite out-of-scope reply.

### 5. Web Search Fallback (`hybrid_rag_system.py` - WebSearchManager class, lines ~49-261)
- If triggered: Use DuckDuckGo API (or fallback to scraping).
- Extract content from top URLs (prioritize 'article', 'main' tags).
- Embed and rank web results semantically against query.
- Combine with local if hybrid mode.

### 6. Result Ranking and Filtering (`hybrid_rag_system.py` - `_combine_and_rank_results`, lines ~1090-1146)
- Merge local/web results.
- Sort by relevance score.
- If no good results (max score <0.3): Return "No similar information found".

### 7. Response Generation (`hybrid_rag_system.py` - `_generate_hybrid_response`, lines ~1146-1257; uses `llm_integration.py`)
- LLM: Ollama (model: llama3.2:3b) via `ollama_llm.generate_answer`.
- First, detect domain with Ollama prompt (options: space_exploration, particle_physics, etc.).
- If non-space (e.g., sports like Wimbledon) and confidence >0.7: Generate out-of-scope response (acknowledge query, note expertise limit, suggest alternatives, offer space help).
- Else: Build context from results, prompt Ollama to generate answer tailored to expertise level.
- Append sources (top 5 with relevance).
- Fallback if Ollama unavailable: Simple string concatenation of top results.

### 8. Output and UI (`app.py` - `main` function, lines ~237-677)
- Display answer in chat.
- Show metrics: Confidence, Time, Agent (HybridRAG), Sources.
- Debug tabs for document explorer and retrieval inspector.

## LLM Usage
- Primary: Ollama (local, free) with model 'llama3.2:3b'.
- Used for: Domain detection, web search decision (if available), out-of-scope responses, and final answer synthesis.
- Fallback: Rule-based if Ollama offline.

## Space Question Detection
- In `ConfidenceEvaluator.calculate_domain_relevance` (confidence_evaluator.py, lines ~1-50): Keyword matching against primary/secondary space terms.
- In response gen: Ollama classifies domain explicitly.
- Non-space triggers polite redirect (as in your Wimbledon example) without web search, to stay focused on space expertise.

## Error Handling and Fallbacks
- If web fails: Use local only.
- If no results: Suggest rephrasing.
- Logging: Errors to console/logs.

This flow ensures efficient, relevant responses while handling failures gracefully. 