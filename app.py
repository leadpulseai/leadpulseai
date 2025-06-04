import streamlit as st
from openai import OpenAI
import os
import re
from datetime import datetime

# Use Streamlit's secrets for cloud compatibility

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# UI Branding
st.markdown(""" <style> body { background-color: #ffffff; background-image: url('https://upload.wikimedia.org/wikipedia/commons/8/88/Example_logo.png'); background-repeat: no-repeat; background-position: center center; background-size: 150px; background-attachment: fixed; font-family: 'Segoe UI', sans-serif; } body::before { content: ""; position: fixed; top: 0; left: 0; height: 100%; width: 100%; background-image: linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px), linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px); background-size: 60px 60px; z-index: -1; } .chat-box { background-color: #f1f1f1; padding: 1rem; border-radius: 12px; margin: 1rem 0; max-height: 60vh; overflow-y: auto; } .user-msg { background-color: #e8f0fe; color: #202124; text-align: right; padding: 0.8rem; border-radius: 10px; margin-bottom: 5px; max-width: 75%; margin-left: 25%; } .bot-msg { background-color: #f8f9fa; color: #3c4043; padding: 0.8rem; border-radius: 10px; margin-bottom: 5px; max-width: 75%; } .footer { text-align: center; font-size: 0.8rem; color: #999; margin-top: 2rem; } </style> """, unsafe_allow_html=True)

Store lead info

lead_data = {"name": None, "email": None, "phone": None, "interest": None}

def extract_lead_info(user_input: str): if not lead_data["email"]: match = re.search(r"[\w.-]+@[\w.-]+.\w+", user_input) if match: lead_data["email"] = match.group() st.success(f"📧 Email: {lead_data['email']}")

if not lead_data["phone"]:
    match = re.search(r"\b\d{10,15}\b", user_input)
    if match:
        lead_data["phone"] = match.group()
        st.success(f"📞 Phone: {lead_data['phone']}")

if not lead_data["name"] and "my name is" in user_input.lower():
    lead_data["name"] = user_input.split("my name is")[-1].strip().split()[0].capitalize()
    st.success(f"🧑 Name: {lead_data['name']}")

if not lead_data["interest"] and "interested in" in user_input.lower():
    lead_data["interest"]