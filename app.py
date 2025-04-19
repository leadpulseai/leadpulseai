import streamlit as st
from openai import OpenAI
import os
import re

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Custom CSS for OpenAI-style UI
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
            font-family: 'Segoe UI', sans-serif;
        }
        .chat-box {
            background-color: #f1f1f1;
            padding: 1rem;
            border-radius: 12px;
            margin: 1rem 0;
        }
        .user-msg {
            background-color: #e8f0fe;
            color: #202124;
            text-align: right;
            padding: 0.8rem;
            border-radius: 10px;
            margin-bottom: 5px;
        }
        .bot-msg {
            background-color: #f8f9fa;
            color: #3c4043;
            padding: 0.8rem;
            border-radius: 10px;
            margin-bottom: 5px;
        }
        .footer {
            text-align: center;
            font-size: 0.8rem;
            color: #888;
            margin-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# Session State Setup
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Lia, a helpful lead assistant. Greet the user and collect their name, email, and interest."}
    ]

lead_data = {"name": None, "email": None, "interest": None}

# Extract lead info
def extract_lead_info(user_input):
    if not lead_data['email']:
        email_match = re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', user_input)
        if email_match:
            lead_data['email'] = email_match.group()
            st.success(f"📧 Email captured: {lead_data['email']}")

    if not lead_data['name'] and "my name is" in user_input.lower():
        lead_data['name'] = user_input.split("is")[-1].strip().split()[0]

    if not lead_data['interest'] and "interested in" in user_input.lower():
        lead_data['interest'] = user_input.split("interested in")[-1].strip().split('.')[0]
        st.success(f"✅ Interest captured: {lead_data['interest']}")

# UI - Welcome
st.title("LeadPulse - Your AI-Powered Lead Assistant")
st.header("What can I help with?")

# Input box (opens a chat-style input and clears automatically)
user_input = st.chat_input("Type your message...")

# Process input
if user_input:
    # Extract and save lead info
    extract_lead_info(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Show typing spinner
    with st.spinner("Lia is typing..."):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

if prompt_input:
    extract_lead_info(prompt_input)
    st.session_state.messages.append({"role": "user", "content": prompt_input})

    with st.spinner("Lia is typing..."):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

# Show messages
st.write("""<div class='chat-box'>""", unsafe_allow_html=True)
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>{msg['content']}</div>", unsafe_allow_html=True)
st.write("""</div>""", unsafe_allow_html=True)

# Footer
st.markdown("""<div class='footer'>FOUNDER  Shayan Faisal </div>""", unsafe_allow_html=True)
