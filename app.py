import streamlit as st
from openai import OpenAI
import os
import re
from datetime import datetime

# Use Streamlit's secrets for cloud compatibility

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)
# UI Branding (Keep your st.markdown CSS here)
st.markdown(""" <style> ... </style> """, unsafe_allow_html=True)

st.title("Lia - Your AI Lead Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Lia. How can I help you today?"}]

# Initialize lead data in session state
if "lead_data" not in st.session_state:
    st.session_state.lead_data = {"name": None, "email": None, "phone": None, "interest": None}

# --- Function Definition --- 
def extract_lead_info(user_input: str):
    # Use st.session_state.lead_data instead of the global one
    lead_data = st.session_state.lead_data 
    
    # Check for email if not already found
    if not lead_data["email"]:
        match = re.search(r"[\w.-]+@[\w.-]+\.\w+", user_input, re.IGNORECASE)
        if match:
            lead_data["email"] = match.group()
            st.toast(f"📧 Email captured: {lead_data["email"]}") # Use toast for subtle confirmation

    # Check for phone if not already found
    if not lead_data["phone"]:
        # Basic North American/International format check - refine as needed
        match = re.search(r"\+?\d[\d\s-]{8,}\d", user_input)
        if match:
            lead_data["phone"] = match.group()
            st.toast(f"📞 Phone captured: {lead_data["phone"]}")

    # Check for name (simple example: "my name is ...")
    if not lead_data["name"]:
        match = re.search(r"my name is\s+([a-zA-Z\s]+)", user_input, re.IGNORECASE)
        if match:
            lead_data["name"] = match.group(1).strip().title()
            st.toast(f"👤 Name captured: {lead_data["name"]}")
            
    # Check for interest (simple example: "interested in ...")
    if not lead_data["interest"]:
        match = re.search(r"interested in\s+(.+)", user_input, re.IGNORECASE)
        if match:
            lead_data["interest"] = match.group(1).strip()
            st.toast(f"💡 Interest captured: {lead_data["interest"]}")

# --- Chat Display and Input Logic --- 

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What can Lia help you with?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Extract lead info from the user's prompt
    extract_lead_info(prompt)

    # --- !! Placeholder for OpenAI response !! ---
    # For now, just acknowledge receipt and show extracted data
    response = f"Got it! Let me see... \n (Current Lead Info: {st.session_state.lead_data})"
    # --- !! End Placeholder !! ---

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Optional: Display collected lead data somewhere persistent (e.g., sidebar)
st.sidebar.write("Collected Lead Data:")
st.sidebar.json(st.session_state.lead_data)

# Footer
st.markdown("<div class='footer'>Powered by LeadPulse & Manus</div>", unsafe_allow_html=True)
