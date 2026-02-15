import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Mathful Minds", page_icon="🧮", layout="wide")

# --- CUSTOM STYLE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Global Canvas ── */
    .stApp {
        background: linear-gradient(165deg, #F0F4FF 0%, #FAFBFF 40%, #FFF8F0 100%);
    }

    /* Hide default Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}

    /* ── Hero Header ── */
    .hero-wrap {
        text-align: center;
        padding: 2.5rem 1rem 1rem;
    }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 4px 14px;
        border-radius: 20px;
        margin-bottom: 0.6rem;
    }
    .hero-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -1.5px;
        color: #1E1B4B;
        margin: 0;
        line-height: 1.1;
    }
    .hero-sub {
        font-size: 1rem;
        color: #6B7280;
        margin-top: 0.4rem;
        font-weight: 400;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #EEF2FF;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
        color: #6B7280;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #4F46E5 !important;
        box-shadow: 0 1px 4px rgba(79, 70, 229, 0.15);
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }

    /* ── Calculator Buttons ── */
    div[data-testid="stPopover"] > button,
    div.stButton > button {
        font-family: 'DM Mono', monospace;
        background: white;
        color: #1E1B4B;
        border: 1.5px solid #E0E7FF;
        border-radius: 10px;
        font-size: 1rem;
        font-weight: 500;
        width: 100%;
        min-height: 48px;
        box-shadow: 0 2px 0 #C7D2FE;
        transition: all 0.15s ease;
    }
    div[data-testid="stPopover"] > button:hover,
    div.stButton > button:hover {
        background: #EEF2FF;
        border-color: #A5B4FC;
        transform: translateY(-1px);
        box-shadow: 0 3px 0 #C7D2FE;
    }
    div[data-testid="stPopover"] > button:active,
    div.stButton > button:active {
        transform: translateY(1px);
        box-shadow: none;
    }

    /* ── Primary Solve Button ── */
    div[data-testid="stButton"] > button[kind="primary"] {
        font-family: 'DM Sans', sans-serif;
        background: linear-gradient(135deg, #4F46E5, #7C3AED);
        color: white;
        border: none;
        border-radius: 12px;
        font-size: 1.05rem;
        font-weight: 700;
        min-height: 54px;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
        letter-spacing: 0.3px;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4338CA, #6D28D9);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45);
        transform: translateY(-1px);
    }

    /* ── Text Area ── */
    .stTextArea textarea {
        font-family: 'DM Mono', monospace;
        font-size: 1.05rem;
        border: 2px solid #E0E7FF;
        border-radius: 12px;
        background: white;
        color: #1E1B4B;
        padding: 12px;
    }
    .stTextArea textarea:focus {
        border-color: #818CF8;
        box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.2);
    }

    /* ── Step Cards ── */
    .step-card {
        background: white;
        border: 1.5px solid #E0E7FF;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.06);
        transition: border-color 0.3s ease;
    }
    .step-card.completed {
        border-color: #86EFAC;
        background: linear-gradient(135deg, #FFFFFF 0%, #F0FFF4 100%);
    }
    .step-card.active {
        border-color: #818CF8;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12);
    }

    .step-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 0.8rem;
    }
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .step-number.completed {
        background: #DCFCE7;
        color: #16A34A;
    }
    .step-number.active {
        background: #E0E7FF;
        color: #4F46E5;
    }
    .step-number.locked {
        background: #F3F4F6;
        color: #9CA3AF;
    }
    .step-label {
        font-weight: 600;
        font-size: 0.95rem;
        color: #374151;
    }

    .locked-overlay {
        color: #9CA3AF;
        font-style: italic;
        border: 1.5px dashed #D1D5DB;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        background: #F9FAFB;
    }

    /* ── Progress Bar ── */
    .progress-track {
        width: 100%;
        background: #E0E7FF;
        border-radius: 20px;
        height: 10px;
        overflow: hidden;
        margin: 0.5rem 0 1.5rem;
    }
    .progress-fill {
        height: 100%;
        border-radius: 20px;
        background: linear-gradient(90deg, #6366F1, #A78BFA);
        transition: width 0.5s ease;
    }

    /* ── Completion Banner ── */
    .complete-banner {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
        border: 2px solid #86EFAC;
        border-radius: 16px;
        margin-top: 1rem;
    }
    .complete-banner h3 {
        color: #16A34A;
        margin: 0.5rem 0 0.25rem;
        font-size: 1.4rem;
    }
    .complete-banner p {
        color: #6B7280;
        margin: 0;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #1E1B4B;
    }
    section[data-testid="stSidebar"] * {
        color: #E0E7FF !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label {
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: #A5B4FC !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #312E81;
    }

    /* ── Popover Panels ── */
    div[data-testid="stPopoverBody"] {
        border-radius: 12px;
        border: 1.5px solid #E0E7FF;
    }

    /* ── File Uploader ── */
    .stFileUploader > div {
        border: 2px dashed #C7D2FE;
        border-radius: 12px;
        background: white;
    }

    /* ── Metrics / Score ── */
    .score-pill {
        display: inline-block;
        background: linear-gradient(135deg, #EEF2FF, #E0E7FF);
        color: #4F46E5;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 6px 16px;
        border-radius: 20px;
        margin-right: 8px;
    }

    /* ── Divider ── */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #C7D2FE, transparent);
        margin: 1.5rem 0;
    }

    /* Fix Streamlit spacing */
    .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("API Key Required", type="password", help="Enter your Google Gemini API key")
    if not api_key:
        st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = 'gemini-flash-latest'

# --- SESSION STATE ---
if "step_count" not in st.session_state:
    st.session_state.step_count = 0
if "solution_data" not in st.session_state:
    st.session_state.solution_data = None
if "interactions" not in st.session_state:
    st.session_state.interactions = {}
if "user_problem" not in st.session_state:
    st.session_state.user_problem = ""
if "score" not in st.session_state:
    st.session_state.score = {"correct_first": 0, "total_steps": 0}


# --- HELPER FUNCTIONS ---
def add_text(text):
    st.session_state.user_problem += text


def get_step_status(index):
    """Return 'completed', 'active', or 'locked' for a given step."""
    if index < st.session_state.step_count:
        return "completed"
    elif index == st.session_state.step_count:
        return "active"
    return "locked"


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding: 1.5rem 0 1rem;">
            <span style="font-size: 2.2rem;">🧮</span>
            <div style="font-family: 'DM Sans'; font-size: 1.3rem; font-weight: 800; color: white; margin-top: 4px; letter-spacing: -0.5px;">
                Mathful Minds
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    grade_level = st.selectbox(
        "GRADE LEVEL",
        ["6th Grade", "7th Grade", "8th Grade"],
        index=0
    )
    subject_focus = st.multiselect(
        "TOPICS",
        ["Algebra", "Geometry", "Arithmetic", "Ratios", "Statistics"],
        default=["Algebra"]
    )

    st.divider()

    # Session stats
    correct = st.session_state.score["correct_first"]
    total = st.session_state.score["total_steps"]
    if total > 0:
        pct = int((correct / total) * 100)
        st.markdown(f"""
            <div style="text-align:center; padding: 0.5rem 0;">
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #A5B4FC; font-weight: 600; margin-bottom: 4px;">Session Accuracy</div>
                <div style="font-size: 2rem; font-weight: 800; color: white;">{pct}%</div>
                <div style="font-size: 0.8rem; color: #818CF8;">{correct} of {total} steps on first try</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align:center; padding: 0.5rem 0;">
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #A5B4FC; font-weight: 600;">Session</div>
                <div style="font-size: 0.85rem; color: #818CF8; margin-top: 4px;">Solve a problem to see stats</div>
            </div>
        """, unsafe_allow_html=True)


# --- HERO HEADER ---
st.markdown("""
    <div class="hero-wrap">
        <div class="hero-badge">Interactive Tutor</div>
        <h1 class="hero-title">Mathful Minds</h1>
        <p class="hero-sub">Build your problem, then solve it step-by-step.</p>
    </div>
""", unsafe_allow_html=True)

# --- INPUT TABS ---
tab_type, tab_photo, tab_draw = st.tabs(["⌨️  Type", "📸  Photo", "✏️  Draw"])
input_image = None
input_text = None

with tab_photo:
    uploaded_file = st.file_uploader(
        "Upload an image of your math problem",
        type=["png", "jpg", "jpeg"],
        key="photo_uploader"
    )
    if uploaded_file:
        input_image = Image.open(uploaded_file)
        st.image(input_image, caption="Uploaded problem", use_container_width=True)

with tab_draw:
    c1, c2, c3 = st.columns([1, 3, 1])
    with c2:
        canvas_result = st_canvas(
            stroke_width=3,
            stroke_color="#1E1B4B",
            background_color="#FFFFFF",
            height=250,
            width=500,
            key="canvas"
        )
        if canvas_result.image_data is not None and canvas_result.json_data is not None:
            if len(canvas_result.json_data["objects"]) > 0:
                input_image = Image.fromarray(
                    canvas_result.image_data.astype('uint8'), 'RGBA'
                ).convert('RGB')

with tab_type:
    # --- CALCULATOR INTERFACE ---
    calc_basic, calc_funcs, calc_trig = st.tabs(["123  Basic", "f(x)  Functions", "θ  Trig"])

    with calc_basic:
        # Row 1: Builders (Popovers)
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            with st.popover("a/b"):
                st.markdown("**Fraction**")
                num = st.text_input("Numerator", key="frac_num")
                den = st.text_input("Denominator", key="frac_den")
                if st.button("Insert", key="frac_btn"):
                    add_text(f"({num})/({den})")
                    st.rerun()

        with c2:
            with st.popover("xʸ"):
                st.markdown("**Exponent**")
                base = st.text_input("Base", key="exp_base")
                exp = st.text_input("Power", key="exp_pow")
                if st.button("Insert", key="exp_btn"):
                    add_text(f"({base})^({exp})")
                    st.rerun()

        with c3:
            with st.popover("√x"):
                st.markdown("**Root**")
                rad = st.text_input("Radicand", key="root_rad")
                idx = st.text_input("Index (blank = square root)", key="root_idx")
                if st.button("Insert", key="root_btn"):
                    if idx:
                        add_text(f"root({rad}, {idx})")
                    else:
                        add_text(f"sqrt({rad})")
                    st.rerun()

        with c4:
            st.button("( )", on_click=add_text, args=("()",), key="parens")
        with c5:
            st.button("x", on_click=add_text, args=("x",), key="var_x")

        # Row 2: Operators
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.button("+", on_click=add_text, args=("+",), key="op_add")
        with c2:
            st.button("−", on_click=add_text, args=("-",), key="op_sub")
        with c3:
            st.button("×", on_click=add_text, args=("*",), key="op_mul")
        with c4:
            st.button("÷", on_click=add_text, args=("/",), key="op_div")
        with c5:
            st.button("=", on_click=add_text, args=("=",), key="op_eq")

    with calc_funcs:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            with st.popover("logₙ"):
                st.markdown("**Logarithm**")
                val = st.text_input("Value", key="log_val")
                log_base = st.text_input("Base (default 10)", key="log_base")
                if st.button("Insert", key="log_btn"):
                    if log_base:
                        add_text(f"log({val}, {log_base})")
                    else:
                        add_text(f"log({val})")
                    st.rerun()
        with c2:
            st.button("ln(", on_click=add_text, args=("ln(",), key="fn_ln")
        with c3:
            st.button("|x|", on_click=add_text, args=("|",), key="fn_abs")
        with c4:
            st.button("n!", on_click=add_text, args=("!",), key="fn_fact")

    with calc_trig:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.button("sin", on_click=add_text, args=("sin(",), key="t_sin")
        with c2:
            st.button("cos", on_click=add_text, args=("cos(",), key="t_cos")
        with c3:
            st.button("tan", on_click=add_text, args=("tan(",), key="t_tan")
        with c4:
            st.button("csc", on_click=add_text, args=("csc(",), key="t_csc")
        with c5:
            st.button("sec", on_click=add_text, args=("sec(",), key="t_sec")
        with c6:
            st.button("cot", on_click=add_text, args=("cot(",), key="t_cot")

    # Main text input
    input_text = st.text_area(
        "",
        key="user_problem",
        placeholder="Type or build your equation here …",
        height=90
    )

# --- SOLVE BUTTON ---
st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
if st.button("Solve Step-by-Step", type="primary", use_container_width=True):
    # Reset
    st.session_state.step_count = 0
    st.session_state.solution_data = None
    st.session_state.interactions = {}

    # Build prompt
    final_prompt = []
    if input_text:
        clean_input = input_text.replace("²", "^2").replace("³", "^3").replace("π", "pi")
        final_prompt = [f"Grade Level: {grade_level}. Topics: {', '.join(subject_focus)}. Problem: {clean_input}"]
    elif input_image:
        final_prompt = [f"Grade Level: {grade_level}. Solve the problem in this image.", input_image]
    else:
        st.warning("Enter a problem first.")
        st.stop()

    SYSTEM_INSTRUCTION = r"""
    You are Mathful, an Interactive Math Tutor.

    GOAL: Break the problem into steps. For each step, provide the CORRECT next move and 2 INCORRECT "distractor" moves.

    OUTPUT FORMAT: JSON ONLY. No markdown. No explanation outside JSON.
    Structure:
    [
      {
        "math_display": "LaTeX of the work AFTER this step is done",
        "question": "What is the best next step?",
        "options": [
          {"text": "Correct Option", "correct": true, "feedback": "Explanation why correct."},
          {"text": "Wrong Option 1", "correct": false, "feedback": "Explanation why wrong. Reference the specific misconception."},
          {"text": "Wrong Option 2", "correct": false, "feedback": "Explanation why wrong. Reference the specific misconception."}
        ]
      }
    ]

    RULES:
    1. "math_display": Use LaTeX. For vertical math, use '\begin{aligned}' or simple newlines '\\'.
    2. "options": Scramble the order randomly. Mark only one as "correct": true.
    3. **FRACTIONS**: Wherever possible, use LaTeX for fractions in text/feedback (e.g. "The slope is $\frac{1}{2}$"). Do NOT use slashes (1/2).
    4. Make distractor options reflect COMMON STUDENT MISCONCEPTIONS (e.g., additive trap for ratios, combining unlike terms, sign errors).
    5. Keep feedback concise: 1-2 sentences max.
    6. If image is unsafe/non-math, return {"error": "..."}
    """

    model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)

    with st.spinner("Building your interactive lesson …"):
        try:
            response = model.generate_content(final_prompt)
            text_data = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(text_data)

            if isinstance(data, dict) and "error" in data:
                st.error(data["error"])
            else:
                st.session_state.solution_data = data
        except Exception as e:
            st.error("Something went wrong — try rephrasing or simplifying the problem.")

# --- DISPLAY SOLUTION STEPS ---
if st.session_state.solution_data:
    steps = st.session_state.solution_data
    total_steps = len(steps)
    completed_steps = st.session_state.step_count

    # Progress bar
    progress_pct = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
            <span class="score-pill">Step {min(completed_steps + 1, total_steps)} of {total_steps}</span>
            <span style="font-size: 0.8rem; color: #6B7280; font-weight: 500;">{progress_pct}% complete</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width: {progress_pct}%;"></div>
        </div>
    """, unsafe_allow_html=True)

    for i in range(len(steps)):
        if i > st.session_state.step_count:
            # Show locked placeholder
            st.markdown(f"""
                <div class="step-card">
                    <div class="step-header">
                        <span class="step-number locked">{i + 1}</span>
                        <span class="step-label" style="color: #9CA3AF;">Step {i + 1}</span>
                    </div>
                    <div class="locked-overlay">Complete the current step to unlock</div>
                </div>
            """, unsafe_allow_html=True)
            continue

        step = steps[i]
        status = get_step_status(i)
        interaction = st.session_state.interactions.get(i)

        # Step card header
        if status == "completed":
            st.markdown(f"""
                <div class="step-card completed">
                    <div class="step-header">
                        <span class="step-number completed">✓</span>
                        <span class="step-label">Step {i + 1} — {step['question']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            # Show math for completed steps
            st.latex(step['math_display'])

        elif status == "active":
            st.markdown(f"""
                <div class="step-card active">
                    <div class="step-header">
                        <span class="step-number active">{i + 1}</span>
                        <span class="step-label">Step {i + 1}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            col_q, col_math = st.columns([3, 2])

            with col_q:
                st.markdown(f"**{step['question']}**")

                # Show previous wrong answer feedback
                if interaction and not interaction["correct"]:
                    sel_idx = interaction["choice"]
                    opt = step['options'][sel_idx]
                    st.error(f"**Not quite.** {opt['feedback']}")

                # Show correct answer feedback
                if interaction and interaction["correct"]:
                    sel_idx = interaction["choice"]
                    opt = step['options'][sel_idx]
                    st.success(f"**{opt['text']}** — {opt['feedback']}")

                    if i < len(steps) - 1:
                        if st.button("Next Step →", key=f"next_{i}", type="primary"):
                            st.session_state.step_count += 1
                            st.rerun()
                    else:
                        st.markdown("""
                            <div class="complete-banner">
                                <div style="font-size: 2rem;">🎉</div>
                                <h3>Problem Complete</h3>
                                <p>Nice work. Ready for the next one?</p>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("New Problem", key="new_problem"):
                            st.session_state.solution_data = None
                            st.session_state.step_count = 0
                            st.session_state.interactions = {}
                            st.rerun()
                else:
                    # Option buttons
                    for idx, option in enumerate(step['options']):
                        clean_text = option["text"].replace('$', '').replace('\\', '')
                        if st.button(clean_text, key=f"opt_{i}_{idx}"):
                            is_correct = option["correct"]
                            st.session_state.interactions[i] = {
                                "choice": idx,
                                "correct": is_correct
                            }
                            # Track score (only first attempt per step)
                            if i not in [k for k, v in st.session_state.interactions.items() if not v.get("_counted")]:
                                st.session_state.score["total_steps"] += 1
                                if is_correct:
                                    st.session_state.score["correct_first"] += 1
                                st.session_state.interactions[i]["_counted"] = True
                            st.rerun()

            with col_math:
                if interaction and interaction["correct"]:
                    st.latex(step['math_display'])
                else:
                    st.markdown("""
                        <div class="locked-overlay">
                            <div style="font-size: 1.5rem; margin-bottom: 4px;">🔒</div>
                            Answer correctly to reveal
                        </div>
                    """, unsafe_allow_html=True)
