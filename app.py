"""
app.py

Main entry point for the InterviewIQ AI Streamlit application.
Orchestrates page routing (Home, Interview Booth, Dashboard, Learning Plan)
and interfaces with the underlying Parser, Interviewer, and Evaluator agents.
"""

import json
import streamlit as st
import pandas as pd
import plotly.express as px

# Import specialized agents
from agents.parser import ResumeParserAgent
from agents.interviewer import InterviewerAgent
from agents.evaluator import EvaluatorAgent
from tools.agent_tools import retrieve_mcp_docs

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="InterviewIQ AI - Premium Mock Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply high-end modern styling for visual excellence and responsive layout
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');

/* Base Container Styling */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: radial-gradient(circle at top left, #0e111d 0%, #07090e 100%) !important;
    color: #e2e8f0;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    letter-spacing: -0.02em;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #080a10 !important;
    border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
}

/* Premium Sidebar Option list as list item buttons */
div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}
div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] > label {
    background-color: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding: 0.8rem 1.1rem !important;
    border-radius: 12px !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
}
div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] > label:hover {
    background-color: rgba(99, 102, 241, 0.08) !important;
    border-color: rgba(99, 102, 241, 0.3) !important;
    color: #ffffff !important;
}
div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%) !important;
    border-color: #6366f1 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25) !important;
}
/* Hide default radio buttons in sidebar */
div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

/* Glassmorphism Action Cards */
.glass-card {
    background: rgba(13, 17, 28, 0.65);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 16px;
    padding: 1.8rem;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 1.5rem;
}
.glass-card:hover {
    transform: translateY(-3px);
    border-color: rgba(139, 92, 246, 0.4);
    box-shadow: 0 18px 45px rgba(99, 102, 241, 0.18);
}

/* Premium Metrics Grid container */
.metric-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2.5rem;
}
.premium-metric {
    background: linear-gradient(135deg, rgba(20, 26, 45, 0.7) 0%, rgba(42, 17, 66, 0.7) 100%);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 18px;
    padding: 1.6rem;
    text-align: center;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.premium-metric:hover {
    transform: translateY(-4px);
    border-color: rgba(139, 92, 246, 0.55);
    box-shadow: 0 12px 35px rgba(139, 92, 246, 0.15);
}
.metric-icon {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: rgba(139, 92, 246, 0.15);
    color: #a78bfa;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    margin-bottom: 0.8rem;
    border: 1px solid rgba(139, 92, 246, 0.3);
}
.metric-lbl {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.metric-val {
    font-size: 2.3rem;
    font-weight: 800;
    color: #ffffff;
    background: linear-gradient(120deg, #a78bfa, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Custom Skill Pill Badges */
.skill-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    margin: 0.3rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    transition: all 0.2s ease;
}
.skill-badge:hover {
    transform: scale(1.05);
}
.badge-user {
    background-color: rgba(16, 185, 129, 0.08);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.badge-missing {
    background-color: rgba(239, 68, 68, 0.08);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}
.badge-required {
    background-color: rgba(59, 130, 246, 0.08);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

/* Custom Input text areas */
.stTextArea textarea {
    background-color: rgba(10, 15, 30, 0.6) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    color: #e2e8f0 !important;
    border-radius: 14px !important;
    padding: 1.2rem !important;
    font-size: 0.95rem !important;
    transition: all 0.25s ease !important;
    line-height: 1.6 !important;
}
.stTextArea textarea:focus {
    border-color: rgba(99, 102, 241, 0.55) !important;
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.25) !important;
}

/* Custom buttons styling */
.stButton button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.02em !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
}
.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.55) !important;
}
.stButton button:active {
    transform: translateY(0) !important;
}

/* Clean progress bars */
.stProgress > div > div > div > div {
    background-color: #6366f1 !important;
}

/* Smooth Alert Banner */
.custom-alert {
    padding: 1.25rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.95rem;
    font-weight: 500;
}
.alert-success {
    background-color: rgba(16, 185, 129, 0.08);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.25);
}
.alert-warning {
    background-color: rgba(245, 158, 11, 0.08);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.25);
}
.alert-error {
    background-color: rgba(239, 68, 68, 0.08);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.25);
}
</style>
""", unsafe_allow_html=True)


# ==================== Session State Management ====================
def init_session():
    """Initializes all state parameters needed for persistent memory."""
    if "resume" not in st.session_state:
        st.session_state.resume = ""
    if "jd" not in st.session_state:
        st.session_state.jd = ""
    if "parsed_profile" not in st.session_state:
        st.session_state.parsed_profile = None
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "answers" not in st.session_state:
        st.session_state.answers = []
    if "scores" not in st.session_state:
        st.session_state.scores = []
    if "feedback" not in st.session_state:
        st.session_state.feedback = []
    if "strong_areas" not in st.session_state:
        st.session_state.strong_areas = []
    if "weak_areas" not in st.session_state:
        st.session_state.weak_areas = []
    if "current_question_idx" not in st.session_state:
        st.session_state.current_question_idx = 0
    if "resume_match_score" not in st.session_state:
        st.session_state.resume_match_score = 0.0
    if "interview_completed" not in st.session_state:
        st.session_state.interview_completed = False
    if "learning_plan" not in st.session_state:
        st.session_state.learning_plan = []
    if "submitted_current" not in st.session_state:
        st.session_state.submitted_current = False
    if "current_streak" not in st.session_state:
        st.session_state.current_streak = 0
    if "current_page" not in st.session_state:
        st.session_state.current_page = "🏠 Home"

init_session()

# Sidebar Title Branding
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 1.5rem;">
    <h2 style="color: #818cf8; margin: 0; font-family: 'Outfit', sans-serif; font-size: 1.6rem; letter-spacing: -0.02em;">InterviewIQ AI</h2>
    <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.2rem;">Premium Mock Prep</p>
</div>
""", unsafe_allow_html=True)

page_options = ["🏠 Home", "🎤 Interview Booth", "📊 Dashboard", "📚 Learning Plan"]
selected_page = st.sidebar.radio(
    "Navigation Options",
    page_options,
    index=page_options.index(st.session_state.current_page),
    label_visibility="collapsed"
)

if selected_page != st.session_state.current_page:
    st.session_state.current_page = selected_page
    st.rerun()


# Helper to generate AI roadmap items
def generate_learning_plan_with_gemini(weak_topics):
    """Uses Gemini via helper tools to create a personalized study syllabus."""
    if not weak_topics:
        weak_topics = ["Advanced Python & System Design"]

    prompt = f"""
    You are an expert technical mentor.

    Create a personalized learning plan for a candidate wanting to improve on the following weak areas:

    {", ".join(weak_topics)}

    Return ONLY valid JSON.

    The response must be a JSON array.

    Each object must contain exactly these fields:

    - topic
    - why_it_matters
    - learning_path

    Rules:
    - Return plain text only.
    - Do NOT generate HTML.
    - Do NOT generate Markdown.
    - Do NOT include <div>, <p>, <h1>, <style>, <span>, or any HTML tags.
    - Do NOT include inline CSS.
    - The values must be human-readable text.

    Example:

    [
      {{
        "topic": "Python",
        "why_it_matters": "Python is essential for backend development, automation, AI, and technical interviews.",
        "learning_path": "1. Learn Python syntax\\n2. Practice functions and OOP\\n3. Solve DSA problems\\n4. Build projects"
      }}
    ]
    """
    try:
        from tools.agent_tools import _generate_content, _clean_json_response
        response_text = _generate_content(prompt, json_mode=True)
        cleaned = _clean_json_response(response_text)

        import re

        plan = json.loads(cleaned)

        for item in plan:
            if "why_it_matters" in item:
                item["why_it_matters"] = re.sub(r"<[^>]+>", "", item["why_it_matters"])

            if "learning_path" in item:
                item["learning_path"] = re.sub(r"<[^>]+>", "", item["learning_path"])

        return plan
    except Exception:
        fallback = []
        for topic in weak_topics:
            fallback.append({
                "topic": topic,
                "why_it_matters": f"Mastery of {topic} is critical to developing scalable, high-performance developer systems.",
                "learning_path": "1. Review official developer documentation.\n2. Work on small, targeted prototype projects.\n3. Take courses or read articles highlighting best practices."
            })
        return fallback


# ==================== PAGE 1: HOME PAGE ====================
if st.session_state.current_page == "🏠 Home":
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 2.5rem; border-radius: 20px; margin-bottom: 2.5rem; text-align: center; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.25);">
        <h1 style="color: white; margin: 0; font-size: 2.8rem; letter-spacing: -0.03em;">🎯 InterviewIQ AI</h1>
        <p style="color: #e2e8f0; margin: 0.6rem 0 0 0; font-size: 1.15rem; font-weight: 400;">Professional mock interview simulator built on Google Agent Development Kit (ADK) and Developer Knowledge MCP.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.4rem;">📄</span>
            <h3 style="margin: 0; font-size: 1.25rem;">Candidate Resume</h3>
        </div>
        """, unsafe_allow_html=True)
        resume_input = st.text_area(
            "Candidate Resume:",
            value=st.session_state.resume,
            height=280,
            placeholder="Paste raw Resume text details here (e.g., Tech stack, roles, credentials)...",
            label_visibility="collapsed"
        )
        st.session_state.resume = resume_input

    with col2:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.4rem;">📋</span>
            <h3 style="margin: 0; font-size: 1.25rem;">Target Job Description</h3>
        </div>
        """, unsafe_allow_html=True)
        jd_input = st.text_area(
            "Job Description:",
            value=st.session_state.jd,
            height=280,
            placeholder="Paste requirements, expectations, and role description here...",
            label_visibility="collapsed"
        )
        st.session_state.jd = jd_input

    # Parse and analysis actions
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Run Resume Analysis", use_container_width=True):
        if not resume_input.strip() or not jd_input.strip():
            st.markdown("""
            <div class="custom-alert alert-error">
                <span>⚠️</span> Incomplete input data. Please paste both Resume and Job Description content to analyze.
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.spinner("🤖 Evaluating match index. Reviewing skills, background, and alignment metrics..."):
                parser = ResumeParserAgent()
                parsed = parser.parse(resume_input, jd_input)
                
                st.session_state.parsed_profile = parsed
                st.session_state.resume_match_score = parsed.get("resume_match_score", 0.0)
                st.markdown("""
                <div class="custom-alert alert-success">
                    <span>🎉</span> Analysis complete! Candidate match profile successfully mapped below.
                </div>
                """, unsafe_allow_html=True)

    # Display results when parsed profile is in session state
    if st.session_state.parsed_profile:
        st.markdown("---")
        st.markdown("### 📊 Skill Fit Mapping Analysis")
        
        # Display match rating inside styled metric layout
        match_val = st.session_state.resume_match_score
        m_col1, m_col2 = st.columns([1, 3])
        with m_col1:
            st.markdown(f"""
            <div class="premium-metric" style="padding: 1.25rem;">
                <div class="metric-icon" style="margin-bottom: 0.5rem; width: 38px; height: 38px; font-size: 1.1rem;">🎯</div>
                <div class="metric-lbl">Target Match</div>
                <div class="metric-val" style="font-size: 1.9rem; background: none; -webkit-text-fill-color: initial; color: #ffffff;">{match_val}%</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.progress(match_val / 100.0)
            
        # Display extracted skill matches
        col_skills1, col_skills2, col_skills3 = st.columns(3)
        
        with col_skills1:
            st.markdown(f"""
            <div class="glass-card" style="min-height: 250px;">
                <h4 style="color: #34d399; margin-top: 0; display: flex; align-items: center; gap: 0.4rem;">
                    <span>✅</span> User Skills
                </h4>
                <hr style="border-color: rgba(99, 102, 241, 0.1); margin-top: 0.5rem; margin-bottom: 0.75rem;">
            """, unsafe_allow_html=True)
            user_skills = st.session_state.parsed_profile.get("user_skills", [])
            if user_skills:
                pills = "".join([f'<span class="skill-badge badge-user">{s}</span>' for s in user_skills])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.info("No matching candidate skills detected.")
            st.markdown("</div>", unsafe_allow_html=True)
                
        with col_skills2:
            st.markdown(f"""
            <div class="glass-card" style="min-height: 250px;">
                <h4 style="color: #f87171; margin-top: 0; display: flex; align-items: center; gap: 0.4rem;">
                    <span>❌</span> Missing Skills
                </h4>
                <hr style="border-color: rgba(99, 102, 241, 0.1); margin-top: 0.5rem; margin-bottom: 0.75rem;">
            """, unsafe_allow_html=True)
            missing_skills = st.session_state.parsed_profile.get("missing_skills", [])
            if missing_skills:
                pills = "".join([f'<span class="skill-badge badge-missing">{m}</span>' for m in missing_skills])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.success("Candidate matches all core requirements!")
            st.markdown("</div>", unsafe_allow_html=True)
                
        with col_skills3:
            st.markdown(f"""
            <div class="glass-card" style="min-height: 250px;">
                <h4 style="color: #60a5fa; margin-top: 0; display: flex; align-items: center; gap: 0.4rem;">
                    <span>📋</span> Required Skills
                </h4>
                <hr style="border-color: rgba(99, 102, 241, 0.1); margin-top: 0.5rem; margin-bottom: 0.75rem;">
            """, unsafe_allow_html=True)
            req_skills = st.session_state.parsed_profile.get("jd_requirements", [])
            if req_skills:
                pills = "".join([f'<span class="skill-badge badge-required">{r}</span>' for r in req_skills])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.info("No explicit requirements found.")
            st.markdown("</div>", unsafe_allow_html=True)

        # Trigger interview queue
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Proceed to Interview Booth", use_container_width=True):
            with st.spinner("🤖 Formulating targeted interview questions based on candidate profile gaps..."):
                interviewer = InterviewerAgent()
                profile = {
                    "user_skills": st.session_state.parsed_profile.get("user_skills", []),
                    "experience": st.session_state.parsed_profile.get("experience", []),
                    "education": st.session_state.parsed_profile.get("education", []),
                    "certifications": st.session_state.parsed_profile.get("certifications", [])
                }
                jd_profile = {
                    "jd_requirements": st.session_state.parsed_profile.get("jd_requirements", []),
                    "jd_responsibilities": st.session_state.parsed_profile.get("jd_responsibilities", [])
                }
                
                questions = interviewer.generate_interview_questions(profile, jd_profile, [])
                st.session_state.questions = questions
                
                # Reset state registers
                st.session_state.answers = []
                st.session_state.scores = []
                st.session_state.feedback = []
                st.session_state.strong_areas = []
                st.session_state.weak_areas = []
                st.session_state.current_question_idx = 0
                st.session_state.submitted_current = False
                st.session_state.interview_completed = False
                st.session_state.learning_plan = []
                
                st.session_state.current_page = "🎤 Interview Booth"
                st.rerun()


# ==================== PAGE 2: INTERVIEW BOOTH ====================
elif st.session_state.current_page == "🎤 Interview Booth":
    st.header("🎤 Interview Booth")
    
    if not st.session_state.questions:
        st.markdown("""
        <div class="custom-alert alert-warning">
            <span>⚠️</span> Mock questions are not loaded. Please set candidate details and trigger 'Proceed to Interview Booth' from the Home screen.
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Home Page"):
            st.session_state.current_page = "🏠 Home"
            st.rerun()
            
    elif st.session_state.interview_completed:
        st.markdown("""
        <div class="glass-card" style="text-align: center; border-left: 6px solid #10b981; padding: 2.2rem;">
            <h3 style="color: #34d399; margin: 0 0 1rem 0;">🎉 Mock Interview Successfully Completed!</h3>
            <p style="font-size: 1.05rem; color: #cbd5e1; margin-bottom: 1.5rem;">All response transcripts have been parsed and evaluated. Inspect metrics dashboard below.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📊 View Performance Dashboard", use_container_width=True):
            st.session_state.current_page = "📊 Dashboard"
            st.rerun()
            
    else:
        idx = st.session_state.current_question_idx
        question = st.session_state.questions[idx]
        
        # Display progress info
        st.markdown(f"#### **Question {idx + 1} of 5**")
        st.progress((idx + 1) / 5.0)
        
        # Premium Styled Question Box
        st.markdown(f"""
        <div class="glass-card" style="border-left: 6px solid #6366f1; background: rgba(30, 27, 75, 0.45);">
            <div style="font-size: 0.8rem; color: #a5b4fc; font-weight: 700; text-transform: uppercase; margin-bottom: 0.6rem; letter-spacing: 0.05em;">
                🤖 Active Prompt Question
            </div>
            <div style="font-size: 1.25rem; font-weight: 600; color: #ffffff; line-height: 1.6; font-family: 'Space Grotesk', sans-serif;">
                {question}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Answer text area
        ans_key = f"answer_box_{idx}"
        answer_text = st.text_area(
            "Your Answer:",
            key=ans_key,
            height=200,
            placeholder="Type your structured answer here (include code blocks, system designs, or workflows to get a higher score)...",
            label_visibility="collapsed"
        )
        
        # Action Buttons
        if not st.session_state.submitted_current:
            if st.button("Submit Answer", use_container_width=True):
                if not answer_text.strip():
                    st.markdown("""
                    <div class="custom-alert alert-error">
                        <span>⚠️</span> Invalid submission. Answer text box cannot be empty.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    with st.spinner("🤖 Evaluating response. Verifying correctness and querying MCP developer docs..."):
                        q_lower = question.lower()
                        topic = "General"
                        for kw in ["streamlit", "gemini", "adk", "mcp", "python", "pytest", "plotly", "git", "sql"]:
                            if kw in q_lower:
                                topic = kw.capitalize()
                                break
                                
                        evaluator = EvaluatorAgent()
                        evaluation = evaluator.evaluate(question, answer_text, topic)
                        
                        st.session_state.scores.append(evaluation.get("score", 5))
                        st.session_state.feedback.append(evaluation)
                        st.session_state.answers.append(answer_text)
                        
                        # Dynamically map strengths and weaknesses based on feedback score
                        rec_topic = evaluation.get("recommended_topic", topic)
                        score_val = evaluation.get("score", 5)
                        if score_val >= 7:
                            if rec_topic not in st.session_state.strong_areas:
                                st.session_state.strong_areas.append(rec_topic)
                        else:
                            if rec_topic not in st.session_state.weak_areas:
                                st.session_state.weak_areas.append(rec_topic)
                                
                        st.session_state.submitted_current = True
                        st.rerun()
                        
        else:
            # Answer submitted -> show evaluation feedback
            current_eval = st.session_state.feedback[-1]
            score_val = current_eval.get("score", 5)
            
            # Highlight evaluation metrics in custom layout
            col_score, col_details = st.columns([1, 3])
            with col_score:
                st.markdown(f"""
                <div class="premium-metric" style="border-color: #10b981; background: linear-gradient(135deg, rgba(6, 78, 59, 0.3) 0%, rgba(20, 24, 45, 0.6) 100%); min-height: 140px; justify-content: center;">
                    <div class="metric-lbl" style="color: #34d399;">Score</div>
                    <div class="metric-val" style="background: none; -webkit-text-fill-color: initial; color: #10b981; font-size: 2.5rem;">{score_val}/10</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_details:
                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid #3b82f6; min-height: 140px; margin-bottom: 0;">
                    <div style="font-size: 0.80rem; color: #60a5fa; font-weight: 700; text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.05em;">📝 Feedback Summary</div>
                    <p style="margin: 0; font-size: 0.95rem; line-height: 1.5; color: #cbd5e1;">{current_eval.get('feedback', '')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid #f59e0b; background: rgba(245, 158, 11, 0.03); margin-top: 1.25rem;">
                <div style="font-size: 0.80rem; color: #fbbf24; font-weight: 700; text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.05em;">💡 Improvement Tip</div>
                <p style="margin: 0; font-size: 0.95rem; line-height: 1.5; color: #fef08a;">{current_eval.get('improvement_tip', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Detailed visual expansion blocks
            col_st, col_wk = st.columns(2)
            with col_st:
                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid #10b981; height: 100%; min-height: 200px;">
                    <h4 style="color: #34d399; margin-top: 0; display: flex; align-items: center; gap: 0.4rem;">
                        <span>💪</span> Strengths
                    </h4>
                    <hr style="border-color: rgba(16, 185, 129, 0.1); margin-top: 0.5rem; margin-bottom: 0.75rem;">
                """, unsafe_allow_html=True)
                strengths = current_eval.get("strengths", [])
                for s in strengths:
                    st.markdown(f"<div style='margin-bottom: 0.45rem; font-size: 0.9rem; color: #cbd5e1;'>✔ {s}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_wk:
                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid #f87171; height: 100%; min-height: 200px;">
                    <h4 style="color: #f87171; margin-top: 0; display: flex; align-items: center; gap: 0.4rem;">
                        <span>⚠️</span> Gaps / Weaknesses
                    </h4>
                    <hr style="border-color: rgba(239, 68, 68, 0.1); margin-top: 0.5rem; margin-bottom: 0.75rem;">
                """, unsafe_allow_html=True)
                weaknesses = current_eval.get("weaknesses", [])
                for w in weaknesses:
                    st.markdown(f"<div style='margin-bottom: 0.45rem; font-size: 0.9rem; color: #cbd5e1;'>• {w}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                        
            # MCP Docs Reference Expander
            with st.expander("📖 Developer Knowledge Reference Docs Context", expanded=False):
                st.code(current_eval.get("official_docs", "No documentation references pulled."), language="markdown")
            
            st.markdown("<br>", unsafe_allow_html=True)
            # Progression button
            if idx < 4:
                if st.button("Next Question ➡️", use_container_width=True):
                    st.session_state.current_question_idx += 1
                    st.session_state.submitted_current = False
                    st.rerun()
            else:
                if st.button("Complete Interview 🏁", use_container_width=True):
                    st.session_state.interview_completed = True
                    
                    # Compute streak (consecutive scores >= 7)
                    max_streak = 0
                    consec = 0
                    for s in st.session_state.scores:
                        if s >= 7:
                            consec += 1
                            if consec > max_streak:
                                max_streak = consec
                        else:
                            consec = 0
                    st.session_state.current_streak = max_streak
                    
                    st.session_state.current_page = "📊 Dashboard"
                    st.rerun()


# ==================== PAGE 3: DASHBOARD ====================
elif st.session_state.current_page == "📊 Dashboard":
    st.header("📊 Performance Dashboard")
    
    if not st.session_state.interview_completed:
        st.markdown("""
        <div class="custom-alert alert-warning">
            <span>⚠️</span> Access Denied. Dashboard telemetry is compiled after the mock interview has been fully completed.
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Interview Booth"):
            st.session_state.current_page = "🎤 Interview Booth"
            st.rerun()
    else:
        avg_score = sum(st.session_state.scores) / len(st.session_state.scores)
        high_score = max(st.session_state.scores)
        match_pct = st.session_state.resume_match_score
        streak = st.session_state.current_streak
        
        # Metric dashboard row
        st.markdown(f"""
        <div class="metric-container">
            <div class="premium-metric">
                <div class="metric-icon">📊</div>
                <div class="metric-lbl">Average Score</div>
                <div class="metric-val">{avg_score:.1f}/10</div>
            </div>
            <div class="premium-metric">
                <div class="metric-icon">🏆</div>
                <div class="metric-lbl">Highest Score</div>
                <div class="metric-val">{high_score}/10</div>
            </div>
            <div class="premium-metric">
                <div class="metric-icon">🎯</div>
                <div class="metric-lbl">Resume Match</div>
                <div class="metric-val">{match_pct}%</div>
            </div>
            <div class="premium-metric">
                <div class="metric-icon">🔥</div>
                <div class="metric-lbl">Current Streak</div>
                <div class="metric-val">{streak}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
            
        # Side-by-side Skills Assessment
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f"""
            <div class="glass-card" style="min-height: 200px;">
                <h4 style="color: #34d399; margin-top: 0; display: flex; align-items: center; gap: 0.4rem;">
                    <span>✅</span> Strengths & Mastery
                </h4>
                <hr style="border-color: rgba(99, 102, 241, 0.1); margin-top: 0.5rem; margin-bottom: 0.75rem;">
            """, unsafe_allow_html=True)
            if st.session_state.strong_areas:
                pills = "".join([f'<span class="skill-badge badge-user">{strong}</span>' for strong in st.session_state.strong_areas])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.info("No strong topics identified.")
            st.markdown("</div>", unsafe_allow_html=True)
                
        with col_right:
            st.markdown(f"""
            <div class="glass-card" style="min-height: 200px;">
                <h4 style="color: #f87171; margin-top: 0; display: flex; align-items: center; gap: 0.4rem;">
                    <span>❌</span> Gaps & Weaknesses
                </h4>
                <hr style="border-color: rgba(99, 102, 241, 0.1); margin-top: 0.5rem; margin-bottom: 0.75rem;">
            """, unsafe_allow_html=True)
            if st.session_state.weak_areas:
                pills = "".join([f'<span class="skill-badge badge-missing">{weak}</span>' for weak in st.session_state.weak_areas])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.success("No weak areas identified! Outstanding answer record.")
            st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown("---")
        
        # Score progress Plotly chart in a glass card
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        df_chart = pd.DataFrame({
            "Question": [f"Q{i+1}" for i in range(5)],
            "Score": st.session_state.scores
        })
        fig = px.line(
            df_chart, 
            x="Question", 
            y="Score", 
            markers=True, 
            title="Question-by-Question Score Track",
            range_y=[0, 11]
        )
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Plus Jakarta Sans"),
            title_font=dict(color="#ffffff", family="Outfit", size=18),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        fig.update_traces(
            line=dict(color="#818cf8", width=4),
            marker=dict(color="#a78bfa", size=10, line=dict(color="#ffffff", width=2))
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Interview Summary List Table
        st.subheader("📋 Response Transcript & Evaluator Reports")
        summary_rows = []
        for i in range(5):
            summary_rows.append({
                "Question No": f"Q{i+1}",
                "Question": st.session_state.questions[i],
                "Candidate Response": st.session_state.answers[i],
                "Score Value": f"{st.session_state.scores[i]}/10",
                "Assigned Feedback": st.session_state.feedback[i].get("feedback", "")
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
        
        # Export/Download results button
                # Export/Download results button - Readable Markdown Report
        st.markdown("---")
        
        # Generate readable Markdown report
        report_lines = []
        report_lines.append("# 🎯 InterviewIQ AI - Interview Report\n\n")
        report_lines.append(f"**Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        report_lines.append("## 📊 Summary Metrics\n\n")
        report_lines.append(f"- **Resume Match Score**: {match_pct}%\n")
        report_lines.append(f"- **Overall Average Score**: {avg_score:.1f}/10\n")
        report_lines.append(f"- **Highest Score**: {high_score}/10\n")
        report_lines.append(f"- **Current Streak**: {streak}\n\n")
        report_lines.append("## 📝 Full Interview Transcript\n\n")
        
        for i, row in enumerate(summary_rows):
            report_lines.append(f"### Question {i+1}: {row['Question']}\n\n")
            report_lines.append(f"**Your Answer**: {row['Candidate Response']}\n\n")
            report_lines.append(f"**Score**: {row['Score Value']}\n\n")
            report_lines.append(f"**Feedback**: {row['Assigned Feedback']}\n\n")
            report_lines.append("---\n\n")
        
        report_lines.append("## 💪 Identified Strengths\n\n")
        if st.session_state.strong_areas:
            for s in st.session_state.strong_areas:
                report_lines.append(f"- {s}\n")
        else:
            report_lines.append("_No specific strengths identified._\n")
        
        report_lines.append("\n## ❌ Identified Weaknesses / Gaps\n\n")
        if st.session_state.weak_areas:
            for w in st.session_state.weak_areas:
                report_lines.append(f"- {w}\n")
        else:
            report_lines.append("_No major weaknesses identified._\n")
        
        report_lines.append("\n---\n")
        report_lines.append("_Report generated by InterviewIQ AI - Powered by Google ADK & Gemini_")
        
        readable_report = "".join(report_lines)
        
        st.download_button(
            label="📥 Download Full Interview Report (Markdown)",
            data=readable_report,
            file_name="interviewiq_ai_report.md",
            mime="text/markdown",
            use_container_width=True
        )


# ==================== PAGE 4: LEARNING PLAN ====================
elif st.session_state.current_page == "📚 Learning Plan":
    st.header("📚 Personalized Learning Syllabus")
    
    if not st.session_state.interview_completed:
        st.markdown("""
        <div class="custom-alert alert-warning">
            <span>⚠️</span> Access Denied. Custom learning path syllabus is constructed after your interview responses have been analyzed.
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Interview Booth"):
            st.session_state.current_page = "🎤 Interview Booth"
            st.rerun()
    else:
        # Determine weak subjects
        weak_topics = st.session_state.weak_areas
        if not weak_topics:
            # Fallback topics if candidate score is high
            missing = st.session_state.parsed_profile.get("missing_skills", []) if st.session_state.parsed_profile else []
            weak_topics = missing[:3]
            if not weak_topics:
                weak_topics = ["Advanced Streamlit Integration", "Google ADK Framework", "Python Async Pipelines"]
                
        # Generate learning plan once if empty
        if not st.session_state.learning_plan:
            with st.spinner("🤖 Assembling custom roadmap & syllabus using evaluation feedback..."):
                st.session_state.learning_plan = generate_learning_plan_with_gemini(weak_topics)
                
        st.markdown("""
        <div class="custom-alert alert-success">
            <span>✨</span> Custom Study Roadmaps and developer tutorials successfully generated!
        </div>
        """, unsafe_allow_html=True)
        
        for item in st.session_state.learning_plan:
            topic_title = item.get("topic", "N/A")
            
            # Glass Card wrapper for syllabus topics
            st.html(f"""
            <div class="glass-card" style="border-left: 6px solid #8b5cf6;">
                <div style="font-size: 0.75rem; color: #a78bfa; font-weight: 700; text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.08em;">
                    Syllabus Target Topic
                </div>
                <h3 style="color: #ffffff; margin: 0 0 1rem 0; font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem;">{topic_title}</h3>
    
                <div style="margin-bottom: 1.2rem;">
                    <h5 style="color: #c084fc; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.3rem; font-family: 'Outfit';">
                        <span>💡</span> Why it matters
                    </h5>
                    <p style="color: #cbd5e1; margin: 0; font-size: 0.95rem; line-height: 1.5;">{item.get("why_it_matters", "")}</p>
                </div>
    
                <div style="margin-bottom: 1.2rem;">
                    <h5 style="color: #c084fc; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.3rem; font-family: 'Outfit';">
                        <span>📋</span> Study Pathway & Checklist
                    </h5>
                    <p style="color: #cbd5e1; margin: 0; font-size: 0.95rem; line-height: 1.5; white-space: pre-line;">{item.get("learning_path", "")}</p>
                </div>
            </div>
            """)

            # Fetch MCP Docs dynamically
            with st.spinner(f"Querying Google Developer Knowledge MCP for '{topic_title}' docs..."):
                try:
                    docs_content = retrieve_mcp_docs(topic_title)
                except Exception:
                    docs_content = "Failed to pull remote docs reference."
                    
            with st.expander(f"📖 View Official {topic_title} Documentation", expanded=False):
                st.code(docs_content, language="markdown")
            st.markdown("<br>", unsafe_allow_html=True)
