# agents/decision_tracker.py
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import uuid

from storage.redis_manager import RedisManager
from storage.neo4j_manager import Neo4jManager
from utils.logging_config import get_logger
from core.config import config

logger = get_logger(__name__)

class DecisionType(Enum):
    AGENT_SELECTION = "agent_selection"
    CONFIDENCE_EVALUATION = "confidence_evaluation"
    RETRIEVAL_STRATEGY = "retrieval_strategy"
    RESPONSE_GENERATION = "response_generation"
    ERROR_HANDLING = "error_handling"
    CACHE_DECISION = "cache_decision"

@dataclass
class DecisionPoint:
    """Represents a single decision point in the system"""
    id: str
    timestamp: datetime
    agent_name: str
    decision_type: DecisionType
    input_data: Dict[str, Any]
    decision_logic: str
    output_decision: Any
    confidence: float
    processing_time_ms: float
    metadata: Dict[str, Any]
    parent_query_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['decision_type'] = self.decision_type.value
        return data

@dataclass
class AgentInteraction:
    """Represents interaction between agents"""
    id: str
    timestamp: datetime
    source_agent: str
    target_agent: str
    interaction_type: str
    data_passed: Dict[str, Any]
    response_received: Dict[str, Any]
    success: bool
    processing_time_ms: float

@dataclass
class QueryJourney:
    """Complete journey of a query through the system"""
    query_id: str
    original_query: str
    start_time: datetime
    end_time: Optional[datetime]
    decision_points: List[DecisionPoint]
    agent_interactions: List[AgentInteraction]
    final_confidence: Optional[float]
    total_processing_time_ms: Optional[float]
    success: bool
    error_message: Optional[str] = None

class DecisionTracker:
    """Tracks and analyzes agent decision-making processes in real-time"""
    
    def __init__(self):
        self.redis_manager = None
        self.neo4j_manager = None
        self.active_queries: Dict[str, QueryJourney] = {}
        self.decision_buffer = deque(maxlen=1000)  # Last 1000 decisions
        self.performance_metrics = defaultdict(list)
        self.subscribers: List[Callable] = []
        
    async def initialize(self):
        """Initialize tracking components"""
        self.redis_manager = RedisManager()
        await self.redis_manager.initialize()
        
        self.neo4j_manager = Neo4jManager()
        await self.neo4j_manager.initialize()
        
        logger.info("Decision Tracker initialized")
        
    def subscribe_to_decisions(self, callback: Callable[[DecisionPoint], None]):
        """Subscribe to real-time decision updates"""
        self.subscribers.append(callback)
        
    async def start_query_tracking(self, query_id: str, original_query: str) -> QueryJourney:
        """Start tracking a new query journey"""
        journey = QueryJourney(
            query_id=query_id,
            original_query=original_query,
            start_time=datetime.now(),
            end_time=None,
            decision_points=[],
            agent_interactions=[],
            final_confidence=None,
            total_processing_time_ms=None,
            success=False
        )
        
        self.active_queries[query_id] = journey
        
        # Store in Redis for real-time access
        await self.redis_manager.set(
            f"query_journey:{query_id}",
            journey.__dict__,
            ttl=3600  # 1 hour
        )
        
        logger.info(f"Started tracking query journey: {query_id}")
        return journey
        
    async def record_decision(
        self,
        agent_name: str,
        decision_type: DecisionType,
        input_data: Dict[str, Any],
        decision_logic: str,
        output_decision: Any,
        confidence: float,
        processing_time_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
        parent_query_id: Optional[str] = None
    ) -> DecisionPoint:
        """Record a decision point"""
        
        decision_point = DecisionPoint(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            agent_name=agent_name,
            decision_type=decision_type,
            input_data=input_data,
            decision_logic=decision_logic,
            output_decision=output_decision,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            metadata=metadata or {},
            parent_query_id=parent_query_id
        )
        
        # Add to buffer for real-time access
        self.decision_buffer.append(decision_point)
        
        # Update active query if applicable
        if parent_query_id and parent_query_id in self.active_queries:
            self.active_queries[parent_query_id].decision_points.append(decision_point)
            
        # Store in Redis for real-time dashboard
        await self.redis_manager.lpush(
            "decision_stream",
            decision_point.to_dict()
        )
        
        # Keep only last 100 decisions in Redis
        await self.redis_manager.ltrim("decision_stream", 0, 99)
        
        # Store in Neo4j for long-term analysis
        await self._store_decision_in_graph(decision_point)
        
        # Notify subscribers
        for callback in self.subscribers:
            try:
                callback(decision_point)
            except Exception as e:
                logger.error(f"Error notifying decision subscriber: {e}")
                
        # Update performance metrics
        self.performance_metrics[agent_name].append({
            'timestamp': decision_point.timestamp,
            'processing_time': processing_time_ms,
            'confidence': confidence,
            'decision_type': decision_type.value
        })
        
        logger.debug(f"Recorded decision: {agent_name} - {decision_type.value}")
        return decision_point
        
    async def record_agent_interaction(
        self,
        source_agent: str,
        target_agent: str,
        interaction_type: str,
        data_passed: Dict[str, Any],
        response_received: Dict[str, Any],
        success: bool,
        processing_time_ms: float,
        parent_query_id: Optional[str] = None
    ) -> AgentInteraction:
        """Record interaction between agents"""
        
        interaction = AgentInteraction(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            source_agent=source_agent,
            target_agent=target_agent,
            interaction_type=interaction_type,
            data_passed=data_passed,
            response_received=response_received,
            success=success,
            processing_time_ms=processing_time_ms
        )
        
        # Update active query if applicable
        if parent_query_id and parent_query_id in self.active_queries:
            self.active_queries[parent_query_id].agent_interactions.append(interaction)
            
        # Store in Redis for real-time access
        await self.redis_manager.lpush(
            "interaction_stream",
            asdict(interaction)
        )
        
        await self.redis_manager.ltrim("interaction_stream", 0, 99)
        
        logger.debug(f"Recorded interaction: {source_agent} -> {target_agent}")
        return interaction
        
    async def complete_query_tracking(
        self,
        query_id: str,
        final_confidence: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Complete tracking for a query"""
        if query_id in self.active_queries:
            journey = self.active_queries[query_id]
            journey.end_time = datetime.now()
            journey.final_confidence = final_confidence
            journey.success = success
            journey.error_message = error_message
            
            if journey.start_time:
                journey.total_processing_time_ms = (
                    journey.end_time - journey.start_time
                ).total_seconds() * 1000
                
            # Store completed journey
            await self._store_journey_in_graph(journey)
            
            # Remove from active tracking
            del self.active_queries[query_id]
            
            logger.info(f"Completed query tracking: {query_id}")
            
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics"""
        now = datetime.now()
        last_minute = now - timedelta(minutes=1)
        last_hour = now - timedelta(hours=1)
        
        # Recent decision metrics
        recent_decisions = [
            dp for dp in self.decision_buffer
            if dp.timestamp >= last_minute
        ]
        
        # Agent performance
        agent_performance = {}
        for agent, metrics in self.performance_metrics.items():
            recent_metrics = [
                m for m in metrics
                if m['timestamp'] >= last_hour
            ]
            
            if recent_metrics:
                avg_time = sum(m['processing_time'] for m in recent_metrics) / len(recent_metrics)
                avg_confidence = sum(m['confidence'] for m in recent_metrics) / len(recent_metrics)
                
                agent_performance[agent] = {
                    'avg_processing_time_ms': avg_time,
                    'avg_confidence': avg_confidence,
                    'decision_count': len(recent_metrics),
                    'decisions_per_minute': len([m for m in recent_metrics if m['timestamp'] >= last_minute])
                }
        
        return {
            'active_queries': len(self.active_queries),
            'decisions_last_minute': len(recent_decisions),
            'total_decisions_tracked': len(self.decision_buffer),
            'agent_performance': agent_performance,
            'system_health': {
                'avg_processing_time': sum(dp.processing_time_ms for dp in recent_decisions) / max(len(recent_decisions), 1),
                'avg_confidence': sum(dp.confidence for dp in recent_decisions) / max(len(recent_decisions), 1),
                'success_rate': len([q for q in self.active_queries.values() if q.success]) / max(len(self.active_queries), 1)
            }
        }
        
    async def get_decision_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze decision patterns over time"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Get recent decisions
        recent_decisions = [
            dp for dp in self.decision_buffer
            if dp.timestamp >= cutoff
        ]
        
        # Pattern analysis
        patterns = {
            'decision_types': defaultdict(int),
            'agent_activity': defaultdict(int),
            'confidence_distribution': [],
            'processing_time_trends': [],
            'error_patterns': defaultdict(int)
        }
        
        for decision in recent_decisions:
            patterns['decision_types'][decision.decision_type.value] += 1
            patterns['agent_activity'][decision.agent_name] += 1
            patterns['confidence_distribution'].append(decision.confidence)
            patterns['processing_time_trends'].append({
                'timestamp': decision.timestamp.isoformat(),
                'processing_time': decision.processing_time_ms,
                'agent': decision.agent_name
            })
            
        return patterns
        
    async def _store_decision_in_graph(self, decision: DecisionPoint):
        """Store decision in Neo4j for long-term analysis"""
        try:
            decision_data = decision.to_dict()
            await self.neo4j_manager.create_node("Decision", decision_data)
            
            # Create relationship to query if applicable
            if decision.parent_query_id:
                await self.neo4j_manager.create_relationship(
                    "Query", {"id": decision.parent_query_id},
                    "Decision", {"id": decision.id},
                    "CONTAINS_DECISION"
                )
                
        except Exception as e:
            logger.error(f"Error storing decision in graph: {e}")
            
    async def _store_journey_in_graph(self, journey: QueryJourney):
        """Store complete query journey in Neo4j"""
        try:
            journey_data = {
                'query_id': journey.query_id,
                'original_query': journey.original_query,
                'start_time': journey.start_time.isoformat(),
                'end_time': journey.end_time.isoformat() if journey.end_time else None,
                'final_confidence': journey.final_confidence,
                'total_processing_time_ms': journey.total_processing_time_ms,
                'success': journey.success,
                'error_message': journey.error_message,
                'decision_count': len(journey.decision_points),
                'interaction_count': len(journey.agent_interactions)
            }
            
            await self.neo4j_manager.create_node("QueryJourney", journey_data)
            
        except Exception as e:
            logger.error(f"Error storing journey in graph: {e}")

# Global instance
decision_tracker = DecisionTracker() 