import streamlit as st
import streamlit.components.v1 as components
import os

# 1. Page Config MUST be first
st.set_page_config(page_title="Serenity AI", page_icon="🌿", layout="wide")

def main():
    try:
        # Use Native Static Component Hosting (The "Standard" Way)
        # This fixes the "Black Screen" locally by allowing browser to fetch relative assets
        base_dir = os.path.dirname(os.path.abspath(__file__))
        build_dir = os.path.join(base_dir, "component", "dist")
        
        if not os.path.exists(build_dir):
            build_dir = os.path.join(base_dir, "dist")

        if not os.path.exists(build_dir):
            st.error("🚀 **Error: Build files missing.** Please re-run the build.")
            return

        # Declare
        serenity_ui = components.declare_component("serenity_ai_final", path=build_dir)

        # Injected Secrets
        project_id = st.secrets.get("VITE_SUPABASE_PROJECT_ID", "")
        url = st.secrets.get("VITE_SUPABASE_URL", "")
        if project_id and not url:
            url = f"https://{project_id}.supabase.co"
        key = st.secrets.get("VITE_SUPABASE_PUBLISHABLE_KEY", "")
        
        # Display Status
        st.sidebar.title("🌿 Serenity AI Live")
        if url and key:
            st.sidebar.success("✅ Connection: Ready")
        else:
            st.sidebar.warning("⚠️ Connection: Missing Keys")

        # Hide padding
        st.markdown("<style>.block-container { padding: 0px; }</style>", unsafe_allow_html=True)

        # Render with the official parameters
        serenity_ui(sb_url=url, sb_key=key, height=1200)

    except Exception as e:
        st.error(f"❌ **System Error:** {str(e)}")

if __name__ == "__main__":
    main()