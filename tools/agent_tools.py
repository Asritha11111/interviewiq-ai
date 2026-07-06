"""
tools/agent_tools.py

This module provides tools for the InterviewIQ AI agents.
It includes functions for resume/job description parsing, interview question generation,
answer evaluation, and Google Developer Knowledge MCP documentation retrieval.
"""

import os
import json
import asyncio
import concurrent.futures
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read the Google API Key
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Default models
PRIMARY_MODEL = "gemini-2.5-flash"

# Offline documentation dictionary fallback for the Google Developer Knowledge MCP
CACHED_MCP_DOCS = {
    "streamlit": (
        "=== Streamlit Documentation Summary ===\n"
        "- Layouts: Use st.columns, st.tabs, st.container, and st.expander for structuring layout.\n"
        "- Session State: Use st.session_state to store variables across page reruns.\n"
        "- Callbacks: Widgets support 'on_change' or 'on_click' parameters to trigger functions."
    ),
    "gemini": (
        "=== Gemini API Documentation Summary ===\n"
        "- Models: Use 'gemini-2.5-flash' for general tasks and 'gemini-2.5-pro' for complex reasoning.\n"
        "- Generation Config: Configure temperature, top_p, and response_mime_type (set to 'application/json').\n"
        "- System Instructions: Pass system instructions during client model initialization."
    ),
    "adk": (
        "=== Google Agent Development Kit (ADK) Documentation Summary ===\n"
        "- Core: ADK is a framework for building AI agent workflows and systems using Gemini.\n"
        "- Agents: Configured with instructions, tools, and a model to execute goals in loops.\n"
        "- Tools: Decorate Python functions with @tool to expose them for agent invocation."
    ),
    "mcp": (
        "=== Model Context Protocol (MCP) Documentation Summary ===\n"
        "- Standard: Open protocol enabling AI models to safely access external resources and databases.\n"
        "- Managed Servers: Accessible via HTTP endpoints (e.g., https://developerknowledge.googleapis.com/mcp).\n"
        "- Tools Exposed: Typically exposes tools like 'search_documents' and 'get_documents'."
    ),
    "python": (
        "=== Python Developer Documentation Summary ===\n"
        "- Type Hints: Use typing module (Union, List, Dict) to annotate functions.\n"
        "- Asyncio: Use 'async def' and 'await' for concurrent programs. Run via asyncio.run()."
    ),
    "pytest": (
        "=== Pytest Documentation Summary ===\n"
        "- Execution: Run tests via 'pytest' CLI. Standard files start with 'test_'.\n"
        "- Assertions: Uses standard Python assert statements.\n"
        "- Fixtures: Use @pytest.fixture to share setup/teardown code across tests."
    ),
    "plotly": (
        "=== Plotly Documentation Summary ===\n"
        "- Visuals: Use plotly.graph_objects or plotly.express for interactive visualizations.\n"
        "- Streamlit: Render charts seamlessly via st.plotly_chart(fig)."
    ),
    # ==================== NEWLY ADDED FOR YOUR LEARNING PLAN ====================
    "communication": (
        "=== Effective Communication in Tech (Official Best Practices) ===\n"
        "- Active Listening: Focus fully on the speaker, confirm understanding by paraphrasing.\n"
        "- STAR Method: Structure answers using Situation, Task, Action, Result for behavioral questions.\n"
        "- Technical Articulation: Avoid jargon when speaking to non-technical stakeholders; use analogies.\n"
        "- Written Communication: Use clear subject lines, bullet points, and concise language in emails and PRs.\n"
        "- Feedback: Actively seek and give constructive feedback to improve team dynamics."
    ),
        "data structures and algorithms": (
        "=== Data Structures & Algorithms (Official Reference) ===\n"
        "- Core Structures: Arrays (O(1) access), Hash Maps (O(1) avg lookup), Trees (BST, AVL - O(log n)), Graphs (BFS/DFS).\n"
        "- Algorithm Paradigms: Divide & Conquer (Merge/Quick Sort), Dynamic Programming (Knapsack, LCS), Greedy (Dijkstra's).\n"
        "- Complexity Analysis: Always evaluate Time & Space complexity using Big O notation.\n"
        "- Recursion: Define clear base cases. Use memoization to optimize overlapping subproblems.\n"
        "- Best Practice: Always test edge cases (empty inputs, duplicates, large values) before submitting solutions."
    ),
}

# Default outputs to ensure the application fails gracefully instead of crashing
DEFAULT_PARSED_RESULT = {
    "user_skills": [],
    "experience": [],
    "education": [],
    "certifications": [],
    "jd_requirements": [],
    "jd_responsibilities": [],
    "missing_skills": [],
    "resume_match_score": 0.0
}

DEFAULT_QUESTIONS = [
    "Could you walk me through your background and key experience relevant to this role?",
    "Tell me about a challenging technical problem you solved. What was the impact?",
    "How do you approach learning a new technology or framework on the job?",
    "Describe a time you had to work with a difficult teammate. How did you handle it?",
    "Why are you interested in this position, and how do you see yourself contributing?"
]

DEFAULT_EVALUATION = {
    "score": 5,
    "feedback": "Unable to evaluate answer due to an API error.",
    "improvement_tip": "Please try submitting your answer again.",
    "strengths": ["Answer was submitted."],
    "weaknesses": ["Unable to analyze weaknesses."],
    "recommended_topic": "General"
}


def _generate_content(prompt: str, json_mode: bool = False) -> str:
    """
    Internal helper to generate LLM responses using Gemini.
    Resiliently supports both 'google-generativeai' and the newer 'google-genai' SDKs.
    """
    if not api_key:
        raise ValueError("Google API key is missing. Please set GOOGLE_API_KEY or GEMINI_API_KEY in the environment.")

    # Try legacy SDK first
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(PRIMARY_MODEL)
        generation_config = {}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"
        
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text
    except ImportError:
        # Fallback to the new SDK (google-genai)
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            config = {}
            if json_mode:
                config["response_mime_type"] = "application/json"
                
            response = client.models.generate_content(
                model=PRIMARY_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(**config) if config else None
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Gemini legacy generation failed: {e}")


def _clean_json_response(response_text: str) -> str:
    """
    Cleans markdown decorators (like ```json ... ```) from JSON responses if returned by LLM.
    """
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) > 2 and (lines[0].startswith("```json") or lines[0].startswith("```")):
            text = "\n".join(lines[1:-1]).strip()
    return text


def run_async(coro):
    """
    Helper to run asynchronous coroutines from synchronous code context.
    Specifically handles running inside environments like Streamlit that might
    already have an active event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


async def _async_retrieve_mcp_docs(topic: str) -> str:
    """
    Asynchronously queries the Google Developer Knowledge MCP server.
    """
    dk_api_key = os.getenv("DEVELOPER_KNOWLEDGE_API_KEY") or api_key
    if not dk_api_key:
        raise ValueError("No API key available for Developer Knowledge MCP connection.")
        
    mcp_url = "https://developerknowledge.googleapis.com/mcp"
    
    # Lazy-load mcp modules
    from mcp.client.streamable_http import streamable_http_client
    from mcp import ClientSession
    from httpx import AsyncClient
    
    headers = {"X-Goog-Api-Key": dk_api_key}
    async with AsyncClient(timeout=10.0, headers=headers) as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "search_documents",
                    {"query": topic}
                )
                
                output_texts = []
                if hasattr(result, "content") and result.content:
                    for block in result.content:
                        if hasattr(block, "text"):
                            output_texts.append(block.text)
                        elif isinstance(block, dict) and "text" in block:
                            output_texts.append(block["text"])
                        else:
                            output_texts.append(str(block))
                
                if output_texts:
                    return "\n\n".join(output_texts)
                else:
                    return f"No results returned from Developer Knowledge MCP for topic: '{topic}'."


# ==================== Core Exposed Functions ====================

def parse_documents(resume_text: str, jd_text: str) -> dict:
    """
    Use Gemini to parse both the resume and job description, and return
    a structured JSON analysis.
    
    Args:
        resume_text (str): Raw text of the candidate's resume.
        jd_text (str): Raw text of the job description.
        
    Returns:
        dict: Parsed profile information containing:
              - user_skills (list of str)
              - experience (list of str)
              - education (list of str)
              - certifications (list of str)
              - jd_requirements (list of str)
              - jd_responsibilities (list of str)
              - missing_skills (list of str)
              - resume_match_score (float/int, scale 0-100)
    """
    prompt = f"""
    You are an expert recruiter and CV parser assistant.
    Analyze the provided Resume and Job Description (JD) below.
    
    Resume Text:
    {resume_text}
    
    Job Description Text:
    {jd_text}
    
    Extract and calculate the following details in JSON format. The response must be a single, valid JSON object containing exactly these keys:
    - user_skills: A list of strings of the candidate's core technical and soft skills.
    - experience: A list of candidate's past work experience descriptions or titles.
    - education: A list of candidate's academic degrees or schools.
    - certifications: A list of candidate's certifications.
    - jd_requirements: A list of key required qualifications/skills from the job description.
    - jd_responsibilities: A list of key responsibilities from the job description.
    - missing_skills: A list of skills/requirements from the job description that are NOT present or implied in the candidate's resume.
    - resume_match_score: A floating-point number or integer from 0 to 100 indicating how well the candidate matches the job requirements.
    
    Provide ONLY the valid JSON object. No markdown wrappers or additional text outside the JSON.
    """
    try:
        response_text = _generate_content(prompt, json_mode=True)
        cleaned_json = _clean_json_response(response_text)
        parsed_result = json.loads(cleaned_json)
        
        # Merge missing keys with default keys
        for key, val in DEFAULT_PARSED_RESULT.items():
            if key not in parsed_result:
                parsed_result[key] = val
        return parsed_result
    except Exception as e:
        # Gracefully handle API errors or parse errors
        # In a real environment, logger.error(f"Error parsing documents: {e}")
        return DEFAULT_PARSED_RESULT


def generate_questions(profile: dict, jd_profile: dict, history: list) -> list:
    """
    Generate exactly 5 interview questions using Gemini based on the candidate's profile,
    job description requirements, and optional history (with past evaluations/scores).
    
    Args:
        profile (dict): The parsed candidate profile dictionary (from parse_documents).
        jd_profile (dict): The parsed job description requirements.
        history (list): List of previous question-answer logs or scores.
        
    Returns:
        list: A Python list of exactly 5 question strings.
    """
    prompt = f"""
    You are an expert technical interviewer.
    Generate exactly 5 high-quality, professional mock interview questions tailored for the candidate.
    
    Candidate Profile Details:
    {json.dumps(profile, indent=2)}
    
    Job Description Details:
    {json.dumps(jd_profile, indent=2)}
    
    Conversation/Evaluation History:
    {json.dumps(history, indent=2)}
    
    Requirements:
    - Return exactly 5 questions.
    - The questions must be a mix of:
      1. Technical questions (testing specific technical skills listed or missing).
      2. Behavioral questions (e.g., handling conflicts, leadership, soft skills).
      3. Scenario-based/situational questions (e.g., "How would you design X given constraints Y?").
    - If previous scores or question evaluations are present in the History, adapt the difficulty. For example:
      - If the candidate performed poorly on a topic, ask a simpler follow-up or test a different core skill.
      - If the candidate performed exceptionally, ask more challenging, senior-level questions.
    - Format output as a JSON array of 5 strings. Example format:
      ["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]
      
    Provide ONLY the valid JSON list. No markdown wrappers or additional text outside the JSON.
    """
    try:
        response_text = _generate_content(prompt, json_mode=True)
        cleaned_json = _clean_json_response(response_text)
        questions = json.loads(cleaned_json)
        
        if isinstance(questions, list) and len(questions) > 0:
            if len(questions) < 5:
                # Pad to 5 if model generated fewer
                questions.extend(DEFAULT_QUESTIONS[len(questions):])
            return [str(q) for q in questions[:5]]
        return DEFAULT_QUESTIONS
    except Exception as e:
        return DEFAULT_QUESTIONS


def evaluate_answer(question: str, answer: str, topic: str) -> dict:
    """
    Evaluate the candidate's answer to a specific question using Gemini.
    
    Args:
        question (str): The interview question asked.
        answer (str): The candidate's answer.
        topic (str): The general topic of the question (e.g., Python, Architecture, Soft Skills).
        
    Returns:
        dict: Evaluation results containing score, feedback, improvement tips, strengths,
              weaknesses, and recommended next topic.
    """
    prompt = f"""
    You are an expert interviewer and evaluator.
    Evaluate the candidate's answer to the interview question below.
    
    Question:
    {question}
    
    Candidate's Answer:
    {answer}
    
    Topic:
    {topic}
    
    Provide a structured, constructive evaluation in JSON format containing exactly the following keys:
    - score: An integer from 1 to 10 (where 10 is perfect and 1 is completely incorrect or empty).
    - feedback: A concise summary explaining the score and how well the candidate answered.
    - improvement_tip: Specific, actionable advice on how the candidate could improve their answer.
    - strengths: A list of strings highlighting the positive aspects of the answer.
    - weaknesses: A list of strings highlighting the gaps, errors, or missing points in the answer.
    - recommended_topic: A string suggesting the next topic or area the candidate should focus on based on their answer performance.
    
    Provide ONLY the valid JSON object. No markdown wrappers or additional text outside the JSON.
    """
    try:
        response_text = _generate_content(prompt, json_mode=True)
        cleaned_json = _clean_json_response(response_text)
        evaluation = json.loads(cleaned_json)
        
        # Merge missing keys with default keys
        for key, val in DEFAULT_EVALUATION.items():
            if key not in evaluation:
                evaluation[key] = val
        return evaluation
    except Exception as e:
        return DEFAULT_EVALUATION


def retrieve_mcp_docs(topic: str) -> str:
    """
    Attempt to retrieve official documentation using the Google Developer Knowledge MCP server.
    If the MCP server is unavailable or returns an error, gracefully fall back to a predefined 
    dictionary of cached documentation snippets.
    
    Args:
        topic (str): The technical topic or query to search for.
        
    Returns:
        str: Formatted documentation content.
    """
    try:
        result = run_async(_async_retrieve_mcp_docs(topic))
        return f"=== Developer Knowledge MCP Search Results for '{topic}' ===\n\n{result}"
    except Exception as e:
        # Format offline fallback output if MCP is unavailable
        topic_lower = topic.lower()
        matched_content = []
        for key, content in CACHED_MCP_DOCS.items():
            if key in topic_lower or topic_lower in key:
                matched_content.append(content)
                
        if matched_content:
            fallback_text = "\n\n".join(matched_content)
        else:
            fallback_text = (
                f"No local snippet available for '{topic}'.\n"
                f"Try searching standard topics: Streamlit, Gemini, ADK, MCP, Python, Pytest, Plotly."
            )
            
        return (
            f"=== Developer Knowledge MCP Offline (Fallback) ===\n"
            f"Note: Remote MCP server search for '{topic}' was unavailable ({e}).\n\n"
            f"{fallback_text}"
        )
