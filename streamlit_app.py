import streamlit as st
import streamlit.components.v1 as components
import os

# Configure the Streamlit page to be as non-intrusive as possible
st.set_page_config(
    page_title="Serenity AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to hide Streamlit's default UI elements (header, footer, padding)
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
            max-width: 100%;
        }
        iframe {
            border: none;
            width: 100vw;
            height: 100vh;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    # Use st.container to ensure content is properly structured
    container = st.container()
    
    try:
        # Load the massive compiled single-file React app output from Vite
        # Normalize path for Streamlit Cloud's Linux environment
        base_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(base_dir, "dist", "index.html")
        
        if not os.path.exists(index_path):
            st.error(f"Deployment Error: dist/index.html not found at {index_path}")
            return
            
        with open(index_path, "r", encoding="utf-8") as file:
            html_content = file.read()
            
        # Dynamically inject API secrets to evade GitHub static scanning blocks
        # Provide fallback empty strings if secrets are not set in the cloud dashboard
        try:
            supabase_url = st.secrets["VITE_SUPABASE_URL"]
            supabase_key = st.secrets["VITE_SUPABASE_PUBLISHABLE_KEY"]
        except (KeyError, FileNotFoundError):
            supabase_url = ""
            supabase_key = ""
            st.warning("⚠️ Supabase secrets not detected. Please add them to Settings > Secrets.")
        
        html_content = html_content.replace("%%SUPABASE_URL%%", supabase_url)
        html_content = html_content.replace("%%SUPABASE_KEY%%", supabase_key)
            
        # Render the React UI natively within an iframe filling the entire window
        # Increased height and adjusted width to prevent clipping
        with container:
            components.html(html_content, height=1200, scrolling=True)
        
    except Exception as e:
        st.error(f"Unexpected Crash: {str(e)}")
        st.info("Check `npm run build` logs or report to developer.")

if __name__ == "__main__":
    main()
