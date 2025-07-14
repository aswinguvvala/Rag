import requests
import json
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Data class for LLM responses"""
    content: str
    confidence: float
    reasoning: str = ""
    model_used: str = ""

class OllamaLLM:
    """Free LLM integration using Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_answer(self, query: str, context_documents: List[Dict], expertise_level: str = "general") -> LLMResponse:
        """Generate a comprehensive answer using retrieved context"""
        if not self.is_available():
            return LLMResponse(
                content="LLM service is not available. Using fallback method.",
                confidence=0.0,
                reasoning="Ollama service offline"
            )
        
        # Build context from documents
        context_text = self._build_context(context_documents)
        
        # Create prompt based on expertise level
        prompt = self._create_answer_prompt(query, context_text, expertise_level)
        
        try:
            response = self._call_ollama(prompt)
            
            # Parse response and extract confidence
            content = response.get("response", "")
            confidence = self._calculate_confidence(content, context_documents)
            
            return LLMResponse(
                content=content,
                confidence=confidence,
                reasoning=f"Generated from {len(context_documents)} sources",
                model_used=self.model
            )
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return LLMResponse(
                content=f"Error generating answer: {str(e)}",
                confidence=0.0,
                reasoning="LLM generation failed"
            )
    
    def detect_query_domain(self, query: str) -> Tuple[str, float]:
        """Detect the domain/topic of the query"""
        if not self.is_available():
            return "unknown", 0.0
        
        prompt = f"""Analyze this query and determine its main domain/topic:
Query: "{query}"

Choose the most appropriate domain from these options:
1. space_exploration - Questions about space, planets, astronauts, NASA, SpaceX, etc.
2. particle_physics - Questions about CERN, particle accelerators, subatomic particles, etc.
3. general_science - Other scientific topics
4. technology - Computing, software, hardware
5. general_knowledge - History, geography, culture, etc.
6. other - None of the above

Respond with only the domain name and a confidence score (0.0-1.0), separated by a comma.
Example: "space_exploration,0.85"
"""
        
        try:
            response = self._call_ollama(prompt)
            content = response.get("response", "").strip()
            
            # Parse domain and confidence
            parts = content.split(',')
            if len(parts) >= 2:
                domain = parts[0].strip()
                confidence = float(parts[1].strip())
                return domain, confidence
            
            return "unknown", 0.0
            
        except Exception as e:
            logger.error(f"Domain detection failed: {e}")
            return "unknown", 0.0
    
    def should_use_web_search(self, query: str, local_results: List[Dict]) -> Tuple[bool, str]:
        """Determine if web search should be used based on query and local results"""
        if not self.is_available():
            # Fallback logic
            if not local_results:
                return True, "No local results available"
            
            best_score = max([r.get('relevance_score', 0) for r in local_results])
            return best_score < 0.6, f"Best local score: {best_score:.2f}"
        
        # Create summary of local results
        results_summary = self._summarize_results(local_results)
        
        prompt = f"""Analyze whether web search is needed for this query:

Query: "{query}"

Local search results summary:
{results_summary}

Based on the query and local results, should we search the web for additional information?

Consider:
1. Are the local results relevant to the query?
2. Do they provide sufficient information?
3. Is the query asking for recent/current information?
4. Is the query outside the scope of the local knowledge base?

Respond with: "YES" or "NO" followed by a brief reason.
Example: "YES - Query is about recent events not covered in local results"
"""
        
        try:
            response = self._call_ollama(prompt)
            content = response.get("response", "").strip()
            
            if content.upper().startswith("YES"):
                return True, content[3:].strip(" -")
            else:
                return False, content[2:].strip(" -")
                
        except Exception as e:
            logger.error(f"Web search decision failed: {e}")
            # Fallback to basic logic
            best_score = max([r.get('relevance_score', 0) for r in local_results]) if local_results else 0
            return best_score < 0.6, f"LLM unavailable, using score: {best_score:.2f}"
    
    def generate_out_of_scope_response(self, query: str, detected_domain: str) -> LLMResponse:
        """Generate a helpful response for out-of-scope queries"""
        if not self.is_available():
            return LLMResponse(
                content=f"I'm specialized in space exploration topics, but your question appears to be about {detected_domain}. I don't have sufficient information to provide a reliable answer.",
                confidence=0.1,
                reasoning="Out of scope, LLM unavailable"
            )
        
        prompt = f"""The user asked a question that's outside my specialized knowledge base:

Query: "{query}"
Detected domain: {detected_domain}

I'm a space exploration AI assistant with knowledge about NASA, SpaceX, planets, astronauts, telescopes, etc.

Generate a helpful response that:
1. Acknowledges the question is outside my expertise
2. Provides what basic information I can (if any)
3. Suggests where they might find better information
4. Offers to help with space-related questions instead

Be friendly and helpful, not dismissive.
"""
        
        try:
            response = self._call_ollama(prompt)
            content = response.get("response", "")
            
            return LLMResponse(
                content=content,
                confidence=0.3,
                reasoning=f"Out of scope query about {detected_domain}",
                model_used=self.model
            )
            
        except Exception as e:
            logger.error(f"Out of scope response generation failed: {e}")
            return LLMResponse(
                content=f"I'm specialized in space exploration topics, but your question appears to be about {detected_domain}. I don't have sufficient information to provide a reliable answer.",
                confidence=0.1,
                reasoning="Out of scope, LLM generation failed"
            )
    
    def _build_context(self, documents: List[Dict]) -> str:
        """Build context string from documents"""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents[:5], 1):  # Limit to top 5 documents
            title = doc.get('title', 'Unknown')
            content = doc.get('content', '')[:500]  # Limit content length
            source = doc.get('source', 'Unknown')
            score = doc.get('relevance_score', 0)
            
            context_parts.append(f"Source {i} ({source}, relevance: {score:.2f}):\nTitle: {title}\nContent: {content}...\n")
        
        return "\n".join(context_parts)
    
    def _create_answer_prompt(self, query: str, context: str, expertise_level: str) -> str:
        """Create a prompt for answer generation"""
        expertise_instructions = {
            "student": "Explain in simple terms suitable for a student. Use analogies and avoid technical jargon.",
            "expert": "Provide detailed technical information with specific data and terminology.",
            "general": "Balance technical accuracy with accessibility for a general audience."
        }
        
        instruction = expertise_instructions.get(expertise_level, expertise_instructions["general"])
        
        return f"""You are a knowledgeable AI assistant. Answer the following question based on the provided context.

Question: {query}

Context from relevant sources:
{context}

Instructions:
- {instruction}
- Base your answer primarily on the provided context
- If the context doesn't contain enough information, say so
- Be accurate and cite specific sources when possible
- If you're unsure about something, express appropriate uncertainty

Answer:"""
    
    def _summarize_results(self, results: List[Dict]) -> str:
        """Create a summary of search results"""
        if not results:
            return "No results found."
        
        summary = f"Found {len(results)} results:\n"
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', 'Unknown')
            score = result.get('relevance_score', 0)
            summary += f"{i}. {title} (relevance: {score:.2f})\n"
        
        return summary
    
    def _calculate_confidence(self, content: str, documents: List[Dict]) -> float:
        """Calculate confidence score based on content and sources"""
        if not content or not documents:
            return 0.0
        
        # Base confidence on number and quality of sources
        num_sources = len(documents)
        avg_relevance = sum([d.get('relevance_score', 0) for d in documents]) / num_sources
        
        # Adjust based on content length and quality
        content_length_factor = min(len(content) / 500, 1.0)
        
        # Check for uncertainty phrases
        uncertainty_phrases = ["I'm not sure", "I don't know", "unclear", "uncertain", "might be", "possibly"]
        uncertainty_penalty = sum([0.1 for phrase in uncertainty_phrases if phrase in content.lower()])
        
        confidence = (avg_relevance * 0.6 + content_length_factor * 0.3 + (num_sources / 5) * 0.1) - uncertainty_penalty
        
        return max(0.0, min(1.0, confidence))
    
    def _call_ollama(self, prompt: str) -> Dict:
        """Make API call to Ollama"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 1000
            }
        }
        
        response = self.session.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json()

# Global instance
ollama_llm = OllamaLLM() 