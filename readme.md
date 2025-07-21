# IntelliSearch - Intelligent Information Retrieval System

A professional RAG (Retrieval-Augmented Generation) system with semantic search and web fallback capabilities. Built for zero-hallucination information retrieval with enterprise-grade interface.

![IntelliSearch](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

🔍 **Semantic Search**: Advanced FAISS-powered similarity search with configurable thresholds
🌐 **Web Fallback**: Automatic web search when local knowledge base lacks relevant content
🚫 **Zero Hallucination**: Strict context-only responses to prevent AI from generating unverified information
🎨 **Professional Interface**: Clean, minimal design suitable for enterprise demonstrations
⚡ **Multi-LLM Support**: Works with both free Ollama models and OpenAI API
📊 **1,100+ Space Articles**: Pre-indexed knowledge base covering space exploration, astronomy, and physics

## Quick Start

### Prerequisites

- Python 3.8 or higher
- (Optional) Ollama for free local AI inference
- (Optional) OpenAI API key for enhanced capabilities

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/intellisearch.git
cd intellisearch
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up AI providers (choose one or both)**

**Option A: Free Local AI with Ollama** (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model (in new terminal)
ollama pull llama3.2:3b
```

**Option B: OpenAI API**
```bash
# Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### Usage

**Start the application**
```bash
streamlit run intellisearch.py
```

**Access the interface**
- Open your browser to `http://localhost:8501`
- Enter queries in the search box
- System automatically searches local knowledge base first
- Falls back to web search if no relevant local content found

## 📖 Example Analysis

### For `karpathy/micrograd`:

**📄 micrograd/engine.py**
> "This file implements the core automatic differentiation engine with the Value class that tracks gradients for backpropagation in neural networks."

**📄 micrograd/nn.py** 
> "This file provides neural network building blocks including Neuron, Layer, and MLP classes for creating trainable networks using the micrograd engine."

**🤖 Overall Insights:**
> "This is a minimal deep learning library focused on educational purposes. The codebase demonstrates clean architecture with separation between the autodiff engine and neural network components..."

## 🛠️ Supported Languages

- **Python** (.py)
- **JavaScript** (.js, .jsx)
- **TypeScript** (.ts, .tsx)
- **Java** (.java)
- **C/C++** (.c, .cpp)
- **Go** (.go)
- **Rust** (.rs)
- **PHP** (.php)
- **Ruby** (.rb)
- **Configuration** files (.json, .yaml, .toml)
- **Documentation** (.md, .txt)

## 📋 Interface Overview

### 🔧 Sidebar Features
- **Ollama Status** - Real-time connection status
- **Model Information** - Currently active model
- **Setup Instructions** - Help for first-time users

### 📊 Analysis Tabs
1. **📁 File Structure** - Visual breakdown and file type distribution
2. **📄 File Explanations** - Searchable, categorized file explanations
3. **🤖 AI Insights** - Overall project analysis and recommendations
4. **⚙️ Technologies** - Detected tech stack and key files

## ⚙️ Configuration

### Ollama Models

Choose the right model for your needs:

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `llama3.2:3b` | 2GB | Fast | Good | Quick analysis, demos |
| `llama3.2:7b` | 4GB | Medium | Better | Detailed analysis |
| `codellama:7b` | 4GB | Medium | Code-focused | Programming projects |

### System Requirements

**Minimum:**
- 8GB RAM
- 5GB free disk space
- Python 3.8+

**Recommended:**
- 16GB RAM (for 7b models)
- 10GB free disk space
- SSD storage

## 🔧 Troubleshooting

### Common Issues

**1. "Ollama not available"**
```bash
# Check if Ollama is running
ollama list

# If not, start it
ollama serve
```

**2. "Model not found"**
```bash
# Pull the default model
ollama pull llama3.2:3b
```

**3. "Analysis failed"**
- Ensure the repository is public
- Check your internet connection for cloning
- Try a smaller repository first

**4. "Port already in use"**
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

## 🏗️ Architecture

```
code_analyzer/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── LICENSE               # MIT license
```

### Key Components

- **RepositoryAnalyzer**: Core analysis engine
- **File Processors**: Extract imports, functions, classes
- **AI Integration**: Ollama communication layer
- **UI Components**: Streamlit interface

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/code_analyzer.git

# Install in development mode
pip install -e .

# Run tests (if available)
pytest
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** for providing free local LLM infrastructure
- **Streamlit** for the amazing web framework
- **The open source community** for inspiration and tools

## 📊 Statistics

- 🎯 **0 API Costs** - Completely free to run
- ⚡ **~30-60 seconds** average analysis time
- 🔍 **20+ file types** supported
- 🧠 **Multiple AI models** available

## 🔗 Links

- [Ollama Installation](https://ollama.ai/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Report Issues](https://github.com/yourusername/code_analyzer/issues)

---

Made with ❤️ for the developer community. Analyze any repository, understand any codebase, completely free!