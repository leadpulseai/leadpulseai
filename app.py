import streamlit as st
import openai
import os
import re

# Initialize client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Session memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful AI assistant for lead generation. Ask the user their name, email, and what service they are interested in."}
    ]

lead_data = {"name": None, "email": None, "interest": None}

def extract_lead_info(user_input):
    if not lead_data['email']:
        email_match = re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', user_input)
        if email_match:
            lead_data['email'] = email_match.group()
            st.success(f"✅ Email captured: {lead_data['email']}")

    if not lead_data['name'] and "my name is" in user_input.lower():
        lead_data['name'] = user_input.split("is")[1].strip().split()[0]
        st.success(f"✅ Name captured: {lead_data['name']}")

    if not lead_data['interest'] and "interested in" in user_input.lower():
        lead_data['interest'] = user_input.split("interested in")[1].strip().split()[0]
        st.success(f"✅ Interest captured: {lead_data['interest']}")

    if all(lead_data.values()):
        with open("leads.txt", "a") as f:
            f.write(f"{lead_data['name']} | {lead_data['email']} | {lead_data['interest']}\n")
        st.balloons()

# Title and UI
st.title("⚡ LeadPulse 🚀 Your AI-Powered Lead Assistant")
st.markdown("""
Welcome to **LeadPulse**, your smart AI agent that collects high-quality leads in seconds.  
Let’s grow your business 📈  
Type your message below to get started!
""")

# User Input
user_input = st.text_input("You:", key="input")

# Handle input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    extract_lead_info(user_input)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages
    )

    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})

# Display full chat like a conversation
for msg in st.session_state.messages[1:]:
    if msg['role'] == 'user':
        st.markdown(f"**You**: {msg['content']}")
    else:
        st.markdown(f"**LeadPulse**: {msg['content']}")
