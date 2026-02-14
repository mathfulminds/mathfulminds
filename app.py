import streamlit as st
from openai import OpenAI
import base64

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

# --- AUTHENTICATION (The Fix) ---
# Check if the key is in the "Vault" (Secrets)
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    # If not in vault, ask for it in the sidebar
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")

if not api_key:
    st.warning("⚠️ key missing. Please add it to Secrets or the Sidebar.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are Mathful, an expert AI math tutor.
1. Use LaTeX for math ($x^2$).
2. Ask guiding questions; do not solve immediately.
3. Watch for misconceptions in Ratios & Proportions.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- UI ---
st.markdown('<div class="main-title">Mathful Minds</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI Tutor for Middle School Math</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📸 Upload Photo", "⌨️ Type Problem"])

with tab1:
    uploaded_file = st.file_uploader("Upload a math problem", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image")
        if st.button("Solve Image"):
            base64_image = encode_image(uploaded_file)
            st.session_state.messages.append({
                "role": "user",
                "content": [{"type": "text", "text": "Help me solve this."}, 
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]
            })
            with st.chat_message("assistant"):
                stream = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages, stream=True)
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

with tab2:
    text_input = st.text_area("Type your problem:")
    if st.button("Solve Text") and text_input:
        st.session_state.messages.append({"role": "user", "content": text_input})
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages, stream=True)
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
