import streamlit as st
import streamlit.components.v1 as components
import os
import base64

# 1. Page Config
st.set_page_config(page_title="Serenity AI", page_icon="🌿", layout="wide")

# Hide focus bar and sidebar
st.markdown("<style>.block-container { padding: 0px; } footer {display:none;} header {display:none;}</style>", unsafe_allow_html=True)

@st.cache_data
def load_app_html():
    # Use the latest build which has HashRouter and ComponentReady signals
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "dist", "index.html")
    
    if not os.path.exists(index_path):
        return None
        
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    html_content = load_app_html()
    
    if not html_content:
        st.error("🚀 **Error: Build files missing.** Please re-run the build.")
        return

    # Injected Secrets
    project_id = st.secrets.get("VITE_SUPABASE_PROJECT_ID", "")
    url = st.secrets.get("VITE_SUPABASE_URL", "")
    if project_id and not url:
        url = f"https://{project_id}.supabase.co"
    key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")

    # Perform the dynamic replacement directly in the HTML
    html_content = html_content.replace("%%SUPABASE_URL%%", url)
    html_content = html_content.replace("%%SUPABASE_KEY%%", key)

    # Encode to Base64 to bypass iframe limits
    b64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    src_data = f"data:text/html;base64,{b64_html}"

    # Render - Using the successful HashRouter+Ready build
    components.html(html_content, height=1200, scrolling=True)

if __name__ == "__main__":
    main()