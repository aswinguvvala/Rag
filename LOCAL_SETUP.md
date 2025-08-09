# Local Development Setup Guide

Complete guide for running IntelliSearch locally with Qwen-first AI integration.

## 🎯 Overview

IntelliSearch now uses **Qwen 0.5B** as the primary AI model with **OpenAI GPT-4o-mini** as fallback. The system implements three intelligent response flows:

1. **Local Content Flow**: Database search → Qwen processes local content
2. **Web Search Flow**: DuckDuckGo search → Qwen processes web content  
3. **General Knowledge Flow**: No external content → Qwen uses built-in knowledge

## 🚀 Quick Start

### 1. Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

### 2. Install and Configure Qwen AI Model

```bash
# Install Ollama (AI model runner)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull Qwen 0.5B model (primary AI - lightweight and fast)
ollama pull qwen2.5:0.5b

# Optional: Pull backup models for redundancy
ollama pull qwen2.5:1.5b  # Slightly larger but more capable
ollama pull llama3.2:1b   # Fallback option
```

### 3. Configure Environment (Optional)

Create a `.env` file for enhanced functionality:

```bash
# Optional: Add OpenAI API key for fallback capability
echo "OPENAI_API_KEY=your-openai-api-key-here" > .env

# Optional: Set preferred model (defaults to qwen2.5:0.5b)
echo "OLLAMA_MODEL=qwen2.5:0.5b" >> .env
```

### 4. Run the Application

```bash
# Start the Streamlit application
streamlit run app.py
```

### 5. Access Locally

- **Local URL**: http://localhost:8501
- **Network URL**: http://[your-local-ip]:8501 (for testing from other devices)

## 🧠 AI Model Hierarchy

The system automatically follows this priority order:

1. **Primary**: Qwen 0.5B (via Ollama) - Fast, efficient, privacy-friendly
2. **Fallback**: OpenAI GPT-4o-mini - Cloud-based, requires API key
3. **Final**: Simple text compilation - Basic response generation

## 🔍 Response Flow Details

### Flow 1: Local Content Available
```
User Query → Vector Search → Local Content Found → Qwen AI → Response
```

### Flow 2: Web Search Required
```
User Query → No Local Content → DuckDuckGo Search → Qwen AI → Response
```

### Flow 3: General Knowledge Mode
```
User Query → No Local/Web Content → Qwen General Knowledge → Response
```

## 🛠️ Advanced Configuration

### Model Selection Priority

The system automatically selects the best available model:

1. `qwen2.5:0.5b` - Primary choice (fastest)
2. `qwen2.5:1.5b` - Better quality option
3. `qwen2.5:3b` - Highest quality Qwen model
4. `llama3.2:1b` - Backup option
5. `llama3.2:3b` - Legacy fallback

### Performance Tuning

For optimal performance on your hardware:

```bash
# For low-end systems (4GB RAM)
ollama pull qwen2.5:0.5b

# For mid-range systems (8GB RAM) 
ollama pull qwen2.5:1.5b

# For high-end systems (16GB+ RAM)
ollama pull qwen2.5:3b
```

### Custom Background/Theme Options

Edit `app.py` to customize the UI:

```python
# Line 32: Change background image
background-image: url('your-custom-background.jpg');

# Line 428: Modify title
<span class="title-text">Your Custom Title</span>

# Line 459: Update subtitle
<p class="cosmic-subtitle">Your custom tagline</p>
```

## 🔧 Troubleshooting

### Common Issues

**1. Qwen model not found**
```bash
# Check available models
ollama list

# Pull the model if missing
ollama pull qwen2.5:0.5b
```

**2. Ollama service not running**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

**3. Port 8501 already in use**
```bash
# Run on different port
streamlit run app.py --server.port 8502
```

**4. Import errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Performance Issues

**Slow AI responses:**
- Switch to smaller model: `ollama pull qwen2.5:0.5b`  
- Close other applications to free up RAM
- Check CPU usage with `htop` or Task Manager

**Memory issues:**
- Use the 0.5B model instead of larger versions
- Restart Ollama: `pkill ollama && ollama serve`

## 📊 System Requirements

### Minimum Requirements
- **RAM**: 4GB (for qwen2.5:0.5b)
- **Storage**: 2GB free space
- **CPU**: Any modern processor
- **OS**: Windows 10+, macOS 10.15+, Linux

### Recommended Setup
- **RAM**: 8GB+ (for qwen2.5:1.5b)
- **Storage**: 5GB free space
- **CPU**: Multi-core processor
- **GPU**: Optional (Ollama can use GPU acceleration)

## 🌐 Sharing Your Local Instance

You can share your local development server:

```bash
# Find your local IP address
ipconfig  # Windows
ifconfig  # Mac/Linux

# Share this URL with others on your network
http://[your-local-ip]:8501
```

**Important**: Your local server is only accessible on your local network unless you configure port forwarding.

## 🔒 Privacy & Security

### Data Privacy
- **Qwen models run locally** - No data sent to external servers
- **OpenAI fallback** - Only used when Qwen fails (requires API key)
- **Web search** - Uses DuckDuckGo (privacy-focused)

### Security Considerations
- Local models are completely private
- Web search queries are not logged
- No user data is stored permanently

## 🚀 Production Deployment

Your AWS EC2 instance (http://18.117.163.37:8501) can be shared with others for testing:

### AWS Free Tier Considerations
- **750 hours/month** EC2 usage (plenty for demos)
- **15GB data transfer/month** (monitor with multiple users)
- **No concurrent user limits** from AWS side

### Monitoring Usage
1. Check AWS billing dashboard regularly
2. Set up CloudWatch alerts for resource usage
3. Monitor data transfer if sharing widely

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Ensure all dependencies are installed correctly
3. Verify Ollama is running and Qwen model is downloaded
4. Check system resources (RAM, CPU usage)

---

## 🎉 You're Ready!

Your IntelliSearch application is now configured with:
- ✅ Qwen 0.5B as primary AI model
- ✅ Three intelligent response flows
- ✅ Local privacy-first operation
- ✅ OpenAI fallback for enhanced capability
- ✅ Comprehensive error handling

Enjoy your local AI-powered search experience! 🚀