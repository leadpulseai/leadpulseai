import os
import streamlit as st
from openai import OpenAI

# Initialize OpenAI Client
api_key = os.getenv("OPENAI_API_KEY")
st.write("🔑 API Key Loaded:", bool(api_key))  # Debug: confirm API key presence

client = OpenAI(api_key=api_key)

# Setup session
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Lia, a helpful assistant."}
    ]

# Input
user_input = st.chat_input("Say something...")

if user_input:
    st.write("✅ Input received:", user_input)  # Debug

    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        with st.spinner("Lia is thinking..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages
            )
        reply = response.choices[0].message.content
        st.write("🤖 Lia's reply:", reply)  # Debug
        st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"❌ OpenAI Error: {e}")

# Display chat history
for msg in st.session_state.messages[1:]:
    role = "You" if msg["role"] == "user" else "Lia"
    st.markdown(f"**{role}:** {msg['content']}")