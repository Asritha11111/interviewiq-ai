"""
tests/test_agents.py

Pytest suite to verify core agent utilities, tool integrations, and Streamlit session states.
Mocks all LLM API calls and MCP socket transports for speed and offline predictability.
"""

import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Mock plotly if it is not installed in the testing environment
# to prevent import errors when loading app.py
sys.modules['plotly'] = MagicMock()
sys.modules['plotly.express'] = MagicMock()

import streamlit as st

# Import the core tool interfaces
from tools.agent_tools import (
    parse_documents,
    generate_questions,
    evaluate_answer,
    retrieve_mcp_docs
)


# ==================== PART 1: TEST PARSE DOCUMENTS ====================

@patch("tools.agent_tools._generate_content")
def test_parse_documents(mock_generate):
    """
    Verify resume and job description parsing return structured matching formats.
    """
    mock_profile = {
        "user_skills": ["Python", "Streamlit", "Docker"],
        "experience": ["Senior Engineer at TechCorp"],
        "education": ["BS in Computer Science"],
        "certifications": ["Google Cloud Certified Architect"],
        "jd_requirements": ["Python", "Streamlit", "Kubernetes"],
        "jd_responsibilities": ["Design responsive mock interview boards"],
        "missing_skills": ["Kubernetes"],
        "resume_match_score": 82.5
    }
    mock_generate.return_value = json.dumps(mock_profile)

    result = parse_documents("Mock resume body", "Mock JD body")

    assert isinstance(result, dict)
    assert result["resume_match_score"] == 82.5
    assert result["user_skills"] == ["Python", "Streamlit", "Docker"]
    assert result["missing_skills"] == ["Kubernetes"]
    assert "experience" in result
    assert "education" in result
    assert "certifications" in result
    assert "jd_requirements" in result
    assert "jd_responsibilities" in result


# ==================== PART 2: TEST GENERATE QUESTIONS ====================

@patch("tools.agent_tools._generate_content")
def test_generate_questions(mock_generate):
    """
    Verify exactly 5 interview questions are generated and returned as a list.
    """
    mock_questions = [
        "Can you explain the difference between st.cache_data and st.cache_resource?",
        "Describe a complex agent workflow you built using the Google ADK.",
        "How do you configure an MCP server client transport in Python?",
        "Tell me about a challenging technical challenge you solved.",
        "How do you optimize Plotly charts for high-frequency dashboard renders?"
    ]
    mock_generate.return_value = json.dumps(mock_questions)

    profile = {"user_skills": ["Python", "Streamlit"]}
    jd_profile = {"jd_requirements": ["Python"]}
    history = []

    result = generate_questions(profile, jd_profile, history)

    assert isinstance(result, list)
    assert len(result) == 5
    assert result[0] == "Can you explain the difference between st.cache_data and st.cache_resource?"
    assert all(isinstance(q, str) for q in result)


# ==================== PART 3: TEST EVALUATE ANSWER ====================

@patch("tools.agent_tools._generate_content")
def test_evaluate_answer(mock_generate):
    """
    Verify evaluation returns correct feedback parameters and rating scale.
    """
    mock_eval = {
        "score": 9,
        "feedback": "Perfect description of Session State components.",
        "improvement_tip": "Explicitly mention thread safety considerations.",
        "strengths": ["Clear explanation", "Excellent terminology usage"],
        "weaknesses": ["Missed callback hooks"],
        "recommended_topic": "Streamlit Callbacks"
    }
    mock_generate.return_value = json.dumps(mock_eval)

    result = evaluate_answer("What is st.session_state?", "It stores persistent variables.", "Streamlit")

    assert isinstance(result, dict)
    assert result["score"] == 9
    assert result["feedback"] == "Perfect description of Session State components."
    assert result["improvement_tip"] == "Explicitly mention thread safety considerations."
    assert result["strengths"] == ["Clear explanation", "Excellent terminology usage"]
    assert result["weaknesses"] == ["Missed callback hooks"]
    assert result["recommended_topic"] == "Streamlit Callbacks"


# ==================== PART 4: TEST RETRIEVE MCP DOCS ====================

@patch("tools.agent_tools._async_retrieve_mcp_docs")
@patch("tools.agent_tools.run_async")
def test_retrieve_mcp_docs(mock_run_async, mock_async_retrieve):
    """
    Mock the MCP server connection to verify fallback cached snippets are returned
    gracefully when the remote server is unreachable, and success blocks are returned otherwise.
    """
    # Prevent coroutine instantiation warnings by mocking the async target
    mock_async_retrieve.return_value = None

    # Case 1: MCP connection fails / raises exception -> falls back to offline cached snippets
    mock_run_async.side_effect = ConnectionError("Could not reach MCP endpoint")

    result_offline = retrieve_mcp_docs("streamlit")
    assert "Developer Knowledge MCP Offline (Fallback)" in result_offline
    assert "Use st.session_state to store variables" in result_offline

    result_missing = retrieve_mcp_docs("unsupported_topic_name")
    assert "No local snippet available for" in result_missing

    # Case 2: MCP query succeeds
    mock_run_async.side_effect = None
    mock_run_async.return_value = "Official documentation text for Streamlit layouts from Google Developer Knowledge MCP"

    result_success = retrieve_mcp_docs("streamlit")
    assert "Developer Knowledge MCP Search Results" in result_success
    assert "Official documentation text for Streamlit layouts" in result_success


# ==================== PART 5: TEST STREAMLIT SESSION STATE ====================

class MockSessionState(dict):
    """Custom dictionary-like mock representing st.session_state."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def test_session_state(monkeypatch):
    """
    Verify Streamlit session state initializes correctly with required memory slots.
    """
    mock_state = MockSessionState()
    monkeypatch.setattr(st, "session_state", mock_state)

    # Import and run key initialization function from app.py
    from app import init_session
    init_session()

    # Validate correct state initialization
    assert "questions" in mock_state
    assert isinstance(mock_state["questions"], list)
    
    assert "answers" in mock_state
    assert isinstance(mock_state["answers"], list)
    
    assert "scores" in mock_state
    assert isinstance(mock_state["scores"], list)
    
    assert "feedback" in mock_state
    assert isinstance(mock_state["feedback"], list)
    
    assert "interview_completed" in mock_state
    assert mock_state["interview_completed"] is False

    assert "resume_match_score" in mock_state
    assert isinstance(mock_state["resume_match_score"], float)
