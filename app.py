import streamlit as st
import streamlit.components.v1 as components
import os
import re
import time
from collections import Counter

# Try importing pypdf for direct PDF reading
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Page Configuration
st.set_page_config(page_title="History Exam Portal", layout="wide")

# ----------------- ANTI-CHEATING CSS & STYLING -----------------
# Added CSS to disable text selection and highlight
st.markdown("""
    <style>
    /* Prevent text selection and copying */
    .stApp, p, h1, h2, h3, h4, h5, h6, span, div {
        -webkit-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
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

# ----------------- ANTI-CHEATING JAVASCRIPT (Disable Right-Click) -----------------
components.html(
    """
    <script>
    // Disable right-click context menu to prevent searching or inspecting
    document.addEventListener('contextmenu', event => event.preventDefault());
    
    // Disable keyboard shortcuts for copy/paste (Ctrl+C, Ctrl+V, etc.)
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'u' || e.key === 'a')) {
            e.preventDefault();
        }
    });
    </script>
    """,
    height=0, width=0
)

# User Credentials & File Mappings
CREDENTIALS = {
    "Rajat": "Rajat4",
    "Manab": "Manab6",
    "Subho": "Subho1"
}

PDF_MAPPING_BASIC = {
    "Rajat": ["ncient_history_set_1.pdf", "ancient_history_set_1.pdf"],
    "Manab": ["ncient_history_set_2.pdf", "ancient_history_set_2.pdf"],
    "Subho": ["ncient_history_set_3.pdf", "ancient_history_set_3.pdf"]
}

PDF_MAPPING_ADVANCED = {
    "Rajat": ["Ancient_Indian_History_Set_1.pdf"],
    "Manab": ["Ancient_Indian_History_Set_2.pdf"],
    "Subho": ["Ancient_Indian_History_Set_3.pdf"]
}

# ----------------- PDF PARSER FUNCTION -----------------
@st.cache_data
def extract_questions_from_pdf(filepath):
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
            
            opt_pattern = r'\b([A-D]\s*\))\s*(.*?)(?=\b[A-D]\s*\)|\bCorrect Answer:|$)'
            option_matches = list(re.finditer(opt_pattern, content, re.DOTALL | re.IGNORECASE))[:4]
            
            if option_matches:
                first_opt_idx = option_matches[0].start()
                raw_q = content[:first_opt_idx].strip()
                
                topic_match = re.search(r'(?i)topic\s*[\:\-]?\s*(.*?)(?=\n|$)', raw_q)
                topic = topic_match.group(1).strip() if topic_match else "General History"
                
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

FALLBACK_QUESTIONS = {
    s: [{"q": "Could not parse Basic PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error"}] for s in CREDENTIALS.keys()
}
FALLBACK_ADV_QUESTIONS = {
    s: [{"q": "Could not parse Advanced PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error"}] for s in CREDENTIALS.keys()
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

def render_dynamic_timer(time_left):
    timer_html = f"""
    <div style="text-align: left; font-family: sans-serif; font-size: 22px; font-weight: bold; color: #d9534f; background: rgba(255,255,255,0.8); padding: 10px; border-radius: 8px; width: 200px; border: 2px solid #d9534f; margin-bottom: 15px;">
        ⏱️ <span id="time_span">{time_left}</span>s left
    </div>
    <script>
        var timeLeft = {time_left};
        var timerId = setInterval(function() {{
            timeLeft--;
            var span = document.getElementById("time_span");
            if (span) span.innerText = Math.max(0, timeLeft);
            if (timeLeft <= 0) {{
                clearInterval(timerId);
                var buttons = window.parent.document.querySelectorAll("button");
                for (var i = 0; i < buttons.length; i++) {{
                    if (buttons[i].innerText.includes("Submit & Next")) {{
                        buttons[i].click();
                        break;
                    }}
                }}
            }}
        }}, 1000);
    </script>
    """
    components.html(timer_html, height=70)

# ----------------- GLOBAL SHARED STATE (Visible to everyone) -----------------
@st.cache_resource
def get_global_data():
    return {
        "marks": {"Rajat": 0, "Manab": 0, "Subho": 0},
        "adv_marks": {"Rajat": 0, "Manab": 0, "Subho": 0},
        "completed_basic": {"Rajat": False, "Manab": False, "Subho": False},
        "completed_adv": {"Rajat": False, "Manab": False, "Subho": False},
        "mistakes": {"Rajat": [], "Manab": [], "Subho": []}
    }

global_data = get_global_data()

# ----------------- LOCAL USER STATE (Only visible to current browser) -----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

st.markdown('<div class="main-header">Ancient History Examination Portal</div>', unsafe_allow_html=True)

app_mode = st.sidebar.radio("App Mode", ["Student Portal", "Admin & Analysis Dashboard"])
st.sidebar.markdown("---")

if app_mode == "Admin & Analysis Dashboard":
    st.header("📊 Admin Dashboard & Weakness Analysis")
    st.write("Detailed breakdown of student performance, mistake tracking, and suggested focus areas.")
    
    students = ["Rajat", "Manab", "Subho"]
    
    # Refresh button to fetch latest scores from other users
    if st.button("🔄 Refresh Live Scores"):
        st.rerun()
    
    st.subheader("Global Scoreboard")
    cols = st.columns(4)
    cols[0].write("**Student**")
    cols[1].write("**Basic Score**")
    cols[2].write("**Advanced Score**")
    cols[3].write("**Total Score**")
    
    for s in students:
        b_score = global_data["marks"][s] if global_data["completed_basic"][s] else 0
        a_score = global_data["adv_marks"][s] if global_data["completed_adv"][s] else "Pending"
        t_score = b_score + (global_data["adv_marks"][s] if global_data["completed_adv"][s] else 0)
        
        cols[0].write(f"**{s}**")
        cols[1].write(str(b_score) if global_data["completed_basic"][s] else "Pending")
        cols[2].write(str(a_score))
        cols[3].write(str(t_score))

    st.markdown("---")
    st.subheader("Targeted Student Analysis")
    
    for s in students:
        with st.container():
            st.markdown(f'<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown(f"### Profile: {s}")
            
            if not global_data["completed_basic"][s] and not global_data["completed_adv"][s]:
                st.info(f"{s} has not completed any exams yet.")
            else:
                student_mistakes = global_data["mistakes"][s]
                error_count = len(student_mistakes)
                
                if error_count == 0:
                    st.success(f"{s} has a perfect record so far! No mistakes recorded.")
                else:
                    st.warning(f"**Total Errors Recorded:** {error_count}")
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

    else:
        current_user = st.session_state.current_user
        
        st.sidebar.header(f"Welcome, {current_user}")
        st.sidebar.write(f"**Basic Score:** {global_data['marks'][current_user]}")
        st.sidebar.write(f"**Advanced Score:** {global_data['adv_marks'][current_user] if global_data['completed_adv'][current_user] else 'Pending'}")
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
            
        test_phase = st.radio("Select Test:", ["Basic Test", "Advanced Test"])

        # ----------------- BASIC TEST LOGIC -----------------
        if test_phase == "Basic Test":
            questions, source_name = get_student_questions(current_user, "basic")
            st.header(f"Basic Test Phase")
            
            if global_data["completed_basic"][current_user]:
                st.warning("You have already submitted this test. Review your summary below.")
                
                st.subheader("Test Review:")
                for i, q_data in enumerate(questions):
                    user_ans = st.session_state.get(f"basic_ans_{current_user}", {}).get(i, "TIMEOUT")
                    correct_ans = q_data['correct']
                    
                    st.markdown(f"**Q{i+1}: {q_data['q']}**")
                    if user_ans == correct_ans:
                        st.markdown(f"<p style='color:green; font-weight:bold;'>Your Answer: {user_ans} (Correct) ✔️</p>", unsafe_allow_html=True)
                    elif user_ans == "TIMEOUT":
                        st.markdown(f"<p style='color:orange; font-weight:bold;'>Time Expired / No Answer ⏱️</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:green; font-weight:bold;'>Correct Answer: {correct_ans}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color:red; font-weight:bold;'>Your Answer: {user_ans} (Wrong) ❌</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:green; font-weight:bold;'>Correct Answer: {correct_ans}</p>", unsafe_allow_html=True)
                        
                    if q_data.get('exp'):
                        st.info(f"**Explanation:** {q_data['exp']}")
                    st.write("---")

            else:
                if f"basic_idx_{current_user}" not in st.session_state:
                    st.session_state[f"basic_idx_{current_user}"] = 0
                    st.session_state[f"basic_ans_{current_user}"] = {}
                
                idx = st.session_state[f"basic_idx_{current_user}"]
                
                if idx < len(questions):
                    q_data = questions[idx]
                    
                    if f"basic_q_{idx}_time_{current_user}" not in st.session_state:
                        st.session_state[f"basic_q_{idx}_time_{current_user}"] = time.time()
                    
                    elapsed = int(time.time() - st.session_state[f"basic_q_{idx}_time_{current_user}"])
                    time_left = max(0, 30 - elapsed)
                    
                    st.subheader(f"Question {idx+1} of {len(questions)}")
                    render_dynamic_timer(time_left)
                    
                    with st.form(key=f"basic_form_{idx}"):
                        st.write(f"**{q_data['q']}**")
                        ans = st.radio("Select Answer:", q_data['options'], index=None, key=f"b_ans_{idx}")
                        
                        submitted = st.form_submit_button("Submit & Next")
                        
                        if submitted:
                            final_elapsed = time.time() - st.session_state[f"basic_q_{idx}_time_{current_user}"]
                            if final_elapsed > 33 or ans is None:
                                st.session_state[f"basic_ans_{current_user}"][idx] = "TIMEOUT"
                            else:
                                st.session_state[f"basic_ans_{current_user}"][idx] = ans
                                
                            st.session_state[f"basic_idx_{current_user}"] += 1
                            st.rerun()
                else:
                    score = 0
                    for i, q_data in enumerate(questions):
                        user_ans = st.session_state[f"basic_ans_{current_user}"].get(i, "TIMEOUT")
                        if user_ans == q_data['correct']:
                            score += 1
                        else:
                            global_data["mistakes"][current_user].append({
                                "phase": "Basic Test",
                                "topic": q_data.get('topic', 'General History'),
                                "q": q_data['q']
                            })
                            
                    global_data["marks"][current_user] = score
                    global_data["completed_basic"][current_user] = True
                    st.success("Test Graded successfully! Click below to view your results.")
                    if st.button("View Results"):
                        st.rerun()

        # ----------------- ADVANCED TEST LOGIC -----------------
        elif test_phase == "Advanced Test":
            st.header("Advanced Test Phase")
            
            if not global_data["completed_basic"][current_user]:
                st.warning("⚠️ You must complete your assigned Basic Test before accessing the Advanced Test.")
            elif global_data["completed_adv"][current_user]:
                st.warning("You have already submitted this test. Review your summary below.")
                
                adv_questions, source_name = get_student_questions(current_user, "advanced")
                st.subheader("Test Review:")
                for i, q_data in enumerate(adv_questions):
                    user_ans = st.session_state.get(f"adv_ans_{current_user}", {}).get(i, "TIMEOUT")
                    correct_ans = q_data['correct']
                    
                    st.markdown(f"**Q{i+1}: {q_data['q']}**")
                    if user_ans == correct_ans:
                        st.markdown(f"<p style='color:green; font-weight:bold;'>Your Answer: {user_ans} (Correct) ✔️</p>", unsafe_allow_html=True)
                    elif user_ans == "TIMEOUT":
                        st.markdown(f"<p style='color:orange; font-weight:bold;'>Time Expired / No Answer ⏱️</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:green; font-weight:bold;'>Correct Answer: {correct_ans}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color:red; font-weight:bold;'>Your Answer: {user_ans} (Wrong) ❌</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:green; font-weight:bold;'>Correct Answer: {correct_ans}</p>", unsafe_allow_html=True)
                        
                    if q_data.get('exp'):
                        st.info(f"**Explanation:** {q_data['exp']}")
                    st.write("---")
            else:
                adv_questions, source_name = get_student_questions(current_user, "advanced")
                
                if f"adv_idx_{current_user}" not in st.session_state:
                    st.session_state[f"adv_idx_{current_user}"] = 0
                    st.session_state[f"adv_ans_{current_user}"] = {}
                
                idx = st.session_state[f"adv_idx_{current_user}"]
                
                if idx < len(adv_questions):
                    q_data = adv_questions[idx]
                    
                    if f"adv_q_{idx}_time_{current_user}" not in st.session_state:
                        st.session_state[f"adv_q_{idx}_time_{current_user}"] = time.time()
                    
                    elapsed = int(time.time() - st.session_state[f"adv_q_{idx}_time_{current_user}"])
                    time_left = max(0, 30 - elapsed)
                    
                    st.subheader(f"Question {idx+1} of {len(adv_questions)}")
                    render_dynamic_timer(time_left)
                    
                    with st.form(key=f"adv_form_{idx}"):
                        st.write(f"**{q_data['q']}**")
                        ans = st.radio("Select Answer:", q_data['options'], index=None, key=f"a_ans_{idx}")
                        
                        submitted = st.form_submit_button("Submit & Next")
                        
                        if submitted:
                            final_elapsed = time.time() - st.session_state[f"adv_q_{idx}_time_{current_user}"]
                            if final_elapsed > 33 or ans is None:
                                st.session_state[f"adv_ans_{current_user}"][idx] = "TIMEOUT"
                            else:
                                st.session_state[f"adv_ans_{current_user}"][idx] = ans
                                
                            st.session_state[f"adv_idx_{current_user}"] += 1
                            st.rerun()
                else:
                    adv_score = 0
                    for i, q_data in enumerate(adv_questions):
                        user_ans = st.session_state[f"adv_ans_{current_user}"].get(i, "TIMEOUT")
                        if user_ans == q_data['correct']:
                            adv_score += 1
                        else:
                            global_data["mistakes"][current_user].append({
                                "phase": "Advanced Test",
                                "topic": q_data.get('topic', 'General History'),
                                "q": q_data['q']
                            })
                            
                    global_data["adv_marks"][current_user] = adv_score
                    global_data["completed_adv"][current_user] = True
                    st.success("Advanced Test Graded successfully! Click below to view your results.")
                    if st.button("View Results"):
                        st.rerun()
