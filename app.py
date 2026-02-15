import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import json
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="Mathful Minds", page_icon="🧠", layout="wide")

# --- CUSTOM STYLE (Slate & Interactive) ---
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
    
    /* MATH CONTAINER (Left) */
    .math-container {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        font-size: 1.3rem;
        text-align: center;
        min-height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* OPTION BUTTON STYLES */
    .option-btn {
        width: 100%;
        padding: 15px;
        margin-bottom: 10px;
        border: 2px solid #E2E8F0;
        border-radius: 8px;
        background-color: white;
        text-align: left;
        font-weight: 600;
        transition: all 0.2s;
        cursor: pointer;
    }
    .option-btn:hover {
        border-color: #94A3B8;
        background-color: #F1F5F9;
    }
    
    /* FEEDBACK BOXES */
    .feedback-correct {
        background-color: #DCFCE7; /* Green 100 */
        border: 2px solid #16A34A; /* Green 600 */
        color: #14532D;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }
    .feedback-wrong {
        background-color: #FEE2E2; /* Red 100 */
        border: 2px solid #DC2626; /* Red 600 */
        color: #7F1D1D;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }

    /* HIDDEN STATE */
    .blur-text {
        color: transparent;
        text-shadow: 0 0 15px rgba(0,0,0,0.3);
        user-select: none;
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
# Track specific interactions: {step_index: {"selected_option": idx, "is_correct": bool}}
if "interactions" not in st.session_state: st.session_state.interactions = {}

# --- HELPER FUNCTIONS ---
def handle_option_click(step_idx, option_idx, is_correct):
    st.session_state.interactions[step_idx] = {
        "selected_option": option_idx,
        "is_correct": is_correct
    }
    # If correct, we unlock the next step automatically? Or wait for user?
    # For now, we update state to show the green box.

# --- MAIN UI ---
st.markdown('<div class="main-title">Mathful Minds</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #64748B;"><b>Interactive Tutor.</b> Choose the right path.</p>', unsafe_allow_html=True)

# --- SIDEBAR (Selectors) ---
with st.sidebar:
    st.header("⚙️ Settings")
    grade_level = st.selectbox("Grade Level", ["5th Grade", "6th Grade", "7th Grade", "8th Grade", "High School"])
    subject_focus = st.multiselect("Topic", ["Algebra", "Geometry", "Arithmetic"], default=["Algebra"])

# Input Tabs
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
    text_val = st.text_area("Enter Math Problem", placeholder="e.g., 2x + 10 = 30", key="text_input")
    if text_val: input_text = text_val

# --- SOLVER LOGIC ---
if st.button("🚀 Start Interactive Solve", use_container_width=True):
    # Reset EVERYTHING
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

    # --- SYSTEM PROMPT (The "Quiz Master") ---
    SYSTEM_INSTRUCTION = r"""
    You are Mathful, an Interactive Math Tutor.
    
    GOAL: Break the problem into steps. For each step, provide the CORRECT next move and 2 INCORRECT "distractor" moves.
    
    OUTPUT FORMAT: JSON ONLY.
    Structure:
    [
      {
        "math_display": "LaTeX of the work AFTER this step is done (e.g. 2x = 20)",
        "question": "What is the best next step?",
        "options": [
          {"text": "Subtract 10 from both sides", "correct": true, "feedback": "Correct! We need to isolate the variable term."},
          {"text": "Divide by 2", "correct": false, "feedback": "Not yet. It's easier to move the constant (+10) first."},
          {"text": "Add 10 to both sides", "correct": false, "feedback": "Careful! It's +10, so adding more won't cancel it out."}
        ]
      },
      ... (repeat for all steps)
    ]
    
    RULES:
    1. "math_display": Use LaTeX. For vertical math, use '\begin{aligned}' or simple newlines '\\'.
    2. "options": Scramble the order if possible, but mark only one as "correct": true.
    3. If image is unsafe/non-math, return {"error": "..."}
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
            st.error("I got confused generating the quiz. Try a simpler problem!")

# --- DISPLAY LOGIC (The Game Loop) ---
if st.session_state.solution_data:
    steps = st.session_state.solution_data
    
    st.divider()
    
    # We display all steps up to the current progress
    # But only the "active" step gets the buttons. Previous steps show the success state.
    
    for i in range(len(steps)):
        # Only show step if we are ON this step or PAST it
        if i > st.session_state.step_count:
            break
            
        step = steps[i]
        is_current_step = (i == st.session_state.step_count)
        
        # Container for the Row
        with st.container():
            col_math, col_interaction = st.columns([1, 1])
            
            # 1. THE MATH (Left Side)
            with col_math:
                # Logic: If this step is solved (we are past it), show math
