import streamlit as st
from openai import OpenAI
import os
import re

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Custom CSS for Perplexity-style Premium Background
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
            background-image: url('https://upload.wikimedia.org/wikipedia/commons/8/88/Example_logo.png'); /* Replace with real logo */
            background-repeat: no-repeat;
            background-position: center center;
            background-size: 150px;
            background-attachment: fixed;
            font-family: 'Segoe UI', sans-serif;
        }
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            height: 100%;
            width: 100%;
            background-image: linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px), 
                              linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            z-index: -1;
        }
        .chat-box {
            background-color: #f1f1f1;
            padding: 1rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            max-height: 65vh;
            overflow-y: auto;
        }
        .user-msg {
            background-color: #e8f0fe;
            color: #202124;
            text-align: right;
            padding: 0.8rem;
            border-radius: 10px;
            margin-bottom: 5px;
            max-width: 75%;
            margin-left: 25%;
        }
        .bot-msg {
            background-color: #f8f9fa;
            color: #3c4043;
            padding: 0.8rem;
            border-radius: 10px;
            margin-bottom: 5px;
            max-width: 75%;
        }
        .footer {
            text-align: center;
            font-size: 0.8rem;
            color: #999;
            margin-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# Session State Setup
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Lia, a helpful AI lead assistant. Greet the user and capture their name, email, and interest."}
    ]

lead_data = {"name": None, "email": None, "interest": None}

# Extract Lead Info
def extract_lead_info(user_input: str):
    if not lead_data["email"]:
        m = re.search(r"\b[\w.-]+@[\w.-]+\.\w+\b", user_input)
        if m:
            lead_data["email"] = m.group()
            st.success(f"📧 Email captured: {lead_data['email']}")

    if not lead_data["name"] and "my name is" in user_input.lower():
        lead_data["name"] = user_input.split("my name is")[-1].strip().split()[0].capitalize()
        st.success(f"😊 Name captured: {lead_data['name']}")

    if not lead_data["interest"] and "interested in" in user_input.lower():
        lead_data["interest"] = user_input.split("interested in")[-1].strip().split('.')[0]
        st.success(f"✅ Interest captured: {lead_data['interest']}")

# App UI
st.title("LeadPulse 🚀")

import time
examples = [
    "Ask me anything about your business...",
    "How can I help you grow today?",
    "Need help capturing leads?",
    "Ask Lia for anything!",
    "Tell me your business goals..."
]
if "ph_idx" not in st.session_state:
    st.session_state.ph_idx = 0
placeholder = examples[st.session_state.ph_idx]
st.session_state.ph_idx = (st.session_state.ph_idx + 1) % len(examples)

# Typing bar input
user_prompt = st.chat_input(placeholder=placeholder)

# Process input
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    extract_lead_info(user_prompt)

    with st.spinner("Lia is thinking..."):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": reply})

# Display chat messages
st.write("""<div class='chat-box'>""", unsafe_allow_html=True)
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>{msg['content']}</div>", unsafe_allow_html=True)
st.write("""</div>""", unsafe_allow_html=True)

# Footer
st.markdown("""<div class='footer'>Built with ❤️ by Founder Shayan Faisal & Co-Founder</div>""", unsafe_allow_html=True)
