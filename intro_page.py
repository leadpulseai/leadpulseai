import streamlit as st
import time
from typing import Dict, List, Optional
import json
import base64

def load_config():
    """Load configuration settings from file."""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_config()

def get_default_config():
    """Return default configuration."""
    return {
        "branding": {
            "name": "Lia",
            "logo_url": "⚡",
            "primary_color": "#3B82F6",
            "secondary_color": "#1E1E1E",
            "font_family": "Segoe UI, sans-serif"
        },
        "intro": {
            "enabled": True,
            "show_once_per_session": True,
            "animation_speed": "medium"
        },
        "intro_description": "An AI assistant that levels up your lead generation.",
        "supported_languages": [
            {"code": "en", "display_name": "English"},
            {"code": "zh", "display_name": "中文"},
            {"code": "es", "display_name": "Español"}
        ]
    }

def render_intro_page():
    """Render the intro page using Streamlit native components."""
    config = load_config()
    
    # Apply custom styling for the background and general text
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(135deg, {config["branding"]["secondary_color"]} 0%, #2d2d2d 100%);
            color: white;
            font-family: {config["branding"]["font_family"]};
        }}
        .stButton>button {{
            background-color: {config["branding"]["primary_color"]};
            color: white;
            border-radius: 20px;
            border: none;
            font-weight: 600;
            padding: 0.8rem 1.5rem;
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            opacity: 0.8;
            transform: translateY(-2px);
        }}
        h1 {{
            font-family: 'Dancing Script', cursive;
            font-size: 5rem;
            color: white;
            text-shadow: 0 0 30px rgba(255,255,255,0.8), 0 0 60px rgba(255,255,255,0.4);
            margin-bottom: 0.5rem;
        }}
        .level-up-text {{
            font-family: 'Courier Prime', monospace;
            font-size: 1.8rem;
            font-weight: 700;
            color: #ccc;
            margin-top: 0;
        }}
        .description-text {{
            font-size: 1.3rem;
            max-width: 600px;
            line-height: 1.6;
            margin-top: 2rem;
        }}
        .language-selector-label {{
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }}
        </style>
        """, 
        unsafe_allow_html=True
    )

    # Center content using columns
    col1, col2, col3 = st.columns([1, 4, 1])

    with col2:
        st.write("<div style=\'text-align: center;\'>", unsafe_allow_html=True)
        
        # Lightning bolt logo
        st.markdown(f"<div style=\'font-size: 4rem; color: {config["branding"]["primary_color"]}; margin-bottom: 1rem;\'>{config["branding"]["logo_url"]}</div>", unsafe_allow_html=True)
        
        # Lia text (simulated animation with st.empty and time.sleep)
        lia_placeholder = st.empty()
        lia_text = "lia"
        for i in range(len(lia_text) + 1):
            lia_placeholder.markdown(f"<h1 class=\'lia-text\'>{lia_text[:i]}</h1>", unsafe_allow_html=True)
            time.sleep(0.1) # Adjust speed as needed
        
        # Level Up text
        st.markdown("<div class=\'level-up-text\'>LEVEL UP</div>", unsafe_allow_html=True)
        
        # Description
        st.markdown(f"<p class=\'description-text\'>{config["intro_description"]}</p>", unsafe_allow_html=True)
        
        st.markdown("<p class=\'language-selector-label\'>Choose your language:</p>", unsafe_allow_html=True)
        
        # Language selection buttons
        lang_cols = st.columns(len(config["supported_languages"]))
        for i, lang in enumerate(config["supported_languages"]):
            with lang_cols[i]:
                if st.button(lang["display_name"], key=f"lang_btn_{lang["code"]}"):
                    st.session_state.language = lang["code"]
                    st.session_state.show_intro = False
                    st.rerun()
        
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Start Chatting with Lia", key="start_chat_btn"):
            st.session_state.show_intro = False
            st.rerun()
            
        st.write("</div>", unsafe_allow_html=True)

def should_show_intro():
    """Check if intro should be shown."""
    config = load_config()
    
    if not config["intro"]["enabled"]:
        return False
    
    if config["intro"]["show_once_per_session"]:
        return st.session_state.get("show_intro", True)
    
    return True