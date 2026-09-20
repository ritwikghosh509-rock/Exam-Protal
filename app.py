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
st.set_page_config(page_title="History Exam Portal", layout="wide", initial_sidebar_state="expanded")

# ----------------- ANTI-CHEATING CSS & PREMIUM STYLING -----------------
st.markdown("""
    <style>
    /* Prevent text selection and copying */
    .stApp, p, h1, h2, h3, h4, h5, h6, span, div {
        -webkit-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    
    /* Modern Soft Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #f0f4fd 0%, #c5d6f6 100%);
    }
    
    /* Sleek Main Header */
    .main-header {
        font-size: 42px;
        font-weight: 900;
        background: -webkit-linear-gradient(45deg, #1e293b, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 30px;
        letter-spacing: -1px;
    }
    
    /* Elegant Login Box */
    .login-box {
        background: rgba(255, 255, 255, 0.95); 
        padding: 40px;
        max-width: 450px;
        margin: auto;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.5);
        backdrop-filter: blur(10px);
    }
    
    /* Analysis Cards */
    .analysis-card {
        background: #ffffff;
        padding: 25px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(149, 157, 165, 0.15);
        border-left: 5px solid #3b82f6;
    }
    
    /* Premium Question Container */
    .question-box {
        background: #ffffff;
        padding: 35px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(50, 50, 93, 0.1), 0 5px 15px rgba(0, 0, 0, 0.07);
        margin-bottom: 25px;
        margin-top: 15px;
        border-top: 6px solid #4F46E5;
    }
    
    /* Vibrant Question Number Badge */
    .q-number-badge {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        padding: 8px 18px;
        border-radius: 30px;
        font-weight: 800;
        font-size: 14px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
    }
    
    /* Interactive Radio Buttons (Options) */
    div.stRadio > div[role="radiogroup"] > label {
        background-color: #f8fafc;
        border: 2px solid #e2e8f0;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        color: #334155;
    }
    div.stRadio > div[role="radiogroup"] > label:hover {
        border-color: #4F46E5;
        background-color: #eef2ff;
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(79, 70, 229, 0.12);
    }
    
    /* Hide the Streamlit footer, but keep the header so the sidebar arrow works */
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ----------------- ANTI-CHEATING JAVASCRIPT -----------------
components.html(
    """
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'u' || e.key === 'a')) {
            e.preventDefault();
        }
    });
    </script>
    """,
    height=0, width=0
)

# User & Admin Credentials
CREDENTIALS = {
    "Rajat": "Rajat4",
    "Manab": "Manab6",
    "Subho": "Subho1"
}
ADMIN_PASSWORD = "Admin123"

# ----------------- FILE MAPPINGS -----------------
PDF_MAPPING_BASIC = {
    "Rajat": ["Basic Sunday Test.pdf"],
    "Manab": ["Basic Sunday Test.pdf"],
    "Subho": ["Basic Sunday Test.pdf"]
}

PDF_MAPPING_ADV_HIST = {
    "Rajat": ["Advance History Sunday Test.pdf"],
    "Manab": ["Advance History Sunday Test.pdf"],
    "Subho": ["Advance History Sunday Test.pdf"]
}

PDF_MAPPING_ADV_GEO = {
    "Rajat": ["Advance Geography Sunday Test.pdf"],
    "Manab": ["Advance Geography Sunday Test.pdf"],
    "Subho": ["Advance Geography Sunday Test.pdf"]
}

# ----------------- BULLETPROOF PDF PARSER -----------------
def clean_pdf_text(text):
    """Strips invisible PDF artifacts, unprintable characters, and private-use unicode blocks (which render as square boxes)"""
    return re.sub(r'[\ue000-\uf8ff\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffd]', '', text).strip()

@st.cache_data
def extract_questions_from_pdf(filepath):
    if not PYPDF_AVAILABLE or not os.path.exists(filepath):
        return []
    try:
        reader = PdfReader(filepath)
        full_text = "\n" + "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        
        parts = re.split(r'(?i)(?:^|\n|\s+)Q(?:uestion)?\s*\d+[\s\.\-\:]+', full_text)
        parsed_questions = []

        for i in range(1, len(parts)):
            block = parts[i]
            
            source_match = re.search(r'(?i)exam (?:history \& )?source\s*[\:\-]?\s*([^\n]+)', block)
            exam_source = clean_pdf_text(source_match.group(1)) if source_match else ""
            
            exp_parts = re.split(r'(?i)\n?\s*(?:Detailed\s+)?(?:Explanation|Deep-Dive Rationale)\s*[\:\-]', block)
            main_body = exp_parts[0]
            
            if len(exp_parts) > 1:
                explanation_clean = re.split(r'(?i)\n\s*(?:Chapter|Exam (?:History \& )?Source|\d+\.\s+(?:Ancient|Indian|Northern|Peninsular|Islands|The))', exp_parts[1])[0]
                explanation = clean_pdf_text(explanation_clean.replace('\n', ' '))
            else:
                explanation = ""
                
            ans_parts = re.split(r'(?i)\s*\b(?:Correct\s+)?Answer\s*[\:\-]', main_body)
            q_and_opts_and_source = ans_parts[0]  
            answer_text = ans_parts[1] if len(ans_parts) > 1 else ""
            
            ans_match = re.search(r'(?i)^\s*[\[\(]?([A-D])[\]\)]?', answer_text)
            correct_letter = ans_match.group(1).upper() if ans_match else ""
            
            source_split = re.split(r'(?i)\s*\bExam(?: History \&)? Source\s*[\:\-]', q_and_opts_and_source)
            q_and_opts = source_split[0]
            
            opt_pattern = r'(?i)(?:^|\n|\s+)[\[\(]?([A-D])[\]\)\.](?:\s*)([\s\S]*?)(?=(?:^|\n|\s+)[\[\(]?[A-D][\]\)\.](?:\s*)|\Z)'
            option_matches = list(re.finditer(opt_pattern, q_and_opts))[-4:]
            
            if len(option_matches) >= 2:
                first_opt_idx = option_matches[0].start()
                question_text_raw = q_and_opts[:first_opt_idx].strip()
                
                clean_q_lines = [line.strip() for line in question_text_raw.split('\n') if not re.match(r'(?i)^[\-\–\s]*(?:topic)', line.strip())]
                question_text = clean_pdf_text("\n".join(clean_q_lines))
                
                options = []
                correct_answer = ""

                for opt in option_matches:
                    opt_letter = opt.group(1).upper()
                    opt_text = clean_pdf_text(opt.group(2).replace('\n', ' '))
                    clean_opt = re.sub(r'(?i)\(\s*correct\s*\)', '', opt_text).strip()
                    options.append(clean_opt)
                    
                    if correct_letter == opt_letter:
                        correct_answer = clean_opt
                
                if not correct_answer and options:
                    correct_answer = options[0]
                
                if question_text and options:
                    parsed_questions.append({
                        "q": question_text,
                        "options": options,
                        "correct": correct_answer,
                        "exp": explanation,
                        "topic": "History/Geography",
                        "source": exam_source
                    })
                    
        return parsed_questions
    except Exception as e:
        return []

FALLBACK = {
    s: [{"q": "Could not parse PDF.", "options": ["OK"], "correct": "OK", "exp": "", "topic": "Error", "source": ""}] for s in CREDENTIALS.keys()
}

def get_student_questions(student_name, phase):
    if phase == "basic":
        mapping = PDF_MAPPING_BASIC
    elif phase == "adv_hist":
        mapping = PDF_MAPPING_ADV_HIST
    else:
        mapping = PDF_MAPPING_ADV_GEO
        
    for filename in mapping[student_name]:
        if os.path.exists(filename):
            parsed = extract_questions_from_pdf(filename)
            if len(parsed) > 0: 
                return parsed, filename
    return FALLBACK[student_name], "PDF File Missing"

# ----------------- DYNAMIC TIMER FUNCTION -----------------
def render_global_timer(time_left, phase):
    timer_html = f"""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; padding: 18px 25px; border-radius: 16px; display: flex; align-items: center; justify-content: flex-start; gap: 20px; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); font-family: sans-serif;">
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 12px; border-radius: 50%; display: flex; align-items: center; justify-content: center; height: 50px; width: 50px; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);">
            <span style="font-size: 22px;">⏳</span>
        </div>
        <div>
            <div id="global_timer_{phase}" style="font-size: 28px; font-weight: 800; letter-spacing: 2px;">00:00</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Time Remaining</div>
        </div>
    </div>
    <script>
        (function() {{
            var timeLeft = {time_left};
            var timerElement = document.getElementById("global_timer_{phase}");
            
            function formatTime(seconds) {{
                var m = Math.floor(seconds / 60);
                var s = Math.floor(seconds % 60);
                return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
            }}
            
            if (timerElement) timerElement.innerText = formatTime(timeLeft);
            
            var timerId = setInterval(function() {{
                timeLeft--;
                if (timerElement) timerElement.innerText = formatTime(Math.max(0, timeLeft));
                if (timeLeft <= 0) {{
                    clearInterval(timerId);
                    var buttons = window.parent.document.querySelectorAll("button");
                    for (var i = 0; i < buttons.length; i++) {{
                        if (buttons[i].innerText.includes("ForceAutoSubmit")) {{
                            buttons[i].click();
                            break;
                        }}
                    }}
                }}
            }}, 1000);
        }})();
    </script>
    """
    components.html(timer_html, height=115)

# ----------------- GLOBAL SHARED STATE -----------------
@st.cache_resource
def get_global_data():
    return {
        "marks": {"Rajat": 0, "Manab": 0, "Subho": 0},
        "adv_hist_marks": {"Rajat": 0, "Manab": 0, "Subho": 0},
        "adv_geo_marks": {"Rajat": 0, "Manab": 0, "Subho": 0},
        "completed_basic": {"Rajat": False, "Manab": False, "Subho": False},
        "completed_adv_hist": {"Rajat": False, "Manab": False, "Subho": False},
        "completed_adv_geo": {"Rajat": False, "Manab": False, "Subho": False},
        "mistakes": {"Rajat": [], "Manab": [], "Subho": []},
        "submitted_answers": {
            "basic": {"Rajat": {}, "Manab": {}, "Subho": {}},
            "adv_hist": {"Rajat": {}, "Manab": {}, "Subho": {}},
            "adv_geo": {"Rajat": {}, "Manab": {}, "Subho": {}}
        }
    }

global_data = get_global_data()

def submit_test(phase_id, current_user, questions, test_phase, score_key, completion_key):
    """Centralized test grading and saving logic"""
    score = 0
    saved_answers = {}
    
    for i, q_data_ in enumerate(questions):
        user_ans = st.session_state[f"{phase_id}_ans_{current_user}"].get(i)
        if user_ans is None:
            user_ans = "TIMEOUT"
            
        saved_answers[i] = user_ans
        if user_ans == q_data_['correct']:
            score += 1
        else:
            global_data["mistakes"][current_user].append({
                "phase": test_phase,
                "topic": q_data_.get('topic', 'General History'),
                "q": q_data_['q']
            })
            
    global_data[score_key][current_user] = score
    global_data["submitted_answers"][phase_id][current_user] = saved_answers
    global_data[completion_key][current_user] = True

# ----------------- LOCAL USER STATE -----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

st.markdown('<div class="main-header">History Examination Portal</div>', unsafe_allow_html=True)

if not PYPDF_AVAILABLE:
    st.error("🚨 CRITICAL ERROR: pypdf is NOT installed.")

app_mode = st.sidebar.radio("App Mode", ["Student Portal", "Admin Dashboard"])
st.sidebar.markdown("---")

# ==================== ADMIN DASHBOARD ====================
if app_mode == "Admin Dashboard":
    st.header("📊 Admin Dashboard")
    st.write("Overview of student performance and scores.")
    
    st.markdown("---")
    st.subheader("System Administration")
    admin_auth = st.text_input("Enter Admin Password to unlock Danger Zone:", type="password")
    
    if admin_auth == ADMIN_PASSWORD:
        with st.expander("⚠️ Danger Zone: Reset System"):
            st.warning("This will permanently delete all student scores, mistakes, and test progress.")
            if st.button("Reset All Data"):
                global_data["marks"] = {"Rajat": 0, "Manab": 0, "Subho": 0}
                global_data["adv_hist_marks"] = {"Rajat": 0, "Manab": 0, "Subho": 0}
                global_data["adv_geo_marks"] = {"Rajat": 0, "Manab": 0, "Subho": 0}
                global_data["completed_basic"] = {"Rajat": False, "Manab": False, "Subho": False}
                global_data["completed_adv_hist"] = {"Rajat": False, "Manab": False, "Subho": False}
                global_data["completed_adv_geo"] = {"Rajat": False, "Manab": False, "Subho": False}
                global_data["mistakes"] = {"Rajat": [], "Manab": [], "Subho": []}
                global_data["submitted_answers"] = {
                    "basic": {"Rajat": {}, "Manab": {}, "Subho": {}},
                    "adv_hist": {"Rajat": {}, "Manab": {}, "Subho": {}},
                    "adv_geo": {"Rajat": {}, "Manab": {}, "Subho": {}}
                }
                
                st.cache_resource.clear()
                keys_to_keep = ['logged_in', 'current_user']
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                st.success("All data has been wiped. Starting fresh!")
                time.sleep(1) 
                st.rerun()
    elif admin_auth:
        st.error("Incorrect Admin Password.")

    students = ["Rajat", "Manab", "Subho"]
    if st.button("🔄 Refresh Live Scores"):
        st.rerun()
    
    st.subheader("Global Scoreboard")
    cols = st.columns(6)
    cols[0].write("**Student**")
    cols[1].write("**Basic**")
    cols[2].write("**Adv History**")
    cols[3].write("**Adv Geo**")
    cols[4].write("**Correct**")
    cols[5].write("**Wrong**")
    
    for s in students:
        b_score = global_data["marks"][s] if global_data["completed_basic"][s] else 0
        ah_score = global_data["adv_hist_marks"][s] if global_data["completed_adv_hist"][s] else "Pending"
        ag_score = global_data["adv_geo_marks"][s] if global_data["completed_adv_geo"][s] else "Pending"
        
        t_correct = b_score + (ah_score if isinstance(ah_score, int) else 0) + (ag_score if isinstance(ag_score, int) else 0)
        t_wrong = len(global_data["mistakes"][s])
        
        cols[0].write(f"**{s}**")
        cols[1].write(str(b_score) if global_data["completed_basic"][s] else "Pending")
        cols[2].write(str(ah_score))
        cols[3].write(str(ag_score))
        cols[4].write(str(t_correct))
        cols[5].write(str(t_wrong))


# ==================== STUDENT PORTAL ====================
elif app_mode == "Student Portal":
    if not st.session_state.logged_in:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#1e293b; margin-bottom: 25px;'>Student Login</h2>", unsafe_allow_html=True)
        selected_user = st.selectbox("Select Username", ["Rajat", "Manab", "Subho"])
        password = st.text_input("Password", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Secure Login →", type="primary", use_container_width=True):
            if password == CREDENTIALS[selected_user]:
                st.session_state.logged_in = True
                st.session_state.current_user = selected_user
                st.rerun()
            else:
                st.error("Incorrect Password. Please try again.")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        current_user = st.session_state.current_user
        
        # Sidebar Updates
        st.sidebar.header(f"👋 Welcome, {current_user}")
        st.sidebar.write(f"**Basic Score:** {global_data['marks'][current_user] if global_data['completed_basic'][current_user] else 'Pending'}")
        st.sidebar.write(f"**Adv History Score:** {global_data['adv_hist_marks'][current_user] if global_data['completed_adv_hist'][current_user] else 'Pending'}")
        st.sidebar.write(f"**Adv Geo Score:** {global_data['adv_geo_marks'][current_user] if global_data['completed_adv_geo'][current_user] else 'Pending'}")
        st.sidebar.markdown("---")
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
            
        # ----------------- CONDITIONAL STUDENT DASHBOARD OVERVIEW -----------------
        if global_data["completed_basic"][current_user] or global_data["completed_adv_hist"][current_user] or global_data["completed_adv_geo"][current_user]:
            b_score = global_data["marks"][current_user] if global_data["completed_basic"][current_user] else 0
            ah_score = global_data["adv_hist_marks"][current_user] if global_data["completed_adv_hist"][current_user] else 0
            ag_score = global_data["adv_geo_marks"][current_user] if global_data["completed_adv_geo"][current_user] else 0
            
            total_correct = b_score + ah_score + ag_score
            total_wrong = len(global_data["mistakes"][current_user])
            
            st.markdown(f"<h3 style='color:#1e293b; margin-bottom: 20px;'>Dashboard Overview</h3>", unsafe_allow_html=True)
            st.markdown(f"""
                <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 20px; border-radius: 12px; color: white; flex: 1; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h2 style="margin: 0; font-size: 36px; color: white;">{total_correct}</h2>
                        <p style="margin: 0; font-size: 16px; opacity: 0.9;">Total Correct Answers</p>
                    </div>
                    <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 20px; border-radius: 12px; color: white; flex: 1; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h2 style="margin: 0; font-size: 36px; color: white;">{total_wrong}</h2>
                        <p style="margin: 0; font-size: 16px; opacity: 0.9;">Total Wrong Answers</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        test_phase = st.radio("Select Test Module:", ["Basic Test", "Advance History Test", "Advance Geography Test"], horizontal=True)

        # Phase mappings: (id, header, score_dict, completion_dict, time_limit_in_seconds)
        phase_keys = {
            "Basic Test": ("basic", "📘 Basic Test Phase", "marks", "completed_basic", 360),
            "Advance History Test": ("adv_hist", "📙 Advance History Test Phase", "adv_hist_marks", "completed_adv_hist", 180),
            "Advance Geography Test": ("adv_geo", "🌍 Advance Geography Test Phase", "adv_geo_marks", "completed_adv_geo", 360),
        }
        
        phase_id, header_title, score_key, completion_key, test_duration = phase_keys[test_phase]
        
        questions, source_name = get_student_questions(current_user, phase_id)
        st.header(header_title)
        
        if phase_id in ["adv_hist", "adv_geo"] and not global_data["completed_basic"][current_user]:
            st.warning("⚠️ You must complete your assigned Basic Test before accessing the Advanced modules.")
        
        elif global_data[completion_key][current_user]:
            st.success("You have successfully submitted this test. Review your summary below.")
            
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.subheader("Detailed Test Review")
            for i, q_data in enumerate(questions):
                
                # Retrieve submitted answers directly from the persistent global dictionary
                user_ans = global_data["submitted_answers"][phase_id][current_user].get(i, "TIMEOUT")
                correct_ans = q_data['correct']
                
                # pre-wrap ensures internal lists in Q1 format correctly
                st.markdown(f"<div style='color:#334155; font-size:16px; font-weight: bold; white-space: pre-wrap;'>Q{i+1}: {q_data['q']}</div>", unsafe_allow_html=True)
                
                # Only show Exam Source for Basic Phase
                if phase_id == "basic" and q_data.get('source'):
                    st.markdown(f"<div style='color:#64748b; font-size:12px; font-weight:600; margin-top:4px;'>📌 {q_data['source']}</div>", unsafe_allow_html=True)
                    
                if user_ans == correct_ans:
                    st.markdown(f"<p style='color:#10b981; font-weight:600; margin-top:10px;'>Your Answer: {user_ans} (Correct) ✔️</p>", unsafe_allow_html=True)
                elif user_ans == "TIMEOUT":
                    st.markdown(f"<p style='color:#f59e0b; font-weight:600; margin-top:10px;'>Time Expired / No Answer ⏱️</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#10b981; font-weight:600;'>Correct Answer: {correct_ans}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color:#ef4444; font-weight:600; margin-top:10px;'>Your Answer: {user_ans} (Wrong) ❌</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#10b981; font-weight:600;'>Correct Answer: {correct_ans}</p>", unsafe_allow_html=True)
                    
                if q_data.get('exp'):
                    st.info(f"**Explanation:** {q_data['exp']}")
                st.write("---")
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            if f"{phase_id}_idx_{current_user}" not in st.session_state:
                st.session_state[f"{phase_id}_idx_{current_user}"] = 0
                st.session_state[f"{phase_id}_ans_{current_user}"] = {}
            
            idx = st.session_state[f"{phase_id}_idx_{current_user}"]
            
            if idx < len(questions):
                q_data = questions[idx]
                
                if f"{phase_id}_start_time_{current_user}" not in st.session_state:
                    st.session_state[f"{phase_id}_start_time_{current_user}"] = time.time()
                
                elapsed = int(time.time() - st.session_state[f"{phase_id}_start_time_{current_user}"])
                time_left = max(0, test_duration - elapsed)
                
                if st.button("ForceAutoSubmit", key=f"auto_submit_{phase_id}"):
                    submit_test(phase_id, current_user, questions, test_phase, score_key, completion_key)
                    st.rerun()
                    
                st.markdown(f"""<style>div:has(button[key="auto_submit_{phase_id}"]) {{ display: none; }}</style>""", unsafe_allow_html=True)
                
                if time_left <= 0:
                    st.warning("Time is up! Auto-submitting...")
                    time.sleep(2)
                    submit_test(phase_id, current_user, questions, test_phase, score_key, completion_key)
                    st.rerun()
                else:
                    render_global_timer(time_left, phase_id)
                    
                    with st.form(key=f"{phase_id}_form_{idx}"):
                        saved_ans = st.session_state[f"{phase_id}_ans_{current_user}"].get(idx)
                        try:
                            default_idx = q_data['options'].index(saved_ans)
                        except (ValueError, TypeError):
                            default_idx = None

                        st.markdown('<div class="question-box">', unsafe_allow_html=True)
                        st.markdown(f'<div class="q-number-badge">Question {idx + 1} of {len(questions)}</div>', unsafe_allow_html=True)
                        
                        if phase_id == "basic" and q_data.get('source'):
                            st.markdown(f"<div style='color:#64748b; font-size:13px; font-weight:700; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.5px;'>📌 {q_data['source']}</div>", unsafe_allow_html=True)
                            
                        # pre-wrap maintains the alignment of lists inside Q1 
                        st.markdown(f"<div style='color:#1e293b; margin-bottom: 25px; line-height: 1.5; font-size: 1.1rem; font-weight: 600; white-space: pre-wrap;'>{q_data['q']}</div>", unsafe_allow_html=True)
                        
                        ans = st.radio("Select Answer:", q_data['options'], index=default_idx, key=f"{phase_id}_ans_{idx}", label_visibility="collapsed")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col1:
                            prev_btn = st.form_submit_button("← Previous") if idx > 0 else False
                        with col3:
                            if idx < len(questions) - 1:
                                next_btn = st.form_submit_button("Save & Next →")
                                submit_btn = False
                            else:
                                next_btn = False
                                submit_btn = st.form_submit_button("Save & Submit Test 🚀")
                                
                        if prev_btn:
                            if ans is not None:
                                st.session_state[f"{phase_id}_ans_{current_user}"][idx] = ans
                            st.session_state[f"{phase_id}_idx_{current_user}"] -= 1
                            st.rerun()
                        if next_btn:
                            if ans is not None:
                                st.session_state[f"{phase_id}_ans_{current_user}"][idx] = ans
                            st.session_state[f"{phase_id}_idx_{current_user}"] += 1
                            st.rerun()
                        if submit_btn:
                            if ans is not None:
                                st.session_state[f"{phase_id}_ans_{current_user}"][idx] = ans
                                
                            submit_test(phase_id, current_user, questions, test_phase, score_key, completion_key)
                            st.success("Test Graded successfully! Click below to view your results.")
                            st.rerun()
