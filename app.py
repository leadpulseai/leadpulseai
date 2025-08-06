import streamlit as st
from openai import OpenAI
import os
import re
import json
import csv
import pandas as pd
from datetime import datetime
import uuid
import hashlib
import time
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="Lia - AI Lead Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client with API key from secrets."""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
        if not api_key:
            st.error("OpenAI API key not found. Please set it in Streamlit secrets or as an environment variable.")
            st.stop()
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {e}")
        st.stop()

# Load configuration
@st.cache_data
def load_config():
    """Load configuration from file or create default if not exists."""
    default_config = {
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
    
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                # Merge with default config to ensure all keys exist
                return merge_config(default_config, config)
        except Exception as e:
            st.error(f"Error loading configuration: {e}")
            return default_config
    else:
        save_config(default_config)
        return default_config

def merge_config(default: Dict, user: Dict) -> Dict:
    """Merge user config with default config to ensure all keys exist."""
    result = default.copy()
    for key, value in user.items():
        if isinstance(value, dict) and key in result:
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result

def save_config(config: Dict):
    """Save configuration to file."""
    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False

# Language support functions
def get_ui_text(key: str, language: str = "en", fallback: str = None) -> str:
    """Get UI text in the specified language."""
    translations = {
        "en": {
            "welcome": "Hi! I'm Lia, your AI assistant from LeadPulse. How can I help you today?",
            "input_placeholder": "Type your message here...",
            "send_button": "Send",
            "lead_captured": "Thank you for providing your information!",
            "email_prompt": "Could you share your email address?",
            "name_prompt": "What's your name?",
            "phone_prompt": "What's your phone number?",
            "interest_prompt": "What are you interested in?",
            "company_prompt": "What company are you with?",
            "budget_prompt": "What's your budget range for this project?",
            "timeline_prompt": "When are you looking to get started?",
            "error_message": "I'm having trouble connecting right now. Please try again in a moment.",
            "lead_score": "Lead Score",
            "contact_info": "Contact Information",
            "qualification_info": "Qualification Details",
            "next_steps": "Recommended Next Steps",
            "high_priority": "High Priority Lead",
            "medium_priority": "Medium Priority Lead",
            "low_priority": "Low Priority Lead",
            "language": "Language",
            "total_leads": "Total Leads",
            "new_today": "New Today",
            "conversion_rate": "Conversion Rate",
            "avg_score": "Average Score"
        },
        "zh": {
            "welcome": "你好！我是Lia，您的LeadPulse AI助手。今天我能帮您什么？",
            "input_placeholder": "在这里输入您的消息...",
            "send_button": "发送",
            "lead_captured": "感谢您提供信息！",
            "email_prompt": "您能分享您的电子邮件地址吗？",
            "name_prompt": "您叫什么名字？",
            "phone_prompt": "您的电话号码是多少？",
            "interest_prompt": "您对什么感兴趣？",
            "company_prompt": "您在哪家公司工作？",
            "budget_prompt": "这个项目的预算范围是多少？",
            "timeline_prompt": "您计划什么时候开始？",
            "error_message": "我现在连接有问题。请稍后再试。",
            "lead_score": "潜在客户评分",
            "contact_info": "联系信息",
            "qualification_info": "资格详情",
            "next_steps": "建议的下一步",
            "high_priority": "高优先级潜在客户",
            "medium_priority": "中等优先级潜在客户",
            "low_priority": "低优先级潜在客户",
            "language": "语言",
            "total_leads": "总潜在客户",
            "new_today": "今日新增",
            "conversion_rate": "转化率",
            "avg_score": "平均分数"
        },
        "es": {
            "welcome": "¡Hola! Soy Lia, tu asistente de IA de LeadPulse. ¿Cómo puedo ayudarte hoy?",
            "input_placeholder": "Escribe tu mensaje aquí...",
            "send_button": "Enviar",
            "lead_captured": "¡Gracias por proporcionar tu información!",
            "email_prompt": "¿Podrías compartir tu dirección de correo electrónico?",
            "name_prompt": "¿Cómo te llamas?",
            "phone_prompt": "¿Cuál es tu número de teléfono?",
            "interest_prompt": "¿En qué estás interesado?",
            "company_prompt": "¿Con qué empresa estás?",
            "budget_prompt": "¿Cuál es tu rango de presupuesto para este proyecto?",
            "timeline_prompt": "¿Cuándo estás buscando comenzar?",
            "error_message": "Tengo problemas de conexión ahora. Por favor, inténtalo de nuevo en un momento.",
            "lead_score": "Puntuación de Lead",
            "contact_info": "Información de Contacto",
            "qualification_info": "Detalles de Calificación",
            "next_steps": "Próximos Pasos Recomendados",
            "high_priority": "Lead de Alta Prioridad",
            "medium_priority": "Lead de Prioridad Media",
            "low_priority": "Lead de Baja Prioridad",
            "language": "Idioma",
            "total_leads": "Total de Leads",
            "new_today": "Nuevos Hoy",
            "conversion_rate": "Tasa de Conversión",
            "avg_score": "Puntuación Promedio"
        }
    }
    
    if language in translations and key in translations[language]:
        return translations[language][key]
    elif fallback:
        return fallback
    else:
        return translations["en"].get(key, key)

def detect_language(text: str) -> str:
    """Detect language from user input using simple heuristics."""
    if not text:
        return "en"
    
    # Simple heuristic detection
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    spanish_chars = len(re.findall(r'[ñáéíóúü]', text.lower()))
    
    # If significant Chinese characters, likely Chinese
    if chinese_chars > len(text) * 0.3:
        return "zh"
    
    # If Spanish characters or common Spanish words
    spanish_words = ['el', 'la', 'es', 'en', 'de', 'que', 'y', 'con', 'por', 'para', 'hola', 'soy', 'estoy']
    if spanish_chars > 0 or any(word in text.lower().split() for word in spanish_words):
        return "es"
    
    return "en"  # Default to English

def extract_lead_info(user_input: str, language: str, lead_data: Dict) -> Dict:
    """Extract lead information using language-specific patterns."""
    if not user_input:
        return lead_data
    
    # Email extraction (universal format)
    if not lead_data.get("email"):
        email_pattern = r"[\w.\-+%]+@[\w.-]+\.[a-zA-Z]{2,}"
        email_match = re.search(email_pattern, user_input, re.IGNORECASE)
        if email_match:
            lead_data["email"] = email_match.group().lower()
            st.toast(f"📧 Email captured: {lead_data['email']}")
    
    # Name extraction
    if not lead_data.get("name"):
        name_patterns = [
            r"(?:my name is|I am|I'm|call me|this is)\s+([A-Za-z\s]{2,30})",
            r"(?:I'm|I am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:name|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, user_input, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip().title()
                if len(name) > 1 and not any(word in name.lower() for word in ['email', 'phone', 'number', 'address']):
                    lead_data["name"] = name
                    st.toast(f"👤 Name captured: {lead_data['name']}")
                    break
    
    # Phone extraction
    if not lead_data.get("phone"):
        phone_pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        phone_match = re.search(phone_pattern, user_input)
        if phone_match:
            phone = re.sub(r'[()\s-]', '', phone_match.group())
            if len(phone) >= 10:
                lead_data["phone"] = phone_match.group()
                st.toast(f"📞 Phone captured: {lead_data['phone']}")
    
    # Company extraction
    if not lead_data.get("company"):
        company_patterns = [
            r"(?:work at|work for|employed by|company is|from)\s+([A-Za-z0-9\s&.,'-]{2,50})",
            r"(?:at|@)\s+([A-Z][A-Za-z0-9\s&.,'-]{1,49})\s*(?:company|corp|inc|ltd|llc)?"
        ]
        
        for pattern in company_patterns:
            company_match = re.search(pattern, user_input, re.IGNORECASE)
            if company_match:
                company = company_match.group(1).strip().title()
                if len(company) > 2 and not any(word in company.lower() for word in ['email', 'phone', 'number']):
                    lead_data["company"] = company
                    st.toast(f"🏢 Company captured: {lead_data['company']}")
                    break
    
    # Interest extraction
    if not lead_data.get("interest"):
        interest_patterns = [
            r"(?:interested in|looking for|need|want|seeking)\s+([^.,;!?]{5,100})",
            r"(?:help with|assistance with|support for)\s+([^.,;!?]{5,100})"
        ]
        
        for pattern in interest_patterns:
            interest_match = re.search(pattern, user_input, re.IGNORECASE)
            if interest_match:
                interest = interest_match.group(1).strip()
                if 5 <= len(interest) <= 100:
                    lead_data["interest"] = interest
                    st.toast(f"💡 Interest captured: {lead_data['interest']}")
                    break
    
    return lead_data

def calculate_lead_score(lead_data: Dict, config: Dict) -> int:
    """Calculate lead score based on available information."""
    score = 0
    scoring_config = config.get("lead_qualification", {}).get("scoring", {})
    
    if lead_data.get("email"):
        score += scoring_config.get("email_provided", 30)
    
    if lead_data.get("phone"):
        score += scoring_config.get("phone_provided", 20)
    
    if lead_data.get("company"):
        score += scoring_config.get("company_provided", 15)
    
    if lead_data.get("budget"):
        score += scoring_config.get("budget_provided", 15)
    
    if lead_data.get("interest"):
        score += scoring_config.get("timeline_provided", 10)
    
    if lead_data.get("name"):
        score += 10
    
    return min(score, 100)

def get_lead_priority(score: int, language: str = "en") -> tuple:
    """Get lead priority based on score."""
    if score >= 70:
        return ("high", get_ui_text("high_priority", language), "🔥")
    elif score >= 40:
        return ("medium", get_ui_text("medium_priority", language), "⚡")
    else:
        return ("low", get_ui_text("low_priority", language), "📝")

def build_system_prompt(config: Dict, language: str) -> str:
    """Build system prompt based on configuration."""
    assistant_name = config["branding"]["name"]
    tone = config["tone"]
    industry = config["industry_template"]
    
    # Get industry settings
    industry_settings = {
        "saas": {"business_type": "a SaaS company", "target_audience": "Business professionals"},
        "b2b": {"business_type": "a B2B service provider", "target_audience": "Business owners"},
        "marketing": {"business_type": "a marketing agency", "target_audience": "Businesses looking to grow"},
        "general": {"business_type": "a business", "target_audience": "Potential customers"}
    }.get(industry, {"business_type": "a business", "target_audience": "Potential customers"})
    
    prompt = f"""You are {assistant_name}, an AI lead generation assistant for LeadPulse.

PERSONALITY & TONE:
- Use a {tone} tone
- Be conversational and engaging
- Keep responses concise but helpful

INDUSTRY FOCUS:
- You work for {industry_settings['business_type']}
- Your target audience is {industry_settings['target_audience']}

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

def initialize_session_state():
    """Initialize session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "lead_data" not in st.session_state:
        st.session_state.lead_data = {}
    
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    if "show_intro" not in st.session_state:
        config = load_config()
        st.session_state.show_intro = config["intro"]["enabled"]
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"
    
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    return st.session_state.session_id

def render_intro_page():
    """Render the intro page."""
    config = load_config()
    
    # Apply custom styling
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(135deg, {config["branding"]["secondary_color"]} 0%, #2d2d2d 100%);
            color: white;
            font-family: {config["branding"]["font_family"]};
        }}
        .intro-container {{
            text-align: center;
            padding: 2rem;
            height: 80vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        .lia-text {{
            font-size: 4rem;
            font-weight: bold;
            color: {config["branding"]["primary_color"]};
            margin: 1rem 0;
            text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        }}
        .level-up-text {{
            font-family: monospace;
            font-size: 1.5rem;
            color: white;
            margin: 1rem 0;
            letter-spacing: 2px;
        }}
        .description-text {{
            font-size: 1.2rem;
            color: #ccc;
            margin: 2rem 0;
            max-width: 600px;
        }}
        .language-selector-label {{
            font-size: 1rem;
            color: #aaa;
            margin: 2rem 0 1rem 0;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Main intro content
    st.markdown('<div class="intro-container">', unsafe_allow_html=True)
    
    # Lightning bolt logo
    st.markdown(f'<div style="font-size: 5rem; margin-bottom: 1rem;">{config["branding"]["logo_url"]}</div>', unsafe_allow_html=True)
    
    # Animated "lia" text
    st.markdown('<div class="lia-text">lia</div>', unsafe_allow_html=True)
    
    # Level Up text
    st.markdown('<div class="level-up-text">LEVEL UP</div>', unsafe_allow_html=True)
    
    # Description
    st.markdown(f'<p class="description-text">{config["intro_description"]}</p>', unsafe_allow_html=True)
    
    st.markdown('<p class="language-selector-label">Choose your language:</p>', unsafe_allow_html=True)
    
    # Language selection buttons
    lang_cols = st.columns(len(config["supported_languages"]))
    for i, lang in enumerate(config["supported_languages"]):
        with lang_cols[i]:
            if st.button(lang["display_name"], key=f"lang_btn_{lang['code']}"):
                st.session_state.language = lang["code"]
                st.session_state.show_intro = False
                st.rerun()
    
    st.write("<br>", unsafe_allow_html=True)
    if st.button("Start Chatting with Lia", key="start_chat_btn"):
        st.session_state.show_intro = False
        st.rerun()
        
    st.markdown("</div>", unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with lead information and navigation."""
    config = load_config()
    language = st.session_state.language
    
    st.sidebar.title(f"{config['branding']['logo_url']} {config['branding']['name']}")
    
    # Navigation
    st.sidebar.subheader("Navigation")
    pages = {
        "chat": "💬 Chat",
        "dashboard": "📊 Dashboard", 
        "settings": "⚙️ Settings"
    }
    
    for page_key, page_name in pages.items():
        if st.sidebar.button(page_name, key=f"nav_{page_key}"):
            st.session_state.current_page = page_key
            st.rerun()
    
    # Language selector
    st.sidebar.subheader(f"🌍 {get_ui_text('language', language)}")
    
    languages = {lang["code"]: lang["display_name"] for lang in config["supported_languages"]}
    selected_language = st.sidebar.selectbox(
        "Select Language",
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=list(languages.keys()).index(st.session_state.language),
        key="language_selector"
    )
    
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()
    
    # Lead information
    if st.session_state.lead_data:
        st.sidebar.subheader(f"📋 {get_ui_text('contact_info', language)}")
        
        lead_score = calculate_lead_score(st.session_state.lead_data, config)
        priority, priority_text, priority_icon = get_lead_priority(lead_score, language)
        
        st.sidebar.metric(
            get_ui_text("lead_score", language),
            f"{lead_score}/100",
            delta=None
        )
        
        st.sidebar.markdown(f"{priority_icon} **{priority_text}**")
        
        # Display lead information
        for key, value in st.session_state.lead_data.items():
            if value:
                icon_map = {
                    "name": "👤",
                    "email": "📧", 
                    "phone": "📞",
                    "company": "🏢",
                    "interest": "💡",
                    "budget": "💰"
                }
                icon = icon_map.get(key, "📝")
                st.sidebar.markdown(f"{icon} **{key.title()}:** {value}")
    
    # Quick stats
    st.sidebar.subheader("📈 Quick Stats")
    
    # Mock stats for demo
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric(get_ui_text("total_leads", language), "42")
        st.metric(get_ui_text("conversion_rate", language), "23%")
    with col2:
        st.metric(get_ui_text("new_today", language), "7")
        st.metric(get_ui_text("avg_score", language), "67")

def render_chat_interface():
    """Render the main chat interface."""
    config = load_config()
    language = st.session_state.language
    client = get_openai_client()
    
    st.title(f"💬 Chat with {config['branding']['name']}")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input(get_ui_text("input_placeholder", language)):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Detect language and extract lead info
        detected_lang = detect_language(prompt)
        if detected_lang != language:
            st.session_state.language = detected_lang
            language = detected_lang
        
        # Extract lead information
        st.session_state.lead_data = extract_lead_info(prompt, language, st.session_state.lead_data)
        
        # Generate AI response
        with st.chat_message("assistant"):
            try:
                system_prompt = build_system_prompt(config, language)
                
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(st.session_state.messages)
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                
                assistant_response = response.choices[0].message.content
                st.markdown(assistant_response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            except Exception as e:
                error_msg = get_ui_text("error_message", language)
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

def render_dashboard_page():
    """Render the dashboard page."""
    language = st.session_state.language
    
    st.title(f"📊 {get_ui_text('dashboard', language, 'Dashboard')}")
    
    # Mock dashboard content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(get_ui_text("total_leads", language), "42", "↗️ 12%")
    with col2:
        st.metric(get_ui_text("new_today", language), "7", "↗️ 3")
    with col3:
        st.metric(get_ui_text("conversion_rate", language), "23%", "↗️ 2%")
    with col4:
        st.metric(get_ui_text("avg_score", language), "67", "↗️ 5")
    
    # Charts placeholder
    st.subheader("📈 Lead Generation Trends")
    
    # Mock data for chart
    import plotly.express as px
    import pandas as pd
    
    df = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=30, freq='D'),
        'Leads': [5, 8, 12, 7, 15, 9, 11, 13, 6, 10, 14, 8, 12, 16, 9, 11, 7, 13, 15, 8, 10, 12, 14, 9, 11, 13, 7, 15, 12, 10]
    })
    
    fig = px.line(df, x='Date', y='Leads', title='Daily Lead Generation')
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent leads table
    st.subheader("🔥 Recent Leads")
    
    # Mock recent leads data
    recent_leads = pd.DataFrame({
        'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
        'Email': ['john@example.com', 'jane@company.com', 'bob@startup.io', 'alice@corp.com'],
        'Company': ['TechCorp', 'StartupXYZ', 'InnovateLab', 'BigCorp'],
        'Score': [85, 72, 91, 68],
        'Priority': ['🔥 High', '⚡ Medium', '🔥 High', '⚡ Medium']
    })
    
    st.dataframe(recent_leads, use_container_width=True)

def render_settings_page():
    """Render the settings page."""
    language = st.session_state.language
    
    st.title(f"⚙️ {get_ui_text('settings', language, 'Settings')}")
    
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
    
    # Conversation Settings
    with st.expander("💬 Conversation Settings"):
        config["welcome_message"] = st.text_area(
            "Welcome Message", 
            config["welcome_message"],
            help="First message shown to users"
        )
        
        tone_options = ["professional", "friendly", "casual"]
        config["tone"] = st.selectbox(
            "Conversation Tone",
            options=tone_options,
            index=tone_options.index(config["tone"]) if config["tone"] in tone_options else 0
        )
        
        industry_options = ["saas", "b2b", "marketing", "general"]
        config["industry_template"] = st.selectbox(
            "Industry Template",
            options=industry_options,
            index=industry_options.index(config["industry_template"]) if config["industry_template"] in industry_options else 0
        )
    
    # Save Settings
    if st.button("💾 Save Settings", type="primary"):
        if save_config(config):
            st.success("✅ Settings saved!")
            st.rerun()
        else:
            st.error("❌ Failed to save settings")

def check_admin_access():
    """Check if user has admin access."""
    query_params = st.query_params
    return "admin" in query_params and st.session_state.admin_authenticated
    
def main():
    """Main application function."""
    # Initialize session state
    session_id = initialize_session_state()
    
    # Check for admin access
    is_admin = check_admin_access()
    
    # Show intro page if configured
    if st.session_state.show_intro and not is_admin:
        render_intro_page()
        return
    
    # Render sidebar
    render_sidebar()
    
    # Render main content based on current page
    current_page = st.session_state.current_page
    
    if current_page == "chat":
        render_chat_interface()
    elif current_page == "dashboard":
        render_dashboard_page()
    elif current_page == "settings":
        render_settings_page()
    
    # Add footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #666; font-size: 12px;'>"
        f"Powered by Lia AI Assistant | LeadPulse Platform | Session: {session_id[:8]}..."
        f"</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

