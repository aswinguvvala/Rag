# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains three integrated AI systems that demonstrate cutting-edge technologies in different domains:

1. **Free LLM Repository Analyzer** - GitHub repository analysis using local AI models
2. **MSEIS (Multi-Modal Space Exploration Intelligence System)** - Advanced space exploration intelligence
3. **Advanced RAG System** - Recruitment intelligence with latest RAG techniques
4. **Unified RAG System** - Integration layer combining all capabilities

## Development Commands

### Environment Setup
```bash
# Core dependencies (choose one environment)
pip install -r requirements.txt  # Main requirements
pip install -r mseis/requirements.txt  # MSEIS-specific requirements

# Optional: Ollama for free local LLM (recommended)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3.1:8b

# Environment variables
export OPENAI_API_KEY="your-key"  # Optional, for enhanced capabilities
export PINECONE_API_KEY="your-key"  # Optional, for cloud vector storage
export NASA_API_KEY="your-key"  # Optional, for enhanced space data
```

### Running Applications

#### Repository Analyzer
```bash
streamlit run app.py
# Access at http://localhost:8501
```

#### MSEIS Space Intelligence System
```bash
# FastAPI backend
python mseis/main.py

# Streamlit interface
streamlit run mseis_streamlit.py

# Master demo
python mseis_master_demo.py

# Enhanced space data demo (NEW)
python space_data_demo.py
python test_space_data_simple.py  # Standalone test
```

#### Advanced RAG System
```bash
cd advanced_rag_system

# Command line demo
python main.py demo
python main.py interactive
python main.py benchmark

# Web interface
streamlit run demo_streamlit.py
```

#### Unified System Demo
```bash
# Integration tests
python test_integration.py

# Recruitment-focused demo
python recruitment_demo.py
```

### Testing & Development

#### System Tests
```bash
# MSEIS system tests
python mseis/test_system.py
python mseis/test_enhanced_agents.py

# Integration testing
python test_integration.py

# RAG system validation
cd advanced_rag_system && python main.py benchmark
```

#### Individual Component Testing
```bash
# Test specific MSEIS agents
python -c "
import asyncio
from mseis.agents.document_agent import DocumentAgent
agent = DocumentAgent()
asyncio.run(agent.initialize())
"

# Test LLM factory
python -c "
import asyncio
from mseis.core.llm_factory import get_llm_status
asyncio.run(get_llm_status())
"
```

## System Architecture

### High-Level Architecture

The repository implements a **layered intelligence architecture** that routes queries to specialized systems:

```
┌─────────────────────────────────────────────────────────┐
│                 Unified RAG System                      │
│         (Intelligent Query Router & Orchestrator)      │
└─────────────────┬─────────────────┬─────────────────────┘
                  │                 │
        ┌─────────▼─────────┐      ┌▼─────────────────┐
        │  Advanced RAG     │      │      MSEIS       │
        │  (Recruitment)    │      │ (Space Exploration)│
        └───────────────────┘      └──────────────────┘
```

### Query Routing Logic
- **Recruitment queries** → Advanced RAG System (Self-RAG, CRAG, Agentic capabilities)
- **Space exploration** → MSEIS specialized agents
- **Code analysis** → MSEIS code intelligence agents  
- **Multi-modal content** → MSEIS document/image agents
- **Complex synthesis** → Combined capabilities through Unified System

### Core Integration Points

#### LLM Factory (`mseis/core/llm_factory.py`)
- **Async-first design** with intelligent fallback (Ollama → OpenAI)
- **Health monitoring** and provider availability checking
- **Unified interface** across all systems

#### Configuration Management (`mseis/config.yaml`)
- **Environment variable substitution** with `${VAR_NAME}` syntax
- **Hierarchical configuration** supporting both systems
- **Provider selection**: `llm.primary_provider: "ollama"` for free operation

#### Vector Storage Strategy
- **Local-first approach**: Chroma DB for development, FAISS for performance
- **Cloud scaling**: Pinecone integration for production workloads
- **Specialized collections**: Separate namespaces for recruitment vs space data

### Agent Architecture (MSEIS)

MSEIS implements a **multi-agent system** where specialized agents handle different aspects:

- **OrchestorAgent**: Routes queries to appropriate specialized agents
- **DocumentAgent**: Processes textual content with advanced chunking strategies
- **ImageAgent**: Handles visual content using CLIP embeddings
- **CodeIntelligenceAgent**: Analyzes repositories and code patterns
- **AutonomousResearchAgent**: Conducts multi-step research with hypothesis generation
- **TemporalAnalysisAgent**: Tracks dependencies and timeline analysis
- **KnowledgeSynthesisAgent**: Cross-domain pattern discovery

### Advanced RAG Patterns

The Advanced RAG system implements cutting-edge techniques:

- **Self-RAG**: Autonomous response evaluation and iterative improvement
- **CRAG (Corrective RAG)**: Fact verification and response correction
- **Agentic RAG**: Multi-agent collaboration for complex tasks
- **Adaptive Strategy**: Dynamic approach selection based on query complexity

## Key Implementation Patterns

### Async-First Design
All major operations use `async/await` patterns for performance:
```python
# Correct pattern used throughout
result = await agent.process_query(context)
await vector_store.add_documents(documents)
```

### Configuration-Driven Behavior
Systems adapt behavior based on YAML configuration:
```python
# Configuration controls system behavior
if config.get('rag.self_rag.enabled'):
    result = await self_rag_pipeline.process(query)
```

### Provider Abstraction
LLM and vector providers are abstracted for easy switching:
```python
# Same interface works with different providers
llm_factory = get_llm_factory()  # Auto-selects Ollama or OpenAI
vector_store = get_vector_store()  # Auto-selects Chroma, FAISS, or Pinecone
```

### Error Handling with Fallbacks
Systems implement graceful degradation:
```python
# Primary provider with fallback
try:
    result = await ollama_provider.generate(prompt)
except Exception:
    result = await openai_provider.generate(prompt)  # Fallback
```

## Data Sources and Knowledge Base

### Current Data Sources
- **Recruitment Data**: Job descriptions, resumes, company profiles, skill requirements
- **Space Data**: NASA APIs, mission databases, celestial body information
- **Code Repositories**: GitHub analysis, architecture patterns, technology stacks

### Adding New Data Sources
1. Create data loader in `mseis/data_sources/`
2. Add configuration in `mseis/config.yaml`
3. Register with appropriate agents in agent initialization
4. Update vector store collections for organized retrieval

### Space Data Enhancement (COMPLETED)
Enhanced space data integration now includes:
- **NASA APOD**: Astronomy Picture of the Day with educational content
- **NASA Missions**: TechPort API for current and planned space missions
- **SpaceX Data**: Launch history and rocket specifications
- **Celestial Bodies**: Comprehensive database of planets, moons, and objects
- **Real-time Tracking**: International Space Station position and status
- **Exoplanet Archive**: Discovered exoplanets and potentially habitable worlds
- **Space Technology**: Instruments, observatories, and spacecraft specifications

**Key Features**:
- 21 documents across 5 categories
- Multi-source async data loading
- Rich metadata and categorization
- Error handling with simulated fallbacks
- Integration with unified RAG system for space queries

**Testing**: Run `python test_space_data_simple.py` to validate space data loading

## Production Considerations

### Free vs Paid Operation
- **Free Mode**: Ollama + Chroma + local processing (recommended for development)
- **Enhanced Mode**: OpenAI + Pinecone + external APIs (production scaling)

### Performance Optimization
- **Caching**: Multi-level caching in embedding managers and retrievers
- **Batching**: Automatic batching for vector operations
- **Async Processing**: Concurrent query handling across agents

### Monitoring and Observability
- **Health Checks**: Available at `/health` endpoints
- **Performance Metrics**: Built-in timing and confidence tracking
- **Quality Monitoring**: Automatic evaluation of response quality

## System Integration Points

### MSEIS ↔ Advanced RAG Integration
- **Query Classification**: Unified system determines optimal processing path
- **Agent Collaboration**: MSEIS agents can be invoked by Advanced RAG for specialized tasks
- **Knowledge Sharing**: Both systems access shared vector stores and configuration

### Multi-Modal Processing Flow
1. **Query Analysis**: Determine content type and complexity
2. **Agent Selection**: Route to appropriate specialized agents
3. **Multi-Modal Fusion**: Combine text, image, and structured data insights
4. **Quality Assurance**: Self-evaluation and correction loops
5. **Response Synthesis**: Unified response generation

This architecture enables sophisticated AI capabilities while maintaining modularity and extensibility for future enhancements.