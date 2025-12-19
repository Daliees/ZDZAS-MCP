"""AI Orchestration system for multi-agent response evaluation."""

import asyncio
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None

logger = logging.getLogger(__name__)


class EvaluationCriteria(Enum):
    """Criteria for evaluating responses."""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    EFFICIENCY = "efficiency"
    SAFETY = "safety"


@dataclass
class AgentResponse:
    """Response from an agent."""
    agent_id: str
    response: str
    confidence: float
    reasoning: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class EvaluationResult:
    """Result of response evaluation."""
    score: float
    criteria_scores: Dict[str, float]
    reasoning: str
    recommended: bool
    improvements: List[str]


@dataclass
class ConsensusResult:
    """Result of multi-agent consensus."""
    best_response: AgentResponse
    all_responses: List[AgentResponse]
    evaluations: List[EvaluationResult]
    consensus_score: float
    final_response: str
    decision_reasoning: str


class AgentOrchestrator:
    """Orchestrates multiple AI agents to evaluate and improve responses."""
    
    def __init__(
        self,
        primary_agent_runner: Callable,
        anthropic_api_key: Optional[str] = None,
        num_evaluator_agents: int = 3
    ):
        """
        Initialize the orchestrator.
        
        Args:
            primary_agent_runner: The primary agent's run function
            anthropic_api_key: Optional Anthropic API key for evaluators
            num_evaluator_agents: Number of evaluator agents (default: 3)
        """
        self.primary_agent = primary_agent_runner
        self.num_evaluators = num_evaluator_agents
        self.anthropic_client = None
        
        if anthropic_api_key and ANTHROPIC_AVAILABLE:
            self.anthropic_client = Anthropic(api_key=anthropic_api_key)
    
    async def run_primary_agent(self, user_input: str, conversation_id: str) -> AgentResponse:
        """
        Run the primary agent and get its response.
        
        Args:
            user_input: User's input message
            conversation_id: Conversation identifier
            
        Returns:
            AgentResponse with the primary agent's output
        """
        try:
            # Run the primary agent (assuming it's synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.primary_agent,
                user_input,
                conversation_id
            )
            
            return AgentResponse(
                agent_id="primary",
                response=response,
                confidence=0.8,
                reasoning="Primary ZAS agent response"
            )
        except Exception as e:
            logger.error(f"Primary agent error: {e}")
            return AgentResponse(
                agent_id="primary",
                response=f"Error: {str(e)}",
                confidence=0.0,
                reasoning="Agent execution failed"
            )
    
    async def evaluate_response(
        self,
        response: AgentResponse,
        original_query: str,
        evaluator_id: str
    ) -> EvaluationResult:
        """
        Evaluate a response using an AI evaluator.
        
        Args:
            response: The response to evaluate
            original_query: Original user query
            evaluator_id: ID of the evaluator
            
        Returns:
            EvaluationResult with scores and recommendations
        """
        if not self.anthropic_client:
            # Fallback: Simple heuristic evaluation
            return self._heuristic_evaluation(response, original_query)
        
        evaluation_prompt = f"""You are an AI response evaluator. Evaluate the following response based on these criteria:
1. Accuracy - Is the information correct?
2. Completeness - Does it fully answer the question?
3. Clarity - Is it clear and well-structured?
4. Efficiency - Is it concise without unnecessary information?
5. Safety - Are there any safety concerns?

Original Query: {original_query}

Response to Evaluate:
{response.response}

Agent's Confidence: {response.confidence}
Agent's Reasoning: {response.reasoning}

Provide your evaluation in JSON format:
{{
    "accuracy": 0.0-1.0,
    "completeness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "efficiency": 0.0-1.0,
    "safety": 0.0-1.0,
    "overall_score": 0.0-1.0,
    "reasoning": "Your detailed reasoning here",
    "recommended": true/false,
    "improvements": ["suggestion 1", "suggestion 2"]
}}"""
        
        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": evaluation_prompt}]
            )
            
            # Parse the JSON response
            eval_text = message.content[0].text
            # Extract JSON from markdown code block if present
            if "```json" in eval_text:
                eval_text = eval_text.split("```json")[1].split("```")[0].strip()
            elif "```" in eval_text:
                eval_text = eval_text.split("```")[1].split("```")[0].strip()
            
            eval_data = json.loads(eval_text)
            
            return EvaluationResult(
                score=eval_data.get("overall_score", 0.5),
                criteria_scores={
                    "accuracy": eval_data.get("accuracy", 0.5),
                    "completeness": eval_data.get("completeness", 0.5),
                    "clarity": eval_data.get("clarity", 0.5),
                    "efficiency": eval_data.get("efficiency", 0.5),
                    "safety": eval_data.get("safety", 0.5),
                },
                reasoning=eval_data.get("reasoning", ""),
                recommended=eval_data.get("recommended", True),
                improvements=eval_data.get("improvements", [])
            )
        except Exception as e:
            logger.error(f"Evaluation error from {evaluator_id}: {e}")
            return self._heuristic_evaluation(response, original_query)
    
    def _heuristic_evaluation(self, response: AgentResponse, original_query: str) -> EvaluationResult:
        """Fallback heuristic evaluation when AI evaluator is unavailable."""
        # Simple heuristic based on response length and confidence
        response_length = len(response.response)
        
        # Score based on length (prefer 100-1000 chars)
        if response_length < 50:
            length_score = 0.3
        elif response_length < 100:
            length_score = 0.6
        elif response_length < 1000:
            length_score = 0.9
        else:
            length_score = 0.7
        
        # Base score on confidence and length
        score = (response.confidence + length_score) / 2
        
        return EvaluationResult(
            score=score,
            criteria_scores={
                "accuracy": response.confidence,
                "completeness": length_score,
                "clarity": 0.7,
                "efficiency": 0.7,
                "safety": 0.9,
            },
            reasoning="Heuristic evaluation based on confidence and response length",
            recommended=score > 0.6,
            improvements=["Enable Anthropic API for detailed evaluation"]
        )
    
    async def get_consensus(
        self,
        user_input: str,
        conversation_id: str
    ) -> ConsensusResult:
        """
        Get multi-agent consensus on the best response.
        
        Args:
            user_input: User's input message
            conversation_id: Conversation identifier
            
        Returns:
            ConsensusResult with the best response and reasoning
        """
        # Step 1: Get primary agent response
        primary_response = await self.run_primary_agent(user_input, conversation_id)
        
        # For now, we only have one agent, but we can evaluate it multiple times
        responses = [primary_response]
        
        # Step 2: Evaluate the response with multiple evaluators
        evaluation_tasks = [
            self.evaluate_response(primary_response, user_input, f"evaluator_{i}")
            for i in range(self.num_evaluators)
        ]
        
        evaluations = await asyncio.gather(*evaluation_tasks)
        
        # Step 3: Calculate consensus score (average of all evaluations)
        avg_score = sum(e.score for e in evaluations) / len(evaluations)
        
        # Step 4: Aggregate improvements
        all_improvements = []
        for eval_result in evaluations:
            all_improvements.extend(eval_result.improvements)
        
        # Deduplicate improvements
        unique_improvements = list(set(all_improvements))
        
        # Step 5: Generate decision reasoning
        decision_reasoning = self._generate_decision_reasoning(
            evaluations,
            avg_score,
            unique_improvements
        )
        
        # Step 6: Decide if response should be modified
        final_response = primary_response.response
        if avg_score < 0.7 and unique_improvements:
            final_response = self._apply_improvements(
                primary_response.response,
                unique_improvements
            )
        
        return ConsensusResult(
            best_response=primary_response,
            all_responses=responses,
            evaluations=evaluations,
            consensus_score=avg_score,
            final_response=final_response,
            decision_reasoning=decision_reasoning
        )
    
    def _generate_decision_reasoning(
        self,
        evaluations: List[EvaluationResult],
        avg_score: float,
        improvements: List[str]
    ) -> str:
        """Generate human-readable decision reasoning."""
        reasoning_parts = [
            f"Consensus Score: {avg_score:.2f}/1.0",
            f"\nEvaluations: {len(evaluations)} evaluators reviewed the response",
        ]
        
        # Average criteria scores
        criteria_avgs = {}
        for criteria in ["accuracy", "completeness", "clarity", "efficiency", "safety"]:
            scores = [e.criteria_scores.get(criteria, 0) for e in evaluations]
            criteria_avgs[criteria] = sum(scores) / len(scores)
        
        reasoning_parts.append("\nCriteria Scores:")
        for criteria, score in criteria_avgs.items():
            reasoning_parts.append(f"  • {criteria.title()}: {score:.2f}")
        
        if improvements:
            reasoning_parts.append(f"\nSuggested Improvements: {len(improvements)}")
            for imp in improvements[:3]:  # Show top 3
                reasoning_parts.append(f"  • {imp}")
        
        recommendation = "✅ Response approved" if avg_score >= 0.7 else "⚠️ Response needs improvement"
        reasoning_parts.append(f"\n{recommendation}")
        
        return "\n".join(reasoning_parts)
    
    def _apply_improvements(self, original_response: str, improvements: List[str]) -> str:
        """Apply suggested improvements to response (simple version)."""
        # In a real implementation, this would use an LLM to rewrite
        # For now, just append improvement notes
        improved = original_response + "\n\n---\n**Improvement Suggestions:**\n"
        for i, imp in enumerate(improvements[:3], 1):
            improved += f"{i}. {imp}\n"
        return improved
    
    def run_with_orchestration(
        self,
        user_input: str,
        conversation_id: str
    ) -> Dict:
        """
        Run the orchestrated agent system (synchronous wrapper).
        
        Args:
            user_input: User's input message
            conversation_id: Conversation identifier
            
        Returns:
            Dictionary with response and metadata
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            consensus = loop.run_until_complete(
                self.get_consensus(user_input, conversation_id)
            )
            
            return {
                "response": consensus.final_response,
                "consensus_score": consensus.consensus_score,
                "decision_reasoning": consensus.decision_reasoning,
                "evaluations": [
                    {
                        "score": e.score,
                        "reasoning": e.reasoning,
                        "recommended": e.recommended,
                    }
                    for e in consensus.evaluations
                ],
                "metadata": {
                    "num_evaluators": len(consensus.evaluations),
                    "avg_score": consensus.consensus_score,
                }
            }
        finally:
            loop.close()


def create_orchestrator(
    primary_agent_runner: Callable,
    anthropic_api_key: Optional[str] = None,
    num_evaluators: int = 3
) -> AgentOrchestrator:
    """
    Create an agent orchestrator instance.
    
    Args:
        primary_agent_runner: The primary agent's run function
        anthropic_api_key: Optional Anthropic API key
        num_evaluators: Number of evaluator agents
        
    Returns:
        Configured AgentOrchestrator
    """
    return AgentOrchestrator(
        primary_agent_runner=primary_agent_runner,
        anthropic_api_key=anthropic_api_key,
        num_evaluator_agents=num_evaluators
    )
