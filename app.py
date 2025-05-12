import streamlit as st
from openai import OpenAI
import os
import re
import random

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Custom CSS for OpenAI-style UI + send-arrow hover
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
            max-height: 60vh;
            overflow-y: auto;
        }
        .user-msg {
            background-color: #e8f0fe;
            color: #202124;
            text-align: right;
            padding: 0.8rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
            max-width: 75%;
            margin-left: 25%;
        }
        .bot-msg {
            background-color: #f8f9fa;
            color: #3c4043;
            padding: 0.8rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
            max-width: 75%;
        }
        button[data-testid="stMarkdownContainer"] svg:hover {
            stroke: #1a73e8;
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
        {
            "role": "system",
            "content": (
                "You are Lia, a friendly AI lead assistant. "
                "Greet the user, then ask for their name, email, and interest in a natural way."
            )
        }
    ]

lead_data = {"name": None, "email": None, "interest": None}

# Extract lead info
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
        lead_data["interest"] = user_input.split("interested in")[-1].strip().split(".")[0]
        st.success(f"✅ Interest captured: {lead_data['interest']}")

# UI – Header
st.title("LeadPulse 🚀")
st.header("What can I help with?")

# Dynamic placeholders
examples = [
    "I am interested in social media",
    "My name is Jane",
    "Tell me about lead generation",
    "Explain in 30 seconds"
]
if "ph_idx" not in st.session_state:
    st.session_state.ph_idx = 0
placeholder = examples[st.session_state.ph_idx]
st.session_state.ph_idx = (st.session_state.ph_idx + 1) % len(examples)

# Chat-style input (✅ FIXED input syntax)

user_prompt = st.chat_input(placeholder)

# Process input with safety
if user_prompt:
    try:
        extract_lead_info(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        with st.spinner("Lia is typing..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content

        st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"❌ Error generating Lia's response: {e}")

# Display the chat
st.markdown("<div class='chat-box'>", unsafe_allow_html=True)
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>{msg['content']}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Footer credit
st.markdown(
    "<div class='footer'>Built with ❤️ by Shayan Faisal and Co‑Founder</div>",
    unsafe_allow_html=True
)
