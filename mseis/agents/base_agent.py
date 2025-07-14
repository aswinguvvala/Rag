# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
from datetime import datetime
import uuid

from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import BaseMessage

from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class AgentResponse:
    """Standardized response from an agent"""
    agent_name: str
    query_id: str
    content: str
    confidence: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time: float
    timestamp: datetime

@dataclass
class QueryContext:
    """Context information for a query"""
    query_id: Optional[str]
    original_query: str
    user_id: Optional[str] = None
    user_expertise_level: str = "general"  # general, expert, student
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class AgentMetricsCallback(BaseCallbackHandler):
    """Callback handler for collecting agent metrics"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_processing_time": 0.0,
            "total_processing_time": 0.0
        }
        
    def on_llm_start(self, *args, **kwargs):
        pass
        
    def on_tool_start(self, *args, **kwargs):
        pass
        
    def record_query(self, success: bool, processing_time: float):
        """Record query metrics"""
        self.metrics["total_queries"] += 1
        if success:
            self.metrics["successful_queries"] += 1
        else:
            self.metrics["failed_queries"] += 1
            
        self.metrics["total_processing_time"] += processing_time
        self.metrics["avg_processing_time"] = (
            self.metrics["total_processing_time"] / self.metrics["total_queries"]
        )

class BaseAgent(ABC):
    """Base class for all agents in the MSEIS system"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = get_logger(f"agent.{name.lower()}")
        self.metrics_callback = AgentMetricsCallback(name)
        self.initialized = False
        
    async def initialize(self):
        """Initialize the agent"""
        if not self.initialized:
            await self._setup()
            self.initialized = True
            self.logger.info(f"{self.name} initialized successfully")
            
    @abstractmethod
    async def _setup(self):
        """Setup agent-specific components"""
        pass
        
    @abstractmethod
    async def _process_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Process a query and return (content, sources, confidence)"""
        pass
        
    async def process(self, context: QueryContext) -> AgentResponse:
        """
        Main processing method for all agents
        
        Args:
            context: Query context with user information
            
        Returns:
            Standardized agent response
        """
        start_time = datetime.now()
        
        if not self.initialized:
            await self.initialize()
            
        # Generate query ID if not provided
        if context.query_id is None:
            context.query_id = str(uuid.uuid4())
            
        self.logger.info(
            "Processing query",
            query_id=context.query_id,
            user_id=context.user_id,
            expertise_level=context.user_expertise_level,
            query_length=len(context.original_query)
        )
        
        try:
            # Process the query
            content, sources, confidence = await self._process_query(context)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Record metrics
            self.metrics_callback.record_query(True, processing_time)
            
            # Create response
            response = AgentResponse(
                agent_name=self.name,
                query_id=context.query_id,
                content=content,
                confidence=confidence,
                sources=sources,
                metadata=context.metadata,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
            self.logger.info(
                "Query processed successfully",
                query_id=context.query_id,
                confidence=confidence,
                num_sources=len(sources),
                processing_time=processing_time
            )
            
            return response
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics_callback.record_query(False, processing_time)
            
            self.logger.error(
                "Error processing query",
                query_id=context.query_id,
                error=str(e),
                processing_time=processing_time
            )
            
            # Return error response
            return AgentResponse(
                agent_name=self.name,
                query_id=context.query_id,
                content=f"Error processing query: {str(e)}",
                confidence=0.0,
                sources=[],
                metadata={"error": str(e)},
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            "agent_name": self.name,
            "status": "healthy" if self.initialized else "not_initialized",
            "metrics": self.metrics_callback.metrics.copy()
        } 