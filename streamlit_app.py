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
    try:
        # Load the massive compiled single-file React app output from Vite
        with open(os.path.join(os.path.dirname(__file__), "dist", "index.html"), "r", encoding="utf-8") as file:
            html_content = file.read()
            
        # Dynamically inject API secrets to evade GitHub static scanning blocks
        # Provide fallback empty strings to prevent client-side crashes if misconfigured in dashboard
        supabase_url = st.secrets.get("VITE_SUPABASE_URL", "")
        supabase_key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")
        
        html_content = html_content.replace("%%SUPABASE_URL%%", supabase_url)
        html_content = html_content.replace("%%SUPABASE_KEY%%", supabase_key)
            
        # Render the React UI natively within an iframe filling the entire window
        components.html(html_content, height=1200, scrolling=True)
        
    except FileNotFoundError:
        st.error("Deployment Error: The React app has not been compiled properly into the `dist/` directory.")
        st.info("Ensure `npm run build` generates `dist/index.html` via vite-plugin-singlefile.")

if __name__ == "__main__":
    main()
