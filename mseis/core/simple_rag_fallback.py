# core/simple_rag_fallback.py
"""
Simple RAG Fallback System
Lightweight alternative when heavy ML dependencies fail
Uses basic text matching and web search
"""

import asyncio
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import aiohttp

class SimpleRAGFallback:
    """Lightweight RAG system using basic text matching"""
    
    def __init__(self):
        self.documents = []
        self.is_initialized = False
        self.simple_index = {}  # Word to document mapping
        
    async def initialize(self):
        """Initialize the simple fallback system"""
        try:
            # Load any existing simple documents
            await self._load_simple_documents()
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Simple RAG initialization failed: {e}")
            return False
    
    async def _load_simple_documents(self):
        """Load documents from a simple JSON file"""
        doc_path = Path("./storage/simple_docs.json")
        if doc_path.exists():
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                self._build_simple_index()
            except:
                # Create some default documents if file doesn't exist or is corrupted
                self.documents = [
                    {
                        "id": "welcome",
                        "title": "Welcome to IntelliSearch",
                        "content": "IntelliSearch is an intelligent information retrieval system that provides semantic search capabilities with web fallback.",
                        "source": "system"
                    },
                    {
                        "id": "features", 
                        "title": "IntelliSearch Features",
                        "content": "Features include advanced RAG (Retrieval-Augmented Generation), semantic search, web fallback, and AI-powered responses.",
                        "source": "system"
                    }
                ]
                self._build_simple_index()
    
    def _build_simple_index(self):
        """Build a simple word-to-document index"""
        self.simple_index = {}
        for i, doc in enumerate(self.documents):
            words = self._extract_words(doc.get('content', '') + ' ' + doc.get('title', ''))
            for word in words:
                if word not in self.simple_index:
                    self.simple_index[word] = set()
                self.simple_index[word].add(i)
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text for simple matching"""
        # Convert to lowercase and extract alphanumeric words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return words
    
    async def query(self, query_text: str, max_results: int = 3) -> Dict[str, Any]:
        """Simple query using basic text matching"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Extract query words
            query_words = set(self._extract_words(query_text))
            
            # Score documents based on word overlap
            doc_scores = {}
            for word in query_words:
                if word in self.simple_index:
                    for doc_idx in self.simple_index[word]:
                        if doc_idx not in doc_scores:
                            doc_scores[doc_idx] = 0
                        doc_scores[doc_idx] += 1
            
            # Get top documents
            top_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:max_results]
            
            results = []
            for doc_idx, score in top_docs:
                if doc_idx < len(self.documents):
                    doc = self.documents[doc_idx]
                    results.append({
                        'content': doc.get('content', ''),
                        'title': doc.get('title', ''),
                        'source': doc.get('source', 'unknown'),
                        'similarity': score / len(query_words) if query_words else 0
                    })
            
            # If no good matches, provide web search suggestion
            if not results or (results and results[0]['similarity'] < 0.3):
                web_suggestion = await self._get_web_search_suggestion(query_text)
                return {
                    'local_results': results,
                    'has_similar': len(results) > 0,
                    'web_suggestion': web_suggestion,
                    'response_type': 'fallback'
                }
            
            return {
                'local_results': results,
                'has_similar': True,
                'response_type': 'simple_match'
            }
            
        except Exception as e:
            return {
                'local_results': [],
                'has_similar': False,
                'error': str(e),
                'response_type': 'error'
            }
    
    async def _get_web_search_suggestion(self, query: str) -> str:
        """Generate a web search suggestion"""
        return f"For more comprehensive results about '{query}', consider searching the web or checking official documentation."
    
    async def add_document(self, title: str, content: str, source: str = "user") -> bool:
        """Add a document to the simple index"""
        try:
            doc_id = f"doc_{len(self.documents)}"
            new_doc = {
                "id": doc_id,
                "title": title,
                "content": content,
                "source": source
            }
            self.documents.append(new_doc)
            self._build_simple_index()  # Rebuild index
            
            # Save to file
            doc_path = Path("./storage")
            doc_path.mkdir(exist_ok=True)
            with open(doc_path / "simple_docs.json", 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to add document: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get simple statistics"""
        return {
            'total_documents': len(self.documents),
            'total_words': len(self.simple_index),
            'system_type': 'simple_fallback',
            'is_initialized': self.is_initialized
        }