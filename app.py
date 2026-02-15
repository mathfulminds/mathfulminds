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
        background: -webkit-linear-gradient(45deg, #6a11cb, #2575fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    
    /* Math Card (Left) */
    .math-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #6a11cb;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }

    /* Hint Card (Right) */
    .hint-card {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #2575fc;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        font-size: 0.95rem;
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

# --- SESSION STATE (The Memory) ---
if "profile" not in st.session_state:
    st.session_state.profile = {"Algebra": 0, "Geometry": 0, "Arithmetic": 0}
if "history" not in st.session_state:
    st.session_state.history = []

# --- SIDEBAR: LEARNING PROFILE ---
with st.sidebar:
    st.header("👤 Student Profile")
    
    # 1. Grade Selector
    grade_level = st.selectbox("Grade Level", ["5th Grade", "6th Grade", "7th Grade", "8th Grade", "High School"])
    
    # 2. Topic Focus
    subject_focus = st.multiselect("Focus Area", ["Algebra", "Geometry", "Word Problems"], default=["Algebra"])
    
    st.divider()
    
    # 3. Live Stats
    st.subheader("Your Strength Stats")
    for subject, count in st.session_state.profile.items():
        st.write(f"**{subject}:** {count} solved")
        st.progress(min(count * 10, 100)) # Simple visual bar

# --- HELPER FUNCTIONS ---
def text_to_speech(text):
    """Generates audio from text for Voice Mode"""
    try:
        tts = gTTS(text=text, lang='en')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except:
        return None

def update_profile(topic):
    """Updates the session profile"""
    if topic in st.session_state.profile:
        st.session_state.profile[topic] += 1
    else:
        st.session_state.profile[topic] = 1

# --- MAIN UI ---
st.markdown('<div class="main-title">Mathful Minds</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Step-by-step learning. No copying.</p>', unsafe_allow_html=True)

# Tabs
tab_photo, tab_draw, tab_type = st.tabs(["📸 Photo", "✏️ Draw", "⌨️ Type"])

user_input = None
image_input = None

with tab_photo:
    uploaded_file = st.file_uploader("Upload a math photo", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image_input = Image.open(uploaded_file)
        st.image(image_input, width=300)

with tab_draw:
    st.write("Draw your math problem here:")
    canvas_result = st_canvas(
        fill_color="#ffffff",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#ffffff",
        height=300,
        width=600,
        drawing_mode="freedraw",
        key="canvas",
    )
    if canvas_result.image_data is not None:
        # Convert canvas to image for AI
        image_input = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert('RGB')

with tab_type:
    text_area = st.text_area("Type your problem here:")
    if text_area:
        user_input = text_area

# --- SOLVER BUTTON ---
if st.button("🚀 Solve with Mathful", use_container_width=True):
    
    if not (user_input or image_input or (canvas_result.image_data is not None and len(canvas_result.json_data["objects"]) > 0)):
        st.warning("Please upload, draw, or type a problem first!")
        st.stop()

    # SYSTEM PROMPT: Forces JSON format for Split Screen
    SYSTEM_INSTRUCTION = f"""
    You are Mathful, a tutor for {grade_level} students.
    
    CRITICAL INSTRUCTION:
    You must respond in valid JSON format ONLY. Do not write normal text.
    The JSON must be a list of steps. 
    Each step must have two fields:
    1. "math": The equation or numbers (LaTeX format).
    2. "hint": A very concise explanation (under 15 words) of WHY we did this step.
    
    Example format:
    [
        {{"math": "3x + 5 = 20", "hint": "This is our starting equation."}},
        {{"math": "3x = 15", "hint": "Subtract 5 from both sides to isolate terms."}},
        {{"math": "x = 5", "hint": "Divide by 3 to find the answer."}}
    ]
    """

    model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)
    
    with st.spinner("Analyzing..."):
        try:
            # Prepare inputs
            inputs = [f"Solve this. Focus on {subject_focus}."]
            if image_input:
                inputs.append(image_input)
            elif user_input:
                inputs.append(user_input)
                
            response = model.generate_content(inputs)
            
            # Extract JSON from response
            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            steps = json.loads(cleaned_text)
            
            # --- DISPLAY SPLIT SCREEN ---
            st.divider()
            
            # Header Row
            c1, c2 = st.columns([1, 1])
            c1.markdown("### 📝 The Math")
            c2.markdown("### 💡 The Logic")

            for i, step in enumerate(steps):
                # We use an expander or container for each step
                with st.container():
                    col_left, col_right = st.columns([1, 1])
                    
                    # LEFT: The Math
                    with col_left:
                        st.markdown(f'<div class="math-card">', unsafe_allow_html=True)
                        st.latex(step['math'])
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    # RIGHT: The Concise Hint
                    with col_right:
                        st.markdown(f'<div class="hint-card"><b>Step {i+1}:</b> {step["hint"]}</div>', unsafe_allow_html=True)
                        # Voice Button
                        audio = text_to_speech(step['hint'])
                        if audio:
                            st.audio(audio, format='audio/mp3')

            # Update Profile (Simulated Logic)
            if "Algebra" in str(steps): update_profile("Algebra")
            elif "Geometry" in str(steps): update_profile("Geometry")
            else: update_profile("Arithmetic")
            
        except Exception as e:
            st.error("Oops! The AI got confused. Try creating a clearer image.")
            st.caption(f"Debug Info: {e}")
