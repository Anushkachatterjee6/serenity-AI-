import streamlit as st
import streamlit.components.v1 as components
import os
import base64

# EARLY LOGGING FOR DIAGNOSTICS
print("--- Serenity AI: Starting App ---")

# Configure the Streamlit page to be as non-intrusive as possible
st.set_page_config(
    page_title="Serenity AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to hide Streamlit's default UI elements
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding: 0px;
            max-width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.title("🌿 Serenity AI Diagnostics")
    
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(base_dir, "dist", "index.html")
        
        print(f"--- Looking for index at: {index_path} ---")
        
        if not os.path.exists(index_path):
            st.error("🚀 **Wait: Building AI Assets...**")
            st.info("The `dist/` folder was not found locally. Please ensure `npm run build` completed and you pushed the `dist` folder to GitHub.")
            return
            
        with open(index_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        
        print(f"--- Read {len(html_content)} bytes of HTML ---")
            
        # Securely inject secrets
        try:
            supabase_url = st.secrets["VITE_SUPABASE_URL"]
            supabase_key = st.secrets["VITE_SUPABASE_PUBLISHABLE_KEY"]
            st.sidebar.success("✅ Supabase Keys Active")
        except Exception as e:
            print(f"--- Secret Error: {str(e)} ---")
            supabase_url = ""
            supabase_key = ""
            st.sidebar.warning("⚠️ Warning: Go to Settings > Secrets")
        
        html_content = html_content.replace("%%SUPABASE_URL%%", supabase_url)
        html_content = html_content.replace("%%SUPABASE_KEY%%", supabase_key)
            
        # ADVANCED: Convert HTML to Base64 to bypass iframe rendering issues
        b64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
        src_data = f"data:text/html;base64,{b64_html}"
        
        # Render the large React app
        st.components.v1.iframe(src=src_data, height=1200, scrolling=True)
        
    except Exception as e:
        print(f"--- CRITICAL UI ERROR: {str(e)} ---")
        st.error(f"❌ **System Error:** {str(e)}")

print("--- Serenity AI: Main function ready ---")
if __name__ == "__main__":
    main()
