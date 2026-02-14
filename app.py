import streamlit as st
import google.generativeai as genai
import importlib.metadata

st.set_page_config(page_title="Mathful Debugger", page_icon="🛠️")
st.title("🛠️ Mechanic Mode: Diagnostics")

# 1. Check Library Version
try:
    version = importlib.metadata.version("google-generativeai")
    st.info(f"installed google-generativeai version: **{version}**")
except:
    st.error("Could not determine library version.")

# 2. Check Connection & Models
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ No API Key found in Secrets!")
else:
    st.success("✅ API Key found.")
    genai.configure(api_key=api_key)
    
    st.write("Asking Google for available models...")
    try:
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)
        
        if models:
            st.success(f"Google responded! Found {len(models)} models.")
            st.json(models)
        else:
            st.warning("Google responded, but sent an empty list.")
            
    except Exception as e:
        st.error(f"❌ Connection Failed: {e}")
