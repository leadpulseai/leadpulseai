import streamlit as st
from openai import OpenAI
import os
import re
import json
import csv
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import uuid
import base64
import io
import hashlib

# --- Configuration & Initialization --- 

# File paths
LEADS_CSV_PATH = "leads.csv"
ADMIN_CREDENTIALS_PATH = "admin_credentials.json"

# Default admin credentials (only used if credentials file doesn't exist)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "leadpulse2025"

# Default notification email (change this to your preferred email)
DEFAULT_NOTIFICATION_EMAIL = "notifications@leadpulse.ai"

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

# --- Helper Functions ---

def setup_admin_credentials():
    """Setup admin credentials if they don't exist."""
    if not os.path.exists(ADMIN_CREDENTIALS_PATH):
        credentials = {
            "username": DEFAULT_ADMIN_USERNAME,
            "password_hash": hashlib.sha256(DEFAULT_ADMIN_PASSWORD.encode()).hexdigest(),
            "notification_email": DEFAULT_NOTIFICATION_EMAIL
        }
        with open(ADMIN_CREDENTIALS_PATH, 'w') as f:
            json.dump(credentials, f)
        return credentials
    else:
        with open(ADMIN_CREDENTIALS_PATH, 'r') as f:
            return json.load(f)

def setup_leads_csv():
    """Setup leads CSV file if it doesn't exist."""
    if not os.path.exists(LEADS_CSV_PATH):
        with open(LEADS_CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'lead_id', 'timestamp', 'name', 'email', 'phone', 'company', 
                'industry', 'interest', 'pain_points', 'buying_signals', 
                'lead_score', 'lead_status', 'conversation_summary'
            ])

def save_lead_to_csv(lead_data, conversation_summary):
    """Save lead data to CSV file."""
    setup_leads_csv()
    
    # Generate a unique ID for the lead if not present
    if 'lead_id' not in lead_data:
        lead_data['lead_id'] = str(uuid.uuid4())
    
    # Prepare row data
    row = [
        lead_data['lead_id'],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        lead_data['name'] or '',
        lead_data['email'] or '',
        lead_data['phone'] or '',
        lead_data['company'] or '',
        lead_data['industry'] or '',
        lead_data['interest'] or '',
        lead_data['pain_points'] or '',
        ', '.join(lead_data['buying_signals']) if lead_data['buying_signals'] else '',
        lead_data['lead_score'],
        lead_data['lead_status'],
        conversation_summary
    ]
    
    # Append to CSV
    with open(LEADS_CSV_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)
    
    return lead_data['lead_id']

def send_email_notification(lead_data):
    """Send email notification about new lead."""
    try:
        # Get notification email from admin credentials
        admin_credentials = setup_admin_credentials()
        recipient_email = admin_credentials.get('notification_email', DEFAULT_NOTIFICATION_EMAIL)
        
        # Only send if we have an email and either a name or company
        if lead_data['email'] and (lead_data['name'] or lead_data['company']):
            # Get SMTP settings from Streamlit secrets
            smtp_server = st.secrets.get("SMTP_SERVER", "")
            smtp_port = st.secrets.get("SMTP_PORT", 587)
            smtp_username = st.secrets.get("SMTP_USERNAME", "")
            smtp_password = st.secrets.get("SMTP_PASSWORD", "")
            
            if not smtp_server or not smtp_username or not smtp_password:
                print("SMTP settings not configured. Email notification skipped.")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = recipient_email
            msg['Subject'] = f"New Lead Alert: {lead_data['name'] or lead_data['email']} - {lead_data['lead_status']}"
            
            # Create email body
            body = f"""
            <html>
            <body>
                <h2>New Lead Captured by Lia!</h2>
                <p><strong>Lead Status:</strong> {lead_data['lead_status']} ({lead_data['lead_score']}/100)</p>
                <p><strong>Name:</strong> {lead_data['name'] or 'Not provided'}</p>
                <p><strong>Email:</strong> {lead_data['email']}</p>
                <p><strong>Phone:</strong> {lead_data['phone'] or 'Not provided'}</p>
                <p><strong>Company:</strong> {lead_data['company'] or 'Not provided'}</p>
                <p><strong>Industry:</strong> {lead_data['industry'] or 'Not provided'}</p>
                <p><strong>Interest:</strong> {lead_data['interest'] or 'Not provided'}</p>
                <p><strong>Pain Points:</strong> {lead_data['pain_points'] or 'Not identified'}</p>
                <p><strong>Buying Signals:</strong> {', '.join(lead_data['buying_signals']) if lead_data['buying_signals'] else 'None detected'}</p>
                <p><strong>Captured At:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p><a href="{st.secrets.get('APP_URL', 'https://leadpulseai.streamlit.app')}/admin">View in Dashboard</a></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            return True
    except Exception as e:
        print(f"Error sending email notification: {e}")
    
    return False

def get_conversation_summary():
    """Generate a summary of the conversation."""
    if len(st.session_state.messages) < 3:
        return "Conversation too short for summary."
    
    try:
        # Prepare the conversation history
        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
        
        # Create the summary prompt
        summary_prompt = f"""
        Summarize this conversation between a lead and an AI assistant in 2-3 sentences.
        Focus on the key points, interests, and needs expressed by the lead.
        
        Conversation:
        {conversation}
        """
        
        # Call OpenAI API for summary
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.3,
            max_tokens=100
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating conversation summary: {e}")
        return "Error generating summary."

def get_table_download_link(df, filename, text):
    """Generate a link to download the dataframe as a file."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def get_excel_download_link(df, filename, text):
    """Generate a link to download the dataframe as an Excel file."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'
    return href

# --- UI Branding & Styling --- 
st.markdown(""" <style> 
body { 
    background-color: #ffffff; 
    background-repeat: no-repeat; 
    background-position: center center; 
    background-size: 150px; 
    background-attachment: fixed; 
    font-family: 'Segoe UI', sans-serif; 
}
/* Optional: Grid pattern background */
body::before { 
    content: ""; 
    position: fixed; 
    top: 0; left: 0; 
    height: 100%; width: 100%; 
    background-image: linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px), linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px); 
    background-size: 60px 60px; 
    z-index: -1; 
}
.stChatMessage {
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    max-width: 75%;
}
.stChatMessage[data-testid="chatAvatarIcon-user"] + div {
    background-color: #e8f0fe; 
    color: #202124;
    margin-left: auto; /* Align user messages to the right */
}
.stChatMessage[data-testid="chatAvatarIcon-assistant"] + div {
    background-color: #f8f9fa; 
    color: #3c4043;
    margin-right: auto; /* Align assistant messages to the left */
}
.footer { 
    text-align: center; 
    font-size: 0.8rem; 
    color: #999; 
    margin-top: 2rem; 
}
.lead-score {
    font-size: 1.5rem;
    font-weight: bold;
    text-align: center;
    margin: 1rem 0;
}
.score-hot {
    color: #ff4b4b;
}
.score-warm {
    color: #ffa64b;
}
.score-cold {
    color: #4b83ff;
}
.admin-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}
.filter-container {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
}
.download-links {
    text-align: right;
    margin: 1rem 0;
}
</style> """, unsafe_allow_html=True)

# --- Page Routing ---
def main():
    # Setup admin credentials
    setup_admin_credentials()
    
    # Check if we're in admin mode
    if "admin" in st.experimental_get_query_params():
        admin_page()
    else:
        chat_page()

def chat_page():
    st.title("Lia - Your AI Lead Assistant")

    # --- Session State Management --- 
    # Initialize chat history if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Lia, your AI assistant from LeadPulse. How can I help you today?"}]

    # Initialize lead data in session state if it doesn't exist
    if "lead_data" not in st.session_state:
        st.session_state.lead_data = {
            "lead_id": str(uuid.uuid4()),
            "name": None, 
            "email": None, 
            "phone": None, 
            "interest": None, 
            "company": None,
            "industry": None,
            "pain_points": None,
            "buying_signals": [],
            "lead_score": 0,
            "lead_status": "New",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # Initialize message counter for periodic analysis
    if "message_counter" not in st.session_state:
        st.session_state.message_counter = 0
        
    # Initialize lead saved flag
    if "lead_saved" not in st.session_state:
        st.session_state.lead_saved = False

    # --- Display existing chat messages ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- React to user input ---
    if prompt := st.chat_input("What can Lia help you with?"):
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Increment message counter
        st.session_state.message_counter += 1

        # Extract lead info using regex
        extract_lead_info_regex(prompt)
        
        # Periodically analyze the conversation with OpenAI
        # Do this every 3 messages to avoid excessive API calls
        if st.session_state.message_counter % 3 == 0:
            analyze_conversation_with_openai()

        # Get response from OpenAI
        assistant_response = get_openai_response()

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(assistant_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
        # Check if we should save the lead
        lead_data = st.session_state.lead_data
        if (lead_data["email"] or lead_data["phone"]) and not st.session_state.lead_saved:
            if lead_data["lead_score"] >= 30 or len(st.session_state.messages) >= 6:
                # Generate conversation summary
                conversation_summary = get_conversation_summary()
                
                # Save lead to CSV
                save_lead_to_csv(lead_data, conversation_summary)
                
                # Send email notification
                send_email_notification(lead_data)
                
                # Mark as saved
                st.session_state.lead_saved = True

        # Rerun to update the chat display smoothly
        st.rerun()

    # --- Sidebar for Lead Data Display --- 
    st.sidebar.header("Lead Intelligence")

    # Display lead score with color coding
    score = st.session_state.lead_data["lead_score"]
    status = st.session_state.lead_data["lead_status"]
    score_class = f"score-{status.lower()}"

    st.sidebar.markdown(f"""
    <div class="lead-score {score_class}">
        Lead Score: {score}/100<br>
        Status: {status}
    </div>
    """, unsafe_allow_html=True)

    # Display collected lead data
    st.sidebar.subheader("Collected Lead Data")
    lead_display = {
        "Name": st.session_state.lead_data["name"] or "Not captured",
        "Email": st.session_state.lead_data["email"] or "Not captured",
        "Phone": st.session_state.lead_data["phone"] or "Not captured",
        "Company": st.session_state.lead_data["company"] or "Not captured",
        "Industry": st.session_state.lead_data["industry"] or "Not captured",
        "Interest": st.session_state.lead_data["interest"] or "Not captured",
        "Pain Points": st.session_state.lead_data["pain_points"] or "Not captured",
        "Buying Signals": ", ".join(st.session_state.lead_data["buying_signals"]) if st.session_state.lead_data["buying_signals"] else "None detected",
        "Last Updated": st.session_state.lead_data["last_updated"]
    }

    for key, value in lead_display.items():
        st.sidebar.text(f"{key}: {value}")
        
    # Admin link
    st.sidebar.markdown("---")
    st.sidebar.markdown("[Admin Dashboard](/admin)", unsafe_allow_html=True)

    # --- Footer --- 
    st.markdown("<div class='footer'>Powered by LeadPulse & Manus</div>", unsafe_allow_html=True)

def admin_page():
    st.title("LeadPulse Admin Dashboard")
    
    # Load admin credentials
    admin_credentials = setup_admin_credentials()
    
    # Check if user is authenticated
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        # Login form
        with st.form("login_form"):
            st.subheader("Admin Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                # Check credentials
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if username == admin_credentials["username"] and password_hash == admin_credentials["password_hash"]:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    else:
        # Admin dashboard
        with st.container():
            st.markdown("<div class='admin-container'>", unsafe_allow_html=True)
            
            # Check if leads file exists
            if not os.path.exists(LEADS_CSV_PATH):
                st.info("No leads captured yet.")
                return
            
            # Load leads data
            leads_df = pd.read_csv(LEADS_CSV_PATH)
            
            if leads_df.empty:
                st.info("No leads captured yet.")
                return
            
            # Convert timestamp to datetime for filtering
            leads_df['timestamp'] = pd.to_datetime(leads_df['timestamp'])
            
            # Dashboard stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Leads", len(leads_df))
            with col2:
                hot_leads = len(leads_df[leads_df['lead_status'] == 'Hot'])
                st.metric("Hot Leads", hot_leads)
            with col3:
                warm_leads = len(leads_df[leads_df['lead_status'] == 'Warm'])
                st.metric("Warm Leads", warm_leads)
            with col4:
                cold_leads = len(leads_df[leads_df['lead_status'] == 'Cold'])
                st.metric("Cold Leads", cold_leads)
            
            # Filters
            st.subheader("Filters")
            with st.expander("Filter Options", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Date range filter
                    min_date = leads_df['timestamp'].min().date()
                    max_date = leads_df['timestamp'].max().date()
                    date_range = st.date_input(
                        "Date Range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    # Status filter
                    statuses = ['All'] + sorted(leads_df['lead_status'].unique().tolist())
                    selected_status = st.selectbox("Lead Status", statuses)
                
                with col2:
                    # Score range filter
                    min_score = int(leads_df['lead_score'].min())
                    max_score = int(leads_df['lead_score'].max())
                    score_range = st.slider(
                        "Lead Score Range",
                        min_score,
                        max_score,
                        (min_score, max_score)
                    )
                    
                    # Search filter
                    search_term = st.text_input("Search (name, email, company)", "")
            
            # Apply filters
            filtered_df = leads_df.copy()
            
            # Date filter
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = filtered_df[
                    (filtered_df['timestamp'].dt.date >= start_date) &
                    (filtered_df['timestamp'].dt.date <= end_date)
                ]
            
            # Status filter
            if selected_status != 'All':
                filtered_df = filtered_df[filtered_df['lead_status'] == selected_status]
            
            # Score filter
            filtered_df = filtered_df[
                (filtered_df['lead_score'] >= score_range[0]) &
                (filtered_df['lead_score'] <= score_range[1])
            ]
            
            # Search filter
            if search_term:
                search_term = search_term.lower()
                filtered_df = filtered_df[
                    filtered_df['name'].fillna('').str.lower().str.contains(search_term) |
                    filtered_df['email'].fillna('').str.lower().str.contains(search_term) |
                    filtered_df['company'].fillna('').str.lower().str.contains(search_