"""
agents/parser.py

This module contains the ResumeParserAgent, utilizing Google ADK and core tools to analyze
candidate resumes and job descriptions.
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

from tools.agent_tools import parse_documents

class ResumeParserAgent:
    """
    Resume Intelligence Agent utilizing Google ADK and the parse_documents tool.
    """
    def __init__(self):
        # Configure Google ADK Agent
        self.adk_agent = Agent(
            name="resume_intelligence_agent",
            model="gemini-2.5-flash",
            instruction=(
                "You are an AI-powered resume and job description parser. "
                "Your task is to analyze candidate applications and map their credentials."
            ),
            tools=[parse_documents]
        )

    def parse(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Accept Resume and Job Description text, parse them using parse_documents tool,
        and return structured profile data.
        
        Args:
            resume_text (str): Raw text of the resume.
            jd_text (str): Raw text of the job description.
            
        Returns:
            Dict[str, Any]: Structured profile details or empty structure if invalid input.
        """
        # Handle invalid or empty inputs gracefully
        if not resume_text or not resume_text.strip() or not jd_text or not jd_text.strip():
            return {
                "user_skills": [],
                "experience": [],
                "education": [],
                "certifications": [],
                "jd_requirements": [],
                "jd_responsibilities": [],
                "missing_skills": [],
                "resume_match_score": 0.0
            }
            
        try:
            profile_data = parse_documents(resume_text, jd_text)
            return profile_data
        except Exception as e:
            # Return empty/default structure if tool execution encounters an error
            return {
                "user_skills": [],
                "experience": [],
                "education": [],
                "certifications": [],
                "jd_requirements": [],
                "jd_responsibilities": [],
                "missing_skills": [],
                "resume_match_score": 0.0
            }
