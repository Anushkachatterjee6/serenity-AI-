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
    st.sidebar.title("🌿 Serenity AI System")
    
    # Diagnostic Check for the user to see what is happening in the Cloud
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "dist", "index.html")
    
    if st.sidebar.checkbox("Show Deployment Diagnostics"):
        st.sidebar.write(f"**Base Dir:** `{base_dir}`")
        st.sidebar.write(f"**Index Path:** `{index_path}`")
        st.sidebar.write(f"**File Exists:** `{os.path.exists(index_path)}`")
        if os.path.exists(index_path):
            st.sidebar.write(f"**File Size:** `{os.path.getsize(index_path)} bytes`")

    # Main Rendering Logic
    try:
        if not os.path.exists(index_path):
            st.error("🚀 **Deploying React Assets...**")
            st.info("The `dist/` folder was not found in the root. If you just pushed, please wait 30 seconds and Reboot.")
            return
            
        with open(index_path, "r", encoding="utf-8") as file:
            html_content = file.read()
            
        # Securely inject secrets from the Streamlit Dashboard
        try:
            supabase_url = st.secrets["VITE_SUPABASE_URL"]
            supabase_key = st.secrets["VITE_SUPABASE_PUBLISHABLE_KEY"]
            st.sidebar.success("✅ Supabase Keys Loaded")
        except Exception:
            supabase_url = ""
            supabase_key = ""
            st.sidebar.warning("⚠️ Missing Secrets: Go to Settings > Secrets")
        
        html_content = html_content.replace("%%SUPABASE_URL%%", supabase_url)
        html_content = html_content.replace("%%SUPABASE_KEY%%", supabase_key)
            
        # Render the React UI inside the Streamlit Frame
        # Using a height of 1000px as a safe standard
        components.html(html_content, height=1000, scrolling=True)
        
    except Exception as e:
        st.error(f"❌ **Rendering Error:** {str(e)}")

if __name__ == "__main__":
    main()
