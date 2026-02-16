import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import json
import random
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Mathful Minds", page_icon="🧠", layout="wide")

# --- CUSTOM STYLE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #0F172A;
    }
    
    .stApp { background-color: #F8FAFC; }

    .main-title {
        font-size: 3rem;
        font-weight: 800;
        color: #000000;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    /* Center the math generally, but align content left inside */
    .katex-display {
        text-align: left !important;
        margin-left: 1rem !important;
        overflow-x: auto;
        overflow-y: hidden;
    }
    
    div.stButton > button {
        background-color: #FFFFFF;
        color: #1E293B;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 0 #CBD5E1;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 8px;
        width: 100%;
        min-height: 50px;
    }
    div.stButton > button:hover {
        background-color: #F8FAFC;
        border-color: #94A3B8;
        color: #0F172A;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #0F172A;
        color: white;
        border: none;
        box-shadow: 0 4px 0 #334155;
        padding: 10px 20px;
        font-size: 1.1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("⚠️ Google API Key Missing:", type="password")
    if not api_key: st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = 'gemini-flash-latest'

# --- SESSION STATE ---
if "step_count" not in st.session_state: st.session_state.step_count = 0
if "solution_data" not in st.session_state: st.session_state.solution_data = None
if "interactions" not in st.session_state: st.session_state.interactions = {}
if "user_problem" not in st.session_state: st.session_state.user_problem = ""

# --- HELPER FUNCTIONS ---
def add_text(text):
    st.session_state.user_problem += text

def extract_json_from_text(text):
    clean_text = text.replace("```json", "").replace("```", "").strip()
    try:
        match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        if match: return match.group(0)
        return clean_text
    except:
        return clean_text

def build_latex_from_lists(step_data):
    """
    THE ANCHORED LIST ARCHITECT (Dynamic Columns):
    Builds a LaTeX array that expands to fit the number of terms.
    Zone A: Left Terms | Zone B: Separator | Zone C: Right Terms
    """
    left_terms = step_data.get("left_terms", [])
    separator = step_data.get("separator", "")
    right_terms = step_data.get("right_terms", [])
    
    # Operation Data
    op_data = step_data.get("operation", {})
    op_val = op_data.get("value", "")
    # Indices are lists of integers (e.g. [0, 2]) meaning apply to term 0 and 2
    targets_left = op_data.get("target_left", [])
    targets_right = op_data.get("target_right", [])

    # 1. Calculate Columns Needed
    num_left = len(left_terms)
    num_right = len(right_terms)
    
    # If empty lists (simplifying expression), ensure at least 1 col so LaTeX doesn't crash
    if num_left == 0 and num_right == 0: return step_data.get("initial_math", "")

    # 2. Build Column Format String (e.g., "c c c | c | c c")
    # c = center aligned column
    cols_latex = "c " * num_left
    if separator:
        cols_latex += "c " # The Separator Column
    cols_latex += "c " * num_right

    # 3. Build Row 1 (The Math Terms)
    # Join terms with ' & '
    row1_parts = []
    
    # Left Zone
    for t in left_terms: row1_parts.append(str(t))
    
    # Separator Zone
    if separator: row1_parts.append(separator)
    
    # Right Zone
    for t in right_terms: row1_parts.append(str(t))
    
    row1_str = " & ".join(row1_parts)

    # 4. Build Row 2 (The Red Operations)
    if not op_val:
        # No operation? Return 1-row array
        return f"\\begin{{array}}{{{cols_latex}}} {row1_str} \\end{{array}}"

    row2_parts = []
    
    # Left Operations
    for i in range(num_left):
        if i in targets_left:
            row2_parts.append(f"\\color{{red}}{{{op_val}}}")
        else:
            row2_parts.append("") # Empty cell

    # Separator Operation (Empty)
    if separator: row2_parts.append("") 

    # Right Operations
    for i in range(num_right):
        if i in targets_right:
            row2_parts.append(f"\\color{{red}}{{{op_val}}}")
        else:
            row2_parts.append("") # Empty cell

    row2_str = " & ".join(row2_parts)

    # 5. Final Assembly
    return f"""
    \\begin{{array}}{{{cols_latex}}}
    {row1_str} \\\\
    {row2_str}
    \\end{{array}}
    """

def safe_parse_option(option, idx):
    if isinstance(option, dict):
        text = str(option.get("text", f"Option {idx+1}"))
        feedback = str(option.get("feedback", ""))
    else:
        text = str(option)
        feedback = ""

    if not feedback: feedback = "Try again!" if idx != 0 else "Correct!"
    clean_text = text.replace('$', '').replace('\\', '')
    return text, clean_text, feedback

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    grade_level = st.selectbox("Grade Level", ["5th Grade", "6th Grade", "7th Grade", "8th Grade", "High School"])
    subject_focus = st.multiselect("Topic", ["Algebra", "Geometry", "Arithmetic"], default=["Algebra"])

# --- INPUT TABS ---
st.markdown('<div class="main-title">Mathful Minds</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #64748B;"><b>Interactive Tutor.</b> Build your problem step-by-step.</p>', unsafe_allow_html=True)

tab_photo, tab_draw, tab_type = st.tabs(["📸 Photo", "✏️ Draw", "⌨️ Type"])
input_image = None
input_text = None

with tab_photo:
    uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="photo_uploader")
    if uploaded_file: input_image = Image.open(uploaded_file)

with tab_draw:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        canvas_result = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=250, width=500, key="canvas")
        if canvas_result.image_data is not None and canvas_result.json_data is not None:
             if len(canvas_result.json_data["objects"]) > 0:
                input_image = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert('RGB')

with tab_type:
    # --- CALCULATOR ---
    calc_basic, calc_funcs, calc_trig = st.tabs(["Basic", "Functions", "Trig"])
    
    with calc_basic:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            with st.popover("a / b"): 
                st.write("**Fraction**")
                num = st.text_input("Top", key="frac_top")
                den = st.text_input("Bottom", key="frac_bot")
                if st.button("Insert", key="btn_frac"):
                    add_text(f"({num})/({den})")
                    st.rerun()
        with c2:
            with st.popover("xʸ"): 
                st.write("**Exponent**")
                base = st.text_input("Base", key="exp_base")
                exp = st.text_input("Power", key="exp_pow")
                if st.button("Insert", key="btn_exp"):
                    add_text(f"({base})^({exp})")
                    st.rerun()
        with c3:
            with st.popover("ⁿ√x"):
                st.write("**Root**")
                rad = st.text_input("Value", key="root_val")
                idx = st.text_input("Index (Optional)", key="root_idx")
                if st.button("Insert", key="btn_root"):
                    if idx: add_text(f"root({rad}, {idx})")
                    else: add_text(f"sqrt({rad})")
                    st.rerun()
        with c4: st.button("(", on_click=add_text, args=("(",))
        with c5: st.button(")", on_click=add_text, args=(")",))

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.button("➕", on_click=add_text, args=("+",))
        with c2: st.button("➖", on_click=add_text, args=("-",))
        with c3: st.button("✖️", on_click=add_text, args=("*",))
        with c4: st.button("➗", on_click=add_text, args=("/",))
        with c5: st.button("=", on_click=add_text, args=("=",))

    with calc_funcs:
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            with st.popover("logₙ"):
                st.write("Logarithm")
                val = st.text_input("Value", key="log_val")
                base = st.text_input("Base", key="log_base")
                if st.button("Insert Log", key="btn_log"):
                    if base: add_text(f"log({val}, {base})")
                    else: add_text(f"log({val})")
                    st.rerun()
        with c2: st.button("ln", on_click=add_text, args=("ln(",))
        with c3: st.button("|x|", on_click=add_text, args=("|",))
        with c4: st.button("!", on_click=add_text, args=("!",))

    with calc_trig:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: st.button("sin", on_click=add_text, args=("sin(",))
        with c2: st.button("cos", on_click=add_text, args=("cos(",))
        with c3: st.button("tan", on_click=add_text, args=("tan(",))
        with c4: st.button("csc", on_click=add_text, args=("csc(",))
        with c5: st.button("sec", on_click=add_text, args=("sec(",))
        with c6: st.button("cot", on_click=add_text, args=("cot(",))

    input_text = st.text_area(
        "", 
        key="user_problem",
        placeholder="Select a tool above to build your equation...", 
        height=100
    )

# --- SOLVER LOGIC ---
if st.button("🚀 Start Interactive Solve", type="primary", use_container_width=True):
    st.session_state.step_count = 0
    st.session_state.solution_data = None
    st.session_state.interactions = {}
    
    final_prompt = []
    if input_text:
        clean_input = input_text.replace("²", "^2").replace("³", "^3").replace("π", "pi")
        final_prompt = [f"Grade Level: {grade_level}. Problem: {clean_input}"]
    elif input_image:
        final_prompt = [f"Grade Level: {grade_level}. Solve the problem in this image.", input_image]
    else:
        st.warning("⚠️ Please provide a problem first!"); st.stop()

    # --- SYSTEM PROMPT (ANCHORED LIST SYSTEM) ---
    SYSTEM_INSTRUCTION = r"""
    You are Mathful, an Interactive Math Tutor.
    GOAL: Break the problem into steps using the "Anchored List" method for perfect alignment.
    
    OUTPUT FORMAT: JSON ONLY. 
    
    Structure:
    [
      {
        "left_terms": ["3x", "+5"],   // List of terms on the left.
        "separator": "=",             // The symbol in the middle (=, <, >, or "" for expressions).
        "right_terms": ["20"],        // List of terms on the right.
        
        "operation": {
            "value": "-5",              // The math to show in red (e.g. -5, \div 3).
            "target_left": [1],         // Indices of left_terms to put op under (e.g. [1] puts it under +5).
            "target_right": [0]         // Indices of right_terms to put op under.
        },
        
        "final_answer": "OPTIONAL: If LAST step, result here (e.g. x=5).",
        "question": "What is the best next step?",
        "options": [
           {"text": "Correct Option", "feedback": "Explanation..."},
           {"text": "Wrong Option", "feedback": "Explanation..."},
           {"text": "Wrong Option", "feedback": "Explanation..."}
        ]
      }
    ]
    
    RULE 1: Split terms logically. "3x + 5" -> ["3x", "+5"].
    RULE 2: Indices start at 0.
    RULE 3: If simplifying an expression, leave "separator" and "right_terms" empty.
    """

    model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)
    
    with st.spinner("Generating interactive lesson..."):
        try:
            response = model.generate_content(final_prompt)
            clean_json_text = extract_json_from_text(response.text)
            data = json.loads(clean_json_text)
            
            for step in data:
                # 1. BUILD THE MATH GRID (Anchored Lists)
                step["display_math"] = build_latex_from_lists(step)
                
                # 2. Shuffle Options
                raw_options = step.get("options", [])
                processed_options = []
                for idx, opt in enumerate(raw_options):
                    txt, cln, fb = safe_parse_option(opt, idx)
                    is_correct = (idx == 0)
                    processed_options.append({
                        "text": txt, "clean_text": cln, "feedback": fb, "correct": is_correct
                    })
                random.shuffle(processed_options)
                step["options"] = processed_options

            st.session_state.solution_data = data
                
        except Exception as e:
            st.error(f"I got confused. Try a simpler problem! (Error: {str(e)})")

# --- DISPLAY LOGIC ---
if st.session_state.solution_data:
    steps = st.session_state.solution_data
    
    st.divider()
    
    for i in range(len(steps)):
        if i > st.session_state.step_count:
            break
            
        step = steps[i]
        
        with st.container():
            col_math, col_interaction = st.columns([1, 1])
            
            with col_math:
                interaction = st.session_state.interactions.get(i)
                display_math = step.get("display_math", "")

                if i < st.session_state.step_count:
                    st.latex(display_math)
                elif i == st.session_state.step_count:
                    if interaction and interaction["correct"]:
                        st.latex(display_math)
                        final_val = step.get('final_answer', '')
                        if final_val:
                            # Render final answer cleanly
                            if "=" in final_val:
                                lhs, rhs = final_val.split("=", 1)
                                final_grid = f"\\begin{{array}}{{r c l}} {lhs} & = & {rhs} \\end{{array}}"
                                st.latex(final_grid)
                            else:
                                st.latex(final_val)
                    else:
                        # Fallback for unsolved state: Show just the equation row
                        # We rebuild it using the builder but without operations
                        fallback_step = step.copy()
                        fallback_step["operation"] = {} # Remove ops
                        fallback_math = build_latex_from_lists(fallback_step)
                        st.latex(fallback_math)
            
            with col_interaction:
                st.markdown(f"**Step {i+1}:** {step.get('question', '')}")
                interaction = st.session_state.interactions.get(i)
                
                if interaction and interaction["correct"]:
                    sel_idx = interaction["choice"]
                    opt = step['options'][sel_idx]
                    clean_fb = opt["feedback"].replace('$', '').replace('\\', '')
                    st.success(f"**{opt['text']}**\n\n{clean_fb}")
                    
                    if i == st.session_state.step_count:
                        if i < len(steps) - 1:
                            if st.button("Next Step ➡️", key=f"next_{i}"):
                                st.session_state.step_count += 1
                                st.rerun()
                        else:
                            st.balloons()
                            st.success("🎉 Problem Complete!")
                            if st.button("Start New Problem"):
                                st.session_state.solution_data = None
                                st.session_state.step_count = 0
                                st.rerun()
                else:
                    if interaction and not interaction["correct"]:
                        sel_idx = interaction["choice"]
                        opt = step['options'][sel_idx]
                        clean_fb = opt["feedback"].replace('$', '').replace('\\', '')
                        st.error(f"**{opt['text']}**\n\n{clean_fb}")

                    for idx, option in enumerate(step['options']):
                        def on_click(step_i, opt_i, is_corr_val):
                            st.session_state.interactions[step_i] = {"choice": opt_i, "correct": is_corr_val}
                        
                        if st.button(option["clean_text"], key=f"btn_{i}_{idx}"):
                            on_click(i, idx, option["correct"])
                            st.rerun()

        st.markdown("---")
