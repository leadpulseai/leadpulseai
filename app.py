import streamlit as st
from openai import OpenAI
import os
import re

# Initialize OpenAI client
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
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .bot-msg {
        background-color: #f8f9fa;
        color: #202124;
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .flipping-text {
        font-weight: 600;
        font-size: 1.4rem;
        animation: flip 4s infinite;
        color: #0b57d0;
    }
    @keyframes flip {
        0% { opacity: 0; transform: translateY(10px); }
        20% { opacity: 1; transform: translateY(0); }
        80% { opacity: 1; transform: translateY(0); }
        100% { opacity: 0; transform: translateY(-10px); }
    }
    </style>
""", unsafe_allow_html=True)

# Flipping text sequence
flipping_prompts = [
    "Generate leads instantly",
    "Collect emails effortlessly",
    "Grow your business with AI"
]

# Simulate flipping prompts (basic simulation)
flipper_index = st.session_state.get("flip_index", 0)
st.session_state.flip_index = (flipper_index + 1) % len(flipping_prompts)
st.markdown(f"<div class='flipping-text'>{flipping_prompts[flipper_index]}</div>", unsafe_allow_html=True)

st.markdown("""
    <h1 style='text-align: center;'>What can I help with?</h1>
""", unsafe_allow_html=True)

# Session state setup
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Lia, a friendly and smart AI lead assistant."}
    ]

lead_data = {"name": None, "email": None, "interest": None}

def extract_lead_info(user_input):
    if not lead_data['email']:
        match = re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', user_input)
        if match:
            lead_data['email'] = match.group()
            st.success(f"📧 Email captured: {lead_data['email']}")

    if not lead_data['name'] and "my name is" in user_input.lower():
        lead_data['name'] = user_input.split("is")[1].strip().split()[0]

# Input box
prompt = st.text_input("", placeholder="Ask anything...", label_visibility="collapsed")

if prompt:
    extract_lead_info(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages
    )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})

# Chat display
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>{msg['content']}</div>", unsafe_allow_html=True)
# Signature footer
st.markdown(
    "<div style='text-align: center; margin-top: 2rem; color: grey;'>"
    "Built with ❤️ by <strong>Shayan Faisal</strong> and Co-Founder"
    "</div>",
    unsafe_allow_html=True
)
# Minor update to trigger redeploy
