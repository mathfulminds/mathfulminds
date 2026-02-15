import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import json

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
    
    /* POP-OVER BUTTON STYLING */
    div[data-testid="stPopover"] > button {
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
    div[data-testid="stPopover"] > button:hover {
        background-color: #F8FAFC;
        border-color: #94A3B8;
        color: #0F172A;
    }
    
    /* STANDARD BUTTON STYLING */
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
    }

    /* Primary Action Button (Solve) override */
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #0F172A;
        color: white;
        border: none;
        box-shadow: 0 4px 0 #334155;
        padding: 10px 20px;
        font-size: 1.1rem;
    }
    
    /* Locked State */
    .locked-state {
        color: #94A3B8;
        font-style: italic;
        border: 1px dashed #CBD5E1;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
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
    """Directly appends text to the problem string"""
    st.session_state.user_problem += text

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
    # --- ADVANCED CALCULATOR INTERFACE ---
    calc_basic, calc_funcs, calc_trig = st.tabs(["Basic", "Functions", "Trig"])
    
    with calc_basic:
        c1, c2, c3, c4, c5 = st.columns(5)
        
        # 1. Fraction Builder
        with c1:
            with st.popover("a / b"): 
                st.write("**Fraction**")
                num = st.text_input("Top", key="frac_top")
                den = st.text_input("Bottom", key="frac_bot")
                if st.button("Insert", key="btn_frac"):
                    add_text(f"({num})/({den})")
                    st.rerun()

        # 2. Exponent Builder
        with c2:
            with st.popover("xʸ"): 
                st.write("**Exponent**")
                base = st.text_input("Base", key="exp_base")
                exp = st.text_input("Power", key="exp_pow")
                if st.button("Insert", key="btn_exp"):
                    add_text(f"({base})^({exp})")
                    st.rerun()

        # 3. Root Builder
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

        # ROW 2: Basic Ops
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

    # --- MAIN INPUT AREA ---
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

    # --- SYSTEM PROMPT ---
    SYSTEM_INSTRUCTION = r"""
    You are Mathful, an Interactive Math Tutor.
    
    GOAL: Break the problem into steps. For each step, provide:
    1. The visual math work (showing operations on both sides).
    2. A multiple-choice question to guide the student.
    
    OUTPUT FORMAT: JSON ONLY.
    Structure:
    [
      {
        "math_display": "LaTeX string",
        "question": "What is the best next step?",
        "options": [
          {"text": "Correct Option", "correct": true, "feedback": "Explanation."},
          {"text": "Wrong Option 1", "correct": false, "feedback": "Explanation."},
          {"text": "Wrong Option 2", "correct": false, "feedback": "Explanation."}
        ]
      }
    ]
    
    CRITICAL RULE FOR "math_display":
    You MUST show the vertical work for algebraic steps.
    Use '\begin{array}' to stack the equation, the operation (in RED), and the result.
    Align them properly.
    
    Example:
    "2x + 5 = 20 \\\\ {\color{red} -5 \quad -5} \\\\ 2x = 15"
    
    If no vertical work is needed, just show the equation.
    """

    model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)
    
    with st.spinner("Generating interactive lesson..."):
        try:
            response = model.generate_content(final_prompt)
            text_data = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(text_data)
            
            if isinstance(data, dict) and "error" in data:
                st.error(data["error"])
            else:
                st.session_state.solution_data = data
                
        except Exception as e:
            st.error("I got confused. Try a simpler problem!")

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
                show_math = False
                
                if i < st.session_state.step_count:
                    show_math = True
                elif interaction and interaction["correct"]:
                    show_math = True
                
                if show_math:
                    st.latex(step['math_display'])
                else:
                    st.markdown('<div class="locked-state">🔒 Solve step to reveal work</div>', unsafe_allow_html=True)
            
            with col_interaction:
                st.markdown(f"**Step {i+1}:** {step['question']}")
                interaction = st.session_state.interactions.get(i)
                
                if interaction and interaction["correct"]:
                    sel_idx = interaction["choice"]
                    opt = step['options'][sel_idx]
                    st.success(f"**{opt['text']}**\n\n{opt['feedback']}")
                    
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
                        st.error(f"**{opt['text']}**\n\n{opt['feedback']}")

                    for idx, option in enumerate(step['options']):
                        def on_click(step_i, opt_i, is_corr):
                            st.session_state.interactions[step_i] = {"choice": opt_i, "correct": is_corr}
                        
                        # --- CRASH FIX HERE ---
                        # We defensively get the text. If it's missing, we default to "Option {idx+1}"
                        raw_text = option.get("text", f"Option {idx+1}")
                        # Force it to be a string just in case
                        safe_text = str(raw_text)
                        clean_btn_text = safe_text.replace('$', '').replace('\\', '')
                        
                        if st.button(clean_btn_text, key=f"btn_{i}_{idx}"):
                            on_click(i, idx, option["correct"])
                            st.rerun()

        st.markdown("---")
