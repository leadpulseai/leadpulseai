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
import plotly.express as px
import plotly.graph_objects as go

# Import our comprehensive modules
from intro_page import render_intro_page, should_show_intro
from customization import (
    render_customization_dashboard, load_config, save_config,
    get_industry_template, get_tone_settings
)
from multilanguage import (
    get_ui_text, detect_language, translate_text, extract_lead_info,
    get_supported_languages
)
from database import get_db_manager
from session_manager import get_session_manager
from advanced_dashboard import get_dashboard
from email_notifications import get_email_manager
from crm_integrations import get_crm_manager

# Initialize managers
db_manager = get_db_manager()
session_manager = get_session_manager()
dashboard = get_dashboard()
email_manager = get_email_manager()
crm_manager = get_crm_manager()

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
            st.error("OpenAI API key not found. Please configure it in Streamlit secrets.")
            st.stop()
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {e}")
        st.stop()

client = get_openai_client()

def initialize_session_state():
    """Initialize session state with persistent data and default values."""
    # Initialize session manager and get session ID
    session_id = session_manager.initialize_session_state()
    
    # Initialize default values if not present
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    if "show_intro" not in st.session_state:
        st.session_state.show_intro = should_show_intro()
    
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"
    
    # Load configuration
    if "config" not in st.session_state:
        st.session_state.config = load_config()
    
    return session_id

def get_ai_response(messages: List[Dict], language: str = "en") -> str:
    """Get AI response from OpenAI with enhanced prompting."""
    config = st.session_state.config
    
    # Build system prompt with configuration
    system_prompt = build_system_prompt(config, language)
    
    # Prepare messages for OpenAI
    openai_messages = [{"role": "system", "content": system_prompt}]
    openai_messages.extend(messages)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error getting AI response: {e}")
        return get_ui_text("error_response", language, "I apologize, but I\"m having trouble responding right now. Please try again.")

def build_system_prompt(config: Dict, language: str) -> str:
    """Build comprehensive system prompt based on configuration."""
    assistant_name = config.get("branding", {}).get("name", "Lia")
    tone = config.get("tone", "friendly")
    industry_template = config.get("industry_template", "saas")
    
    # Get tone and industry settings
    tone_settings = get_tone_settings(tone)
    industry_settings = get_industry_template(industry_template)
    
    # Build dynamic prompt
    system_prompt = f"""You are {assistant_name}, an AI lead generation assistant for {industry_settings.get("business_type", "a business")}. 

PERSONALITY & TONE:
{tone_settings.get("description", "Be helpful and professional.")}
- Communication style: {tone_settings.get("style", "Professional and friendly")}
- Use language: {language}

BUSINESS CONTEXT:
- Industry: {industry_settings.get("name", "General Business")}
- Target audience: {industry_settings.get("target_audience", "Business professionals")}
- Key value propositions: {", ".join(industry_settings.get("value_props", ["Quality service", "Expert solutions"]))}

LEAD QUALIFICATION GOALS:
Your primary objective is to naturally extract the following information through conversation:
1. Name (essential)
2. Email address (essential) 
3. Phone number (if possible)
4. Company name and size
5. Specific interests or needs
6. Budget range or timeline
7. Decision-making authority

CONVERSATION GUIDELINES:
- Start with a warm, personalized greeting
- Ask open-ended questions to understand their needs
- Provide value and insights related to their interests
- Gradually and naturally request contact information
- Be helpful even if they don\'t provide all information
- If they ask about pricing, gather their requirements first
- Always maintain a {tone} tone throughout the conversation

LEAD SCORING CRITERIA:
- Email provided: High priority
- Phone + Email: Very high priority  
- Company information: Medium priority
- Budget/timeline discussed: High priority
- Decision maker confirmed: Very high priority

Remember: Focus on being genuinely helpful while naturally gathering lead information. Never be pushy or overly sales-focused."""

    return system_prompt

def extract_and_save_lead_info(conversation_history: List[Dict], session_id: str, language: str):
    """Extract lead information from conversation and save to database."""
    # Extract lead info using multilanguage module
    lead_info = extract_lead_info(conversation_history, language)
    
    if lead_info and any(lead_info.values()):
        # Calculate lead score
        score = calculate_lead_score(lead_info)
        lead_info["score"] = score
        lead_info["priority"] = get_lead_priority(score)
        lead_info["language"] = language
        
        # Save to database
        lead_id = session_manager.save_lead_data(session_id, lead_info)
        
        # Update session state
        st.session_state.lead_data.update(lead_info)
        
        # Trigger integrations if configured
        if any(crm_manager._is_integration_enabled(integration) for integration in ["hubspot", "salesforce", "airtable", "notion"]):
            sync_results = crm_manager.sync_lead_to_integrations(lead_info, session_id)
            
        # Send notifications if configured
        if any(crm_manager._is_integration_enabled(integration) for integration in ["slack", "discord", "webhook"]):
            notification_results = crm_manager.send_lead_notification(lead_info, session_id)
        
        # Send email notification if configured
        if email_manager.smtp_config.get("username") and st.session_state.config.get("admin", {}).get("email_notifications", False):
            admin_email = st.session_state.config.get("admin", {}).get("email", "")
            if admin_email:
                email_manager.send_new_lead_notification(lead_info, [admin_email], language)
        
        return lead_info
    
    return None

def calculate_lead_score(lead_info: Dict) -> int:
    """Calculate lead score based on available information."""
    config = st.session_state.config
    scoring = config.get("lead_qualification", {}).get("scoring", {})
    
    score = 0
    
    # Apply scoring rules
    if lead_info.get("email"):
        score += scoring.get("email_provided", 30)
    
    if lead_info.get("phone"):
        score += scoring.get("phone_provided", 20)
    
    if lead_info.get("company"):
        score += scoring.get("company_provided", 15)
    
    if lead_info.get("budget"):
        score += scoring.get("budget_provided", 15)
    
    if lead_info.get("timeline"):
        score += scoring.get("timeline_provided", 10)
    
    # Additional scoring based on conversation quality
    if lead_info.get("interest") and len(lead_info.get("interest", "")) > 20:
        score += 10  # Detailed interest
    
    return min(score, 100)  # Cap at 100

def get_lead_priority(score: int) -> str:
    """Determine lead priority based on score."""
    if score >= 70:
        return "high"
    elif score >= 40:
        return "medium"
    else:
        return "low"

def render_sidebar():
    """Render sidebar with lead information and navigation."""
    with st.sidebar:
        st.title("⚡ Lia Dashboard")
        
        # Navigation
        page = st.selectbox(
            "Navigate",
            options=["chat", "dashboard", "settings", "integrations"],
            format_func=lambda x: {
                "chat": "💬 Chat",
                "dashboard": "📊 Dashboard", 
                "settings": "⚙️ Settings",
                "integrations": "🔗 Integrations"
            }.get(x, x),
            index=["chat", "dashboard", "settings", "integrations"].index(st.session_state.current_page)
        )
        
        if page != st.session_state.current_page:
            st.session_state.current_page = page
            st.rerun()
        
        st.divider()
        
        # Current lead information
        st.subheader("📋 Current Lead")
        lead_data = st.session_state.get("lead_data", {})
        
        if any(lead_data.values()):
            # Display lead info
            if lead_data.get("name"):
                st.write(f"**Name:** {lead_data["name"]}")
            if lead_data.get("email"):
                st.write(f"**Email:** {lead_data["email"]}")
            if lead_data.get("company"):
                st.write(f"**Company:** {lead_data["company"]}")
            if lead_data.get("phone"):
                st.write(f"**Phone:** {lead_data["phone"]}")
            
            # Lead score and priority
            score = lead_data.get("score", 0)
            priority = lead_data.get("priority", "low")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Score", f"{score}/100")
            with col2:
                priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                st.write(f"**Priority:** {priority_color.get(priority, "⚪")} {priority.title()}")
        else:
            st.info("No lead information captured yet.")
        
        st.divider()
        
        # Quick stats
        st.subheader("📈 Quick Stats")
        analytics = db_manager.get_analytics_summary(days=7)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Leads (7d)", analytics["total_leads"])
        with col2:
            st.metric("Avg Score", f"{analytics["average_score"]:.1f}")
        
        # Language selector
        st.divider()
        st.subheader("🌍 Language")
        
        languages = get_supported_languages()
        current_lang = st.session_state.get("language", "en")
        
        selected_lang = st.selectbox(
            "Select Language",
            options=[lang["code"] for lang in languages],
            format_func=lambda x: next(lang["display_name"] for lang in languages if lang["code"] == x),
            index=[lang["code"] for lang in languages].index(current_lang)
        )
        
        if selected_lang != current_lang:
            st.session_state.language = selected_lang
            st.rerun()

def render_chat_interface():
    """Render the main chat interface."""
    language = st.session_state.get("language", "en")
    
    # Chat header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title(f"⚡ {st.session_state.config.get("branding", {}).get("name", "Lia")}")
        st.caption(get_ui_text("chat_subtitle", language, "AI Lead Generation Assistant"))
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        # Display conversation history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input(get_ui_text("chat_placeholder", language, "Type your message here...")):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Save user message to database
        session_manager.save_message(
            session_id=st.session_state.session_id,
            role="user",
            content=prompt,
            language=language
        )
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner(get_ui_text("thinking", language, "Thinking...")):
                response = get_ai_response(st.session_state.messages, language)
                st.write(response)
        
        # Add assistant response to chat
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Save assistant message to database
        session_manager.save_message(
            session_id=st.session_state.session_id,
            role="assistant", 
            content=response,
            language=language
        )
        
        # Extract and save lead information
        lead_info = extract_and_save_lead_info(
            st.session_state.messages,
            st.session_state.session_id,
            language
        )
        
        # Show lead capture notification
        if lead_info and any(lead_info.values()):
            st.success(get_ui_text("lead_updated", language, "✅ Lead information updated!"))
        
        # Rerun to update the interface
        st.rerun()

def render_dashboard_page():
    """Render the advanced dashboard page."""
    language = st.session_state.get("language", "en")
    dashboard.render_dashboard(language)

def render_settings_page():
    """Render the settings and customization page."""
    language = st.session_state.get("language", "en")
    
    st.title(get_ui_text("settings_title", language, "⚙️ Settings & Customization"))
    
    # Settings tabs
    tab1, tab2, tab3 = st.tabs([
        get_ui_text("branding", language, "Branding"),
        get_ui_text("email_settings", language, "Email Settings"),
        get_ui_text("admin_settings", language, "Admin Settings")
    ])
    
    with tab1:
        render_customization_dashboard(language)
    
    with tab2:
        render_email_settings(language)
    
    with tab3:
        render_admin_settings(language)

def render_email_settings(language: str):
    """Render email configuration settings."""
    st.subheader(get_ui_text("email_config", language, "📧 Email Configuration"))
    
    with st.expander(get_ui_text("smtp_settings", language, "SMTP Settings"), expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input(
                get_ui_text("smtp_server", language, "SMTP Server"),
                value=email_manager.smtp_config.get("smtp_server", "smtp.gmail.com")
            )
            
            smtp_port = st.number_input(
                get_ui_text("smtp_port", language, "SMTP Port"),
                value=email_manager.smtp_config.get("smtp_port", 587),
                min_value=1,
                max_value=65535
            )
        
        with col2:
            username = st.text_input(
                get_ui_text("email_username", language, "Email Username"),
                value=email_manager.smtp_config.get("username", "")
            )
            
            password = st.text_input(
                get_ui_text("email_password", language, "Email Password"),
                type="password",
                value=email_manager.smtp_config.get("password", "")
            )
        
        from_email = st.text_input(
                get_ui_text("from_email", language, "From Email"),
                value=email_manager.smtp_config.get("from_email", "")
            )
            
        from_name = st.text_input(
                get_ui_text("from_name", language, "From Name"),
                value=email_manager.smtp_config.get("from_name", "Lia - LeadPulse")
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(get_ui_text("save_email_config", language, "💾 Save Configuration")):
                email_manager.configure_smtp(
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    username=username,
                    password=password,
                    from_email=from_email,
                    from_name=from_name
                )
                st.success(get_ui_text("email_config_saved", language, "Email configuration saved!"))
        
        with col2:
            if st.button(get_ui_text("test_email", language, "🧪 Test Connection")):
                if email_manager.test_smtp_connection():
                    st.success(get_ui_text("email_test_success", language, "✅ Email connection successful!"))
                else:
                    st.error(get_ui_text("email_test_failed", language, "❌ Email connection failed!"))
    
    # Notification settings
    st.subheader(get_ui_text("notification_settings", language, "🔔 Notification Settings"))
    
    enable_notifications = st.checkbox(
        get_ui_text("enable_email_notifications", language, "Enable email notifications for new leads"),
        value=st.session_state.config.get("admin", {}).get("email_notifications", False)
    )
    
    admin_email = st.text_input(
        get_ui_text("admin_email", language, "Admin Email for Notifications"),
        value=st.session_state.config.get("admin", {}).get("email", "")
    )
    
    if st.button(get_ui_text("save_notification_settings", language, "💾 Save Notification Settings")):
        config = st.session_state.config
        if "admin" not in config:
            config["admin"] = {}
        
        config["admin"]["email_notifications"] = enable_notifications
        config["admin"]["email"] = admin_email
        
        save_config(config)
        st.session_state.config = config
        st.success(get_ui_text("notification_settings_saved", language, "Notification settings saved!"))

def render_admin_settings(language: str):
    """Render admin-specific settings."""
    st.subheader(get_ui_text("admin_panel", language, "👨‍💼 Admin Panel"))
    
    # Database management
    with st.expander(get_ui_text("database_management", language, "🗄️ Database Management"), expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(get_ui_text("cleanup_old_sessions", language, "🧹 Cleanup Old Sessions")):
                db_manager.cleanup_old_sessions(days=30)
                st.success(get_ui_text("cleanup_success", language, "Old sessions cleaned up!"))
        
        with col2:
            if st.button(get_ui_text("export_all_data", language, "📤 Export All Data")):
                # Export functionality would be implemented here
                st.info(get_ui_text("export_coming_soon", language, "Export functionality coming soon!"))
        
        with col3:
            if st.button(get_ui_text("reset_analytics", language, "🔄 Reset Analytics")):
                st.warning(get_ui_text("reset_warning", language, "This action cannot be undone!"))
    
    # System information
    st.subheader(get_ui_text("system_info", language, "ℹ️ System Information"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{get_ui_text("session_id", language, "Session ID")}:** {st.session_state.session_id[:8]}...")
        st.markdown(f"**{get_ui_text("language", language, "Language")}:** {language}")
        st.markdown(f"**{get_ui_text("messages_count", language, "Messages")}:** {len(st.session_state.messages)}")
    
    with col2:
        analytics = db_manager.get_analytics_summary(days=1)
        st.markdown(f"**{get_ui_text("todays_leads", language, "Today\"s Leads")}:** {analytics["total_leads"]}")
        st.markdown(f"**{get_ui_text("avg_score", language, "Avg Score")}:** {analytics["average_score"]:.1f}")

def render_integrations_page():
    """Render the integrations configuration page."""
    language = st.session_state.get("language", "en")
    
    st.title(get_ui_text("integrations_title", language, "🔗 Integrations"))
    
    # Get available integrations
    integrations = crm_manager.get_available_integrations()
    
    # Group integrations by category
    categories = {}
    for integration in integrations:
        category = integration["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(integration)
    
    # Render integration categories
    for category, category_integrations in categories.items():
        st.subheader(f"{category} Integrations")
        
        for integration in category_integrations:
            with st.expander(f"{integration["icon"]} {integration["name"]}", expanded=False):
                st.write(integration["description"])
                
                status = integration["status"]
                status_colors = {
                    "enabled": "🟢",
                    "configured": "🟡", 
                    "disabled": "🔴"
                }
                
                st.write(f"**Status:** {status_colors.get(status, "⚪")} {status.title()}")
                
                # Configuration form based on integration type
                if integration["id"] == "hubspot":
                    render_hubspot_config(integration["id"], language)
                elif integration["id"] == "slack":
                    render_slack_config(integration["id"], language)
                elif integration["id"] == "webhook":
                    render_webhook_config(integration["id"], language)
                # Add more integration configs as needed

def render_hubspot_config(integration_id: str, language: str):
    """Render HubSpot configuration form."""
    st.write("**Configuration:**")
    
    api_key = st.text_input(
        "HubSpot API Key",
        type="password",
        key=f"{integration_id}_api_key"
    )
    
    portal_id = st.text_input(
        "Portal ID",
        key=f"{integration_id}_portal_id"
    )
    
    enabled = st.checkbox(
        "Enable Integration",
        key=f"{integration_id}_enabled"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Configuration", key=f"{integration_id}_save"):
            config = {
                "api_key": api_key,
                "portal_id": portal_id,
                "enabled": enabled
            }
            
            if crm_manager.configure_integration(integration_id, config):
                st.success("Configuration saved!")
            else:
                st.error("Failed to save configuration!")
    
    with col2:
        if st.button("Test Connection", key=f"{integration_id}_test"):
            if crm_manager.test_integration(integration_id):
                st.success("✅ Connection successful!")
            else:
                st.error("❌ Connection failed!")

def render_slack_config(integration_id: str, language: str):
    """Render Slack configuration form."""
    st.write("**Configuration:**")
    
    webhook_url = st.text_input(
        "Slack Webhook URL",
        type="password",
        key=f"{integration_id}_webhook"
    )
    
    enabled = st.checkbox(
        "Enable Integration",
        key=f"{integration_id}_enabled"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Configuration", key=f"{integration_id}_save"):
            config = {
                "webhook_url": webhook_url,
                "enabled": enabled
            }
            
            if crm_manager.configure_integration(integration_id, config):
                st.success("Configuration saved!")
            else:
                st.error("Failed to save configuration!")
    
    with col2:
        if st.button("Test Connection", key=f"{integration_id}_test"):
            if crm_manager.test_integration(integration_id):
                st.success("✅ Connection successful!")
            else:
                st.error("❌ Connection failed!")

def render_webhook_config(integration_id: str, language: str):
    """Render webhook configuration form."""
    st.write("**Configuration:**")
    
    webhook_url = st.text_input(
        "Webhook URL",
        key=f"{integration_id}_webhook"
    )
    
    headers = st.text_area(
        "Custom Headers (JSON format)",
        placeholder="{\"Authorization\": \"Bearer token\", \"Content-Type\": \"application/json\"}",
        key=f"{integration_id}_headers"
    )
    
    enabled = st.checkbox(
        "Enable Integration",
        key=f"{integration_id}_enabled"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Configuration", key=f"{integration_id}_save"):
            config = {
                "webhook_url": webhook_url,
                "enabled": enabled
            }
            
            if headers:
                try:
                    config["headers"] = json.loads(headers)
                except json.JSONDecodeError:
                    st.error("Invalid JSON format for headers!")
                    return
            
            if crm_manager.configure_integration(integration_id, config):
                st.success("Configuration saved!")
            else:
                st.error("Failed to save configuration!")
    
    with col2:
        if st.button("Test Connection", key=f"{integration_id}_test"):
            if crm_manager.test_integration(integration_id):
                st.success("✅ Connection successful!")
            else:
                st.error("❌ Connection failed!")

def check_admin_access():
    """Check if user has admin access."""
    # Check URL parameters for admin access
    query_params = st.experimental_get_query_params()
    
    if "admin" in query_params and not st.session_state.admin_authenticated:
        st.title("🔐 Admin Login")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # Simple authentication (in production, use proper authentication)
            config = st.session_state.config
            admin_config = config.get("admin", {})
            
            if (username == admin_config.get("username", "admin") and 
                hashlib.sha256(password.encode()).hexdigest() == admin_config.get("password_hash", 
                "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9")):  # admin123
                st.session_state.admin_authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials!")
        
        st.stop()
    
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
    elif current_page == "integrations":
        render_integrations_page()
    
    # Add footer
    st.markdown("---")
    st.markdown(
        f"<div style=\"text-align: center; color: #666; font-size: 12px;\">"
        f"Powered by Lia AI Assistant | LeadPulse Platform | Session: {session_id[:8]}..."
        f"</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

