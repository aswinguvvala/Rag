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
from agents.autonomous_research_agent import AutonomousResearchAgent
from agents.temporal_analysis_agent import TemporalAnalysisAgent
from agents.simulation_integration_agent import SimulationIntegrationAgent
from agents.knowledge_synthesis_agent import KnowledgeSynthesisAgent
from agents.collaborative_planning_agent import CollaborativeMissionPlanningAgent
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
        self.advanced_agents = {}  # New: Advanced agents registry
        
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
        
        # Initialize core specialized agents
        logger.info("Initializing core specialized agents...")
        
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
            
        # Initialize advanced agents
        logger.info("Initializing advanced AI agents...")
        
        # Autonomous Research Agent
        try:
            self.advanced_agents["AutonomousResearchAgent"] = AutonomousResearchAgent()
            await self.advanced_agents["AutonomousResearchAgent"].initialize()
            # Register other agents for research
            for agent_type, agent in self.agents.items():
                self.advanced_agents["AutonomousResearchAgent"].register_agent(agent_type, agent)
            logger.info("✓ AutonomousResearchAgent initialized")
        except Exception as e:
            logger.warning(f"AutonomousResearchAgent initialization failed: {str(e)}")
            
        # Temporal Analysis Agent
        try:
            self.advanced_agents["TemporalAnalysisAgent"] = TemporalAnalysisAgent()
            await self.advanced_agents["TemporalAnalysisAgent"].initialize()
            logger.info("✓ TemporalAnalysisAgent initialized")
        except Exception as e:
            logger.warning(f"TemporalAnalysisAgent initialization failed: {str(e)}")
            
        # Simulation Integration Agent
        try:
            self.advanced_agents["SimulationIntegrationAgent"] = SimulationIntegrationAgent()
            await self.advanced_agents["SimulationIntegrationAgent"].initialize()
            logger.info("✓ SimulationIntegrationAgent initialized")
        except Exception as e:
            logger.warning(f"SimulationIntegrationAgent initialization failed: {str(e)}")
            
        # Knowledge Synthesis Agent
        try:
            self.advanced_agents["KnowledgeSynthesisAgent"] = KnowledgeSynthesisAgent()
            await self.advanced_agents["KnowledgeSynthesisAgent"].initialize()
            # Register other agents for knowledge synthesis
            for agent_type, agent in {**self.agents, **self.advanced_agents}.items():
                if agent_type != "KnowledgeSynthesisAgent":
                    self.advanced_agents["KnowledgeSynthesisAgent"].register_agent(agent_type, agent)
            logger.info("✓ KnowledgeSynthesisAgent initialized")
        except Exception as e:
            logger.warning(f"KnowledgeSynthesisAgent initialization failed: {str(e)}")
            
        # Collaborative Mission Planning Agent
        try:
            self.advanced_agents["CollaborativeMissionPlanningAgent"] = CollaborativeMissionPlanningAgent()
            await self.advanced_agents["CollaborativeMissionPlanningAgent"].initialize()
            logger.info("✓ CollaborativeMissionPlanningAgent initialized")
        except Exception as e:
            logger.warning(f"CollaborativeMissionPlanningAgent initialization failed: {str(e)}")
        
        # Planning Agent
        try:
            self.planning_agent = PlanningAgent()
            await self.planning_agent.initialize()
            
            # Register all agents with the planning agent
            for agent_type, agent in {**self.agents, **self.advanced_agents}.items():
                self.planning_agent.register_agent(agent_type, agent)
                
            logger.info("✓ PlanningAgent initialized and all agents registered")
        except Exception as e:
            logger.warning(f"PlanningAgent initialization failed: {str(e)}")
            
        total_agents = len(self.agents) + len(self.advanced_agents)
        logger.info(f"🚀 Enhanced Orchestrator initialized with {total_agents} agents ({len(self.agents)} core + {len(self.advanced_agents)} advanced)")
        
    async def _process_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Main query processing with intelligent routing to core and advanced agents"""
        
        # Start tracking the query journey
        await decision_tracker.start_query_tracking(context.query_id, context.original_query)
        
        try:
            # 1. Analyze query complexity and type
            query_analysis = await self._analyze_query_complexity(context)
            
            # 2. Determine if advanced agents are needed
            advanced_agent_needed = await self._requires_advanced_agent(context, query_analysis)
            
            # 3. Route to appropriate processing strategy
            if advanced_agent_needed:
                # Use advanced agent for sophisticated analysis
                result = await self._process_with_advanced_agent(context, query_analysis, advanced_agent_needed)
            elif query_analysis["complexity"] == "complex" or query_analysis["requires_planning"]:
                # Use planning agent for complex queries
                result = await self._process_with_planning(context, query_analysis)
            else:
                # Route to single core agent for simple queries
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
    
    async def _requires_advanced_agent(self, context: QueryContext, query_analysis: Dict[str, Any]) -> Optional[str]:
        """Determine if query requires advanced agent capabilities"""
        
        query = context.original_query.lower()
        
        # Research and hypothesis testing patterns
        if any(pattern in query for pattern in [
            "research", "investigate", "analyze why", "what caused", "hypothesis", 
            "evidence", "study", "compare multiple", "comprehensive analysis",
            "autonomous research", "multi-step analysis"
        ]):
            return "AutonomousResearchAgent"
        
        # Timeline and temporal analysis patterns  
        if any(pattern in query for pattern in [
            "timeline", "schedule", "duration", "when will", "delays", "critical path",
            "mission timeline", "project schedule", "dependencies", "milestone",
            "temporal analysis", "cascade effects", "perturbation"
        ]):
            return "TemporalAnalysisAgent"
        
        # Simulation and predictive modeling patterns
        if any(pattern in query for pattern in [
            "simulate", "predict", "what if", "scenario", "model", "calculate",
            "orbit", "trajectory", "thermal", "radiation", "propulsion",
            "simulation", "predictive", "modeling", "performance"
        ]):
            return "SimulationIntegrationAgent"
        
        # Knowledge synthesis and pattern recognition patterns
        if any(pattern in query for pattern in [
            "pattern", "trend", "connection", "insight", "synthesis", "innovation",
            "cross-domain", "analogy", "breakthrough", "opportunity",
            "knowledge synthesis", "hidden connections", "emerging trends"
        ]):
            return "KnowledgeSynthesisAgent"
        
        # Collaborative planning and stakeholder patterns
        if any(pattern in query for pattern in [
            "stakeholder", "collaboration", "planning", "partnership", "negotiate",
            "multi-stakeholder", "consensus", "agreement", "resource allocation",
            "mission planning", "collaborative", "optimization", "trade-off"
        ]):
            return "CollaborativeMissionPlanningAgent"
        
        # Check for complex analytical queries that would benefit from advanced capabilities
        complexity_indicators = [
            "comprehensive", "sophisticated", "advanced", "detailed analysis",
            "multiple perspectives", "complex", "in-depth", "thorough"
        ]
        
        if any(indicator in query for indicator in complexity_indicators):
            # Default to research agent for complex analytical queries
            return "AutonomousResearchAgent"
        
        return None
    
    async def _process_with_advanced_agent(self, context: QueryContext, query_analysis: Dict[str, Any], agent_type: str) -> Tuple[str, List[Dict], float]:
        """Process query with specified advanced agent"""
        
        if agent_type not in self.advanced_agents:
            logger.warning(f"Advanced agent {agent_type} not available, falling back to planning agent")
            return await self._process_with_planning(context, query_analysis)
        
        agent = self.advanced_agents[agent_type]
        
        await decision_tracker.record_decision(
            agent_name=self.name,
            decision_type=DecisionType.AGENT_SELECTION,
            input_data={"analysis": query_analysis},
            decision_logic=f"Advanced agent routing: {agent_type} selected for sophisticated analysis",
            output_decision=agent_type,
            confidence=0.9,
            processing_time_ms=50,
            parent_query_id=context.query_id
        )
        
        # Process with selected advanced agent
        response = await agent.process(context)
        
        # Record the advanced agent interaction
        await decision_tracker.record_agent_interaction(
            source_agent=self.name,
            target_agent=agent_type,
            interaction_type="advanced_processing",
            data_passed={"query": context.original_query},
            response_received={"content_length": len(response.content), "confidence": response.confidence},
            success=True,
            processing_time_ms=response.processing_time * 1000,
            parent_query_id=context.query_id
        )
        
        return response.content, response.sources, response.confidence
        
    @monitor_performance("orchestrator", "analyze_query")
    async def _analyze_query_complexity(self, context: QueryContext) -> Dict[str, Any]:
        """Analyze query to determine routing strategy"""
        
        query = context.original_query.lower()
        
        # Pattern matching for different query types
        analysis = {
            "query_type": "general",
            "complexity": "simple",
            "requires_planning": False,
            "requires_advanced_agent": False,
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
            
        # Advanced analysis patterns
        elif any(pattern in query for pattern in [
            "autonomous research", "multi-step", "hypothesis", "evidence",
            "timeline analysis", "temporal", "simulation", "predict",
            "knowledge synthesis", "pattern", "stakeholder", "collaborative"
        ]):
            analysis["query_type"] = "advanced_analysis"
            analysis["complexity"] = "advanced"
            analysis["requires_advanced_agent"] = True
            
        # Complex multi-step patterns
        elif any(pattern in query for pattern in [
            "compare", "analyze both", "step by step", "comprehensive", 
            "detailed analysis", "multiple", "various", "different approaches"
        ]) or len(query.split()) > 20:
            analysis["complexity"] = "complex"
            analysis["requires_planning"] = True
            analysis["suggested_agents"] = ["DocumentAgent", "CodeIntelligenceAgent"]
        
        # Use LLM for more sophisticated analysis if query is complex
        if analysis["complexity"] in ["complex", "advanced"] or len(query.split()) > 15:
            llm_analysis = await self._llm_query_analysis(context)
            if llm_analysis.get("confidence", 0) > analysis["confidence"]:
                analysis.update(llm_analysis)
        
        return analysis
        
    async def _llm_query_analysis(self, context: QueryContext) -> Dict[str, Any]:
        """Use LLM for sophisticated query analysis"""
        
        analysis_prompt = f"""
        Analyze this user query and determine the best processing strategy:
        
        Query: "{context.original_query}"
        User Expertise Level: {context.user_expertise_level}
        
        Available Agents:
        
        Core Agents:
        - DocumentAgent: Searches documents, papers, articles, general knowledge
        - ImageAgent: Processes and analyzes images, creates visualizations
        - CodeIntelligenceAgent: Analyzes GitHub repositories, code architecture, programming
        - PlanningAgent: Coordinates multi-step tasks, complex analysis
        
        Advanced Agents:
        - AutonomousResearchAgent: Multi-step hypothesis testing, scientific investigation
        - TemporalAnalysisAgent: Mission timeline analysis, dependency tracking
        - SimulationIntegrationAgent: Predictive modeling, what-if analysis
        - KnowledgeSynthesisAgent: Pattern recognition, cross-domain insights
        - CollaborativeMissionPlanningAgent: Multi-stakeholder optimization
        
        Determine:
        1. Query type (code_analysis, image_analysis, document_search, advanced_research, temporal_analysis, simulation_modeling, knowledge_synthesis, collaborative_planning, multi_modal, complex_analysis)
        2. Complexity level (simple, medium, complex, advanced)
        3. Whether advanced agents are needed (true/false)
        4. Which agents should be involved (list)
        5. Confidence in routing decision (0.0-1.0)
        
        Respond in JSON format:
        {{"query_type": "...", "complexity": "...", "requires_advanced_agent": false, "suggested_agents": [...], "confidence": 0.9}}
        """
        
        try:
            messages = [
                SystemMessage(content="You are an expert query router for an advanced multi-agent AI system with sophisticated capabilities."),
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
            # Fallback to single agent if planning agent not available
            return await self._process_with_single_agent(context, analysis)
        
        await decision_tracker.record_decision(
            agent_name=self.name,
            decision_type=DecisionType.AGENT_SELECTION,
            input_data={"analysis": analysis},
            decision_logic=f"Complex query routing to planning agent: {analysis.get('query_type')}",
            output_decision="PlanningAgent",
            confidence=analysis.get("confidence", 0.8),
            processing_time_ms=75,
            parent_query_id=context.query_id
        )
        
        # Process with planning agent
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
        
        return response.content, response.sources, response.confidence

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including advanced agents"""
        status = {
            "orchestrator": "active",
            "core_agents": {},
            "advanced_agents": {},
            "planning_agent": "active" if self.planning_agent else "inactive",
            "total_agents": len(self.agents) + len(self.advanced_agents),
            "cache_status": "active" if self.cache_manager else "inactive",
            "routing_llm": "active" if self.routing_llm else "inactive"
        }
        
        # Check core agent status
        for agent_type, agent in self.agents.items():
            try:
                status["core_agents"][agent_type] = "active"
            except Exception:
                status["core_agents"][agent_type] = "error"
        
        # Check advanced agent status
        for agent_type, agent in self.advanced_agents.items():
            try:
                status["advanced_agents"][agent_type] = "active"
            except Exception:
                status["advanced_agents"][agent_type] = "error"
                
        return status
        
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = {
            "system_metrics": await self.get_system_status(),
            "decision_patterns": await decision_tracker.get_decision_patterns() if decision_tracker else {},
            "cache_performance": self.cache_manager.get_stats() if self.cache_manager else {},
            "advanced_agent_metrics": {
                "total_advanced_agents": len(self.advanced_agents),
                "available_capabilities": list(self.advanced_agents.keys())
            }
        }
        
        return metrics
        
    def get_available_agents(self) -> List[str]:
        """Get list of all available agent types"""
        available = list(self.agents.keys()) + list(self.advanced_agents.keys())
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
        
        elif agent_type in self.advanced_agents:
            agent = self.advanced_agents[agent_type]
            response = await agent.process(context)
            return response.content, response.sources, response.confidence
            
        else:
            return f"Agent {agent_type} is not available.", [], 0.0 