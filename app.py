import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import json
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Mathful Minds", page_icon="📐", layout="wide")

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
    
    /* Math Container */
    .math-container {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        font-size: 1.3rem; /* Slightly larger math */
        text-align: center;
    }

    /* Hint Box */
    .hint-box {
        background-color: #FFFFFF;
        border: 2px solid #000000;
        color: #000000;
        padding: 15px;
        font-weight: 700;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 1rem;
        box-shadow: 4px 4px 0px #000000;
    }

    /* Buttons */
    .stButton button {
        background-color: #0F172A;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 10px 20px;
    }
    .stButton button:hover {
        background-color: #334155;
        color: white;
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
if "error_message" not in st.session_state: st.session_state.error_message = None

# --- HELPER: LATEX CLEANER ---
def clean_latex(latex_str):
    """
    Fixes common backslash issues that cause the 'Red Text' error.
    """
    if not latex_str: return ""
    # Ensure double backslashes for newlines and commands
    clean = latex_str.replace('\0', '') # Remove null bytes
    return clean

# --- MAIN UI ---
st.markdown('<div class="main-title">Mathful Minds</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #64748B;"><b>Step-by-Step.</b> No Shortcuts.</p>', unsafe_allow_html=True)

# Input Tabs
tab_photo, tab_draw, tab_type = st.tabs(["📸 Photo", "✏️ Draw", "⌨️ Type"])

input_image = None
input_text = None

with tab_photo:
    uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="photo_uploader")
    if uploaded_file: input_image = Image.open(uploaded_file)

with tab_draw:
    canvas_result = st_canvas(
        stroke_width=3, stroke_color="#000", background_color="#fff", 
        height=250, width=600, drawing_mode="freedraw", key="canvas"
    )
    if canvas_result.image_data is not None and canvas_result.json_data is not None:
         if len(canvas_result.json_data["objects"]) > 0:
            input_image = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert('RGB')

with tab_type:
    text_val = st.text_area("Enter Math Problem", placeholder="e.g., 3(x + 5) = 45", key="text_input")
    if text_val: input_text = text_val

# --- SOLVER LOGIC ---
if st.button("🚀 Solve It", use_container_width=True):
    st.session_state.step_count = 0
    st.session_state.solution_data = None
    st.session_state.error_message = None
    
    # Input Priority
    final_prompt_content = []
    if input_text:
        final_prompt_content = [f"Solve this math problem: {input_text}"]
    elif input_image:
        final_prompt_content = ["Solve the math problem in this image.", input_image]
    else:
        st.warning("⚠️ Please enter a problem or upload an image first!")
        st.stop()

    # --- SYSTEM PROMPT (Fixed for Vertical Alignment) ---
    SYSTEM_INSTRUCTION = r"""
    You are Mathful.
    
    1. **SAFETY CHECK**: 
       - If NON_MATH -> {"error": "NON_MATH"}
       - If UNSAFE -> {"error": "UNSAFE"}
    
    2. **FORMATTING (CRITICAL)**:
       - Return ONLY valid JSON.
       - "math": Use LaTeX.
       - **VERTICAL ALIGNMENT RULE**:
         When performing arithmetic on both sides (like -5 or /3), do NOT use the '\begin{array}' command directly.
         Instead, use standard LaTeX alignment with '\\' for new lines.
         Example of subtraction:
         "3x + 5 = 20 \\\\ \quad -5 \quad -5 \\\\ 3x = 15"
         
         Example of division:
         "\frac{3x}{3} = \frac{15}{3} \\\\ x = 5"
         
       - "hint": concise text (under 15 words).
       
    3. **RESPONSE STRUCTURE**:
       [
         {"math": "LaTeX string", "hint": "String"},
         {"math": "LaTeX string", "hint": "String"}
       ]
    """

    model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)
    
    with st.spinner("Analyzing..."):
        try:
            response = model.generate_content(final_prompt_content)
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_text)
            
            if isinstance(data, dict) and "error" in data:
                if data["error"] == "UNSAFE": st.session_state.error_message = "⛔ SHUTDOWN: Inappropriate content."
                elif data["error"] == "NON_MATH": st.session_state.error_message = "⚠️ Math questions only."
            else:
                st.session_state.solution_data = data
                
        except Exception as e:
            st.error("I couldn't read that. Please try writing it clearer!")

# --- DISPLAY LOGIC ---
if st.session_state.error_message:
    st.error(st.session_state.error_message)
    if "SHUTDOWN" in st.session_state.error_message: st.stop()

if st.session_state.solution_data:
    steps = st.session_state.solution_data
    current_step_idx = st.session_state.step_count
    
    st.divider()
    col_math, col_hint = st.columns([2, 1]) 
    
    for i in range(current_step_idx + 1):
        step = steps[i]
        
        with col_math:
            st.markdown(f'<div class="math-container">', unsafe_allow_html=True)
            # We use st.markdown with $$ for better compatibility than st.latex
            st.markdown(f"$${clean_latex(step['math'])}$$") 
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_hint:
            st.markdown(f'<div class="hint-box">{step["hint"]}</div>', unsafe_allow_html=True)

    if st.session_state.step_count < len(steps) - 1:
        if st.button("👉 Next Step", key="next_btn"):
            st.session_state.step_count += 1
            st.rerun()
    else:
        st.balloons()
        st.success("🎉 Great Job!")
        if st.button("Start New Problem"):
            st.session_state.solution_data = None
            st.session_state.step_count = 0
            st.rerun()
