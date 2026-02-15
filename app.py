import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import json
import time

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
    
    /* MATH CONTAINER */
    .math-container {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        font-size: 1.3rem;
        text-align: center;
        min-height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* BLURRED TEXT */
    .blur-text {
        color: transparent;
        text-shadow: 0 0 15px rgba(0,0,0,0.3);
        user-select: none;
    }
    
    /* FEEDBACK BOXES */
    .success-box {
        padding: 1rem;
        background-color: #DCFCE7;
        border: 1px solid #16A34A;
        border-radius: 0.5rem;
        color: #14532D;
        margin-bottom: 1rem;
    }
    
    .error-box {
        padding: 1rem;
        background-color: #FEE2E2;
        border: 1px solid #DC2626;
        border-radius: 0.5rem;
        color: #7F1D1D;
        margin-bottom: 1rem;
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
# Dictionary to store user choices: { step_index: { "choice": idx, "correct": bool } }
if "interactions" not in st.session_state: st.session_state.interactions = {}

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
                input_image = Image.fromarray(canvas_result.image_data.)
