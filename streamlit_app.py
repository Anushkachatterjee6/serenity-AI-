import streamlit as st
import streamlit.components.v1 as components
import os

# Ultra-simple Streamlit wrapper for React
st.set_page_config(page_title="Serenity AI", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
        .block-container { padding: 0px; }
        iframe { width: 100%; height: 100vh; border: none; }
    </style>
""", unsafe_allow_html=True)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "dist", "index.html")

    if not os.path.exists(index_path):
        st.error("Assets not found. Please wait for the build to finish.")
        return

    with open(index_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Inject secrets
    supabase_url = st.secrets.get("VITE_SUPABASE_URL", "")
    supabase_key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")
    
    html_content = html_content.replace("%%SUPABASE_URL%%", supabase_url)
    html_content = html_content.replace("%%SUPABASE_KEY%%", supabase_key)

    # Use the standard component which is most stable
    components.html(html_content, height=1200, scrolling=True)

if __name__ == "__main__":
    main()
