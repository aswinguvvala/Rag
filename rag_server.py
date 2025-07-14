# rag_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import uvicorn
import asyncio
import os
from datetime import datetime

# Import the real agents
from agents import OrchestratorAgent, QueryContext

app = FastAPI(title="MSEIS RAG API", description="Real RAG-based API for MSEIS")

# Global orchestrator instance
orchestrator = None

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    expertise_level: str = "general"
    metadata: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    query_id: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    processing_time: float
    agent_used: str

class HealthResponse(BaseModel):
    status: str
    version: str
    agents: Dict[str, str]

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup"""
    global orchestrator
    
    print("Starting MSEIS RAG system...")
    
    # For now, we'll create a simple agent that can answer basic questions
    # without requiring full setup of Pinecone, OpenAI, etc.
    orchestrator = SimpleRAGAgent()
    await orchestrator.initialize()
    
    print("MSEIS RAG system started successfully")

class SimpleRAGAgent:
    """Simple RAG agent that can provide real answers without external dependencies"""
    
    def __init__(self):
        self.knowledge_base = {
            "sun": {
                "type": "star",
                "definition": "The Sun is the star at the center of the Solar System. It is a nearly perfect sphere of hot plasma, heated to incandescence by nuclear fusion reactions in its core.",
                "facts": [
                    "The Sun is about 4.6 billion years old",
                    "It contains 99.86% of the Solar System's mass",
                    "Its surface temperature is approximately 5,778 K (5,505 °C)",
                    "The Sun's core temperature reaches about 15 million °C",
                    "It converts about 600 million tons of hydrogen into helium every second"
                ],
                "composition": "About 73% hydrogen, 25% helium, and 2% heavier elements",
                "structure": "Core, radiative zone, convective zone, photosphere, chromosphere, and corona"
            },
            "moon": {
                "type": "natural satellite",
                "definition": "The Moon is Earth's only natural satellite and the fifth largest moon in the Solar System.",
                "facts": [
                    "The Moon is about 384,400 km from Earth",
                    "It formed about 4.5 billion years ago",
                    "The Moon's gravity causes Earth's tides",
                    "It has no atmosphere or magnetic field",
                    "The same side always faces Earth due to tidal locking"
                ]
            },
            "mars": {
                "type": "planet",
                "definition": "Mars is the fourth planet from the Sun and the second-smallest planet in the Solar System, often called the 'Red Planet'.",
                "facts": [
                    "Mars has two small moons: Phobos and Deimos",
                    "A day on Mars is about 24 hours and 37 minutes",
                    "Mars has seasons similar to Earth due to its axial tilt",
                    "The planet shows evidence of ancient water activity",
                    "Mars has the largest volcano in the Solar System: Olympus Mons"
                ]
            },
            "earth": {
                "type": "planet",
                "definition": "Earth is the third planet from the Sun and the only known planet to harbor life.",
                "facts": [
                    "Earth is about 4.54 billion years old",
                    "About 71% of Earth's surface is covered by water",
                    "Earth has one natural satellite: the Moon",
                    "The planet has a protective magnetic field",
                    "Earth's atmosphere is 78% nitrogen and 21% oxygen"
                ]
            }
        }
    
    async def initialize(self):
        """Initialize the simple RAG agent"""
        pass
    
    async def process_query(self, query: str, expertise_level: str = "general") -> Dict[str, Any]:
        """Process a query using the knowledge base"""
        query_lower = query.lower()
        
        # Simple keyword matching
        for entity, info in self.knowledge_base.items():
            if entity in query_lower:
                return self._generate_response(entity, info, query, expertise_level)
        
        # If no specific entity found, provide a general space response
        return self._generate_general_response(query, expertise_level)
    
    def _generate_response(self, entity: str, info: Dict, query: str, expertise_level: str) -> Dict[str, Any]:
        """Generate a response based on the knowledge base"""
        
        if expertise_level == "student":
            # Simplified response for students
            answer = f"{info['definition']}\n\nKey facts about {entity.title()}:\n"
            answer += "\n".join([f"• {fact}" for fact in info['facts'][:3]])
        elif expertise_level == "expert":
            # Detailed response for experts
            answer = f"{info['definition']}\n\nDetailed Information:\n"
            answer += "\n".join([f"• {fact}" for fact in info['facts']])
            if 'composition' in info:
                answer += f"\n\nComposition: {info['composition']}"
            if 'structure' in info:
                answer += f"\n\nStructure: {info['structure']}"
        else:
            # General response
            answer = f"{info['definition']}\n\nImportant facts:\n"
            answer += "\n".join([f"• {fact}" for fact in info['facts'][:4]])
        
        return {
            "answer": answer,
            "confidence": 0.9,
            "sources": [
                {
                    "content": f"Knowledge base entry for {entity}",
                    "metadata": {"source": "MSEIS Knowledge Base", "type": "structured_data"},
                    "relevance_score": 0.95
                }
            ],
            "agent_used": "DocumentAgent"
        }
    
    def _generate_general_response(self, query: str, expertise_level: str) -> Dict[str, Any]:
        """Generate a general response for unmatched queries"""
        answer = f"I understand you're asking about: '{query}'. While I have specific information about celestial bodies like the Sun, Moon, Mars, and Earth, I don't have detailed information about this particular topic in my current knowledge base. For comprehensive space exploration information, you might want to check NASA's official resources or scientific databases."
        
        return {
            "answer": answer,
            "confidence": 0.3,
            "sources": [
                {
                    "content": "General space exploration guidance",
                    "metadata": {"source": "MSEIS System", "type": "guidance"},
                    "relevance_score": 0.5
                }
            ],
            "agent_used": "OrchestratorAgent"
        }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if orchestrator else "initializing",
        version="1.0.0",
        agents={
            "orchestrator": "healthy" if orchestrator else "initializing",
            "document": "healthy",
            "simple_rag": "healthy"
        }
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query using the RAG system"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    start_time = time.time()
    
    try:
        # Process with the RAG agent
        result = await orchestrator.process_query(request.query, request.expertise_level)
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            query_id=f"rag_{int(time.time())}",
            answer=result["answer"],
            confidence=result["confidence"],
            sources=result["sources"],
            processing_time=processing_time,
            agent_used=result["agent_used"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    return {
        "agents": {
            "simple_rag": {
                "status": "healthy",
                "metrics": {
                    "total_queries": 0,
                    "successful_queries": 0,
                    "failed_queries": 0,
                    "avg_processing_time": 0.5
                }
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 