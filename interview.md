# CosmoRAG EC2 Deployment - Technical Interview Guide

## Overview
This document explains the complete deployment architecture and process for CosmoRAG, a space-themed RAG (Retrieval-Augmented Generation) application deployed on AWS EC2. This covers the technical implementation, deployment strategies, and operational procedures.

## Application Architecture

### Core Components
- **Frontend**: Streamlit web application with cosmic-themed UI
- **Backend**: Python-based RAG system with OpenAI GPT-4o-mini integration
- **Vector Database**: FAISS for local vector storage with embedding search
- **Web Search**: DuckDuckGo integration for real-time information retrieval
- **Knowledge Base**: Curated space exploration content and NASA data

### Technology Stack
- **Runtime**: Python 3.8+ with virtual environment
- **Web Framework**: Streamlit for rapid UI development
- **AI/ML**: OpenAI API, sentence-transformers, FAISS
- **Search**: Custom web search manager with DuckDuckGo
- **Infrastructure**: AWS EC2 Ubuntu instance
- **Deployment**: Automated bash scripts with SSH/SCP

## AWS EC2 Infrastructure

### Instance Configuration
```yaml
Instance Type: t2.micro (1 vCPU, 1GB RAM)
Operating System: Ubuntu 22.04 LTS
Public IP: 18.117.163.37
Region: us-east-2 (Ohio)
Storage: 8GB gp2 EBS volume
```

### Security Configuration
```yaml
Security Groups:
  - HTTP (80): 0.0.0.0/0
  - HTTPS (443): 0.0.0.0/0  
  - Custom TCP (8501): 0.0.0.0/0  # Streamlit port
  - SSH (22): Restricted to specific IPs

SSH Access:
  - Key Pair: aswin.pem (RSA 2048-bit)
  - Username: ubuntu
  - Connection: ssh -i aswin.pem ubuntu@18.117.163.37
```

### Server Environment Setup
```bash
# System packages
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git curl -y

# Python virtual environment
cd /home/ubuntu/NEW_RAG
python3 -m venv venv
source venv/bin/activate

# Application dependencies
pip install -r requirements.txt
```

## Deployment Process

### 1. Automated Deployment Script (`update_ec2.sh`)

The deployment is fully automated through a bash script that handles:

```bash
#!/bin/bash
# Key configuration
EC2_HOST="18.117.163.37"
EC2_USER="ubuntu"
PEM_KEY_PATH="/Users/aswin/Downloads/aswin.pem"
PROJECT_PATH="/home/ubuntu/NEW_RAG"
```

**Script Functions:**
1. **Directory Creation**: Creates necessary folders on EC2
2. **Secrets Management**: Configures Streamlit secrets.toml with API keys
3. **File Upload**: Uses SCP to transfer application files
4. **Dependency Management**: Installs/updates Python packages
5. **Service Restart**: Restarts Streamlit application

### 2. File Transfer Process

**Core Application Files:**
```bash
# Main application
scp app.py ubuntu@EC2_HOST:/home/ubuntu/NEW_RAG/

# RAG system components  
scp simple_rag_system.py ubuntu@EC2_HOST:/home/ubuntu/NEW_RAG/
scp web_search_manager.py ubuntu@EC2_HOST:/home/ubuntu/NEW_RAG/

# Dependencies and data
scp requirements.txt ubuntu@EC2_HOST:/home/ubuntu/NEW_RAG/
scp data/knowledge_base.json ubuntu@EC2_HOST:/home/ubuntu/NEW_RAG/data/
scp storage/space_facts.json ubuntu@EC2_HOST:/home/ubuntu/NEW_RAG/storage/

# Static assets
scp static/backgrounds/main_nasa_bg.jpg ubuntu@EC2_HOST:/home/ubuntu/NEW_RAG/static/backgrounds/
```

### 3. Configuration Management

**Streamlit Secrets (`/.streamlit/secrets.toml`):**
```toml
# API Configuration - Deployed automatically
OPENAI_API_KEY = "your-api-key-here"
```

**Environment Variables:**
- OpenAI API key for enhanced AI responses
- Configured through Streamlit secrets for security
- No fallback mode - production uses OpenAI exclusively

### 4. Service Management

**Application Startup:**
```bash
# Kill existing processes
pkill -f streamlit || true

# Clean logs
rm -f streamlit.log

# Start Streamlit in background
nohup ./venv/bin/streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  > streamlit.log 2>&1 &
```

**Health Monitoring:**
```bash
# Check HTTP status
curl -s -o /dev/null -w "%{http_code}" http://18.117.163.37:8501

# Monitor logs
tail -f /home/ubuntu/NEW_RAG/streamlit.log

# Process verification
ps aux | grep streamlit
```

## Development Workflow

### 1. Local Development
```bash
# Local testing environment
streamlit run app.py  # Test at localhost:8501
python -m pytest     # Run unit tests if available
```

### 2. Code Changes Process
1. **Local Development**: Make changes in local repository
2. **Testing**: Verify functionality locally
3. **Deployment**: Run `./update_ec2.sh` for automated deployment
4. **Verification**: Check application status and logs
5. **Monitoring**: Ensure proper operation

### 3. Deployment Commands
```bash
# Full deployment
chmod +x update_ec2.sh && ./update_ec2.sh

# Manual deployment steps (if script fails)
scp app.py ubuntu@18.117.163.37:/home/ubuntu/NEW_RAG/
ssh ubuntu@18.117.163.37 "cd /home/ubuntu/NEW_RAG && ./restart.sh"
```

## Technical Implementation Details

### 1. RAG System Architecture

**Query Processing Flow:**
```python
# 1. Query received from Streamlit UI
# 2. Vector similarity search in FAISS index
# 3. Web search fallback using DuckDuckGo
# 4. Context assembly with retrieved documents
# 5. OpenAI GPT-4o-mini generation with context
# 6. Response formatting and source attribution
```

**Smart LLM Selection:**
```python
async def _generate_smart_response(self, query: str, search_results: List[SearchResult]) -> str:
    # OpenAI-first approach for cloud deployment reliability
    if self.openai_available:
        return await self._generate_openai_response(query, search_results)
    # Local Ollama fallback (disabled in production)
```

### 2. Performance Optimizations

**Caching Strategy:**
- Streamlit `@st.cache_resource` for RAG system initialization
- `@st.cache_data` for static content loading
- Session state management for query persistence

**Async Operations:**
- Async/await pattern for AI model calls
- Concurrent web search requests
- Non-blocking UI updates

### 3. Error Handling

**Graceful Degradation:**
```python
# Network connectivity issues
except ConnectionError:
    return "Network connection issue. Please check connectivity."

# API rate limiting
except RateLimitError:
    return "AI service temporarily unavailable. Please try again."

# General exceptions
except Exception as e:
    return f"Technical issue encountered: {str(e)}"
```

## Key Files and Purpose

### Core Application Files
- **`app.py`**: Main Streamlit application with cosmic UI
- **`simple_rag_system.py`**: RAG implementation with OpenAI integration
- **`web_search_manager.py`**: DuckDuckGo search functionality
- **`requirements.txt`**: Python dependencies specification

### Configuration Files  
- **`update_ec2.sh`**: Automated deployment script
- **`.streamlit/secrets.toml`**: API keys and sensitive configuration
- **`data/knowledge_base.json`**: Curated space exploration content
- **`storage/space_facts.json`**: Space facts for educational content

### Static Assets
- **`static/backgrounds/main_nasa_bg.jpg`**: NASA Hubble Deep Field background
- **Custom CSS**: Embedded cosmic theme styling

## Monitoring and Troubleshooting

### 1. Health Checks
```bash
# Application availability
curl -I http://18.117.163.37:8501

# Process monitoring  
ssh ubuntu@18.117.163.37 "ps aux | grep streamlit"

# Log analysis
ssh ubuntu@18.117.163.37 "tail -f /home/ubuntu/NEW_RAG/streamlit.log"
```

### 2. Common Issues and Solutions

**Issue: Application not responding**
```bash
# Solution: Restart service
ssh ubuntu@18.117.163.37 "cd /home/ubuntu/NEW_RAG && pkill -f streamlit && nohup ./venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &"
```

**Issue: Import errors**  
```bash
# Solution: Reinstall dependencies
ssh ubuntu@18.117.163.37 "cd /home/ubuntu/NEW_RAG && source venv/bin/activate && pip install -r requirements.txt"
```

**Issue: API key not working**
```bash
# Solution: Verify secrets configuration
ssh ubuntu@18.117.163.37 "cat /home/ubuntu/NEW_RAG/.streamlit/secrets.toml"
```

### 3. Performance Monitoring

**Response Time Tracking:**
- Built-in timing in RAG system
- Query processing metrics logged
- Token usage monitoring for cost optimization

**Resource Usage:**
```bash
# Memory and CPU monitoring
ssh ubuntu@18.117.163.37 "htop"
ssh ubuntu@18.117.163.37 "free -h && df -h"
```

## Security Considerations

### 1. API Key Management
- OpenAI API key stored in Streamlit secrets
- Not committed to version control
- Deployed securely through automation script

### 2. Network Security
- EC2 security groups restrict access appropriately  
- SSH key-based authentication only
- HTTPS ready (though currently HTTP for development)

### 3. Application Security  
- Input validation for user queries
- Safe HTML rendering in Streamlit
- No sensitive data logged

## Scalability and Future Improvements

### 1. Current Limitations
- Single EC2 instance (no high availability)
- Local FAISS storage (not distributed) 
- Manual deployment process

### 2. Scaling Opportunities
- **Load Balancing**: Multiple EC2 instances behind ALB
- **Database**: Migration to managed vector database (Pinecone)
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Monitoring**: CloudWatch integration for metrics and alerting
- **Containerization**: Docker deployment for consistency

### 3. Cost Optimization
- Current setup: ~$8-12/month (t2.micro + OpenAI API usage)
- Token usage optimization in RAG system
- Efficient query processing to minimize API calls

## Interview Discussion Points

### Technical Architecture
- Why RAG over fine-tuning for this use case?
- OpenAI vs local models trade-offs
- Vector database selection criteria
- Async programming benefits in web applications

### Infrastructure Decisions
- EC2 vs managed services (ECS, Lambda, App Runner)
- Security group configuration rationale
- Cost vs performance optimization

### Development Practices  
- Deployment automation benefits
- Error handling and graceful degradation
- Monitoring and observability strategies
- Code organization and maintainability

### Scalability Planning
- Bottleneck identification and mitigation
- Horizontal vs vertical scaling approaches  
- Database migration strategies
- CI/CD implementation roadmap

This deployment demonstrates practical cloud infrastructure management, automated deployment processes, and production-ready application architecture suitable for real-world applications.