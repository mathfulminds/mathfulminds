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
    
    /* HIDDEN STATE STYLE */
    .locked-state {
        color: #94A3B8;
        font-style: italic;
        border: 1px dashed #CBD5E1;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
    }
    
    /* HELPER BUTTONS */
    div.stButton > button {
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
        padding: 0px; 
        font-size: 1rem;
        font-weight: 600;
        border-radius: 6px;
        width: 100%;
        min-height: 40px;
    }
    div.stButton > button:hover {
        background-color: #E2E8F0;
        border-color: #94A3B8;
    }
    
    /* Primary Action Button (Solve) override */
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #0F172A;
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 1rem;
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

# IMPORTANT: Initialize the key we will bind to the text area
if "user_problem" not in st.session_state: st.session_state.user_problem = ""

# --- HELPER TO ADD SYMBOL ---
def add_symbol(sym):
    # This directly modifies the session state variable bound to the text box
    st.session_state.user_problem += sym

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    grade_level = st.selectbox("Grade Level", ["5th Grade", "6th Grade", "7th Grade", "8th Grade", "High School"])
    subject_focus = st.multiselect("Topic", ["Algebra", "Geometry", "Arithmetic"], default=["Algebra"])

# --- INPUT TABS ---
st.markdown('<div class="main-title">Mathful Minds</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #64748B;"><b>Interactive Tutor.</b> Choose the right path.</p>', unsafe_allow_html=True)

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
    st.write("Math Keypad:")
    
    # ROW 1: Operations
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.button("➕", on_click=add_symbol, args=("+",))
    with c2: st.button("➖", on_click=add_symbol, args=("-",))
    with c3: st.button("✖️", on_click=add_symbol, args=("*",))
    with c4: st.button("➗", on_click=add_symbol, args=("/",))
    with c5: st.button("(", on_click=add_symbol, args=("(",))
    with c6: st.button(")", on_click=add_symbol, args=(")",))

    # ROW 2: Variables & Algebra
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.button("x²", on_click=add_symbol, args=("^2",))
    with c2: st.button("√", on_click=add_symbol, args=("sqrt(",))
    with c3: st.button("≤", on_click=add_symbol, args=("≤",))
    with c4: st.button("≥", on_click=add_symbol, args=("≥",))
    with c5: st.button("π", on_click=add_symbol, args=("pi",))
    with c6: st.button("|x|", on_click=add_symbol, args=("|",))

    # EXPANDER: Advanced Trig/Log
    with st.expander("More Functions (Trig, Log, etc.)"):
        t1, t2, t3, t4, t5, t6 = st.columns(6)
        with t1: st.button("sin", on_click=add_symbol, args=("sin(",))
        with t2: st.button("cos", on_click=add_symbol, args=("cos(",))
        with t3: st.button("tan", on_click=add_symbol, args=("tan(",))
        with t4: st.button("log", on_click=add_symbol, args=("log(",))
        with t5: st.button("ln", on_click=add_symbol, args=("ln(",))
        with t6: st.button("!", on_click=add_symbol, args=("!",))

    # THE TEXT AREA (Bound directly to session state)
    # The key="user_problem" connects this box to st.session_state.user_problem
    # When the buttons update the state, this box updates automatically.
    input_text = st.text_area(
        "", 
        key="user_problem",
        placeholder="Type here or click buttons above...", 
        height=100
    )

# --- SOLVER LOGIC ---
if st.button("🚀 Start Interactive Solve", type="primary", use_container_width=True):
    # Reset State
    st.session_state.step_count = 0
    st.session_state.solution_data = None
    st.session_state.interactions = {}
    
    # Priority Check
    final_prompt = []
    if input_text:
        final_prompt = [f"Grade Level: {grade_level}. Problem: {input_text}"]
    elif input_image:
        final_prompt = [f"Grade Level: {grade_level}. Solve the problem in this image.", input_image]
    else:
        st.warning("⚠️ Please provide a problem first!"); st.stop()

    # --- SYSTEM PROMPT ---
    SYSTEM_INSTRUCTION = r"""
    You are Mathful, an Interactive Math Tutor.
    
    GOAL: Break the problem into steps. For each step, provide the CORRECT next move and 2 INCORRECT "distractor" moves.
    
    OUTPUT FORMAT: JSON ONLY.
    Structure:
    [
      {
        "math_display": "LaTeX of the work AFTER this step is done",
        "question": "What is the best next step?",
        "options": [
          {"text": "Correct Option", "correct": true, "feedback": "Explanation why correct."},
          {"text": "Wrong Option 1", "correct": false, "feedback": "Explanation why wrong."},
          {"text": "Wrong Option 2", "correct": false, "feedback": "Explanation why wrong."}
        ]
      }
    ]
    
    RULES:
    1. "math_display": Use LaTeX. For vertical math, use '\begin{aligned}' or simple newlines '\\'.
    2. "options": Scramble the order. Mark only one as "correct": true.
    3. **FRACTIONS**: Wherever possible, use LaTeX for fractions in text/feedback (e.g. "The slope is $\frac{1}{2}$"). Do NOT use slashes (1/2).
    4. If image is unsafe/non-math, return {"error": "..."}
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
    
    # Loop through ALL steps
    for i in range(len(steps)):
        # Only show steps we have reached
        if i > st.session_state.step_count:
            break
            
        step = steps[i]
        
        # Container for the Row
        with st.container():
            col_math, col_interaction = st.columns([1, 1])
            
            # --- LEFT COLUMN: MATH ---
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
            
            # --- RIGHT COLUMN: INTERACTION ---
            with col_interaction:
                st.markdown(f"**Step {i+1}:** {step['question']}")
                interaction = st.session_state.interactions.get(i)
                
                if interaction and interaction["correct"]:
                    # --- SUCCESS STATE ---
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
                    # --- CHOICE STATE ---
                    if interaction and not interaction["correct"]:
                        sel_idx = interaction["choice"]
                        opt = step['options'][sel_idx]
                        st.error(f"**{opt['text']}**\n\n{opt['feedback']}")

                    for idx, option in enumerate(step['options']):
                        def on_click(step_i, opt_i, is_corr):
                            st.session_state.interactions[step_i] = {"choice": opt_i, "correct": is_corr}
                        
                        clean_btn_text = option["text"].replace('$', '').replace('\\', '')
                        if st.button(clean_btn_text, key=f"btn_{i}_{idx}"):
                            on_click(i, idx, option["correct"])
                            st.rerun()

        st.markdown("---")
