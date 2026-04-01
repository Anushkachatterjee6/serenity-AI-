import streamlit as st
import streamlit.components.v1 as components
import os
import base64

# 1. Page Config MUST be first
st.set_page_config(page_title="Serenity AI", page_icon="🌿", layout="wide")

@st.cache_data
def load_app_html():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "dist", "index.html")
    if not os.path.exists(index_path):
        return None
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    # Diagnostic Status in Sidebar
    st.sidebar.title("🌿 Serenity AI Live")
    
    html_content = load_app_html()
    
    if not html_content:
        st.error("🚀 **Assets not found in `dist/`.** Please check your GitHub repo.")
        return

    # Injected Secrets
    url = st.secrets.get("VITE_SUPABASE_URL", st.secrets.get("VITE_SUPABASE_PROJECT_ID", ""))
    if url and "https://" not in url:
        url = f"https://{url}.supabase.co"
    key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")
    
    # Status Check
    if url and key:
        st.sidebar.success("✅ Connection: Ready")
    else:
        st.sidebar.warning("⚠️ Connection: Missing Keys")

    # Perform the dynamic replacement
    html_content = html_content.replace("%%SUPABASE_URL%%", url)
    html_content = html_content.replace("%%SUPABASE_KEY%%", key)

    # Convert to Base64 to bypass platform-specific iframe limits
    b64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    src_data = f"data:text/html;base64,{b64_html}"

    # Render React UI using an absolute source URI
    components.iframe(src=src_data, height=1200, scrolling=True)

if __name__ == "__main__":
    main()