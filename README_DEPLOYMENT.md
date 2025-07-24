# IntelliSearch - Streamlit Deployment Guide

🚀 **Advanced Space Intelligence & Research System**

## Quick Deploy to Streamlit Cloud

1. **Fork or Clone** this repository to your GitHub account

2. **Go to** [share.streamlit.io](https://share.streamlit.io)

3. **Connect your GitHub** account and select this repository

4. **Set the main file path** to: `intellisearch.py`

5. **Add Environment Variables** (Optional but recommended):
   - `OPENAI_API_KEY`: Your OpenAI API key for enhanced capabilities
   - `PINECONE_API_KEY`: For cloud vector storage (optional)

6. **Deploy!** - Streamlit Cloud will automatically install dependencies and launch your app

## Features

✨ **Enhanced User Experience**:
- AI response displayed first, then sources
- Space-themed background with stunning visuals
- Fixed query input box styling
- Enhanced source linking with full URLs
- Clickable [Source X] citations linking to full articles
- Professional Sources & References section

🔧 **Technical Improvements**:
- Streamlit Cloud optimized configuration
- Proper fallback systems for all services
- Mobile-responsive design
- Performance optimized assets

## Usage

1. Enter your query in the search box
2. Click "🚀 SEARCH" to process your question
3. View the AI response with enhanced citations
4. Explore sources with full article links
5. Click on any [Source X] citation to view the full article

## System Requirements

- Python 3.8+
- Dependencies automatically installed from `requirements.txt`
- Optional: OpenAI API key for enhanced capabilities
- Automatic fallback to basic mode if advanced features unavailable

## Configuration

- **Theme**: Space-themed with customizable colors in `.streamlit/config.toml`
- **Performance**: Optimized for cloud deployment
- **Security**: Production-ready configuration

Built with ❤️ for space exploration and intelligent research.