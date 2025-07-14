# agents/planning_agent.py
import asyncio
import json
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent, QueryContext
from agents.decision_tracker import decision_tracker, DecisionType
from storage.neo4j_manager import Neo4jManager
from storage.cache_manager import CacheManager
from core.config import config
from utils.monitoring import monitor_performance
from utils.logging_config import get_logger

logger = get_logger(__name__)

class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class SubTask:
    """Represents a single subtask in a plan"""
    id: str
    description: str
    agent_type: str
    input_requirements: Dict[str, Any]
    expected_output: Dict[str, Any]
    priority: TaskPriority
    estimated_time_ms: int
    dependencies: List[str]
    status: TaskStatus = TaskStatus.PENDING
    actual_output: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    confidence: Optional[float] = None
    error_message: Optional[str] = None

class ExecutionPlan(BaseModel):
    """Structured plan for query execution"""
    plan_id: str = Field(description="Unique identifier for the plan")
    original_query: str = Field(description="The original user query")
    plan_summary: str = Field(description="High-level description of the plan")
    subtasks: List[Dict[str, Any]] = Field(description="List of subtasks to execute")
    estimated_total_time_ms: int = Field(description="Estimated total execution time")
    complexity_score: float = Field(description="Complexity score from 0-1")
    confidence_prediction: float = Field(description="Predicted confidence of success")

class ReflectionResult(BaseModel):
    """Results of self-reflection on outputs"""
    quality_score: float = Field(description="Quality assessment 0-1")
    completeness_score: float = Field(description="How complete the answer is 0-1")
    accuracy_confidence: float = Field(description="Confidence in accuracy 0-1")
    improvement_suggestions: List[str] = Field(description="Specific improvement suggestions")
    should_retry: bool = Field(description="Whether the task should be retried")
    retry_strategy: Optional[str] = Field(description="Strategy for retry if needed")

class PlanningAgent(BaseAgent):
    """Advanced agent that can plan, coordinate, and self-reflect on multi-step tasks"""
    
    def __init__(self):
        super().__init__(
            name="PlanningAgent",
            config=config.get("agents.planning", {})
        )
        self.llm = None
        self.planning_llm = None
        self.reflection_llm = None
        self.neo4j_manager = None
        self.cache_manager = None
        self.execution_plans: Dict[str, ExecutionPlan] = {}
        self.agent_registry: Dict[str, BaseAgent] = {}
        
    async def _setup(self):
        """Initialize planning components"""
        # Use different LLM configurations for different tasks
        self.llm = ChatOpenAI(
            model=config.api.openai_model,
            temperature=0.1,
            openai_api_key=config.api.openai_api_key
        )
        
        # More creative LLM for planning
        self.planning_llm = ChatOpenAI(
            model=config.api.openai_model,
            temperature=0.3,
            openai_api_key=config.api.openai_api_key
        )
        
        # Analytical LLM for reflection
        self.reflection_llm = ChatOpenAI(
            model=config.api.openai_model,
            temperature=0.0,
            openai_api_key=config.api.openai_api_key
        )
        
        self.neo4j_manager = Neo4jManager()
        await self.neo4j_manager.initialize()
        
        self.cache_manager = CacheManager()
        await self.cache_manager.initialize()
        
        logger.info("Planning Agent initialized with multi-LLM setup")
        
    def register_agent(self, agent_type: str, agent: BaseAgent):
        """Register an agent for task execution"""
        self.agent_registry[agent_type] = agent
        logger.info(f"Registered agent: {agent_type}")
        
    async def _process_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Process query using intelligent planning and coordination"""
        
        # Start decision tracking
        await decision_tracker.record_decision(
            agent_name=self.name,
            decision_type=DecisionType.AGENT_SELECTION,
            input_data={"query": context.original_query},
            decision_logic="Analyzing query complexity for planning strategy",
            output_decision="planning_required",
            confidence=0.9,
            processing_time_ms=50,
            parent_query_id=context.query_id
        )
        
        try:
            # 1. Create execution plan
            execution_plan = await self._create_execution_plan(context)
            
            # 2. Execute plan with coordination
            execution_results = await self._execute_plan(execution_plan, context)
            
            # 3. Self-reflect on results
            reflection = await self._reflect_on_results(execution_results, context)
            
            # 4. Improve if necessary
            if reflection.should_retry and reflection.retry_strategy:
                logger.info(f"Retrying with strategy: {reflection.retry_strategy}")
                execution_results = await self._retry_execution(execution_plan, execution_results, reflection, context)
                reflection = await self._reflect_on_results(execution_results, context)
            
            # 5. Synthesize final response
            final_response = await self._synthesize_response(execution_results, reflection, context)
            
            # Calculate overall confidence
            avg_confidence = sum(task.confidence or 0.5 for task in execution_results.values()) / len(execution_results)
            final_confidence = (avg_confidence + reflection.accuracy_confidence) / 2
            
            # Extract sources
            sources = []
            for task_id, task in execution_results.items():
                if task.actual_output and 'sources' in task.actual_output:
                    sources.extend(task.actual_output['sources'])
            
            return final_response, sources, final_confidence
            
        except Exception as e:
            logger.error(f"Error in planning execution: {str(e)}")
            await decision_tracker.record_decision(
                agent_name=self.name,
                decision_type=DecisionType.ERROR_HANDLING,
                input_data={"error": str(e)},
                decision_logic="Fallback to simple processing",
                output_decision="simple_fallback",
                confidence=0.3,
                processing_time_ms=100,
                parent_query_id=context.query_id
            )
            return f"I encountered an error while planning the response: {str(e)}", [], 0.3
            
    @monitor_performance("planning_agent", "create_execution_plan")
    async def _create_execution_plan(self, context: QueryContext) -> ExecutionPlan:
        """Create a detailed execution plan for the query"""
        
        planning_prompt = """You are an AI planning expert. Analyze the following query and create a detailed execution plan.

Query: {query}
User Expertise Level: {expertise_level}

Available Agent Types:
- DocumentAgent: Searches and analyzes text documents, papers, and articles
- ImageAgent: Processes and analyzes images using CLIP and vision models  
- CodeIntelligenceAgent: Analyzes GitHub repositories and code architecture
- GraphAgent: Queries knowledge graphs and entity relationships

Create a plan that breaks down the query into specific subtasks. Each subtask should:
1. Be assigned to the most appropriate agent type
2. Have clear input requirements and expected outputs
3. Include realistic time estimates
4. Specify dependencies between tasks
5. Have appropriate priority levels

Consider the user's expertise level when planning the response depth and complexity.

Return your plan in the following JSON format:
{{
    "plan_summary": "Brief description of the overall approach",
    "subtasks": [
        {{
            "description": "What this subtask accomplishes",
            "agent_type": "Which agent should handle this",
            "input_requirements": {{"key": "description of needed inputs"}},
            "expected_output": {{"key": "description of expected outputs"}},
            "priority": "critical|high|medium|low",
            "estimated_time_ms": 1000,
            "dependencies": ["list", "of", "subtask", "ids", "that", "must", "complete", "first"]
        }}
    ],
    "estimated_total_time_ms": 5000,
    "complexity_score": 0.7,
    "confidence_prediction": 0.85
}}

Make the plan realistic and executable. Focus on breaking complex queries into manageable pieces."""

        try:
            messages = [
                SystemMessage(content="You are an expert AI system planner."),
                HumanMessage(content=planning_prompt.format(
                    query=context.original_query,
                    expertise_level=context.user_expertise_level
                ))
            ]
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.planning_llm.invoke,
                messages
            )
            
            # Parse the JSON response
            plan_data = json.loads(response.content)
            
            # Create execution plan
            execution_plan = ExecutionPlan(
                plan_id=str(uuid.uuid4()),
                original_query=context.original_query,
                plan_summary=plan_data["plan_summary"],
                subtasks=plan_data["subtasks"],
                estimated_total_time_ms=plan_data["estimated_total_time_ms"],
                complexity_score=plan_data["complexity_score"],
                confidence_prediction=plan_data["confidence_prediction"]
            )
            
            # Store plan for tracking
            self.execution_plans[execution_plan.plan_id] = execution_plan
            
            await decision_tracker.record_decision(
                agent_name=self.name,
                decision_type=DecisionType.RETRIEVAL_STRATEGY,
                input_data={"query": context.original_query},
                decision_logic=f"Created {len(plan_data['subtasks'])} subtask plan",
                output_decision=plan_data["plan_summary"],
                confidence=plan_data["confidence_prediction"],
                processing_time_ms=500,
                parent_query_id=context.query_id
            )
            
            logger.info(f"Created execution plan with {len(plan_data['subtasks'])} subtasks")
            return execution_plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {str(e)}")
            # Fallback to simple plan
            return ExecutionPlan(
                plan_id=str(uuid.uuid4()),
                original_query=context.original_query,
                plan_summary="Simple single-agent processing",
                subtasks=[{
                    "description": "Process query with document search",
                    "agent_type": "DocumentAgent",
                    "input_requirements": {"query": context.original_query},
                    "expected_output": {"answer": "text response"},
                    "priority": "high",
                    "estimated_time_ms": 2000,
                    "dependencies": []
                }],
                estimated_total_time_ms=2000,
                complexity_score=0.3,
                confidence_prediction=0.7
            )
            
    async def _execute_plan(self, plan: ExecutionPlan, context: QueryContext) -> Dict[str, SubTask]:
        """Execute the plan by coordinating multiple agents"""
        
        # Convert plan subtasks to SubTask objects
        subtasks = {}
        for i, task_data in enumerate(plan.subtasks):
            task_id = f"task_{i+1}"
            subtask = SubTask(
                id=task_id,
                description=task_data["description"],
                agent_type=task_data["agent_type"],
                input_requirements=task_data["input_requirements"],
                expected_output=task_data["expected_output"],
                priority=TaskPriority(task_data["priority"]),
                estimated_time_ms=task_data["estimated_time_ms"],
                dependencies=task_data.get("dependencies", [])
            )
            subtasks[task_id] = subtask
        
        # Execute tasks in dependency order
        completed_tasks = {}
        remaining_tasks = subtasks.copy()
        
        while remaining_tasks:
            # Find tasks ready to execute (dependencies satisfied)
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                if all(dep in completed_tasks for dep in task.dependencies):
                    ready_tasks.append((task_id, task))
            
            if not ready_tasks:
                logger.error("Circular dependency detected in execution plan")
                break
                
            # Execute ready tasks (could be parallel, but sequential for now)
            for task_id, task in ready_tasks:
                try:
                    start_time = datetime.now()
                    task.status = TaskStatus.IN_PROGRESS
                    
                    # Execute task with appropriate agent
                    result = await self._execute_single_task(task, completed_tasks, context)
                    
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    task.execution_time_ms = execution_time
                    task.actual_output = result.get("output", {})
                    task.confidence = result.get("confidence", 0.5)
                    task.status = TaskStatus.COMPLETED
                    
                    completed_tasks[task_id] = task
                    del remaining_tasks[task_id]
                    
                    # Record the agent interaction
                    await decision_tracker.record_agent_interaction(
                        source_agent=self.name,
                        target_agent=task.agent_type,
                        interaction_type="task_execution",
                        data_passed=task.input_requirements,
                        response_received=task.actual_output,
                        success=True,
                        processing_time_ms=execution_time,
                        parent_query_id=context.query_id
                    )
                    
                    logger.info(f"Completed task {task_id}: {task.description}")
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                    completed_tasks[task_id] = task
                    del remaining_tasks[task_id]
                    
                    logger.error(f"Task {task_id} failed: {str(e)}")
        
        return completed_tasks
        
    async def _execute_single_task(self, task: SubTask, completed_tasks: Dict[str, SubTask], context: QueryContext) -> Dict[str, Any]:
        """Execute a single subtask using the appropriate agent"""
        
        # Get the agent for this task type
        if task.agent_type not in self.agent_registry:
            logger.warning(f"Agent type {task.agent_type} not registered, using DocumentAgent")
            task.agent_type = "DocumentAgent"
            
        if task.agent_type not in self.agent_registry:
            # Fallback to LLM-only processing
            return await self._llm_fallback_execution(task, context)
            
        agent = self.agent_registry[task.agent_type]
        
        # Prepare context for the agent
        task_context = QueryContext(
            query_id=context.query_id,
            original_query=task.description,
            user_id=context.user_id,
            user_expertise_level=context.user_expertise_level,
            metadata={
                **context.metadata,
                "task_id": task.id,
                "input_requirements": task.input_requirements,
                "parent_plan_id": context.query_id
            }
        )
        
        # Execute with the agent
        response = await agent.process(task_context)
        
        return {
            "output": {
                "content": response.content,
                "sources": response.sources,
                "metadata": response.metadata
            },
            "confidence": response.confidence,
            "processing_time": response.processing_time
        }
        
    async def _llm_fallback_execution(self, task: SubTask, context: QueryContext) -> Dict[str, Any]:
        """Fallback execution using LLM when agent is not available"""
        
        fallback_prompt = f"""
        As an AI assistant, help with this specific task:
        
        Task: {task.description}
        User Query Context: {context.original_query}
        User Expertise Level: {context.user_expertise_level}
        
        Provide a helpful response for this subtask.
        """
        
        try:
            messages = [
                SystemMessage(content="You are a helpful AI assistant."),
                HumanMessage(content=fallback_prompt)
            ]
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.llm.invoke,
                messages
            )
            
            return {
                "output": {
                    "content": response.content,
                    "sources": [{"type": "llm_fallback", "agent_type": task.agent_type}],
                    "metadata": {"execution_method": "llm_fallback"}
                },
                "confidence": 0.6,
                "processing_time": 1000
            }
            
        except Exception as e:
            logger.error(f"LLM fallback failed: {str(e)}")
            return {
                "output": {
                    "content": f"Unable to complete task: {task.description}",
                    "sources": [],
                    "metadata": {"error": str(e)}
                },
                "confidence": 0.1,
                "processing_time": 100
            }
            
    async def _reflect_on_results(self, execution_results: Dict[str, SubTask], context: QueryContext) -> ReflectionResult:
        """Self-reflect on the quality and completeness of results"""
        
        # Prepare reflection data
        results_summary = {}
        for task_id, task in execution_results.items():
            results_summary[task_id] = {
                "description": task.description,
                "status": task.status.value,
                "confidence": task.confidence,
                "has_output": task.actual_output is not None,
                "error": task.error_message
            }
        
        reflection_prompt = f"""
        Analyze the execution results for this query and provide a self-reflection assessment.
        
        Original Query: {context.original_query}
        User Expertise Level: {context.user_expertise_level}
        
        Execution Results Summary:
        {json.dumps(results_summary, indent=2)}
        
        Evaluate:
        1. Quality: How well do the results address the query?
        2. Completeness: Are all aspects of the query covered?
        3. Accuracy: How confident are you in the accuracy?
        4. Improvements: What specific improvements could be made?
        5. Retry: Should any tasks be retried with a different approach?
        
        Provide your assessment in this JSON format:
        {{
            "quality_score": 0.85,
            "completeness_score": 0.90,
            "accuracy_confidence": 0.88,
            "improvement_suggestions": ["specific suggestion 1", "specific suggestion 2"],
            "should_retry": false,
            "retry_strategy": "strategy description if retry needed"
        }}
        """
        
        try:
            messages = [
                SystemMessage(content="You are an expert at evaluating AI system performance."),
                HumanMessage(content=reflection_prompt)
            ]
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.reflection_llm.invoke,
                messages
            )
            
            reflection_data = json.loads(response.content)
            
            reflection = ReflectionResult(
                quality_score=reflection_data["quality_score"],
                completeness_score=reflection_data["completeness_score"],
                accuracy_confidence=reflection_data["accuracy_confidence"],
                improvement_suggestions=reflection_data["improvement_suggestions"],
                should_retry=reflection_data["should_retry"],
                retry_strategy=reflection_data.get("retry_strategy")
            )
            
            await decision_tracker.record_decision(
                agent_name=self.name,
                decision_type=DecisionType.CONFIDENCE_EVALUATION,
                input_data={"results_count": len(execution_results)},
                decision_logic="Self-reflection on execution quality",
                output_decision=f"Quality: {reflection.quality_score:.2f}, Retry: {reflection.should_retry}",
                confidence=reflection.accuracy_confidence,
                processing_time_ms=300,
                parent_query_id=context.query_id
            )
            
            return reflection
            
        except Exception as e:
            logger.error(f"Error in self-reflection: {str(e)}")
            return ReflectionResult(
                quality_score=0.7,
                completeness_score=0.7,
                accuracy_confidence=0.6,
                improvement_suggestions=["Unable to perform detailed reflection"],
                should_retry=False,
                retry_strategy=None
            )
            
    async def _retry_execution(
        self, 
        plan: ExecutionPlan, 
        execution_results: Dict[str, SubTask], 
        reflection: ReflectionResult, 
        context: QueryContext
    ) -> Dict[str, SubTask]:
        """Retry failed or low-quality tasks with improved strategy"""
        
        # Identify tasks to retry based on reflection
        retry_tasks = []
        for task_id, task in execution_results.items():
            if (task.status == TaskStatus.FAILED or 
                (task.confidence and task.confidence < 0.6)):
                retry_tasks.append(task_id)
        
        # Re-execute identified tasks
        for task_id in retry_tasks:
            task = execution_results[task_id]
            try:
                logger.info(f"Retrying task {task_id} with strategy: {reflection.retry_strategy}")
                
                # Modify task based on retry strategy
                if "different_agent" in reflection.retry_strategy.lower():
                    # Try with a different agent type
                    original_agent_type = task.agent_type
                    alternative_agents = ["DocumentAgent", "ImageAgent", "CodeIntelligenceAgent"]
                    alternative_agents = [a for a in alternative_agents if a != original_agent_type]
                    if alternative_agents:
                        task.agent_type = alternative_agents[0]
                
                # Re-execute the task
                result = await self._execute_single_task(task, execution_results, context)
                
                task.actual_output = result.get("output", {})
                task.confidence = result.get("confidence", 0.5)
                task.status = TaskStatus.COMPLETED
                
                logger.info(f"Successfully retried task {task_id}")
                
            except Exception as e:
                logger.error(f"Retry failed for task {task_id}: {str(e)}")
                task.error_message = f"Retry failed: {str(e)}"
        
        return execution_results
        
    async def _synthesize_response(
        self, 
        execution_results: Dict[str, SubTask], 
        reflection: ReflectionResult, 
        context: QueryContext
    ) -> str:
        """Synthesize final response from all execution results"""
        
        # Collect all successful outputs
        successful_outputs = []
        for task_id, task in execution_results.items():
            if task.status == TaskStatus.COMPLETED and task.actual_output:
                successful_outputs.append({
                    "task": task.description,
                    "content": task.actual_output.get("content", ""),
                    "confidence": task.confidence
                })
        
        synthesis_prompt = f"""
        Synthesize a comprehensive response to the user's query using the results from multiple specialized agents.
        
        Original Query: {context.original_query}
        User Expertise Level: {context.user_expertise_level}
        
        Agent Results:
        {json.dumps(successful_outputs, indent=2)}
        
        Quality Assessment:
        - Quality Score: {reflection.quality_score:.2f}
        - Completeness Score: {reflection.completeness_score:.2f}
        - Accuracy Confidence: {reflection.accuracy_confidence:.2f}
        
        Create a cohesive, well-structured response that:
        1. Directly addresses the user's query
        2. Integrates insights from all agent results
        3. Maintains appropriate technical depth for the user's expertise level
        4. Acknowledges any limitations or uncertainties
        5. Provides actionable insights where applicable
        
        Make the response natural and helpful, not just a summary of results.
        """
        
        try:
            messages = [
                SystemMessage(content="You are an expert at synthesizing multi-agent AI responses."),
                HumanMessage(content=synthesis_prompt)
            ]
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.llm.invoke,
                messages
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error synthesizing response: {str(e)}")
            # Fallback synthesis
            if successful_outputs:
                return f"Based on the analysis, here's what I found: {successful_outputs[0]['content'][:500]}..."
            else:
                return "I apologize, but I wasn't able to generate a comprehensive response to your query at this time." 