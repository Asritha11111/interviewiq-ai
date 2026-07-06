"""
agents/interviewer.py

This module contains the InterviewerAgent, utilizing Google ADK and tools to generate adaptive
interview questions based on candidate profile, job description, and history.
"""

from typing import List, Dict, Any

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

from tools.agent_tools import generate_questions

class InterviewerAgent:
    """
    Interview Generator Agent utilizing Google ADK and the generate_questions tool.
    """
    def __init__(self):
        # Configure Google ADK Agent
        self.adk_agent = Agent(
            name="interviewer_agent",
            model="gemini-2.5-flash",
            instruction=(
                "You are an expert technical and behavioral interviewer. "
                "Your role is to formulate relevant, balanced, and progressive questions "
                "tailored to the candidate's experience and the target job description."
            ),
            tools=[generate_questions]
        )

    def generate_interview_questions(
        self, profile: Dict[str, Any], jd_profile: Dict[str, Any], history: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Accept candidate profile, JD, and past history, call generate_questions tool,
        and return exactly five adaptive questions.
        
        Args:
            profile (Dict[str, Any]): Candidate profile mapping user skills, experience, etc.
            jd_profile (Dict[str, Any]): Job description requirements/responsibilities.
            history (List[Dict[str, Any]]): Past conversation transcripts or score history.
            
        Returns:
            List[str]: List of exactly five questions.
        """
        # Handle empty/invalid parameters gracefully
        if not profile or not jd_profile:
            # Fallback questions if input is incomplete
            return [
                "Could you walk me through your background and key experience relevant to this role?",
                "Tell me about a challenging technical problem you solved. What was the impact?",
                "How do you approach learning a new technology or framework on the job?",
                "Describe a time you had to work with a difficult teammate. How did you handle it?",
                "Why are you interested in this position, and how do you see yourself contributing?"
            ]

        try:
            questions = generate_questions(profile, jd_profile, history or [])
            return questions
        except Exception as e:
            # Return standard fallback list on failure
            return [
                "Could you walk me through your background and key experience relevant to this role?",
                "Tell me about a challenging technical problem you solved. What was the impact?",
                "How do you approach learning a new technology or framework on the job?",
                "Describe a time you had to work with a difficult teammate. How did you handle it?",
                "Why are you interested in this position, and how do you see yourself contributing?"
            ]
