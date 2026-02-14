import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Mathful Minds", page_icon="🧠")

# --- STYLE ---
st.markdown("""
    <style>
    .main-title {font-size: 3rem; font-weight: 800; color: #1E293B; text-align: center;}
    .subtitle {font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 2rem;}
    .stButton>button {width: 100%; background-color: #4F46E5; color: white;}
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("⚠️ Google API Key Missing. Enter it here:", type="password")

if not api_key:
    st.warning("Please enter your Google API Key to start.")
    st.stop()

# Configure Google Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- SYSTEM PROMPT ---
# We prepend this to every request to keep the AI focused
SYSTEM_INSTRUCTION = """
You are Mathful, an expert AI math tutor.
1. Use LaTeX for math expressions (e.g., $x^2$).
2. Ask guiding questions; do not solve immediately.
3. If an image is provided, analyze the handwriting carefully.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- UI ---
st.markdown('<div class="main-title">Mathful Minds</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Powered by Google Gemini (Free Tier)</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📸 Upload Photo", "⌨️ Type Problem"])

# --- TAB 1: UPLOAD ---
with tab1:
    uploaded_file = st.file_uploader("Upload a math problem", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        if st.button("Solve Image"):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": "Help me solve this math problem."})
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing handwriting..."):
                    # Gemini handles images natively + text instruction
                    response = model.generate_content([SYSTEM_INSTRUCTION, "Solve this:", image])
                    st.markdown(response.text)
                    
            # Add AI response to history
            st.session_state.messages.append({"role": "model", "content": response.text})

# --- TAB 2: TYPE ---
with tab2:
    text_input = st.text_area("Type your problem:")
    if st.button("Solve Text") and text_input:
        st.session_state.messages.append({"role": "user", "content": text_input})
        
        with st.chat_message("assistant"):
             with st.spinner("Thinking..."):
                response = model.generate_content([SYSTEM_INSTRUCTION, text_input])
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "model", "content": response.text})
