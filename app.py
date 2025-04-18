import streamlit as st
from openai import OpenAI
import os
import re
import time

# --- Initialization ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Lia, a friendly AI assistant for lead generation. Greet the user, ask their name, email, and what service they’re interested in."}
    ]

lead_data = {"name": None, "email": None, "interest": None}

# --- Landing Page Section ---
st.markdown("""
    <style>
    .hero {
        text-align: center;
        padding: 5rem 2rem 2rem 2rem;
    }
    .headline {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .subtext {
        font-size: 1.25rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .flipper {
        font-style: italic;
        color: #444;
    }
    .chatbox {
        margin-top: 4rem;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 1rem;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="headline">Capture more leads. Close more deals.</div>
    <div class="subtext">Lia helps you qualify leads in seconds and grow faster.</div>
    <div class="flipper" id="fliptext">I can help you generate leads...</div>
    <script>
        let phrases = ["I can help you generate leads...", "Need help engaging visitors?", "Want CRM-ready contacts?", "Let’s grow your business!"];
        let el = document.getElementById("fliptext");
        let i = 0;
        setInterval(() => {
            el.innerText = phrases[i % phrases.length];
            i++;
        }, 3000);
    </script>
</div>
""", unsafe_allow_html=True)

# --- Chat Section ---
st.markdown("<div class='chatbox'>", unsafe_allow_html=True)
st.subheader("💬 Meet Lia – Your AI-Powered Lead Assistant")
user_input = st.text_input("Type your message below:")

# --- Lead Info Extraction ---
def extract_lead_info(text):
    if not lead_data["email"]:
        match = re.search(r"\b[\w.-]+@[\w.-]+\.\w+\b", text)
        if match:
            lead_data["email"] = match.group()
            st.success(f"📧 Email captured: {lead_data['email']}")

    if not lead_data["name"] and "my name is" in text.lower():
        lead_data["name"] = text.split("is")[-1].strip().split()[0]
        st.success(f"👤 Name captured: {lead_data['name']}")

    if not lead_data["interest"] and "interested in" in text.lower():
        lead_data["interest"] = text.split("interested in")[-1].strip()
        st.success(f"🎯 Interest captured: {lead_data['interest']}")

# --- Chat Logic ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    extract_lead_info(user_input)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages
    )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Chat Display ---
for msg in st.session_state.messages[1:]:
    role = "You" if msg["role"] == "user" else "Lia"
    st.markdown(f"**{role}:** {msg['content']}")

st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
---
<div style='text-align: center; color: grey; font-size: 0.85rem;'>
    © 2025 LeadPulse. Built with ❤️ by Shayan & Co-founder.
</div>
""", unsafe_allow_html=True)
