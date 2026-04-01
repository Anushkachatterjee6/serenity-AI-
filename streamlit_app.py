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
        st.error(f"❌ Critical Error: `dist/index.html` not found at {index_path}")
        return

    with open(index_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Get secrets from Streamlit Cloud dashboard
    project_id = st.secrets.get("VITE_SUPABASE_PROJECT_ID", "")
    supabase_url = st.secrets.get("VITE_SUPABASE_URL", "")
    supabase_key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")
    
    # Auto-construct URL if user provided Project ID instead of full URL
    if project_id and not supabase_url:
        supabase_url = f"https://{project_id}.supabase.co"
    
    # MASKED LOGGING FOR UI
    st.sidebar.write(f"Supabase Status: {'✅ Ready' if (supabase_url and supabase_key) else '❌ Not Ready'}")
    if not supabase_url or not supabase_key:
        st.sidebar.info("Hint: Add VITE_SUPABASE_URL or VITE_SUPABASE_PROJECT_ID to Secrets")
    
    # Inject Error Catcher to see why it's blank
    error_catcher = """
    <script>
    window.onerror = function(msg, url, line, col, error) {
        var div = document.createElement('div');
        div.style.color = 'red';
        div.style.padding = '20px';
        div.style.background = 'white';
        div.innerHTML = '<h3>❌ JS Runtime Error:</h3>' + msg + '<br>Line: ' + line;
        document.body.prepend(div);
    };
    </script>
    """
    html_content = html_content.replace("<head>", "<head>" + error_catcher)

    html_content = html_content.replace("%%SUPABASE_URL%%", supabase_url)
    html_content = html_content.replace("%%SUPABASE_KEY%%", supabase_key)

    # Render the React component
    try:
        components.html(html_content, height=1200, scrolling=True)
    except Exception as e:
        st.error(f"Render Fail: {str(e)}")

if __name__ == "__main__":
    main()