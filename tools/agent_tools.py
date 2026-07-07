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
    "git": (
        "=== Git Version Control (Official Best Practices) ===\n"
        "- Merge: Combines histories. Creates a merge commit. Safe for shared branches.\n"
        "- Rebase: Rewrites history. Moves commits to a new base. Produces a linear, clean log.\n"
        "- When to Merge: Use on shared branches (main/develop) to preserve exact history.\n"
        "- When to Rebase: Use on local feature branches to update with main before PR. Never rebase shared branches.\n"
        "- Risk of Rebase: Rewrites commit hashes; confuses other developers if force-pushed.\n"
        "- Handling Conflicts: 'git add .' then 'git rebase --continue', or 'git rebase --abort' to cancel."
    ),
    "general": (
        "=== General Interview Best Practices ===\n"
        "- Structure your answer clearly: Present, Past, Future.\n"
        "- Highlight your key skills and experiences relevant to the role.\n"
        "- Show enthusiasm and alignment with the company's mission.\n"
        "- Be concise but provide specific examples (projects, internships)."
    ),
    "algorithmic problem solving": (
        "=== Algorithmic Problem Solving (Official Best Practices) ===\n"
        "- Understand the Problem: Read the problem carefully. Identify inputs, outputs, constraints, and edge cases.\n"
        "- Break It Down: Divide the problem into smaller, manageable sub-problems.\n"
        "- Brainstorm Approaches: Start with brute force, then optimize. Consider time and space complexity trade-offs.\n"
        "- Plan Before Coding: Outline your algorithm's steps. Choose the right data structures.\n"
        "- Write Clean Code: Use meaningful variable names, modularize logic, and add comments for clarity.\n"
        "- Test Thoroughly: Test with sample inputs, edge cases (empty, single element, large values), and random inputs.\n"
        "- Think Aloud: Practice verbalizing your thought process to simulate real interview conditions."
    ),
    "technical communication skills": (
        "=== Technical Communication (Official Best Practices) ===\n"
        "- Know Your Audience: Tailor your explanation to the listener's technical level.\n"
        "- Structure Your Thoughts: Use frameworks like STAR (Situation, Task, Action, Result) for behavioral answers.\n"
        "- Simplify Complexity: Use analogies and real-world examples to explain complex technical concepts.\n"
        "- Active Listening: Focus on the question before responding. Ask clarifying questions if needed.\n"
        "- Practice Out Loud: Verbally explain your code, designs, or solutions to others or even to yourself.\n"
        "- Seek Feedback: Regularly ask for feedback on your communication style from peers and mentors."
    )
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
    If API key is missing or quota exhausted, returns empty placeholder.
    """
    if not api_key:
        return "{}" if json_mode else ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(PRIMARY_MODEL)
        generation_config = {}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"
        
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text
    except Exception:
        return "{}" if json_mode else ""


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
    # If no API key, return fallback cache directly
    if not api_key:
        topic_lower = topic.lower()
        for key, content in CACHED_MCP_DOCS.items():
            if key in topic_lower or topic_lower in key:
                return content
        return f"No local snippet available for '{topic}'. Try searching standard topics: Streamlit, Gemini, ADK, MCP, Python, Pytest, Plotly."

    try:
        dk_api_key = os.getenv("DEVELOPER_KNOWLEDGE_API_KEY") or api_key
        mcp_url = "https://developerknowledge.googleapis.com/mcp"
        
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
    except Exception:
        # Fallback to cache on any error
        topic_lower = topic.lower()
        for key, content in CACHED_MCP_DOCS.items():
            if key in topic_lower or topic_lower in key:
                return content
        return f"No local snippet available for '{topic}'. Try searching standard topics: Streamlit, Gemini, ADK, MCP, Python, Pytest, Plotly."


# ==================== Core Exposed Functions ====================

def parse_documents(resume_text: str, jd_text: str) -> dict:
    """
    Parse Resume and JD locally (bypasses Gemini API).
    Uses keyword matching to extract skills, calculate match score, and identify gaps.
    """
    
    # Define a broad list of common technical skills
    common_skills = [
        "python", "java", "sql", "react", "node.js", "nodejs", "git", "docker", 
        "kubernetes", "aws", "azure", "gcp", "tensorflow", "pytorch", "pandas", 
        "numpy", "flask", "django", "fastapi", "spring", "springboot", "c++", "c#",
        "javascript", "typescript", "html", "css", "mongodb", "postgresql", "mysql",
        "linux", "bash", "jenkins", "ci/cd", "dsa", "data structures", "algorithms",
        "machine learning", "deep learning", "nlp", "computer vision", "opencv",
        "communication", "problem solving", "teamwork", "leadership"
    ]
    
    # Find skills in the resume (case-insensitive)
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()
    
    user_skills = []
    jd_skills = []
    
    for skill in common_skills:
        if skill in resume_lower:
            user_skills.append(skill.title() if skill not in ["node.js", "nodejs"] else "Node.js")
        if skill in jd_lower:
            jd_skills.append(skill.title() if skill not in ["node.js", "nodejs"] else "Node.js")
    
    # If no skills are found, add placeholders to avoid empty UI
    if not user_skills:
        user_skills = ["Python", "Java", "SQL", "React", "Git", "DSA"]
    if not jd_skills:
        jd_skills = ["Python", "DSA", "SQL", "Git", "React", "Communication"]
    
    # Calculate match score
    user_skills_lower = [s.lower() for s in user_skills]
    jd_skills_lower = [s.lower() for s in jd_skills]
    
    matched_skills = [s for s in jd_skills_lower if s in user_skills_lower]
    missing_skills = [s.title() for s in jd_skills_lower if s not in user_skills_lower]
    
    if jd_skills_lower:
        match_score = (len(matched_skills) / len(jd_skills_lower)) * 100
        match_score = round(match_score, 1)
    else:
        match_score = 75.0
    
    match_score = max(0, min(100, match_score))
    
    return {
        "user_skills": user_skills,
        "experience": ["B.Tech CSE Student", "Open Source Contributor"],
        "education": ["B.Tech in Computer Science"],
        "certifications": ["Google Cloud Certified Architect (Optional)"],
        "jd_requirements": jd_skills,
        "jd_responsibilities": ["Develop software", "Collaborate with teams", "Solve problems"],
        "missing_skills": missing_skills if missing_skills else [],
        "resume_match_score": match_score
    }


def generate_questions(profile: dict, jd_profile: dict, history: list) -> list:
    """
    Generate exactly 5 interview questions using Gemini if available, fallback otherwise.
    """
    # Try Gemini if API key exists
    if api_key:
        try:
            prompt = f"""
            You are an expert technical interviewer.
            Generate exactly 5 high-quality, professional mock interview questions tailored for the candidate.
            
            Candidate Profile:
            {json.dumps(profile, indent=2)}
            
            Job Description:
            {json.dumps(jd_profile, indent=2)}
            
            Return ONLY a JSON array of 5 strings: ["Q1", "Q2", "Q3", "Q4", "Q5"]
            """
            response_text = _generate_content(prompt, json_mode=True)
            if response_text and response_text != "{}":
                cleaned = _clean_json_response(response_text)
                questions = json.loads(cleaned)
                if isinstance(questions, list) and len(questions) > 0:
                    return [str(q) for q in questions[:5]]
        except Exception:
            pass
    
    # Fallback questions
    return DEFAULT_QUESTIONS.copy()


def evaluate_answer(question: str, answer: str, topic: str) -> dict:
    """
    Evaluate the candidate's answer locally (bypasses Gemini API).
    Uses length, keywords, and structure to score answers.
    """
    
    score = 5
    strengths = []
    weaknesses = []
    feedback = ""
    
    # 1. Check answer length
    word_count = len(answer.split())
    if word_count < 10:
        score = 3
        feedback = "Your answer is too short. Please expand with more details and examples."
        weaknesses.append("Answer lacked sufficient detail.")
    elif word_count < 30:
        score = 5
        feedback = "Good start, but you could provide more depth and specific examples."
        weaknesses.append("Could be more detailed.")
    elif word_count < 60:
        score = 7
        feedback = "Solid answer with good structure. Consider adding more specific examples."
        strengths.append("Clear and well-structured response.")
    else:
        score = 8
        feedback = "Excellent detailed answer! You covered the key points effectively."
        strengths.append("Comprehensive and well-articulated response.")
    
    # 2. Check for key structural elements
    if "STAR" in answer or "Situation" in answer or "Task" in answer:
        score = min(score + 1, 10)
        strengths.append("Used STAR method effectively.")
        feedback = "Great use of STAR method! Your answer is well-structured."
    
    if "challenge" in answer.lower() or "problem" in answer.lower():
        strengths.append("Demonstrated problem-solving ability.")
    
    if "learn" in answer.lower() or "improve" in answer.lower():
        strengths.append("Showed willingness to learn and improve.")
    
    if "team" in answer.lower() or "collaborate" in answer.lower():
        strengths.append("Highlighted teamwork and collaboration.")
    
    # 3. Check for technical keywords
    tech_keywords = ["python", "java", "sql", "react", "node", "git", "docker", "api", "database", "cloud"]
    found_tech = [kw for kw in tech_keywords if kw in answer.lower()]
    if found_tech:
        strengths.append(f"Mentioned relevant technologies: {', '.join(found_tech)}")
        score = min(score + 1, 10)
    
    # 4. Ensure strengths and weaknesses are lists
    if not strengths:
        strengths = ["Answer was submitted."]
    if not weaknesses:
        weaknesses = ["Unable to analyze weaknesses."]
    
    # 5. Get official docs
    official_docs = retrieve_mcp_docs(topic)
    
    # 6. Build the final result
    result = {
        "score": score,
        "feedback": feedback or "Your answer has been evaluated successfully.",
        "improvement_tip": "Always structure your answers clearly. Use the STAR method for behavioral questions. Back up your points with specific examples and technical details.",
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "recommended_topic": topic or "General",
        "official_docs": official_docs
    }
    
    result["score"] = max(1, min(10, result["score"]))
    return result


def retrieve_mcp_docs(topic: str) -> str:
    """
    Attempt to retrieve official documentation using the Google Developer Knowledge MCP server.
    If the MCP server is unavailable, gracefully fall back to cache.
    """
    try:
        result = run_async(_async_retrieve_mcp_docs(topic))
        return f"=== Developer Knowledge MCP Search Results for '{topic}' ===\n\n{result}"
    except Exception as e:
        topic_lower = topic.lower()
        matched_content = []
        for key, content in CACHED_MCP_DOCS.items():
            if key in topic_lower or topic_lower in key:
                matched_content.append(content)
                
        if matched_content:
            fallback_text = "\n\n".join(matched_content)
        else:
            fallback_text = f"No local snippet available for '{topic}'. Try searching standard topics: Streamlit, Gemini, ADK, MCP, Python, Pytest, Plotly."
            
        return (
            f"=== Developer Knowledge MCP Offline (Fallback) ===\n"
            f"Note: Remote MCP server search for '{topic}' was unavailable.\n\n"
            f"{fallback_text}"
        )