import streamlit as st
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import time

# Default configuration
DEFAULT_CONFIG = {
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
    "welcome_message": "Hi! I'm Lia, your AI assistant from LeadPulse. How can I help you today?",
    "tone": "professional",
    "industry_template": "saas",
    "intro_description": "An AI assistant that levels up your lead generation.",
    "supported_languages": [
        {"code": "en", "display_name": "English"},
        {"code": "zh", "display_name": "中文"},
        {"code": "es", "display_name": "Español"}
    ],
    "lead_qualification": {
        "questions": {
            "budget": "What's your budget range for this project?",
            "timeline": "When are you looking to get started?",
            "decision_maker": "Are you the decision maker for this purchase?",
            "company_size": "How many employees does your company have?",
            "industry": "What industry is your business in?",
            "pain_point": "What's your biggest challenge right now?"
        },
        "scoring": {
            "email_provided": 30,
            "phone_provided": 20,
            "company_provided": 15,
            "budget_provided": 15,
            "timeline_provided": 10,
            "decision_maker_yes": 10
        }
    },
    "features": {
        "lead_capture": True,
        "visitor_engagement": True,
        "auto_qualification": True,
        "instant_answers": True,
        "data_storage": True,
        "time_saving": True
    },
    "admin": {
        "username": "admin",
        "password_hash": None,
        "email_notifications": True,
        "dashboard_enabled": True
    }
}

def save_config(config: Dict):
    """Save configuration to file."""
    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False

def load_config():
    """Load configuration from file or create default if not exists."""
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return merge_config(DEFAULT_CONFIG, config)
        except Exception as e:
            st.error(f"Error loading configuration: {e}")
            return DEFAULT_CONFIG
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def merge_config(default: Dict, user: Dict) -> Dict:
    """Merge user config with default config to ensure all keys exist."""
    result = default.copy()
    for key, value in user.items():
        if isinstance(value, dict) and key in result:
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result

def get_industry_template(template_name: str) -> Dict:
    """Get specific industry template."""
    templates = {
        "saas": {
            "name": "SaaS & Software",
            "business_type": "a SaaS company",
            "target_audience": "Business professionals and decision makers",
            "value_props": ["Scalable solutions", "Cost-effective", "Easy integration"]
        },
        "b2b": {
            "name": "B2B Services", 
            "business_type": "a B2B service provider",
            "target_audience": "Business owners and managers",
            "value_props": ["Professional expertise", "Proven results", "Custom solutions"]
        },
        "marketing": {
            "name": "Marketing Agency",
            "business_type": "a marketing agency", 
            "target_audience": "Businesses looking to grow",
            "value_props": ["Data-driven strategies", "Creative campaigns", "ROI focused"]
        },
        "general": {
            "name": "General Business",
            "business_type": "a business",
            "target_audience": "Potential customers",
            "value_props": ["Quality service", "Expert solutions", "Customer satisfaction"]
        }
    }
    return templates.get(template_name, templates["general"])

def get_tone_settings(tone_name: str) -> Dict:
    """Get specific tone settings."""
    tones = {
        "professional": {
            "name": "Professional",
            "description": "Formal, business-focused communication style",
            "style": "Professional and authoritative"
        },
        "friendly": {
            "name": "Friendly", 
            "description": "Warm, approachable, and conversational style",
            "style": "Friendly and approachable"
        },
        "casual": {
            "name": "Casual",
            "description": "Relaxed, informal, and easy-going style", 
            "style": "Casual and relaxed"
        }
    }
    return tones.get(tone_name, tones["friendly"])

def render_customization_dashboard(language: str):
    """Render the customization settings dashboard."""
    st.header("🎨 Customization & Branding")
    
    config = load_config()
    
    # Branding Settings
    with st.expander("🏷️ Branding Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            config["branding"]["name"] = st.text_input(
                "Assistant Name", 
                config["branding"]["name"],
                help="The name of your AI assistant"
            )
            config["branding"]["primary_color"] = st.color_picker(
                "Primary Color", 
                config["branding"]["primary_color"],
                help="Main brand color"
            )
        
        with col2:
            config["branding"]["logo_url"] = st.text_input(
                "Logo/Emoji", 
                config["branding"]["logo_url"],
                help="Logo or emoji"
            )
            config["branding"]["secondary_color"] = st.color_picker(
                "Secondary Color", 
                config["branding"]["secondary_color"],
                help="Background color"
            )
    
    # Save Settings
    if st.button("💾 Save Settings", type="primary"):
        if save_config(config):
            st.success("✅ Settings saved!")
            st.rerun()
        else:
            st.error("❌ Failed to save settings")
    
    return config


