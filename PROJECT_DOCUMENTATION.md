# 🚀 MSEIS - Multi-Modal Space Exploration Intelligence System
## Complete Project Documentation

---

## 📋 Table of Contents
1. [Project Overview](#-project-overview)
2. [Quick Start Guide](#-quick-start-guide)
3. [System Architecture](#-system-architecture)
4. [Component Documentation](#-component-documentation)
5. [Installation Guide](#-installation-guide)
6. [Usage Examples](#-usage-examples)
7. [API Documentation](#-api-documentation)
8. [Configuration](#-configuration)
9. [Development Guide](#-development-guide)
10. [Troubleshooting](#-troubleshooting)

---

## 🌟 Project Overview

**MSEIS** (Multi-Modal Space Exploration Intelligence System) is an advanced RAG (Retrieval-Augmented Generation) system that demonstrates cutting-edge AI engineering practices. The system integrates multiple AI technologies to provide intelligent question-answering about space exploration topics.

### 🎯 Key Features
- **Advanced RAG Implementation** with hybrid retrieval strategies
- **Multi-Agent Architecture** with specialized processing agents
- **Real-time Data Integration** from NASA, ESA, SpaceX, and arXiv
- **Multi-modal Processing** supporting text and images
- **Production-ready Infrastructure** with monitoring and caching
- **Multiple Interface Options** (Streamlit, FastAPI, Web UI)

### 🏗️ System Components
1. **True RAG System** (`true_rag_system.py`) - Complete standalone implementation
2. **MSEIS Framework** (`mseis/`) - Production-grade multi-agent system
3. **API Server** (`rag_server.py`) - RESTful web service
4. **Alternative UIs** - Multiple interface options

---

## 🚀 Quick Start Guide

### Option 1: Run True RAG System (Recommended for first-time users)
```bash
# Already running on port 8504
# Access at: http://localhost:8504

# If not running, start with:
streamlit run true_rag_system.py --server.port 8504
```

### Option 2: Run API Server
```bash
python rag_server.py
# Access API docs at: http://localhost:8000/docs
```

### Option 3: Run MSEIS Framework
```bash
cd mseis
python main.py
# Access at: http://localhost:8000
```

---

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                    │
│  ┌─────────────┬─────────────┬─────────────────────────────┐│
│  │ Streamlit   │ FastAPI     │ Alternative UIs             ││
│  │ Web App     │ REST API    │ (Gradio, Custom)            ││
│  └─────────────┴─────────────┴─────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                   Application Logic Layer                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Orchestrator Agent                         ││
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────────┐││
│  │  │Document │ Image   │ Graph   │Realtime │ Custom      │││
│  │  │Agent    │ Agent   │ Agent   │Agent    │ Agents      │││
│  │  └─────────┴─────────┴─────────┴─────────┴─────────────┘││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                     Processing Layer                        │
│  ┌─────────────┬─────────────┬─────────────────────────────┐│
│  │ Retrievers  │ Embeddings  │ Rerankers                   ││
│  │ - Vector    │ - OpenAI    │ - Cross-encoder             ││
│  │ - Keyword   │ - Sentence  │ - Diversity                 ││
│  │ - Graph     │   Transform │ - Confidence                ││
│  │ - Hybrid    │ - CLIP      │                             ││
│  └─────────────┴─────────────┴─────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                          │
│  ┌─────────────┬─────────────┬─────────────────────────────┐│
│  │ Vector DBs  │ Graph DB    │ Caching                     ││
│  │ - Pinecone  │ - Neo4j     │ - Redis                     ││
│  │ - FAISS     │             │ - Local Cache               ││
│  └─────────────┴─────────────┴─────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources Layer                       │
│  ┌─────────────┬─────────────┬─────────────────────────────┐│
│  │ NASA APIs   │ Scientific  │ News & Media                ││
│  │ - APOD      │ - arXiv     │ - RSS Feeds                 ││
│  │ - Mars Data │ - Papers    │ - Space News                ││
│  │ - ISS Track │ - Research  │ - Social Media              ││
│  └─────────────┴─────────────┴─────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture
```
Query Input → Query Analysis → Agent Selection → Information Retrieval → 
Content Synthesis → Response Generation → User Interface
```

---

## 📦 Component Documentation

### 1. True RAG System (`true_rag_system.py`)
**Purpose**: Complete, self-contained RAG implementation  
**Status**: ✅ Currently running on port 8504

#### Features:
- **Real-time Web Scraping**: 10+ space-related data sources
- **FAISS Vector Search**: Local vector indexing with sentence transformers
- **Semantic Search**: Advanced query understanding and matching
- **Interactive UI**: Streamlit-based interface with caching
- **Local Data Storage**: Pickle-based persistence in `rag_data/`

#### Key Methods:
```python
class TrueRAGSystem:
    def scrape_nasa_news()           # NASA RSS feeds & articles
    def scrape_arxiv_papers()        # Scientific research papers
    def scrape_esa_news()            # European Space Agency
    def scrape_spacex_updates()      # SpaceX news & launches
    def create_embeddings()          # Vector generation
    def semantic_search()            # Query processing
    def generate_answer()            # Response synthesis
```

### 2. MSEIS Framework (`mseis/`)
**Purpose**: Production-grade multi-agent RAG system  
**Status**: 🚧 Framework ready, needs configuration

#### Core Components:
```
mseis/
├── agents/                      # Specialized processing agents
│   ├── base_agent.py           # Abstract agent interface
│   ├── document_agent.py       # Text processing specialist
│   ├── image_agent.py          # CLIP-based image analysis
│   └── orchestrator_agent.py   # Master coordinator
├── core/                       # Core processing modules
│   ├── config.py               # Configuration management
│   ├── embeddings.py           # Embedding providers
│   ├── retrievers.py           # Search implementations
│   └── rerankers.py            # Relevance optimization
├── storage/                    # Data persistence
│   ├── pinecone_manager.py     # Vector database
│   ├── neo4j_manager.py        # Graph database
│   └── cache_manager.py        # Redis caching
└── utils/                      # Utilities
    ├── logging_config.py       # Structured logging
    ├── monitoring.py           # Metrics collection
    └── rate_limiter.py         # API protection
```

### 3. API Server (`rag_server.py`)
**Purpose**: RESTful web service for RAG functionality  
**Status**: 🔄 Ready to deploy

#### Endpoints:
- `POST /query` - Process user queries
- `GET /health` - System health status
- `GET /metrics` - Performance metrics

#### Example Usage:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest Mars discoveries?",
    "expertise_level": "general"
  }'
```

### 4. Alternative UIs
- **`app.py`**: Streamlit app with hardcoded knowledge base
- **`mseis_streamlit.py`**: Advanced UI connecting to API server

---

## 🛠️ Installation Guide

### Prerequisites
```bash
# Required Software
- Python 3.11 or higher
- Git
- Docker (optional, for full deployment)

# Optional Services
- Redis (for advanced caching)
- Neo4j (for graph features)
```

### Step-by-Step Installation

#### 1. Clone Repository
```bash
git clone <your-repository-url>
cd NEW_RAG
```

#### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
# Install core dependencies
pip install -r mseis/requirements.txt

# Additional dependencies for True RAG System
pip install streamlit sentence-transformers faiss-cpu
pip install beautifulsoup4 requests feedparser arxiv
```

#### 4. Configure Environment (Optional)
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys (optional)
nano .env
```

#### 5. Verify Installation
```bash
# Test True RAG System
streamlit run true_rag_system.py --server.port 8504

# Test API Server
python rag_server.py

# Test MSEIS Framework
cd mseis
python test_system.py
```

---

## 💡 Usage Examples

### Basic Query Processing
```python
# Using True RAG System directly
from true_rag_system import TrueRAGSystem

# Initialize system
rag = TrueRAGSystem()
rag.initialize()

# Build knowledge base (one-time setup)
rag.build_knowledge_base()

# Process queries
results = rag.semantic_search("What is the James Webb Space Telescope?")
answer = rag.generate_answer("What is the James Webb Space Telescope?", results)
print(answer)
```

### API Client Usage
```python
import aiohttp
import asyncio

async def query_api(question: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/query",
            json={
                "query": question,
                "expertise_level": "general"
            }
        ) as response:
            return await response.json()

# Usage
result = asyncio.run(query_api("Explain how rockets work"))
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
```

### Streamlit Interface Usage
1. Open http://localhost:8504 in your browser
2. Click "Build Knowledge Base" (first time only)
3. Wait for data scraping to complete
4. Ask questions in the chat interface
5. View sources and confidence scores

---

## 📖 API Documentation

### Query Endpoint
**POST** `/query`

#### Request Body:
```json
{
  "query": "string",                    // Required: User question
  "user_id": "string",                  // Optional: User identifier
  "expertise_level": "general",         // Optional: student|general|expert
  "metadata": {                         // Optional: Additional context
    "session_id": "string",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### Response:
```json
{
  "query_id": "string",                 // Unique query identifier
  "answer": "string",                   // Generated response
  "confidence": 0.95,                   // Confidence score (0-1)
  "sources": [                          // Retrieved sources
    {
      "content": "string",              // Source content
      "metadata": {                     // Source metadata
        "source": "NASA",
        "url": "https://...",
        "date": "2024-01-01"
      },
      "relevance_score": 0.95           // Relevance score (0-1)
    }
  ],
  "processing_time": 1.23,              // Processing time in seconds
  "agent_used": "DocumentAgent"         // Agent that processed the query
}
```

### Health Check Endpoint
**GET** `/health`

#### Response:
```json
{
  "status": "healthy",                  // healthy|degraded|offline
  "version": "1.0.0",                   // System version
  "agents": {                           // Agent status
    "orchestrator": "healthy",
    "document": "healthy",
    "image": "healthy"
  }
}
```

### Metrics Endpoint
**GET** `/metrics`

#### Response:
```json
{
  "agents": {
    "orchestrator": {
      "total_queries": 1000,
      "successful_queries": 950,
      "avg_processing_time": 1.5,
      "cache_hit_rate": 0.75
    }
  },
  "system": {
    "uptime": 86400,
    "memory_usage": "2.1GB",
    "cpu_usage": "15%"
  }
}
```

---

## ⚙️ Configuration

### System Configuration (`mseis/config.yaml`)
```yaml
# Core system settings
system:
  name: "MSEIS"
  version: "1.0.0"
  environment: "development"

# Agent configuration
agents:
  document:
    enabled: true
    chunk_size: 1000
    chunk_overlap: 200
  
  image:
    enabled: true
    model: "openai/clip-vit-base-patch32"
    batch_size: 32

# Retrieval settings
retrieval:
  hybrid:
    vector_weight: 0.7
    keyword_weight: 0.2
    graph_weight: 0.1
  top_k: 20
  rerank_top_k: 5

# Data sources
data_sources:
  nasa:
    endpoints:
      apod: "https://api.nasa.gov/planetary/apod"
      neo: "https://api.nasa.gov/neo/rest/v1/neo"
  
  arxiv:
    categories: ["astro-ph", "astro-ph.GA"]
    max_results: 100
```

### Environment Variables (`.env`)
```bash
# AI Service APIs
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment

# Graph Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Caching
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# External APIs
NASA_API_KEY=your_nasa_api_key_here
```

---

## 👨‍💻 Development Guide

### Adding New Data Sources
```python
# 1. Create scraper function in true_rag_system.py
def scrape_new_source(self, max_articles=20) -> List[Dict]:
    """Scrape data from new source"""
    documents = []
    
    try:
        # Your scraping logic here
        response = requests.get('https://api.newsource.com/data')
        data = response.json()
        
        for item in data:
            documents.append({
                'title': item['title'],
                'content': item['content'],
                'url': item['url'],
                'source': 'New Source',
                'date': item['date']
            })
            
    except Exception as e:
        st.error(f"Error scraping new source: {str(e)}")
    
    return documents

# 2. Add to build_knowledge_base method
def build_knowledge_base(self):
    # ... existing code ...
    
    # Add new source
    with st.spinner("Scraping new source..."):
        new_docs = self.scrape_new_source(max_articles=15)
        all_documents.extend(new_docs)
        st.write(f"✅ Scraped {len(new_docs)} articles from new source")
```

### Creating Custom Agents (MSEIS Framework)
```python
# agents/custom_agent.py
from agents.base_agent import BaseAgent, QueryContext
from typing import List, Dict, Tuple

class CustomAgent(BaseAgent):
    """Custom agent for specialized processing"""
    
    async def _setup(self):
        """Initialize agent-specific resources"""
        self.custom_model = load_custom_model()
        self.logger.info("Custom agent initialized")
    
    async def _process_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Process query with custom logic"""
        query = context.original_query
        
        # Your custom processing logic here
        results = await self.custom_processing(query)
        
        # Generate response
        content = self.generate_response(results)
        sources = self.format_sources(results)
        confidence = self.calculate_confidence(results)
        
        return content, sources, confidence
```

### Running Tests
```bash
# Unit tests
pytest tests/ -v

# Integration tests
pytest tests/test_integration.py -v

# Performance tests
pytest tests/test_performance.py -v

# Coverage report
pytest --cov=. --cov-report=html
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Run all quality checks
pre-commit run --all-files
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Cannot hash argument" Error in Streamlit
**Problem**: Streamlit caching error with object instances  
**Solution**: Add underscore prefix to method parameters
```python
# Wrong
@st.cache_resource
def load_model(self):
    return model

# Correct
@st.cache_resource
def load_model(_self):
    return model
```

#### 2. Import Errors in MSEIS Framework
**Problem**: Module not found errors  
**Solution**: Check Python path and virtual environment
```bash
# Ensure you're in the right directory
cd NEW_RAG/mseis

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Activate virtual environment
source ../venv/bin/activate  # On macOS/Linux
```

#### 3. API Connection Errors
**Problem**: Cannot connect to external APIs  
**Solution**: Check internet connection and API keys
```bash
# Test internet connectivity
curl https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY

# Verify API keys in .env file
cat .env | grep API_KEY
```

#### 4. Memory Issues with Large Knowledge Base
**Problem**: Out of memory during knowledge base building  
**Solution**: Reduce batch size or use incremental processing
```python
# In true_rag_system.py, reduce max_articles
nasa_docs = self.scrape_nasa_news(max_articles=20)  # Reduced from 50
arxiv_docs = self.scrape_arxiv_papers(query, max_papers=10)  # Reduced from 20
```

#### 5. Streamlit Port Already in Use
**Problem**: Port 8504 already occupied  
**Solution**: Use different port or kill existing process
```bash
# Check what's using the port
lsof -i :8504

# Kill process
kill -9 <PID>

# Or use different port
streamlit run true_rag_system.py --server.port 8505
```

### Performance Optimization

#### 1. Speed up Knowledge Base Building
```python
# Enable concurrent scraping
import asyncio
import aiohttp

async def scrape_multiple_sources():
    tasks = [
        scrape_nasa_news_async(),
        scrape_arxiv_papers_async(),
        scrape_esa_news_async()
    ]
    results = await asyncio.gather(*tasks)
    return results
```

#### 2. Optimize Vector Search
```python
# Use smaller embedding models for faster processing
model = SentenceTransformer('all-MiniLM-L6-v2')  # Faster
# vs
model = SentenceTransformer('all-mpnet-base-v2')  # More accurate but slower
```

### Logging and Debugging

#### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In Streamlit
st.write(f"Debug: Processing query: {query}")
st.write(f"Debug: Found {len(results)} results")
```

#### Monitor Performance
```python
import time

start_time = time.time()
# Your operation here
end_time = time.time()
st.write(f"Operation took {end_time - start_time:.2f} seconds")
```

---

## 📚 Additional Resources

### Documentation Links
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS Documentation](https://faiss.ai/)

### API Documentation
- [NASA Open Data API](https://api.nasa.gov/)
- [arXiv API](https://arxiv.org/help/api)
- [OpenAI API](https://platform.openai.com/docs)
- [Pinecone API](https://docs.pinecone.io/)

### Community Resources
- [RAG Best Practices](https://www.anthropic.com/research)
- [Vector Database Comparison](https://weaviate.io/blog/vector-database-comparison)
- [Multi-Agent Systems](https://github.com/microsoft/autogen)

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:
- Code style and formatting requirements
- Testing procedures
- Documentation standards
- Pull request process

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

**Happy Space Exploring! 🚀✨** 