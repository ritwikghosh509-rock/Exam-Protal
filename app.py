import streamlit as st
import os
import re
from collections import Counter

# Try importing pypdf for direct PDF reading
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Page Configuration
st.set_page_config(page_title="History Exam Portal", layout="wide")

# Gradient Background and Transparent Login Box
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
    }
    .main-header {
        font-size: 40px;
        font-weight: bold;
        color: #333;
        text-align: center;
        margin-bottom: 20px;
    }
    .login-box {
        background: transparent; 
        padding: 30px;
        max-width: 400px;
        margin: auto;
    }
    .analysis-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# User Credentials & File Mappings
CREDENTIALS = {
    "Rajat": "Rajat4",
    "Manab": "Manab6",
    "Subho": "Subho1"
}

# Mapping for Basic Test PDFs
PDF_MAPPING_BASIC = {
    "Rajat": ["ancient_history_set_1.pdf"],
    "Manab": ["ancient_history_set_2.pdf"],
    "Subho": ["ancient_history_set_3.pdf"]
}

# Mapping for Advanced Test PDFs
PDF_MAPPING_ADVANCED = {
    "Rajat": ["Ancient_Indian_History_Set_1.pdf"],
    "Manab": ["Ancient_Indian_History_Set_2.pdf"],
    "Subho": ["Ancient_Indian_History_Set_3.pdf"]
}

# ----------------- IMPROVED PDF PARSER FUNCTION -----------------
@st.cache_data
def extract_questions_from_pdf(filepath):
    """Parses questions, options, correct answers, explanations, and TOPICS."""
    if not PYPDF_AVAILABLE or not os.path.exists(filepath):
        return []
    
    try:
        reader = PdfReader(filepath)
        full_text = "\n" + "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        
        split_pattern = r'(?i)\n\s*(?:Question\s+\d+[\s\-\:]*|\d+\.\s+)'
        raw_blocks = re.split(split_pattern, full_text)[1:]

        parsed_questions = []

        for block in raw_blocks:
            exp_parts = re.split(r'(?i)\n?\s*(?:Detailed\s+)?Explanation:', block)
            content = exp_parts[0]
            explanation = exp_parts[1].strip().replace('\n', ' ') if len(exp_parts) > 1 else ""
            
            # Extract Options strictly limited to 4
            opt_pattern = r'\b([A-D]\s*\))\s*(.*?)(?=\b[A-D]\s*\)|\bCorrect Answer:|$)'
            option_matches = list(re.finditer(opt_pattern, content, re.DOTALL | re.IGNORECASE))[:4]
            
            if option_matches:
                first_opt_idx = option_matches[0].start()
                raw_q = content[:first_opt_idx].strip()
                
                # Extract Topic if present (e.g., "Topic: Prehistoric Period")
                topic_match = re.search(r'(?i)topic\s*[\:\-]?\s*(.*?)(?=\n|$)', raw_q)
                topic = topic_match.group(1).strip() if topic_match else "General History"
                
                # Clean the topic line out of the actual question text
                clean_q_lines = [line.strip() for line in raw_q.split('\n') if not re.match(r'(?i)^[\-\–\s]*topic', line.strip())]
                question_text = " ".join(clean_q_lines).strip()
                
                options = []
                correct_answer = ""
                
                ans_match = re.search(r'(?i)\bCorrect Answer:\s*(?:[A-D]\s*\)|\.)?\s*(.*?)(?=\n|$)', content)
                explicit_ans = ans_match.group(1).strip() if ans_match else ""

                for opt in option_matches:
                    opt_text = opt.group(2).strip().replace('\n', ' ')
                    clean_opt = re.sub(r'(?i)\(\s*correct\s*\)', '', opt_text).strip()
                    options.append(clean_opt)
                    
                    if explicit_ans and clean_opt in explicit_ans:
                        correct_answer = clean_opt
                    elif "(correct)" in opt_text.lower():
                        correct_answer = clean_opt
                
                if question_text and options:
                    parsed_questions.append({
                        "q": question_text,
                        "options": options,
                        "correct": correct_answer if correct_answer else options[0],
                        "exp": explanation,
                        "topic": topic
                    })
                    
        return parsed_questions
    except Exception as e:
        return []

# ----------------- DATABASES -----------------
FALLBACK_QUESTIONS = {
    "Rajat": [{"q": "Could not parse Basic PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error"}],
    "Manab": [{"q": "Could not parse Basic PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error"}],
    "Subho": [{"q": "Could not parse Basic PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error"}]
}

FALLBACK_ADV_QUESTIONS = {
    "Rajat": [{"q": "Could not parse Advanced PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error"}],
    "Manab": [{"q": "Could not parse Advanced PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error"}],
    "Subho": [{"q": "Could not parse Advanced PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error"}]
}

def get_student_questions(student_name, phase):
    mapping = PDF_MAPPING_BASIC if phase == "basic" else PDF_MAPPING_ADVANCED
    fallback = FALLBACK_QUESTIONS if phase == "basic" else FALLBACK_ADV_QUESTIONS
    
    for filename in mapping[student_name]:
        if os.path.exists(filename):
            parsed = extract_questions_from_pdf(filename)
            if len(parsed) > 0: 
                return parsed, filename
    return fallback[student_name], "PDF File Missing"

# ----------------- SESSION STATE -----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'marks' not in st.session_state:
    st.session_state.marks = {"Rajat": 0, "Manab": 0, "Subho": 0}
if 'adv_marks' not in st.session_state:
    st.session_state.adv_marks = {"Rajat": 0, "Manab": 0, "Subho": 0}
if 'completed_basic' not in st.session_state:
    st.session_state.completed_basic = {"Rajat": False, "Manab": False, "Subho": False}
if 'completed_adv' not in st.session_state:
    st.session_state.completed_adv = {"Rajat": False, "Manab": False, "Subho": False}
if 'mistakes' not in st.session_state:
    # Tracks detailed mistakes: {"Rajat": [{"phase": "Basic", "topic": "Vedic Period", "q": "..."}], ...}
    st.session_state.mistakes = {"Rajat": [], "Manab": [], "Subho": []}

st.markdown('<div class="main-header">Ancient History Examination Portal</div>', unsafe_allow_html=True)

if not PYPDF_AVAILABLE:
    st.error("🚨 CRITICAL ERROR: pypdf is NOT installed. Ensure requirements.txt is deployed.")
else:
    st.success("✅ synced and ready.")
# ----------------- TOP-LEVEL NAVIGATION -----------------
app_mode = st.sidebar.radio("App Mode", ["Student Portal", "Admin & Analysis Dashboard"])
st.sidebar.markdown("---")

if app_mode == "Admin & Analysis Dashboard":
    st.header("📊 Admin Dashboard & Weakness Analysis")
    st.write("Detailed breakdown of student performance, mistake tracking, and suggested focus areas.")
    
    students = ["Rajat", "Manab", "Subho"]
    
    # Overview Scoreboard
    st.subheader("Global Scoreboard")
    cols = st.columns(4)
    cols[0].write("**Student**")
    cols[1].write("**Basic Score**")
    cols[2].write("**Advanced Score**")
    cols[3].write("**Total Score**")
    
    for s in students:
        b_score = st.session_state.marks[s] if st.session_state.completed_basic[s] else 0
        a_score = st.session_state.adv_marks[s] if st.session_state.completed_adv[s] else "Pending"
        t_score = b_score + (st.session_state.adv_marks[s] if st.session_state.completed_adv[s] else 0)
        
        cols[0].write(f"**{s}**")
        cols[1].write(str(b_score) if st.session_state.completed_basic[s] else "Pending")
        cols[2].write(str(a_score))
        cols[3].write(str(t_score))

    st.markdown("---")
    st.subheader("Targeted Student Analysis")
    
    # Detailed Analysis Per Student
    for s in students:
        with st.container():
            st.markdown(f'<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown(f"### Profile: {s}")
            
            if not st.session_state.completed_basic[s] and not st.session_state.completed_adv[s]:
                st.info(f"{s} has not completed any exams yet.")
            else:
                student_mistakes = st.session_state.mistakes[s]
                error_count = len(student_mistakes)
                
                if error_count == 0:
                    st.success(f"{s} has a perfect record so far! No mistakes recorded.")
                else:
                    st.warning(f"**Total Errors Recorded:** {error_count}")
                    
                    # Extract topics to find weak areas
                    topics = [m['topic'] for m in student_mistakes]
                    topic_counts = Counter(topics)
                    
                    st.markdown("**Critical Focus Areas (Most Mistakes):**")
                    for topic, count in topic_counts.most_common():
                        st.write(f"- {topic}: {count} error(s)")
                        
                    with st.expander(f"View Specific Mistakes for {s}"):
                        for idx, m in enumerate(student_mistakes):
                            st.write(f"**{idx+1}. [{m['phase']}] Topic: {m['topic']}**")
                            st.write(f"*Question:* {m['q']}")
                            st.write("---")
                            
            st.markdown('</div>', unsafe_allow_html=True)

elif app_mode == "Student Portal":
    # ----------------- LOGIN PAGE -----------------
    if not st.session_state.logged_in:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.subheader("Student Login")
        selected_user = st.selectbox("Select Username", ["Rajat", "Manab", "Subho"])
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if password == CREDENTIALS[selected_user]:
                st.session_state.logged_in = True
                st.session_state.current_user = selected_user
                st.rerun()
            else:
                st.error("Incorrect Password. Please try again.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------- STUDENT TEST INTERFACE -----------------
    else:
        current_user = st.session_state.current_user
        
        st.sidebar.header(f"Welcome, {current_user}")
        st.sidebar.write(f"**Basic Score:** {st.session_state.marks[current_user]}")
        st.sidebar.write(f"**Advanced Score:** {st.session_state.adv_marks[current_user] if st.session_state.completed_adv[current_user] else 'Pending'}")
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
            
        test_phase = st.radio("Select Test:", ["Basic Test", "Advanced Test"])

        # Basic Test View
        if test_phase == "Basic Test":
            questions, source_name = get_student_questions(current_user, "basic")
            st.header(f"Basic Test Phase")
            st.caption(f"Loaded questions from: {source_name}")
            
            if st.session_state.completed_basic[current_user]:
                st.warning("You have already submitted this test. You can now unlock the Advanced Test.")
            else:
                user_answers = {}
                with st.form(key=f"basic_form_{current_user}"):
                    for i, q_data in enumerate(questions):
                        st.subheader(f"Q{i+1}: {q_data['q']}")
                        user_answers[i] = st.radio("Select Answer:", q_data['options'], key=f"basic_{current_user}_q{i}")
                        st.markdown("---")
                        
                    submit_button = st.form_submit_button(label="Submit Basic Test")
                    
                    if submit_button:
                        score = 0
                        st.subheader("Test Results:")
                        for i, q_data in enumerate(questions):
                            user_ans = user_answers[i]
                            correct_ans = q_data['correct']
                            
                            if user_ans == correct_ans:
                                score += 1
                                st.markdown(f"**Q{i+1}: {q_data['q']}**")
                                st.markdown(f"<p style='color:green; font-weight:bold;'>Your Answer: {user_ans} (Correct) ✔️</p>", unsafe_allow_html=True)
                            else:
                                # Track Mistake
                                st.session_state.mistakes[current_user].append({
                                    "phase": "Basic Test",
                                    "topic": q_data.get('topic', 'General History'),
                                    "q": q_data['q']
                                })
                                st.markdown(f"**Q{i+1}: {q_data['q']}**")
                                st.markdown(f"<p style='color:red; font-weight:bold;'>Your Answer: {user_ans} (Wrong) ❌</p>", unsafe_allow_html=True)
                                st.markdown(f"<p style='color:green; font-weight:bold;'>Correct Answer: {correct_ans}</p>", unsafe_allow_html=True)
                                
                            if q_data.get('exp'):
                                st.info(f"**Explanation:** {q_data['exp']}")
                            st.write("---")
                            
                        st.session_state.marks[current_user] = score
                        st.session_state.completed_basic[current_user] = True
                        st.success(f"Test Submitted! You scored {score} out of {len(questions)}.")

        # Advanced Test View
        elif test_phase == "Advanced Test":
            st.header("Advanced Test Phase")
            
            if not st.session_state.completed_basic[current_user]:
                st.warning("⚠️ You must complete your assigned Basic Test before accessing the Advanced Test.")
            elif st.session_state.completed_adv[current_user]:
                st.warning("You have already submitted the Advanced Test.")
            else:
                adv_questions, source_name = get_student_questions(current_user, "advanced")
                st.caption(f"Loaded questions from: {source_name}")
                
                adv_user_answers = {}
                with st.form(key=f"adv_form_{current_user}"):
                    for i, q_data in enumerate(adv_questions):
                        st.subheader(f"Q{i+1}: {q_data['q']}")
                        adv_user_answers[i] = st.radio("Select Answer:", q_data['options'], key=f"adv_{current_user}_q{i}")
                        st.markdown("---")
                        
                    adv_submit = st.form_submit_button(label="Submit Advanced Test")
                    
                    if adv_submit:
                        adv_score = 0
                        st.subheader("Test Results:")
                        for i, q_data in enumerate(adv_questions):
                            user_ans = adv_user_answers[i]
                            correct_ans = q_data['correct']
                            
                            if user_ans == correct_ans:
                                adv_score += 1
                                st.markdown(f"**Q{i+1}: {q_data['q']}**")
                                st.markdown(f"<p style='color:green; font-weight:bold;'>Your Answer: {user_ans} (Correct) ✔️</p>", unsafe_allow_html=True)
                            else:
                                # Track Mistake
                                st.session_state.mistakes[current_user].append({
                                    "phase": "Advanced Test",
                                    "topic": q_data.get('topic', 'General History'),
                                    "q": q_data['q']
                                })
                                st.markdown(f"**Q{i+1}: {q_data['q']}**")
                                st.markdown(f"<p style='color:red; font-weight:bold;'>Your Answer: {user_ans} (Wrong) ❌</p>", unsafe_allow_html=True)
                                st.markdown(f"<p style='color:green; font-weight:bold;'>Correct Answer: {correct_ans}</p>", unsafe_allow_html=True)
                                
                            if q_data.get('exp'):
                                st.info(f"**Explanation:** {q_data['exp']}")
                            st.write("---")
                                
                        st.session_state.adv_marks[current_user] = adv_score
                        st.session_state.completed_adv[current_user] = True
                        st.success(f"Advanced Test Submitted! You scored {adv_score} out of {len(adv_questions)}.")
