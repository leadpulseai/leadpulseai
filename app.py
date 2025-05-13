import streamlit as st
from openai import OpenAI
import os
import re
from datetime import datetime
from dotenv import load_dotenv 
load_dotenv()                   
st.write("✅ API Key Loaded:", bool(os.getenv("OPENAI_API_KEY")))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 1. Initialize OpenAI client securely
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 2. Custom Perplexity-inspired UI and embedded branding
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
            background-image: url('https://upload.wikimedia.org/wikipedia/commons/8/88/Example_logo.png');
            background-repeat: no-repeat;
            background-position: center center;
            background-size: 150px;
            background-attachment: fixed;
            font-family: 'Segoe UI', sans-serif;
        }
        body::before {
            content: "";
            position: fixed;
            top: 0; left: 0;
            height: 100%; width: 100%;
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
            max-height: 60vh;
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

# 3. Lead data storage
lead_data = {"name": None, "email": None, "phone": None, "interest": None}

# 4. Extract function
def extract_lead_info(user_input: str):
    if not lead_data["email"]:
        match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_input)
        if match:
            lead_data["email"] = match.group()
            st.success(f"📧 Email: {lead_data['email']}")

    if not lead_data["phone"]:
        match = re.search(r"\b\d{10,15}\b", user_input)
        if match:
            lead_data["phone"] = match.group()
            st.success(f"📞 Phone: {lead_data['phone']}")

    if not lead_data["name"] and "my name is" in user_input.lower():
        lead_data["name"] = user_input.split("my name is")[-1].strip().split()[0].capitalize()
        st.success(f"🧑 Name: {lead_data['name']}")

    if not lead_data["interest"] and "interested in" in user_input.lower():
        lead_data["interest"] = user_input.split("interested in")[-1].strip().split('.')[0]
        st.success(f"💼 Interest: {lead_data['interest']}")

    # Save lead to leads.txt
    if all(lead_data.values()):
        with open("leads.txt", "a") as f:
            f.write(f"{lead_data['name']} {lead_data['email']} {lead_data['phone']} {lead_data['interest']} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 5. UI – Header and flipping placeholder
st.title("LeadPulse 🚀")
st.header("What can I help with?")

examples = [
    "I am interested in social media",
    "My name is Ali and I want help",
    "Contact: ali@example.com, 03001234567",
    "What’s the best way to get leads?",
    "I need help with marketing"
]
if "ph_idx" not in st.session_state:
    st.session_state.ph_idx = 0
placeholder = examples[st.session_state.ph_idx]
st.session_state.ph_idx = (st.session_state.ph_idx + 1) % len(examples)

# 6. Session memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Lia, an AI lead assistant. Greet warmly. Ask for user's name, email, phone, and interest smoothly."}
    ]

# 7. Chat input
user_prompt = st.chat_input(placeholder=placeholder)
try:
    test_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Test system"},
            {"role": "user", "content": "Say hello"},
        ]
    )
    st.success("✅ OpenAI Test Passed")
except Exception as e:
    st.error(f"❌ OpenAI Error: {e}")

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

# 8. Display messages
st.write("<div class='chat-box'>", unsafe_allow_html=True)
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>{msg['content']}</div>", unsafe_allow_html=True)
st.write("</div>", unsafe_allow_html=True)

# 9. Footer
st.markdown("<div class='footer'>Built with ❤️ by Founder Shayan Faisal & Co-Founder</div>", unsafe_allow_html=True)
