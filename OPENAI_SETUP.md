# OpenAI Setup Guide for RAG System

This guide helps you set up cost-optimized OpenAI integration for your RAG system.

## 🎯 Quick Setup (5 minutes)

### 1. Get OpenAI API Key
- Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
- Click "Create new secret key"
- Name it "RAG-System" 
- **Copy the key immediately** (you won't see it again)
- Add $5-10 in credits for extensive testing

### 2. Set Environment Variable

**macOS/Linux:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Windows:**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**For permanent setup, add to your shell profile:**
```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Test the Integration
```bash
python test_openai_integration.py
```

## 💰 Cost Optimization Settings

### Environment Variables
```bash
export OPENAI_MODEL="gpt-4o-mini"      # Cheapest model (~$0.001/query)
export OPENAI_MAX_TOKENS="150"         # Control response length
```

### Cost Analysis
- **Model**: gpt-4o-mini (cheapest option)
- **Cost**: ~$0.001 per query
- **$5 Budget**: ~5,000 queries  
- **$10 Budget**: ~10,000 queries
- **Recruiter Demo**: 20 queries = $0.02

## 🌐 Streamlit Cloud Deployment

### 1. Add API Key to Streamlit Secrets
1. Go to your Streamlit Cloud app
2. Click "Settings" → "Secrets"
3. Add this content:
```toml
OPENAI_API_KEY = "your-api-key-here"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = "150"
```

### 2. Deploy Your App
- Push your code to GitHub
- Streamlit Cloud will automatically use the secrets
- Your app will show "🤖 OpenAI Ready" in the status

## ✅ Verification Checklist

### Local Testing
- [ ] OpenAI API key set in environment
- [ ] `python test_openai_integration.py` passes
- [ ] Cost tracking shows in console output
- [ ] Responses are high quality and concise

### Streamlit Cloud Testing  
- [ ] API key added to Streamlit secrets
- [ ] App status shows "🚀 AI: gpt-4o-mini ($0.001/query)"
- [ ] Queries generate proper AI responses (not just text compilation)
- [ ] No "Ollama unavailable" messages

## 🎯 Recruiter Demo Optimization

### Perfect Demo Setup
```bash
# Optimal settings for showcase
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_MAX_TOKENS="200"  # Slightly longer for impressive responses
```

### Demo Script Ideas
1. **Technical Query**: "Explain machine learning algorithms"
2. **Domain Knowledge**: "What are the latest trends in AI?"
3. **Complex Topic**: "Compare different database architectures"

### Cost Monitoring
- Each demo query costs ~$0.001
- 50 interview queries = $0.05
- Monthly showcase = ~$2-3 total

## 🚀 Production Scaling

### For Heavy Usage
```bash
export OPENAI_MODEL="gpt-3.5-turbo"  # Backup option if needed
export OPENAI_MAX_TOKENS="300"       # Longer responses
```

### Cost Management
- Monitor usage at [OpenAI Dashboard](https://platform.openai.com/usage)
- Set billing limits for safety
- gpt-4o-mini is already the cheapest option

## 🛠️ Troubleshooting

### Common Issues

**"OpenAI not available"**
- Check API key is set: `echo $OPENAI_API_KEY`
- Verify key is valid (not expired)
- Ensure you have credits in your account

**"API key needed for cloud deployment"**
- Add key to Streamlit Cloud secrets
- Restart your Streamlit app after adding secrets

**High costs**
- Reduce `OPENAI_MAX_TOKENS` 
- Use gpt-4o-mini (already set as default)
- Monitor usage in OpenAI dashboard

### Support Resources
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Streamlit Cloud Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

**🎉 You're ready to showcase your AI-powered RAG system to recruiters!**