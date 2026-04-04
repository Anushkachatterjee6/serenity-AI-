import os
import streamlit.components.v1 as components

# Get the absolute path to the directory where this file is located
parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "dist")

# Declare the Streamlit component
_release_ready = components.declare_component("serenity_ai_app", path=build_dir)

def serenity_ai_app(url="", supabase_key="", key=None):
    """
    Renders the Serenity AI React application.
    Passes Supabase credentials as component props.
    """
    return _release_ready(url=url, supabase_key=supabase_key, key=key)
