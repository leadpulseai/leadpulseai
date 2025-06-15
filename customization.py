import streamlit as st
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

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
    "tone": "professional",  # Options: professional, friendly, casual
    "industry_template": "saas",  # Options: saas, b2b, marketing, general
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
        "password_hash": None,  # Will be set on first run
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
                # Merge with default config to ensure all keys exist
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

def get_industry_templates():
    """Return available industry templates."""
    return {
        "saas": {
            "name": "SaaS & Software",
            "description": "For software companies and SaaS businesses",
            "tone": "professional",
            "questions": [
                "What type of software solution are you looking for?",
                "How many users would need access?",
                "What's your current tech stack?",
                "When do you need to implement this solution?"
            ]
        },
        "b2b": {
            "name": "B2B Services",
            "description": "For business-to-business service providers",
            "tone": "professional",
            "questions": [
                "What services are you interested in?",
                "What's the size of your company?",
                "What's your timeline for this project?",
                "What's your budget range?"
            ]
        },
        "marketing": {
            "name": "Marketing Agency",
            "description": "For marketing agencies and consultants",
            "tone": "friendly",
            "questions": [
                "What marketing challenges are you facing?",
                "What's your current marketing budget?",
                "Which channels are you currently using?",
                "What are your growth goals?"
            ]
        },
        "ecommerce": {
            "name": "E-commerce",
            "description": "For online stores and e-commerce businesses",
            "tone": "friendly",
            "questions": [
                "What products are you interested in?",
                "Are you shopping for personal or business use?",
                "What's your budget range?",
                "When do you need this delivered?"
            ]
        },
        "consulting": {
            "name": "Consulting",
            "description": "For consultants and professional services",
            "tone": "professional",
            "questions": [
                "What type of consulting do you need?",
                "What's the scope of your project?",
                "What's your timeline?",
                "Have you worked with consultants before?"
            ]
        },
        "general": {
            "name": "General Business",
            "description": "For general business inquiries",
            "tone": "friendly",
            "questions": [
                "How can we help you today?",
                "What's your main goal?",
                "What's your timeline?",
                "What's your budget range?"
            ]
        }
    }

def get_tone_settings():
    """Return available tone settings."""
    return {
        "professional": {
            "name": "Professional",
            "description": "Formal, business-focused communication",
            "sample": "Good day! I'm here to assist you with your business needs. How may I help you today?"
        },
        "friendly": {
            "name": "Friendly",
            "description": "Warm, approachable, and conversational",
            "sample": "Hi there! I'm Lia, and I'm excited to help you out. What can I do for you today?"
        },
        "casual": {
            "name": "Casual",
            "description": "Relaxed, informal, and easy-going",
            "sample": "Hey! I'm Lia. What's up? How can I help you out?"
        }
    }

def render_customization_settings():
    """Render the customization settings in the admin dashboard."""
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
                help="Main brand color for buttons and highlights"
            )
            config["branding"]["font_family"] = st.selectbox(
                "Font Family",
                ["Segoe UI, sans-serif", "Arial, sans-serif", "Helvetica, sans-serif", "Georgia, serif"],
                index=0 if config["branding"]["font_family"] == "Segoe UI, sans-serif" else 0
            )
        
        with col2:
            config["branding"]["logo_url"] = st.text_input(
                "Logo/Emoji", 
                config["branding"]["logo_url"],
                help="URL to logo image or emoji character"
            )
            config["branding"]["secondary_color"] = st.color_picker(
                "Secondary Color", 
                config["branding"]["secondary_color"],
                help="Background and secondary elements color"
            )
    
    # Intro Page Settings
    with st.expander("🌟 Intro Page Settings"):
        config["intro"]["enabled"] = st.checkbox(
            "Enable Intro Page", 
            config["intro"]["enabled"],
            help="Show intro page before chat interface"
        )
        
        if config["intro"]["enabled"]:
            config["intro"]["show_once_per_session"] = st.checkbox(
                "Show Once Per Session", 
                config["intro"]["show_once_per_session"],
                help="Only show intro page once per browser session"
            )
            
            config["intro_description"] = st.text_area(
                "Intro Description", 
                config["intro_description"],
                help="Description text shown on intro page"
            )
            
            animation_options = {"slow": "Slow", "medium": "Medium", "fast": "Fast"}
            config["intro"]["animation_speed"] = st.selectbox(
                "Animation Speed",
                options=list(animation_options.keys()),
                format_func=lambda x: animation_options[x],
                index=list(animation_options.keys()).index(config["intro"]["animation_speed"])
            )
    
    # Conversation Settings
    with st.expander("💬 Conversation Settings"):
        config["welcome_message"] = st.text_area(
            "Welcome Message", 
            config["welcome_message"],
            help="First message shown to users"
        )
        
        tone_options = get_tone_settings()
        selected_tone = st.selectbox(
            "Conversation Tone",
            options=list(tone_options.keys()),
            format_func=lambda x: f"{tone_options[x]['name']} - {tone_options[x]['description']}",
            index=list(tone_options.keys()).index(config["tone"])
        )
        config["tone"] = selected_tone
        
        # Show sample message for selected tone
        st.info(f"Sample message: {tone_options[selected_tone]['sample']}")
    
    # Industry Template Settings
    with st.expander("🏢 Industry Template"):
        industry_options = get_industry_templates()
        selected_industry = st.selectbox(
            "Industry Template",
            options=list(industry_options.keys()),
            format_func=lambda x: f"{industry_options[x]['name']} - {industry_options[x]['description']}",
            index=list(industry_options.keys()).index(config["industry_template"])
        )
        config["industry_template"] = selected_industry
        
        # Show template details
        template = industry_options[selected_industry]
        st.info(f"Template: {template['name']}")
        st.write("**Sample Questions:**")
        for question in template["questions"]:
            st.write(f"• {question}")
    
    # Lead Qualification Settings
    with st.expander("🎯 Lead Qualification"):
        st.subheader("Qualification Questions")
        
        for key, question in config["lead_qualification"]["questions"].items():
            config["lead_qualification"]["questions"][key] = st.text_input(
                f"{key.replace('_', ' ').title()} Question",
                question
            )
        
        st.subheader("Lead Scoring")
        st.write("Points awarded for different lead information:")
        
        for key, score in config["lead_qualification"]["scoring"].items():
            config["lead_qualification"]["scoring"][key] = st.number_input(
                f"{key.replace('_', ' ').title()}",
                min_value=0,
                max_value=50,
                value=score,
                step=5
            )
    
    # Language Settings
    with st.expander("🌍 Language Settings"):
        st.subheader("Supported Languages")
        
        # Display current languages
        for i, lang in enumerate(config["supported_languages"]):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                lang["code"] = st.text_input(f"Language Code {i+1}", lang["code"], key=f"lang_code_{i}")
            with col2:
                lang["display_name"] = st.text_input(f"Display Name {i+1}", lang["display_name"], key=f"lang_name_{i}")
            with col3:
                if st.button("Remove", key=f"remove_lang_{i}"):
                    config["supported_languages"].pop(i)
                    st.rerun()
        
        # Add new language
        if st.button("Add Language"):
            config["supported_languages"].append({"code": "new", "display_name": "New Language"})
            st.rerun()
    
    # Feature Toggles
    with st.expander("⚙️ Feature Settings"):
        st.subheader("Core Features")
        
        feature_descriptions = {
            "lead_capture": "🧲 Captures leads instantly with smart questions",
            "visitor_engagement": "💬 Engages visitors immediately to reduce bounce rate",
            "auto_qualification": "🎯 Qualifies leads automatically with scoring",
            "instant_answers": "🧠 Answers questions instantly without delay",
            "data_storage": "📥 Stores and manages lead data efficiently",
            "time_saving": "⏱️ Saves time and money with automation"
        }
        
        for feature, description in feature_descriptions.items():
            config["features"][feature] = st.checkbox(
                description,
                config["features"][feature],
                key=f"feature_{feature}"
            )
    
    # Save Settings
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💾 Save All Settings", type="primary"):
            if save_config(config):
                st.success("✅ Settings saved successfully!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to save settings. Please try again.")
    
    return config

def get_system_prompt(industry: str, tone: str, language: str = "en") -> str:
    """Generate system prompt based on configuration."""
    industry_templates = get_industry_templates()
    tone_settings = get_tone_settings()
    
    industry_info = industry_templates.get(industry, industry_templates["general"])
    tone_info = tone_settings.get(tone, tone_settings["friendly"])
    
    prompt = f"""You are Lia, an AI lead generation assistant for LeadPulse. 

PERSONALITY & TONE:
- Use a {tone_info['name'].lower()} tone: {tone_info['description']}
- Be conversational and engaging
- Keep responses concise but helpful

INDUSTRY FOCUS:
- You specialize in {industry_info['name']}
- {industry_info['description']}

PRIMARY GOALS:
1. Engage visitors in natural conversation
2. Collect lead information (name, email, phone, company, interest)
3. Qualify leads by understanding their needs
4. Provide helpful information about services
5. Guide qualified leads toward next steps

LEAD COLLECTION STRATEGY:
- Ask for information naturally within conversation flow
- Don't be pushy - build rapport first
- Use the conversation context to ask relevant questions
- Celebrate when users provide information

LANGUAGE:
- Respond in {language} language
- Adapt your communication style to the user's language and tone

CONVERSATION FLOW:
1. Greet warmly and ask how you can help
2. Listen to their needs and ask clarifying questions
3. Naturally collect contact information during the conversation
4. Qualify their interest level and timeline
5. Suggest next steps or offer to connect them with a human

Remember: You're not just collecting data - you're building relationships and providing value."""
    
    return prompt

def apply_custom_styling(config: Dict) -> str:
    """Generate custom CSS based on configuration."""
    return f"""
    <style>
    :root {{
        --primary-color: {config['branding']['primary_color']};
        --secondary-color: {config['branding']['secondary_color']};
        --font-family: {config['branding']['font_family']};
    }}
    
    .stApp {{
        font-family: var(--font-family);
    }}
    
    .stChatMessage[data-testid="chatAvatarIcon-user"] + div {{
        background-color: var(--primary-color);
        color: white;
        border-radius: 15px;
    }}
    
    .stChatMessage[data-testid="chatAvatarIcon-assistant"] + div {{
        background-color: #f8f9fa;
        color: #333;
        border-radius: 15px;
    }}
    
    .stButton > button {{
        background-color: var(--primary-color);
        color: white;
        border-radius: 20px;
        border: none;
        font-weight: 600;
    }}
    
    .stButton > button:hover {{
        background-color: var(--primary-color);
        opacity: 0.8;
    }}
    
    .lead-info-card {{
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }}
    </style>
    """

