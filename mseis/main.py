# main.py
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import signal
import sys

from core.config import config
from utils.logging_config import setup_logging, get_logger
from utils.monitoring import start_metrics_server
from agents.orchestrator_agent import OrchestratorAgent
from agents.code_intelligence_agent import CodeIntelligenceAgent
from agents.base_agent import QueryContext
from evaluation.evaluator import MSEISEvaluator

# Setup logging
setup_logging(config.system.log_level)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MSEIS API",
    description="Multi-Modal Space Exploration Intelligence System",
    version=config.system.version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances
orchestrator = None
code_intelligence_agent = None

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    expertise_level: str = "general"
    metadata: Optional[Dict[str, Any]] = None

class CodeAnalysisRequest(BaseModel):
    repository_url: str
    expertise_level: str = "general"
    force_refresh: bool = False
    user_id: Optional[str] = None

class CodeAnalysisResponse(BaseModel):
    repository: str
    analysis: str
    confidence: float
    metrics: Dict[str, Any]
    technologies: List[str]
    architecture_patterns: List[str]
    processing_time: float

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
    """Initialize the system on startup"""
    global orchestrator, code_intelligence_agent
    
    logger.info("Starting MSEIS system...")
    
    # Start metrics server
    start_metrics_server(config.get("monitoring.prometheus_port", 8000))
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    
    # Initialize code intelligence agent
    code_intelligence_agent = CodeIntelligenceAgent()
    await code_intelligence_agent.initialize()
    
    logger.info("MSEIS system started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MSEIS system...")
    # Add cleanup code here

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
        
    status = await orchestrator.get_system_status()
    
    return HealthResponse(
        status="healthy" if all(
            agent["status"] == "healthy" 
            for agent in status["agents"].values()
        ) else "degraded",
        version=config.system.version,
        agents={
            name: info["status"] 
            for name, info in status["agents"].items()
        }
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
        
    try:
        # Create query context
        context = QueryContext(
            query_id=None,  # Will be generated
            original_query=request.query,
            user_id=request.user_id,
            user_expertise_level=request.expertise_level,
            metadata=request.metadata or {}
        )
        
        # Process query
        response = await orchestrator.process(context)
        
        return QueryResponse(
            query_id=response.query_id,
            answer=response.content,
            confidence=response.confidence,
            sources=response.sources,
            processing_time=response.processing_time,
            agent_used=response.agent_name
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-code", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze a GitHub repository for architecture and code quality"""
    if code_intelligence_agent is None:
        raise HTTPException(status_code=503, detail="Code Intelligence Agent not initialized")
        
    try:
        # Create query context for code analysis
        context = QueryContext(
            query_id=None,
            original_query=f"Analyze repository: {request.repository_url}",
            user_id=request.user_id,
            user_expertise_level=request.expertise_level,
            metadata={"force_refresh": request.force_refresh}
        )
        
        # Process analysis
        response = await code_intelligence_agent.process(context)
        
        # Extract metrics from sources
        metrics = {}
        technologies = []
        architecture_patterns = []
        
        if response.sources:
            source_data = response.sources[0]
            metrics = {
                "total_files": source_data.get("analyzed_files", 0),
                "processing_time": response.processing_time
            }
            
        return CodeAnalysisResponse(
            repository=request.repository_url,
            analysis=response.content,
            confidence=response.confidence,
            metrics=metrics,
            technologies=technologies,
            architecture_patterns=architecture_patterns,
            processing_time=response.processing_time
        )
        
    except Exception as e:
        logger.error(f"Error analyzing code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def run_evaluation(background_tasks: BackgroundTasks):
    """Run system evaluation"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
        
    # Run evaluation in background
    evaluator = MSEISEvaluator(orchestrator)
    background_tasks.add_task(evaluator.evaluate_system)
    
    return {"message": "Evaluation started in background"}

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
        
    status = await orchestrator.get_system_status()
    
    metrics = {
        "agents": {}
    }
    
    for agent_name, agent_info in status["agents"].items():
        if "metrics" in agent_info:
            metrics["agents"][agent_name] = agent_info["metrics"]
            
    return metrics

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    sys.exit(0)

def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None  # Use our custom logging
    )

if __name__ == "__main__":
    main() 