import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from gtts import gTTS
import json
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Mathful Minds", page_icon="🧠", layout="wide")

# --- CUSTOM STYLE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: #1E293B;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Math Display (Left) */
    .math-text {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E293B;
        padding: 15px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        text-align: center;
    }

    /* Hint Box (Right) */
    .hint-box {
        background-color: #EFF6FF; /* Light Blue */
        border-left: 5px solid #3B82F6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        color: #1E3A8A;
        font-size: 1rem;
    }
    
    /* Reveal Button */
    .stButton button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
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
if "profile" not in st.session_state: st.session_state.profile = {"Algebra": 0, "Geometry": 0, "Arithmetic": 0}

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Profile")
    grade = st.selectbox("Grade", ["5th", "6th", "7th", "8th", "HS"])
    subject = st.multiselect("Focus", ["Algebra", "Geometry"], default=["Algebra"])
    st.divider()
    st.write("📊 **Stats:**")
    for s, c in st.session_state.profile.items():
        st.write(f"{s}: {c}")

# --- HELPER FUNCTIONS ---
def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except: return None

# --- MAIN UI ---
st.markdown('<div class="main-title">Mathful Minds</div>', unsafe_allow_html=True)

# Input Tabs
tab1, tab2, tab3 = st.tabs(["📸 Photo", "✏️ Draw", "⌨️ Type"])
user_input = None
image_input = None

with tab1:
    f = st.file_uploader("Upload", type=["png", "jpg"])
    if f: image_input = Image.open(f)

with tab2:
    canvas = st_canvas(stroke_width=3, stroke_color="#000", background_color="#fff", height=250, key="canvas")
    if canvas.image_data is not None:
        image_input = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA').convert('RGB')

with tab3:
    txt = st.text_area("Type problem (e.g., 2x + 10 = 30)")
    if txt: user_input = txt

# --- SOLVE LOGIC ---
if st.button("🚀 Solve It", use_container_width=True):
    # Reset state for new problem
    st.session_state.step_count = 0
    st.session_state.solution_data = None
    
    # 1. Input Check
    final_prompt = []
    if image_input:
        final_prompt = ["Analyze this image and solve the math problem inside it.", image_input]
    elif user_input:
        final_prompt = [f"The math problem is strictly: {user_input}. Solve this specific problem."]
    else:
        st.warning("Please provide a problem first!")
        st.stop()

    # 2. Strict System Prompt
    SYS_PROMPT = f"""
    You are a math tutor for {grade} grade.
    OUTPUT FORMAT: JSON Only. List of steps.
    Each step needs: "math" (LaTeX) and "hint" (Concise explanation).
    
    Example JSON structure:
    [
        {{"math": "2x + 10 = 30", "hint": "Subtract 10 from both sides."}},
        {{"math": "2x = 20", "hint": "Divide by 2."}},
        {{"math": "x = 10", "hint": "Final answer."}}
    ]
    """
    
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYS_PROMPT)
    
    with st.spinner("Thinking..."):
        try:
            response = model.generate_content(final_prompt)
            clean_json = response.text.strip().replace("```json", "").replace("```", "")
            st.session_state.solution_data = json.loads(clean_json)
            
            # Update stats
            if "x" in str(st.session_state.solution_data): 
                st.session_state.profile["Algebra"] += 1
                
        except:
            st.error("Could not read the problem. Please try again.")

# --- DISPLAY RESULTS (The "Method A" Reveal) ---
if st.session_state.solution_data:
    steps = st.session_state.solution_data
    
    st.divider()
    c1, c2 = st.columns([1, 1])
    c1.subheader("📝 The Math")
    c2.subheader("💡 The Logic")
    
    # Loop through ONLY the steps we have revealed so far
    # We use (step_count + 1) to show the current step
    steps_to_show = steps[:st.session_state.step_count + 1]
    
    for i, step in enumerate(steps_to_show):
        with st.container():
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                st.markdown(f'<div class="math-text">', unsafe_allow_html=True)
                st.latex(step['math'])
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_right:
                st.markdown(f'<div class="hint-box"><b>Step {i+1}:</b> {step["hint"]}</div>', unsafe_allow_html=True)
                # Optional Voice (Tiny player)
                audio = text_to_speech(step['hint'])
                if audio: st.audio(audio, format='audio/mp3')

    # "Show Next Step" Button
    if st.session_state.step_count < len(steps) - 1:
        if st.button("👇 Show Next Step"):
            st.session_state.step_count += 1
            st.rerun()
    else:
        st.success("🎉 Problem Solved!")
