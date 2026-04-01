import streamlit as st
import streamlit.components.v1 as components
import os

# 1. Page Config
st.set_page_config(page_title="Serenity AI", page_icon="🌿", layout="wide")

# Hide focus bar and sidebar padding
st.markdown("<style>.block-container { padding: 0px; } footer {display:none;} header {display:none;}</style>", unsafe_allow_html=True)

@st.cache_data
def load_app_html():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # We use the built file from dist/
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

    # Diagnostic Status in Sidebar
    st.sidebar.title("🌿 Serenity AI Live")
    
    # 1. Load Secrets Safely
    try:
        url = st.secrets.get("VITE_SUPABASE_URL", st.secrets.get("VITE_SUPABASE_PROJECT_ID", ""))
        key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")
    except:
        url = ""
        key = ""

    # Construct full URL if only project ID is given
    if url and "https://" not in url:
        url = f"https://{url}.supabase.co"
    
    # Status Check
    if url and key:
        st.sidebar.success("✅ Connection: Ready")
    else:
        st.sidebar.warning("⚠️ Connection: Missing Keys")
        st.sidebar.info("Please add secrets in Streamlit Cloud Settings > Secrets.")

    # Perform the dynamic replacement directly in the large HTML string
    # This is the most reliable way to ensure the React app sees the keys
    html_content = html_content.replace("%%SUPABASE_URL%%", url)
    html_content = html_content.replace("%%SUPABASE_KEY%%", key)

    # Render - This uses the established 'HashRouter' and 'ReadySignal' fixed build
    components.html(html_content, height=1200, scrolling=True)

if __name__ == "__main__":
    main()