import streamlit as st
import os
from component import serenity_ai_app

# 1. Page Config MUST be first
st.set_page_config(page_title="Serenity AI", page_icon="🌿", layout="wide")

# 2. Hide Streamlit noise
st.markdown("<style>.block-container { padding: 0px; } footer {display:none;} header {display:none;}</style>", unsafe_allow_html=True)

def main():
    # Injected Secrets
    project_id = st.secrets.get("VITE_SUPABASE_PROJECT_ID", "")
    url = st.secrets.get("VITE_SUPABASE_URL", "")
    if project_id and not url:
        url = f"https://{project_id}.supabase.co"
    
    key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")
    
    # Render the Static Component (Bypasses Websocket Limits)
    # We pass these as props which will be available to React
    serenity_ai_app(url=url, supabase_key=key)

if __name__ == "__main__":
    main()