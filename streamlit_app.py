import streamlit as st
import streamlit.components.v1 as components
import os
import shutil

# 1. Page Config MUST be first
st.set_page_config(page_title="Serenity AI", page_icon="🌿", layout="wide")

def main():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        build_dir = os.path.join(base_dir, "dist")
        
        # We'll use a specific folder for the live component to avoid race conditions with builds
        serve_dir = os.path.join(base_dir, "component", "dist")
        
        if not os.path.exists(build_dir):
            st.error("🚀 **Error: Build files missing.** Please re-run the build.")
            return

        # 1. Load Secrets
        url = st.secrets.get("VITE_SUPABASE_URL", st.secrets.get("VITE_SUPABASE_PROJECT_ID", ""))
        if url and "https://" not in url:
            url = f"https://{url}.supabase.co"
        key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")

        # 2. Sync and Inject (This is the bulletproof step)
        if not os.path.exists(serve_dir):
            os.makedirs(serve_dir, exist_ok=True)
            
        # Copy everything from dist to component/dist
        for item in os.listdir(build_dir):
            s = os.path.join(build_dir, item)
            d = os.path.join(serve_dir, item)
            if os.path.isdir(s):
                if os.path.exists(d): shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # 3. Perform the injection into the HTML file on disk
        index_path = os.path.join(serve_dir, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()
        
        # Hard-inject the actual values into the placeholders
        html = html.replace("%%SUPABASE_URL%%", url)
        html = html.replace("%%SUPABASE_KEY%%", key)
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 4. Declare the component from the injected directory
        serenity_ui = components.declare_component("serenity_ai_final", path=serve_dir)

        # Display Status
        st.sidebar.title("🌿 Serenity AI Live")
        if url and key:
            st.sidebar.success("✅ Connection: Ready")
        else:
            st.sidebar.warning("⚠️ Connection: Missing Keys")

        # Hide padding
        st.markdown("<style>.block-container { padding: 0px; }</style>", unsafe_allow_html=True)

        # Render
        serenity_ui(sb_url=url, sb_key=key, height=1200)

    except Exception as e:
        st.error(f"❌ **System Error:** {str(e)}")

if __name__ == "__main__":
    main()