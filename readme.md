# Multi-Modal Space Exploration Intelligence System (MSEIS)

A production-ready RAG system demonstrating advanced techniques for space exploration knowledge management using multi-agent orchestration, graph databases, and real-time data integration.

## 🚀 Features

### Core Capabilities
- **Multi-Agent Architecture**: Specialized agents for documents, images, graphs, and real-time data
- **Hybrid Retrieval**: Combines vector search, keyword matching, and graph traversal
- **Advanced Reranking**: Cross-encoder models with diversity optimization
- **Real-time Integration**: Live data from NASA APIs, ISS tracking, and space news
- **Graph RAG**: Neo4j-powered entity relationship management
- **Multi-modal Support**: Handles text, images, and structured data

### Technical Features
- **Production-Ready**: Docker containerization, monitoring, and logging
- **Scalable Design**: Horizontal scaling support with load balancing
- **Comprehensive Caching**: Redis-based caching for embeddings and responses
- **Rate Limiting**: Protects external API usage
- **Evaluation Framework**: Built-in metrics and LLM-based quality assessment

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Neo4j 5.15+
- Redis 7+
- CUDA-capable GPU (optional, for faster embeddings)

### API Keys Required
- OpenAI API key (GPT-4 and embeddings)
- Pinecone API key and environment
- NASA API key (free from https://api.nasa.gov)
- Optional: Anthropic API key

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/mseis.git
cd mseis
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 3. Install Dependencies

#### Using Docker (Recommended)
```bash
docker-compose up -d
```

#### Manual Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start required services
docker-compose up -d neo4j redis
```

### 4. Initialize Databases

#### Pinecone Setup
```python
# Run in Python shell
from storage.pinecone_manager import PineconeManager
import asyncio

async def setup_pinecone():
    manager = PineconeManager()
    await manager.initialize()
    print("Pinecone initialized successfully")

asyncio.run(setup_pinecone())
```

#### Neo4j Setup
The system will automatically create constraints and sample data on first run.

## 🚀 Quick Start

### 1. Start the API Server
```bash
python main.py
```

### 2. Launch Streamlit Interface
```bash
streamlit run streamlit_app.py
```

### 3. Access the Applications
- Streamlit UI: http://localhost:8501
- FastAPI Docs: http://localhost:8000/docs
- Prometheus Metrics: http://localhost:8000/metrics
- Neo4j Browser: http://localhost:7474

## 📖 Usage Examples

### Python API Client
```python
import aiohttp
import asyncio

async def query_mseis(query: str, expertise_level: str = "general"):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/query",
            json={
                "query": query,
                "expertise_level": expertise_level
            }
        ) as response:
            return await response.json()

# Example queries
result = asyncio.run(query_mseis(
    "What are the latest findings from the James Webb Space Telescope?"
))
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
print(f"Sources: {len(result['sources'])}")
```

### cURL Examples
```bash
# Simple query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current position of the ISS?",
    "expertise_level": "general"
  }'

# Health check
curl "http://localhost:8000/health"

# Get metrics
curl "http://localhost:8000/metrics"
```

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI                           │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Server                         │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                        │
│  ┌──────────┬──────────┬──────────┬──────────┐           │
│  │Document  │ Image    │ Graph    │ Realtime │           │
│  │Agent     │ Agent    │ Agent    │ Agent    │           │
│  └──────────┴──────────┴──────────┴──────────┘           │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                            │
│  ┌──────────┬──────────┬──────────┐                      │
│  │Pinecone  │ Neo4j    │ Redis    │                      │
│  │Vectors   │ Graph    │ Cache    │                      │
│  └──────────┴──────────┴──────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

1. **DocumentAgent**: Processes NASA papers, technical reports, and documentation
2. **ImageAgent**: Handles space imagery using CLIP embeddings and vision models
3. **GraphAgent**: Manages entity relationships (missions, astronauts, celestial bodies)
4. **RealtimeAgent**: Integrates live data (ISS position, NEOs, Mars weather)
5. **OrchestratorAgent**: Routes queries and synthesizes multi-agent responses

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/ -v --cov=.
```

### Run Integration Tests
```bash
pytest tests/test_integration.py -v
```

### Run Evaluation Benchmark
```bash
# Via API
curl -X POST "http://localhost:8000/evaluate"

# Via Python
python -m evaluation.evaluator
```

## 📊 Monitoring & Observability

### Prometheus Metrics
- Query latency by agent
- Cache hit rates
- Error rates
- Active queries
- Agent-specific metrics

### Structured Logging
All logs are in JSON format with correlation IDs for request tracing.

### Grafana Dashboards
Import dashboards from `monitoring/grafana/dashboards/`

## 🔧 Configuration

### Key Configuration Files
- `config.yaml`: System configuration
- `.env`: Environment variables and API keys
- `docker-compose.yml`: Service orchestration

### Performance Tuning
```yaml
# config.yaml
retrieval:
  top_k: 20              # Initial retrieval count
  rerank_top_k: 5        # Final result count
  hybrid:
    vector_weight: 0.7   # Vector search weight
    keyword_weight: 0.2  # Keyword search weight
    graph_weight: 0.1    # Graph search weight

cache:
  ttl: 3600             # Cache TTL in seconds
  max_size: 1000        # Maximum cache entries
```

## 📈 Performance Optimization

### 1. Embedding Caching
The system automatically caches embeddings in Redis to avoid recomputation.

### 2. Batch Processing
```python
# Process documents in batches
await document_agent.process_documents(
    documents=large_document_list,
    batch_size=100
)
```

### 3. Async Operations
All I/O operations are async for maximum concurrency.

### 4. Connection Pooling
Neo4j and Redis connections are pooled for efficiency.

## 🚢 Production Deployment

### Using Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale specific services
docker-compose up -d --scale mseis-app=3
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mseis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mseis
  template:
    metadata:
      labels:
        app: mseis
    spec:
      containers:
      - name: mseis
        image: mseis:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

### Environment Variables for Production
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_WORKERS=8
RATE_LIMIT_CALLS=1000
RATE_LIMIT_PERIOD=3600
```

## 🔒 Security Considerations

1. **API Key Management**: Use environment variables or secret management systems
2. **Rate Limiting**: Configured per endpoint to prevent abuse
3. **Input Validation**: All inputs are validated using Pydantic models
4. **CORS Configuration**: Restricted to allowed origins in production

## 🐛 Troubleshooting

### Common Issues

1. **Pinecone Connection Error**
   ```bash
   # Check Pinecone status
   curl https://status.pinecone.io/api/v2/status.json
   ```

2. **Neo4j Connection Failed**
   ```bash
   # Check Neo4j logs
   docker logs mseis-neo4j
   ```

3. **Out of Memory**
   - Reduce batch sizes in config.yaml
   - Increase Docker memory limits

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## 📚 Advanced Usage

### Adding New Data Sources

1. Create a new loader in `data_sources/`:
```python
# data_sources/custom_loader.py
class CustomSpaceDataLoader:
    async def load_data(self) -> List[Document]:
        # Implementation
        pass
```

2. Integrate with appropriate agent:
```python
# In document_agent.py
from data_sources.custom_loader import CustomSpaceDataLoader

loader = CustomSpaceDataLoader()
documents = await loader.load_data()
await self.process_documents(documents)
```

### Custom Evaluation Metrics

Add custom metrics to `evaluation/metrics.py`:
```python
class CustomMetrics:
    @staticmethod
    def space_accuracy(prediction: str, ground_truth: str) -> float:
        # Custom metric implementation
        pass
```

### Extending Agents

Create a new agent by extending BaseAgent:
```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def _setup(self):
        # Initialize agent components
        pass
        
    async def _process_query(self, context: QueryContext):
        # Process queries
        pass
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- NASA for providing open APIs and data
- OpenAI for GPT-4 and embeddings
- Pinecone for vector database
- Neo4j for graph database
- The open-source community for amazing tools

## 📮 Support

- Documentation: [Link to full docs]
- Issues: [GitHub Issues]
- Discussions: [GitHub Discussions]
- Email: support@mseis.example.com

---

Built with ❤️ for space exploration enthusiasts and AI researchers