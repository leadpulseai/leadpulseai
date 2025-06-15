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

def get_intro_css():
    """Return CSS for the intro page."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&family=Courier+Prime:wght@400;700&display=swap');
    
    .intro-container {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
    }
    
    .background-elements {
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: 1;
        opacity: 0.15;
        pointer-events: none;
    }
    
    .sketch-element {
        position: absolute;
        color: #666;
        font-size: 2rem;
        animation: float 6s ease-in-out infinite;
    }
    
    .sketch-element:nth-child(1) { top: 10%; left: 10%; animation-delay: 0s; }
    .sketch-element:nth-child(2) { top: 20%; right: 15%; animation-delay: 1s; }
    .sketch-element:nth-child(3) { bottom: 30%; left: 20%; animation-delay: 2s; }
    .sketch-element:nth-child(4) { bottom: 20%; right: 10%; animation-delay: 3s; }
    .sketch-element:nth-child(5) { top: 50%; left: 5%; animation-delay: 4s; }
    .sketch-element:nth-child(6) { top: 60%; right: 5%; animation-delay: 5s; }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    .main-content {
        z-index: 10;
        position: relative;
    }
    
    .lightning-logo {
        font-size: 4rem;
        color: #3B82F6;
        margin-bottom: 1rem;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    .lia-text {
        font-family: 'Dancing Script', cursive;
        font-size: 5rem;
        font-weight: 700;
        color: white;
        text-shadow: 0 0 30px rgba(255,255,255,0.8), 0 0 60px rgba(255,255,255,0.4);
        margin: 0;
        opacity: 0;
        animation: fadeInSpotlight 3s ease-out forwards;
    }
    
    @keyframes fadeInSpotlight {
        0% { 
            opacity: 0; 
            transform: scale(0.5);
            text-shadow: 0 0 0 rgba(255,255,255,0);
        }
        50% { 
            opacity: 0.7; 
            transform: scale(0.8);
            text-shadow: 0 0 20px rgba(255,255,255,0.6);
        }
        100% { 
            opacity: 1; 
            transform: scale(1);
            text-shadow: 0 0 30px rgba(255,255,255,0.8), 0 0 60px rgba(255,255,255,0.4);
        }
    }
    
    .level-up-text {
        font-family: 'Courier Prime', monospace;
        font-size: 1.8rem;
        font-weight: 700;
        color: #ccc;
        margin-top: 1rem;
        opacity: 0;
        animation: typewriter 2s steps(8) 3.5s forwards;
        border-right: 2px solid #ccc;
        white-space: nowrap;
        overflow: hidden;
        width: 0;
    }
    
    @keyframes typewriter {
        0% { width: 0; }
        100% { width: 8ch; }
    }
    
    .description {
        margin-top: 3rem;
        font-size: 1.3rem;
        max-width: 600px;
        line-height: 1.6;
        opacity: 0;
        animation: fadeInUp 1s ease-out 5s forwards;
    }
    
    @keyframes fadeInUp {
        0% { 
            opacity: 0; 
            transform: translateY(30px);
        }
        100% { 
            opacity: 1; 
            transform: translateY(0);
        }
    }
    
    .language-selector {
        margin-top: 3rem;
        opacity: 0;
        animation: fadeInUp 1s ease-out 6s forwards;
    }
    
    .language-btn {
        background: transparent;
        border: 2px solid rgba(255,255,255,0.3);
        color: white;
        padding: 0.8rem 1.5rem;
        margin: 0 0.5rem;
        border-radius: 25px;
        cursor: pointer;
        font-size: 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .language-btn:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: #3B82F6;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.3);
    }
    
    .start-chat-btn {
        background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
        border: none;
        color: white;
        padding: 1rem 2rem;
        margin-top: 2rem;
        border-radius: 30px;
        cursor: pointer;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        opacity: 0;
        animation: fadeInUp 1s ease-out 7s forwards;
    }
    
    .start-chat-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
    }
    
    /* Hide Streamlit elements */
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .lia-text {
            font-size: 3.5rem;
        }
        .level-up-text {
            font-size: 1.4rem;
        }
        .description {
            font-size: 1.1rem;
            padding: 0 1rem;
        }
        .language-btn {
            padding: 0.6rem 1rem;
            margin: 0.3rem;
            font-size: 0.9rem;
        }
    }
    </style>
    """

def get_background_elements():
    """Return SVG background elements."""
    return """
    <div class="background-elements">
        <div class="sketch-element">↗</div>
        <div class="sketch-element">🎯</div>
        <div class="sketch-element">📈</div>
        <div class="sketch-element">⚡</div>
        <div class="sketch-element">🚀</div>
        <div class="sketch-element">💡</div>
    </div>
    """

def render_intro_page():
    """Render the intro page with Apple-style animation."""
    config = load_config()
    
    # Apply custom CSS
    st.markdown(get_intro_css(), unsafe_allow_html=True)
    
    # Hide Streamlit UI elements
    st.markdown("""
    <style>
    .stApp > header {
        background-color: transparent;
    }
    .stDeployButton {
        display: none;
    }
    .stDecoration {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the intro page container
    intro_html = f"""
    <div class="intro-container">
        {get_background_elements()}
        
        <div class="main-content">
            <div class="lightning-logo">{config['branding']['logo_url']}</div>
            <h1 class="lia-text">lia</h1>
            <div class="level-up-text">LEVEL UP</div>
            <p class="description">{config['intro_description']}</p>
            
            <div class="language-selector">
                <p style="margin-bottom: 1rem; font-size: 1.1rem;">Choose your language:</p>
    """
    
    # Add language buttons
    for lang in config['supported_languages']:
        intro_html += f"""
                <button class="language-btn" onclick="selectLanguage('{lang['code']}')">{lang['display_name']}</button>
        """
    
    intro_html += """
            </div>
            
            <button class="start-chat-btn" onclick="startChat()">Start Chatting with Lia</button>
        </div>
    </div>
    
    <script>
    function selectLanguage(langCode) {
        // Store language selection
        sessionStorage.setItem('selectedLanguage', langCode);
        
        // Highlight selected button
        const buttons = document.querySelectorAll('.language-btn');
        buttons.forEach(btn => btn.style.background = 'transparent');
        event.target.style.background = 'rgba(59, 130, 246, 0.3)';
        event.target.style.borderColor = '#3B82F6';
    }
    
    function startChat() {
        // This will be handled by Streamlit
        const selectedLang = sessionStorage.getItem('selectedLanguage') || 'en';
        
        // Create a custom event to communicate with Streamlit
        const event = new CustomEvent('startChat', { 
            detail: { language: selectedLang } 
        });
        window.dispatchEvent(event);
        
        // For now, we'll use a simple approach
        window.parent.postMessage({
            type: 'startChat',
            language: selectedLang
        }, '*');
    }
    </script>
    """
    
    st.markdown(intro_html, unsafe_allow_html=True)
    
    # Add language selection buttons using Streamlit
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col2:
        if st.button("English", key="lang_en", help="Select English"):
            st.session_state.language = "en"
            st.session_state.show_intro = False
            st.rerun()
    
    with col3:
        if st.button("中文", key="lang_zh", help="Select Chinese"):
            st.session_state.language = "zh"
            st.session_state.show_intro = False
            st.rerun()
    
    with col4:
        if st.button("Español", key="lang_es", help="Select Spanish"):
            st.session_state.language = "es"
            st.session_state.show_intro = False
            st.rerun()
    
    # Add a skip intro button for testing
    if st.button("Skip Intro", key="skip_intro"):
        st.session_state.show_intro = False
        st.rerun()

def should_show_intro():
    """Check if intro should be shown."""
    config = load_config()
    
    if not config["intro"]["enabled"]:
        return False
    
    if config["intro"]["show_once_per_session"]:
        return st.session_state.get("show_intro", True)
    
    return True