# agents/orchestrator_agent.py
import asyncio
import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from agents.base_agent import BaseAgent, QueryContext
from agents.document_agent import DocumentAgent
from agents.image_agent import ImageAgent
from agents.code_intelligence_agent import CodeIntelligenceAgent
from agents.planning_agent import PlanningAgent
from agents.decision_tracker import decision_tracker, DecisionType
from storage.cache_manager import CacheManager
from core.config import config
from utils.monitoring import monitor_performance
from utils.logging_config import get_logger

logger = get_logger(__name__)

class OrchestratorAgent(BaseAgent):
    """Main orchestrator that routes queries to appropriate specialized agents"""
    
    def __init__(self):
        super().__init__(
            name="OrchestratorAgent",
            config=config.get("agents.orchestrator", {})
        )
        self.cache_manager = None
        self.routing_llm = None
        self.agents = {}
        self.planning_agent = None
        
    async def _setup(self):
        """Initialize orchestrator and all specialized agents"""
        # Initialize cache
        self.cache_manager = CacheManager()
        await self.cache_manager.initialize()
        
        # Initialize routing LLM
        self.routing_llm = ChatOpenAI(
            model=config.api.openai_model,
            temperature=0.1,
            openai_api_key=config.api.openai_api_key
        )
        
        # Initialize decision tracker
        await decision_tracker.initialize()
        
        # Initialize all specialized agents
        logger.info("Initializing specialized agents...")
        
        # Document Agent
        try:
            self.agents["DocumentAgent"] = DocumentAgent()
            await self.agents["DocumentAgent"].initialize()
            logger.info("✓ DocumentAgent initialized")
        except Exception as e:
            logger.warning(f"DocumentAgent initialization failed: {str(e)}")
            
        # Image Agent
        try:
            self.agents["ImageAgent"] = ImageAgent()
            await self.agents["ImageAgent"].initialize()
            logger.info("✓ ImageAgent initialized")
        except Exception as e:
            logger.warning(f"ImageAgent initialization failed: {str(e)}")
            
        # Code Intelligence Agent
        try:
            self.agents["CodeIntelligenceAgent"] = CodeIntelligenceAgent()
            await self.agents["CodeIntelligenceAgent"].initialize()
            logger.info("✓ CodeIntelligenceAgent initialized")
        except Exception as e:
            logger.warning(f"CodeIntelligenceAgent initialization failed: {str(e)}")
            
        # Planning Agent
        try:
            self.planning_agent = PlanningAgent()
            await self.planning_agent.initialize()
            
            # Register all agents with the planning agent
            for agent_type, agent in self.agents.items():
                self.planning_agent.register_agent(agent_type, agent)
                
            logger.info("✓ PlanningAgent initialized and agents registered")
        except Exception as e:
            logger.warning(f"PlanningAgent initialization failed: {str(e)}")
            
        logger.info(f"Orchestrator initialized with {len(self.agents)} specialized agents")
        
    async def _process_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Main query processing with intelligent routing"""
        
        # Start tracking the query journey
        await decision_tracker.start_query_tracking(context.query_id, context.original_query)
        
        try:
            # 1. Analyze query complexity and type
            query_analysis = await self._analyze_query_complexity(context)
            
            # 2. Route to appropriate processing strategy
            if query_analysis["complexity"] == "complex" or query_analysis["requires_planning"]:
                # Use planning agent for complex queries
                result = await self._process_with_planning(context, query_analysis)
            else:
                # Route to single agent for simple queries
                result = await self._process_with_single_agent(context, query_analysis)
                
            # 3. Complete tracking
            await decision_tracker.complete_query_tracking(
                context.query_id,
                final_confidence=result[2],
                success=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in orchestrator processing: {str(e)}")
            
            # Complete tracking with error
            await decision_tracker.complete_query_tracking(
                context.query_id,
                final_confidence=0.1,
                success=False,
                error_message=str(e)
            )
            
            return f"I encountered an error processing your query: {str(e)}", [], 0.1
            
    @monitor_performance("orchestrator", "analyze_query")
    async def _analyze_query_complexity(self, context: QueryContext) -> Dict[str, Any]:
        """Analyze query to determine routing strategy"""
        
        query = context.original_query.lower()
        
        # Pattern matching for different query types
        analysis = {
            "query_type": "general",
            "complexity": "simple",
            "requires_planning": False,
            "suggested_agents": [],
            "confidence": 0.8
        }
        
        # Code-related patterns
        if any(pattern in query for pattern in [
            "github", "repository", "code", "architecture", "analyze repo", 
            "codebase", "programming", "software design", "api design"
        ]):
            analysis["query_type"] = "code_analysis"
            analysis["suggested_agents"] = ["CodeIntelligenceAgent"]
            
        # Image-related patterns
        elif any(pattern in query for pattern in [
            "image", "picture", "photo", "visual", "diagram", "chart", "graph"
        ]):
            analysis["query_type"] = "image_analysis"
            analysis["suggested_agents"] = ["ImageAgent"]
            
        # Document/research patterns
        elif any(pattern in query for pattern in [
            "research", "paper", "document", "article", "study", "analysis", 
            "report", "publication", "find information"
        ]):
            analysis["query_type"] = "document_search"
            analysis["suggested_agents"] = ["DocumentAgent"]
            
        # Complex multi-step patterns
        elif any(pattern in query for pattern in [
            "compare", "analyze both", "step by step", "comprehensive", 
            "detailed analysis", "multiple", "various", "different approaches"
        ]) or len(query.split()) > 20:
            analysis["complexity"] = "complex"
            analysis["requires_planning"] = True
            analysis["suggested_agents"] = ["DocumentAgent", "CodeIntelligenceAgent"]
            
        # If no specific pattern, default to document search
        else:
            analysis["suggested_agents"] = ["DocumentAgent"]
            
        # Use LLM for more sophisticated analysis if enabled
        if self.config.get("routing_strategy") == "llm_based":
            llm_analysis = await self._llm_query_analysis(context)
            analysis.update(llm_analysis)
            
        # Record routing decision
        await decision_tracker.record_decision(
            agent_name=self.name,
            decision_type=DecisionType.AGENT_SELECTION,
            input_data={"query": context.original_query},
            decision_logic=f"Pattern matching + {self.config.get('routing_strategy', 'rule_based')} analysis",
            output_decision=analysis["suggested_agents"],
            confidence=analysis["confidence"],
            processing_time_ms=100,
            parent_query_id=context.query_id
        )
        
        return analysis
        
    async def _llm_query_analysis(self, context: QueryContext) -> Dict[str, Any]:
        """Use LLM for sophisticated query analysis"""
        
        analysis_prompt = f"""
        Analyze this user query and determine the best processing strategy:
        
        Query: "{context.original_query}"
        User Expertise Level: {context.user_expertise_level}
        
        Available Agents:
        - DocumentAgent: Searches documents, papers, articles, general knowledge
        - ImageAgent: Processes and analyzes images, creates visualizations
        - CodeIntelligenceAgent: Analyzes GitHub repositories, code architecture, programming
        - PlanningAgent: Coordinates multi-step tasks, complex analysis
        
        Determine:
        1. Query type (code_analysis, image_analysis, document_search, multi_modal, complex_analysis)
        2. Complexity level (simple, medium, complex)
        3. Whether planning is required (true/false)
        4. Which agents should be involved (list)
        5. Confidence in routing decision (0.0-1.0)
        
        Respond in JSON format:
        {{"query_type": "...", "complexity": "...", "requires_planning": false, "suggested_agents": [...], "confidence": 0.9}}
        """
        
        try:
            messages = [
                SystemMessage(content="You are an expert query router for a multi-agent AI system."),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.routing_llm.invoke,
                messages
            )
            
            import json
            return json.loads(response.content)
            
        except Exception as e:
            logger.error(f"LLM query analysis failed: {str(e)}")
            return {"confidence": 0.5}
            
    async def _process_with_planning(self, context: QueryContext, analysis: Dict[str, Any]) -> Tuple[str, List[Dict], float]:
        """Process complex queries using the planning agent"""
        
        if not self.planning_agent:
            logger.warning("Planning agent not available, falling back to single agent")
            return await self._process_with_single_agent(context, analysis)
            
        await decision_tracker.record_decision(
            agent_name=self.name,
            decision_type=DecisionType.RETRIEVAL_STRATEGY,
            input_data={"analysis": analysis},
            decision_logic="Complex query requires multi-step planning",
            output_decision="planning_agent_routing",
            confidence=0.9,
            processing_time_ms=50,
            parent_query_id=context.query_id
        )
        
        # Use planning agent for complex queries
        response = await self.planning_agent.process(context)
        
        return response.content, response.sources, response.confidence
        
    async def _process_with_single_agent(self, context: QueryContext, analysis: Dict[str, Any]) -> Tuple[str, List[Dict], float]:
        """Process simple queries with a single specialized agent"""
        
        suggested_agents = analysis.get("suggested_agents", ["DocumentAgent"])
        selected_agent_type = suggested_agents[0] if suggested_agents else "DocumentAgent"
        
        # Fallback if suggested agent is not available
        if selected_agent_type not in self.agents:
            logger.warning(f"Agent {selected_agent_type} not available, using DocumentAgent")
            selected_agent_type = "DocumentAgent"
            
        if selected_agent_type not in self.agents:
            # Final fallback - return basic response
            return "I apologize, but the specialized agents are currently unavailable. Please try again later.", [], 0.1
            
        agent = self.agents[selected_agent_type]
        
        await decision_tracker.record_decision(
            agent_name=self.name,
            decision_type=DecisionType.AGENT_SELECTION,
            input_data={"analysis": analysis},
            decision_logic=f"Single agent routing based on query type: {analysis.get('query_type')}",
            output_decision=selected_agent_type,
            confidence=analysis.get("confidence", 0.8),
            processing_time_ms=25,
            parent_query_id=context.query_id
        )
        
        # Process with selected agent
        response = await agent.process(context)
        
        # Record agent interaction
        await decision_tracker.record_agent_interaction(
            source_agent=self.name,
            target_agent=selected_agent_type,
            interaction_type="query_processing",
            data_passed={"query": context.original_query},
            response_received={"content_length": len(response.content), "sources_count": len(response.sources)},
            success=response.confidence > 0.3,
            processing_time_ms=response.processing_time * 1000,
            parent_query_id=context.query_id
        )
        
        return response.content, response.sources, response.confidence
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all agents in the system"""
        status = {
            "orchestrator": {
                "status": "healthy" if self.initialized else "not_initialized",
                "agents_managed": len(self.agents)
            },
            "agents": {},
            "decision_tracker": await decision_tracker.get_real_time_metrics() if decision_tracker else {"status": "unavailable"}
        }
        
        # Get status of each agent
        for agent_type, agent in self.agents.items():
            try:
                agent_status = agent.get_metrics() if hasattr(agent, 'get_metrics') else {"status": "unknown"}
                status["agents"][agent_type] = agent_status
            except Exception as e:
                status["agents"][agent_type] = {"status": "error", "error": str(e)}
                
        # Planning agent status
        if self.planning_agent:
            try:
                planning_status = self.planning_agent.get_metrics() if hasattr(self.planning_agent, 'get_metrics') else {"status": "healthy"}
                status["planning_agent"] = planning_status
            except Exception as e:
                status["planning_agent"] = {"status": "error", "error": str(e)}
                
        return status
        
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = {
            "system_metrics": await self.get_system_status(),
            "decision_patterns": await decision_tracker.get_decision_patterns() if decision_tracker else {},
            "cache_performance": self.cache_manager.get_stats() if self.cache_manager else {}
        }
        
        return metrics
        
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types"""
        available = list(self.agents.keys())
        if self.planning_agent:
            available.append("PlanningAgent")
        return available
        
    async def force_agent_selection(self, agent_type: str, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Force query processing with a specific agent (for testing/debugging)"""
        
        if agent_type == "PlanningAgent" and self.planning_agent:
            response = await self.planning_agent.process(context)
            return response.content, response.sources, response.confidence
            
        elif agent_type in self.agents:
            agent = self.agents[agent_type]
            response = await agent.process(context)
            return response.content, response.sources, response.confidence
            
        else:
            return f"Agent {agent_type} is not available.", [], 0.0 