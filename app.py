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

    # Email Extraction
    if not lead_data["email"]:
        match = re.search(r"[\w.\-+%]+@[\w.-]+\.[a-zA-Z]{2,}", user_input, re.IGNORECASE)
        if match:
            lead_data["email"] = match.group()
            st.toast(f"📧 Email captured: {lead_data['email']}")
            updated = True

    # Phone Extraction (Improved slightly)
    if not lead_data["phone"]:
        # Looks for sequences of digits, possibly with spaces, hyphens, parentheses, starting with optional +
        match = re.search(r"(\+?\d{1,3}[-\s.]?)?(\(?\d{3}\)?[-\s.]?)?\d{3}[-\s.]?\d{4}\b", user_input)
        if match:
            # Clean up the extracted number (remove non-digits, except leading +)
            phone_number = re.sub(r"[()\s-]", "", match.group())
            lead_data["phone"] = phone_number
            st.toast(f"📞 Phone captured: {lead_data['phone']}")
            updated = True

    # Name Extraction (Refined)
    if not lead_data["name"]:
        # Look for patterns like "my name is [Name]", "I'm [Name]", "call me [Name]"
        # Captures one or more capitalized words following the pattern
        match = re.search(r"(?:my\s+name\s+is|I'm|I\s+am|call\s+me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", user_input, re.IGNORECASE)
        if match:
            lead_data["name"] = match.group(1).strip()
            st.toast(f"👤 Name captured: {lead_data['name']}")
            updated = True

    # Interest Extraction
    if not lead_data["interest"]:
        match = re.search(r"(?:interested\s+in|looking\s+for|need\s+help\s+with)\s+(.+)", user_input, re.IGNORECASE)
        if match:
            # Simple capture, might need refinement based on common interests
            interest = match.group(1).strip()
            # Avoid capturing overly long sentences
            if len(interest.split()) < 15: 
                lead_data["interest"] = interest
                st.toast(f"💡 Interest captured: {lead_data['interest']}")
                updated = True
                
    # Company Extraction (New)
    if not lead_data["company"]:
        match = re.search(r"(?:work\s+at|work\s+for|my\s+company\s+is|from\s+the\s+company)\s+([A-Z][A-Za-z\s&.,'-]+)", user_input, re.IGNORECASE)
        if match:
            lead_data["company"] = match.group(1).strip()
            st.toast(f"🏢 Company captured: {lead_data['company']}")
            updated = True
            
    # Update session state explicitly if changes were made
    if updated:
        st.session_state.lead_data = lead_data

def get_openai_response(prompt: str):
    """Gets a response from OpenAI based on the current conversation history."""
    # Add the user's prompt to the history before sending to OpenAI
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # Construct messages payload for OpenAI
        # Optional: Add a system prompt to guide Lia's behavior
        system_prompt = {"role": "system", "content": "You are Lia, a friendly and helpful AI lead generation assistant for LeadPulse. Your goal is to understand the user's needs, collect relevant information (name, email, company, interest) naturally through conversation, and qualify them as a lead. Be conversational and engaging. Ask clarifying questions if needed. Keep responses concise."}
        messages_for_api = [system_prompt] + st.session_state.messages
        
        # Make the API call
        completion = client.chat.completions.create(
            model="gpt-4o", # Or your preferred model
            messages=messages_for_api,
            temperature=0.7, # Adjust for creativity vs. predictability
            max_tokens=150 # Limit response length
        )
        response_content = completion.choices[0].message.content
        return response_content

    except Exception as e:
        st.error(f"Error communicating with OpenAI: {e}")
        # Provide a fallback response
        return "Sorry, I'm having trouble connecting right now. Please try again in a moment."

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

    # Extract lead info from the user's prompt *before* getting AI response
    extract_lead_info(prompt)

    # Get response from OpenAI (this function now also appends the user message to history)
    assistant_response = get_openai_response(prompt)

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