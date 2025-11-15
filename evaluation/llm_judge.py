"""
LLM-as-Judge Evaluation Module

This implements the "Agent evaluation" concept from the course by using
an LLM to evaluate agent performance and responses.
"""

from typing import Dict, Any, List
import google.generativeai as genai


class LLMJudge:
    """Uses LLM to evaluate agent performance."""
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """Initialize the LLM judge with a Gemini model."""
        self.model = genai.GenerativeModel(model_name)
    
    def evaluate_agent_response(self, agent_name: str, task: str, response: str, 
                                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate an agent's response using LLM-as-judge.
        
        Args:
            agent_name: Name of the agent being evaluated
            task: Description of the task
            response: Agent's response/action
            context: Additional context about the incident
            
        Returns:
            Evaluation results with scores and feedback
        """
        evaluation_prompt = f"""You are an expert evaluator assessing an AI agent's performance in an enterprise incident response system.

Agent: {agent_name}
Task: {task}
Agent Response: {response}
Context: {context or {}}

Evaluate the agent's response on the following criteria (1-10 scale):
1. Accuracy: Was the response correct and appropriate?
2. Completeness: Did the agent address all aspects of the task?
3. Clarity: Was the response clear and well-structured?
4. Actionability: Did the response provide actionable next steps?
5. Efficiency: Was the response concise and to the point?

Provide:
- Scores for each criterion (1-10)
- Overall score (average)
- Strengths: What the agent did well
- Weaknesses: Areas for improvement
- Recommendation: "excellent", "good", "needs_improvement", or "poor"

Format your response as a structured evaluation."""

        try:
            result = self.model.generate_content(evaluation_prompt)
            evaluation_text = result.text
            
            # Parse the evaluation (simplified - in production would use structured output)
            # For now, return the raw evaluation text with a simple score extraction
            overall_score = self._extract_score(evaluation_text)
            
            return {
                "agent": agent_name,
                "task": task,
                "evaluation_text": evaluation_text,
                "overall_score": overall_score,
                "recommendation": self._extract_recommendation(evaluation_text)
            }
        except Exception as e:
            return {
                "agent": agent_name,
                "task": task,
                "error": str(e),
                "overall_score": None
            }
    
    def _extract_score(self, text: str) -> float:
        """Extract overall score from evaluation text."""
        import re
        # Look for patterns like "Overall score: 8.5" or "Score: 7"
        patterns = [
            r"overall score[:\s]+(\d+\.?\d*)",
            r"score[:\s]+(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*out of 10"
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        return 7.0  # Default if not found
    
    def _extract_recommendation(self, text: str) -> str:
        """Extract recommendation from evaluation text."""
        text_lower = text.lower()
        if "excellent" in text_lower:
            return "excellent"
        elif "good" in text_lower:
            return "good"
        elif "needs improvement" in text_lower or "needs_improvement" in text_lower:
            return "needs_improvement"
        elif "poor" in text_lower:
            return "poor"
        return "good"  # Default
    
    def compare_agents(self, agent_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple agent responses for the same task.
        
        Args:
            agent_responses: List of dicts with agent_name, task, response, context
            
        Returns:
            Comparative evaluation
        """
        evaluations = []
        for response_data in agent_responses:
            eval_result = self.evaluate_agent_response(
                response_data["agent_name"],
                response_data["task"],
                response_data["response"],
                response_data.get("context")
            )
            evaluations.append(eval_result)
        
        # Find best agent
        valid_scores = [(e["overall_score"], e["agent"]) for e in evaluations if e.get("overall_score")]
        if valid_scores:
            best_score, best_agent = max(valid_scores, key=lambda x: x[0])
        else:
            best_agent = None
            best_score = None
        
        return {
            "evaluations": evaluations,
            "best_agent": best_agent,
            "best_score": best_score
        }

