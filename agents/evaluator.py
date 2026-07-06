"""
agents/evaluator.py

This module contains the EvaluatorAgent, utilizing Google ADK and tools to evaluate candidate
answers and supply grading, suggestions, and official documentation context.
"""

from typing import Dict, Any

try:
    from google.adk import Agent
except ImportError:
    try:
        from google.adk.agents import Agent
    except ImportError:
        # Graceful fallback for environment setups where google-adk is not yet installed
        class Agent:  # type: ignore
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

from tools.agent_tools import evaluate_answer, retrieve_mcp_docs

class EvaluatorAgent:
    """
    Evaluation Agent utilizing Google ADK, evaluate_answer, and retrieve_mcp_docs tools.
    """
    def __init__(self):
        # Configure Google ADK Agent
        self.adk_agent = Agent(
            name="evaluation_agent",
            model="gemini-2.5-flash",
            instruction=(
                "You are a rigorous candidate evaluation agent. "
                "Analyze answer accuracy and detail, referencing official developer documentation."
            ),
            tools=[evaluate_answer, retrieve_mcp_docs]
        )

    def evaluate(self, question: str, answer: str, topic: str) -> Dict[str, Any]:
        """
        Evaluate candidate answer and retrieve official documentation.
        
        Args:
            question (str): The mock interview question.
            answer (str): Candidate's response.
            topic (str): General topic (e.g., Streamlit, Gemini).
            
        Returns:
            Dict[str, Any]: Comprehensive evaluation report including score, feedback, strengths, 
                            weaknesses, recommended topic, and official documentation text.
        """
        # Setup fallback default evaluation
        default_eval = {
            "score": 5,
            "feedback": "Evaluation failed due to an internal error or missing inputs.",
            "improvement_tip": "Please try submitting your answer again.",
            "strengths": ["Answer received."],
            "weaknesses": ["Unable to fully analyze weaknesses."],
            "recommended_topic": topic,
            "official_docs": ""
        }

        if not question or not answer:
            return default_eval

        try:
            # 1. Evaluate the answer
            evaluation_report = evaluate_answer(question, answer, topic)
            
            # 2. Retrieve official docs from Developer Knowledge MCP
            official_docs = retrieve_mcp_docs(topic)
            
            # 3. Combine results
            evaluation_report["official_docs"] = official_docs
            return evaluation_report
            
        except Exception as e:
            # Fallback gracefully
            default_eval["feedback"] = f"Evaluation encountered an error: {e}"
            try:
                # Attempt to at least fetch docs if available
                default_eval["official_docs"] = retrieve_mcp_docs(topic)
            except Exception:
                pass
            return default_eval
