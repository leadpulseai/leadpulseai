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

# Import our new modules
from intro_page import render_intro_page, should_show_intro
from customization import (
    render_customization_settings, load_config, save_config, 
    get_system_prompt, apply_custom_styling
)
from multilanguage import (
    detect_language, translate_text, get_ui_text, 
    extract_lead_info_multilingual, calculate_lead_score,
    get_lead_priority, format_lead_summary, render_language_selector,
    get_language_specific_system_prompt
)

# --- Configuration & Initialization --- 
def setup_admin_credentials():
    """Setup admin credentials if not exists."""
    config = load_config()
    
    if not config.get("admin", {}).get("password_hash"):
        # Default admin password: "admin123" (should be changed in production)
        default_password = "admin123"
        password_hash = hashlib.sha256(default_password.encode()).hexdigest()
        
        if "admin" not in config:
            config["admin"] = {}
        config["admin"]["password_hash"] = password_hash
        config["admin"]["username"] = "admin"
        
        save_config(config)

def check_admin_login():
    """Check if user is logged in as admin."""
    return st.session_state.get("admin_logged_in", False)

def admin_login():
    """Handle admin login."""
    st.title("🔐 Admin Login")
    
    config = load_config()
    
    with st.form("admin_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            stored_hash = config.get("admin", {}).get("password_hash")
            stored_username = config.get("admin", {}).get("username", "admin")
            
            if username == stored_username and password_hash == stored_hash:
                st.session_state.admin_logged_in = True
                st.success("✅ Login successful!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    
    st.info("💡 Default credentials: admin / admin123")

# Ensure API key is set in Streamlit secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except KeyError:
    st.error("OpenAI API key not found. Please add it to your Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error initializing OpenAI client: {e}")
    st.stop()

def save_lead_to_csv(lead_data: Dict, language: str = "en"):
    """Save lead data to CSV file."""
    csv_file = "leads.csv"
    
    # Prepare lead data with metadata
    lead_record = {
        "timestamp": datetime.now().isoformat(),
        "lead_id": str(uuid.uuid4())[:8],
        "name": lead_data.get("name", ""),
        "email": lead_data.get("email", ""),
        "phone": lead_data.get("phone", ""),
        "company": lead_data.get("company", ""),
        "interest": lead_data.get("interest", ""),
        "budget": lead_data.get("budget", ""),
        "language": language,
        "score": calculate_lead_score(lead_data, load_config()),
        "priority": get_lead_priority(calculate_lead_score(lead_data, load_config()), language)[0],
        "status": "new"
    }
    
    # Check if file exists
    file_exists = os.path.isfile(csv_file)
    
    # Write to CSV
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=lead_record.keys())
        
        # Write header if file is new
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(lead_record)
    
    return lead_record["lead_id"]

def get_openai_response(language: str = "en"):
    """Get response from OpenAI based on conversation history."""
    config = load_config()
    
    # Get base system prompt
    base_prompt = get_system_prompt(
        config["industry_template"], 
        config["tone"], 
        language
    )
    
    # Add language-specific instructions
    system_prompt = get_language_specific_system_prompt(base_prompt, language)
    
    # Prepare messages for OpenAI
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (limit to last 10 messages for context)
    recent_messages = st.session_state.messages[-10:]
    for message in recent_messages:
        messages.append(message)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return get_ui_text("error_message", language)

def render_lead_dashboard():
    """Render the lead dashboard."""
    st.header("📊 Lead Dashboard")
    
    # Load leads from CSV
    if os.path.exists("leads.csv"):
        df = pd.read_csv("leads.csv")
        
        if not df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Leads", len(df))
            
            with col2:
                high_priority = len(df[df['priority'] == 'high'])
                st.metric("High Priority", high_priority)
            
            with col3:
                avg_score = df['score'].mean()
                st.metric("Avg Score", f"{avg_score:.1f}")
            
            with col4:
                today_leads = len(df[df['timestamp'].str.contains(datetime.now().strftime('%Y-%m-%d'))])
                st.metric("Today's Leads", today_leads)
            
            # Filters
            st.subheader("🔍 Filters")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                priority_filter = st.selectbox(
                    "Priority", 
                    ["All", "high", "medium", "low"]
                )
            
            with col2:
                language_filter = st.selectbox(
                    "Language",
                    ["All"] + list(df['language'].unique())
                )
            
            with col3:
                status_filter = st.selectbox(
                    "Status",
                    ["All"] + list(df['status'].unique())
                )
            
            # Apply filters
            filtered_df = df.copy()
            
            if priority_filter != "All":
                filtered_df = filtered_df[filtered_df['priority'] == priority_filter]
            
            if language_filter != "All":
                filtered_df = filtered_df[filtered_df['language'] == language_filter]
            
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            # Display leads table
            st.subheader("📋 Leads")
            
            if not filtered_df.empty:
                # Sort by score (highest first)
                filtered_df = filtered_df.sort_values('score', ascending=False)
                
                # Display table
                st.dataframe(
                    filtered_df[['timestamp', 'name', 'email', 'company', 'score', 'priority', 'status']],
                    use_container_width=True
                )
                
                # Export functionality
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📥 Export to CSV"):
                        csv_data = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name=f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with col2:
                    if st.button("📊 Generate Report"):
                        st.info("Report generation feature coming soon!")
            
            else:
                st.info("No leads match the selected filters.")
        
        else:
            st.info("No leads found. Start chatting to generate leads!")
    
    else:
        st.info("No leads data available yet. The CSV file will be created when the first lead is captured.")

def admin_page():
    """Render the admin dashboard."""
    setup_admin_credentials()
    
    if not check_admin_login():
        admin_login()
        return
    
    st.title("🛠️ Lia Admin Dashboard")
    
    # Logout button
    if st.button("🚪 Logout", key="admin_logout"):
        st.session_state.admin_logged_in = False
        st.rerun()
    
    # Admin navigation
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎨 Customization", "⚙️ Settings"])
    
    with tab1:
        render_lead_dashboard()
    
    with tab2:
        render_customization_settings()
    
    with tab3:
        st.header("⚙️ System Settings")
        
        config = load_config()
        
        # Admin settings
        st.subheader("👤 Admin Account")
        
        with st.form("change_password"):
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Change Password"):
                if new_password and new_password == confirm_password:
                    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                    config["admin"]["password_hash"] = password_hash
                    save_config(config)
                    st.success("✅ Password changed successfully!")
                else:
                    st.error("❌ Passwords don't match or are empty!")
        
        # System info
        st.subheader("📋 System Information")
        st.info(f"**Config File:** config.json")
        st.info(f"**Leads File:** leads.csv")
        st.info(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def chat_page():
    """Render the main chat page."""
    config = load_config()
    
    # Apply custom styling
    st.markdown(apply_custom_styling(config), unsafe_allow_html=True)
    
    # Get current language
    language = render_language_selector()
    
    # Page title with branding
    st.title(f"{config['branding']['logo_url']} {config['branding']['name']}")
    st.caption(get_ui_text("welcome", language))
    
    # Initialize chat history
    if "messages" not in st.session_state:
        welcome_msg = config.get("welcome_message", get_ui_text("welcome", language))
        if language != "en":
            welcome_msg = translate_text(welcome_msg, language)
        
        st.session_state.messages = [
            {"role": "assistant", "content": welcome_msg}
        ]
    
    # Initialize lead data
    if "lead_data" not in st.session_state:
        st.session_state.lead_data = {
            "name": None, "email": None, "phone": None, 
            "company": None, "interest": None, "budget": None
        }
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    prompt = st.chat_input(get_ui_text("input_placeholder", language))
    
    if prompt:
        # Detect language if auto-detection is enabled
        detected_language = detect_language(prompt)
        if detected_language != language:
            st.session_state.language = detected_language
            language = detected_language
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Extract lead info using language-specific patterns
        old_lead_data = st.session_state.lead_data.copy()
        st.session_state.lead_data = extract_lead_info_multilingual(
            prompt, language, st.session_state.lead_data
        )
        
        # Check if new lead info was captured
        lead_info_updated = old_lead_data != st.session_state.lead_data
        
        # Get response from OpenAI
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                assistant_response = get_openai_response(language)
            st.markdown(assistant_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
        # Save lead if significant info was captured
        if lead_info_updated and (st.session_state.lead_data.get("email") or st.session_state.lead_data.get("phone")):
            lead_id = save_lead_to_csv(st.session_state.lead_data, language)
            st.success(f"✅ Lead information saved! ID: {lead_id}")
        
        # Rerun to update the chat display
        st.rerun()
    
    # Sidebar with lead information
    with st.sidebar:
        st.header("📋 Current Lead Info")
        
        # Calculate and display lead score
        score = calculate_lead_score(st.session_state.lead_data, config)
        priority, priority_text, priority_icon = get_lead_priority(score, language)
        
        # Lead score display
        st.metric(
            get_ui_text("lead_score", language), 
            f"{score}/100",
            help="Score based on information provided"
        )
        
        # Priority indicator
        st.markdown(f"**{priority_icon} {priority_text}**")
        
        # Lead information summary
        if any(st.session_state.lead_data.values()):
            st.markdown("### " + get_ui_text("contact_info", language))
            lead_summary = format_lead_summary(st.session_state.lead_data, language)
            st.markdown(lead_summary)
        else:
            st.info(get_ui_text("lead_captured", language))
        
        # Quick actions
        st.markdown("---")
        
        if st.button("🔄 Reset Chat"):
            st.session_state.messages = [
                {"role": "assistant", "content": get_ui_text("welcome", language)}
            ]
            st.session_state.lead_data = {
                "name": None, "email": None, "phone": None, 
                "company": None, "interest": None, "budget": None
            }
            st.rerun()
        
        if st.button("📊 View Dashboard"):
            st.query_params.admin = "true"
            st.rerun()

def main():
    """Main application function."""
    # Setup page config
    st.set_page_config(
        page_title="Lia - AI Lead Assistant",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    if "show_intro" not in st.session_state:
        config = load_config()
        st.session_state.show_intro = config.get("intro", {}).get("enabled", True)
    
    # Check URL parameters for admin access
    query_params = st.query_params
    
    if "admin" in query_params:
        admin_page()
    elif st.session_state.get("show_intro", True) and should_show_intro():
        render_intro_page()
    else:
        chat_page()

if __name__ == "__main__":
    main()
