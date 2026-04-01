import streamlit as st
import streamlit.components.v1 as components
import os

# 1. Page Config MUST be first
st.set_page_config(page_title="Serenity AI", page_icon="🌿", layout="wide")

# 2. Hide Streamlit noise
st.markdown("<style>.block-container { padding: 0px; } footer {display:none;} header {display:none;}</style>", unsafe_allow_html=True)

@st.cache_data
def load_app_html():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "dist", "index.html")
    if not os.path.exists(index_path):
        return None
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    html_content = load_app_html()
    
    if not html_content:
        st.error("🚀 **Building Assets... Please Wait.**")
        st.info("The `dist/index.html` file was not found. Please ensure your GitHub repo has the `dist` folder.")
        return

    # Injected Secrets
    project_id = st.secrets.get("VITE_SUPABASE_PROJECT_ID", "")
    url = st.secrets.get("VITE_SUPABASE_URL", "")
    if project_id and not url:
        url = f"https://{project_id}.supabase.co"
    
    key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")
    
    # Perform the dynamic replacement
    html_content = html_content.replace("%%SUPABASE_URL%%", url)
    html_content = html_content.replace("%%SUPABASE_KEY%%", key)

    # Render React UI
    components.html(html_content, height=1200, scrolling=True)

if __name__ == "__main__":
    main()