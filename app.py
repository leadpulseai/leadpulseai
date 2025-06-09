import streamlit as st
from openai import OpenAI
import os
import re
from datetime import datetime

# --- Configuration & Initialization --- 

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

# --- UI Branding & Styling --- 
st.markdown(""" <style> 
body { 
    background-color: #ffffff; 
    /* Optional: Add background image if needed, ensure URL is correct */
    /* background-image: url('...'); */
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
</style> """, unsafe_allow_html=True)

st.title("Lia - Your AI Lead Assistant")

# --- Session State Management --- 

# Initialize chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Lia, your AI assistant from LeadPulse. How can I help you today?"}]

# Initialize lead data in session state if it doesn't exist
if "lead_data" not in st.session_state:
    st.session_state.lead_data = {"name": None, "email": None, "phone": None, "interest": None, "company": None} # Added company

# --- Core Functions --- 

def extract_lead_info(user_input: str):
    """Extracts lead information using regex and updates session state."""
    lead_data = st.session_state.lead_data
    updated = False
    user_input_lower = user_input.lower() # Work with lowercase for matching

    # Email Extraction
    if not lead_data["email"]:
        match = re.search(r"[\w.\-+%]+@[\w.-]+\.[a-zA-Z]{2,}", user_input, re.IGNORECASE)
        if match:
            lead_data["email"] = match.group()
            st.toast(f"📧 Email captured: {lead_data['email']}")
            updated = True

    # Phone Extraction (More flexible)
    if not lead_data["phone"]:
        # Look for sequences of 7-15 digits, possibly with spaces/hyphens
        # Triggered by phrases like "my phone is", "call me at", or just finds a likely number
        match = re.search(r"(?:my\s+phone(?:\s+number)?\s+is|call\s+me\s+at)?\s*(\+?[\d\s-]{7,15}\d)\b", user_input_lower)
        if match:
            # Clean up the extracted number (remove non-digits, except leading +)
            phone_number = re.sub(r"[()\s-]", "", match.group(1))
            lead_data["phone"] = phone_number
            st.toast(f"📞 Phone captured: {lead_data['phone']}")
            updated = True

    # Name Extraction (Refined)
    if not lead_data["name"]:
        match = re.search(r"(?:my\s+name\s+is|I\'m|I\s+am|call\s+me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", user_input, re.IGNORECASE) # Use original case input here
        if match:
            lead_data["name"] = match.group(1).strip()
            st.toast(f"👤 Name captured: {lead_data['name']}")
            updated = True

    # Interest Extraction (More flexible)
    if not lead_data["interest"]:
        # Added "my interest is"
        match = re.search(r"(?:interested\s+in|looking\s+for|need\s+help\s+with|my\s+interest\s+is)\s+(.+)", user_input_lower)
        if match:
            interest = match.group(1).strip()
            if len(interest.split()) < 15: 
                lead_data["interest"] = interest.capitalize() # Capitalize first letter
                st.toast(f"💡 Interest captured: {lead_data['interest']}")
                updated = True
                
    # Company Extraction
    if not lead_data["company"]:
        match = re.search(r"(?:work\s+at|work\s+for|my\s+company\s+is|from\s+the\s+company)\s+([A-Z][A-Za-z\s&.,\[\]\{\}\\'-]+)", user_input, re.IGNORECASE) # Use original case input
        if match:
            lead_data["company"] = match.group(1).strip()
            st.toast(f"🏢 Company captured: {lead_data['company']}")
            updated = True
            
    if updated:
        st.session_state.lead_data = lead_data

def get_openai_response(): # Removed prompt argument, uses session state directly
    """Gets a response from OpenAI based on the current conversation history."""
    # Ensure the latest user message is in session state before calling API
    if not st.session_state.messages or st.session_state.messages[-1]["role"] != "user":
        # This should ideally not happen if called correctly, but safety check
        return "Hmm, I seem to have missed what you just said. Could you please repeat that?"
        
    try:
        system_prompt = {"role": "system", "content": "You are Lia, a friendly and helpful AI lead generation assistant for LeadPulse. Your goal is to understand the user's needs, collect relevant information (name, email, company, phone, interest) naturally through conversation, and qualify them as a lead. Be conversational and engaging. Ask clarifying questions if needed. Keep responses concise and friendly."}
        messages_for_api = [system_prompt] + st.session_state.messages # Send the whole history
        
        print(f"DEBUG: Sending to OpenAI: {messages_for_api}") # Debug print

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_api,
            temperature=0.7,
            max_tokens=150
        )
        response_content = completion.choices[0].message.content
        
        print(f"DEBUG: Received from OpenAI: {response_content}") # Debug print
        return response_content

    except Exception as e:
        print(f"ERROR: OpenAI API call failed: {e}") # Debug print for error
        st.error(f"Error communicating with OpenAI: {e}")
        return "Sorry, I encountered a technical glitch. Please give me a moment and try again."

# --- Main Chat Interface Logic --- 

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What can Lia help you with?"):
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to chat history *first*
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Extract lead info from the latest prompt
    extract_lead_info(prompt)

    # Get response from OpenAI (uses history including the latest prompt)
    assistant_response = get_openai_response()

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    # Rerun to update the chat display smoothly
    st.rerun()

# --- Sidebar for Debugging/Display --- 
st.sidebar.header("Collected Lead Data")
st.sidebar.json(st.session_state.lead_data)

# --- Footer --- 
st.markdown("<div class='footer'>Powered by LeadPulse & Manus</div>", unsafe_allow_html=True)