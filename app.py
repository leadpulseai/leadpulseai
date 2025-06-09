import streamlit as st
from openai import OpenAI
import os
import re
import json
from datetime import datetime
import pandas as pd

# --- Configuration & Initialization --- 

# Ensure API key is set in Streamlit secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except KeyError:
    st.error("OpenAI API key not found. Please add it to your Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error initializing OpenAI client: {e}")
    st.stop()

# --- UI Branding & Styling --- 
st.markdown(""" <style> 
body { 
    background-color: #ffffff; 
    background-repeat: no-repeat; 
    background-position: center center; 
    background-size: 150px; 
    background-attachment: fixed; 
    font-family: 'Segoe UI', sans-serif; 
}
/* Optional: Grid pattern background */
body::before { 
    content: ""; 
    position: fixed; 
    top: 0; left: 0; 
    height: 100%; width: 100%; 
    background-image: linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px), linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px); 
    background-size: 60px 60px; 
    z-index: -1; 
}
.stChatMessage {
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    max-width: 75%;
}
.stChatMessage[data-testid="chatAvatarIcon-user"] + div {
    background-color: #e8f0fe; 
    color: #202124;
    margin-left: auto; /* Align user messages to the right */
}
.stChatMessage[data-testid="chatAvatarIcon-assistant"] + div {
    background-color: #f8f9fa; 
    color: #3c4043;
    margin-right: auto; /* Align assistant messages to the left */
}
.footer { 
    text-align: center; 
    font-size: 0.8rem; 
    color: #999; 
    margin-top: 2rem; 
}
.lead-score {
    font-size: 1.5rem;
    font-weight: bold;
    text-align: center;
    margin: 1rem 0;
}
.score-hot {
    color: #ff4b4b;
}
.score-warm {
    color: #ffa64b;
}
.score-cold {
    color: #4b83ff;
}
</style> """, unsafe_allow_html=True)

st.title("Lia - Your AI Lead Assistant")

# --- Session State Management --- 

# Initialize chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Lia, your AI assistant from LeadPulse. How can I help you today?"}]

# Initialize lead data in session state if it doesn't exist
if "lead_data" not in st.session_state:
    st.session_state.lead_data = {
        "name": None, 
        "email": None, 
        "phone": None, 
        "interest": None, 
        "company": None,
        "industry": None,
        "pain_points": None,
        "buying_signals": [],
        "lead_score": 0,
        "lead_status": "New",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Initialize message counter for periodic analysis
if "message_counter" not in st.session_state:
    st.session_state.message_counter = 0

# --- Core Functions --- 

def extract_lead_info_regex(user_input: str):
    """Extracts lead information using regex patterns and updates session state."""
    lead_data = st.session_state.lead_data
    updated = False
    user_input_lower = user_input.lower() # Work with lowercase for matching

    # Email Extraction
    if not lead_data["email"]:
        match = re.search(r"[\w.\-+%]+@[\w.-]+\.[a-zA-Z]{2,}", user_input, re.IGNORECASE)
        if match:
            lead_data["email"] = match.group()
            st.toast(f"📧 Email captured: {lead_data['email']}")
            updated = True

    # Phone Extraction (More flexible)
    if not lead_data["phone"]:
        # Look for sequences of 7-15 digits, possibly with spaces/hyphens
        # Triggered by phrases like "my phone is", "call me at", or just finds a likely number
        match = re.search(r"(?:my\s+phone(?:\s+number)?\s+is|call\s+me\s+at|reach\s+me\s+at)?\s*(\+?[\d\s-]{7,15}\d)\b", user_input_lower)
        if match:
            # Clean up the extracted number (remove non-digits, except leading +)
            phone_number = re.sub(r"[()\s-]", "", match.group(1))
            lead_data["phone"] = phone_number
            st.toast(f"📞 Phone captured: {lead_data['phone']}")
            updated = True

    # Name Extraction (Refined)
    if not lead_data["name"]:
        # Expanded to catch more variations
        match = re.search(r"(?:my\s+name\s+is|I\'m|I\s+am|call\s+me|this\s+is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", user_input, re.IGNORECASE)
        if match:
            lead_data["name"] = match.group(1).strip()
            st.toast(f"👤 Name captured: {lead_data['name']}")
            updated = True

    # Interest Extraction (More flexible)
    if not lead_data["interest"]:
        # Expanded to catch implied interests
        match = re.search(r"(?:interested\s+in|looking\s+for|need\s+help\s+with|my\s+interest\s+is|thinking\s+about|considering|exploring|working\s+with|focused\s+on)\s+(.+?)[\.,:;!?]", user_input_lower)
        if match:
            interest = match.group(1).strip()
            if len(interest.split()) < 15: 
                lead_data["interest"] = interest.capitalize()
                st.toast(f"💡 Interest captured: {lead_data['interest']}")
                updated = True
                
    # Company Extraction (Enhanced)
    if not lead_data["company"]:
        match = re.search(r"(?:work\s+at|work\s+for|my\s+company\s+is|from\s+the\s+company|our\s+company|we\s+at|with\s+company)\s+([A-Z][A-Za-z0-9\s&.,\[\]\{\}\\'-]+)", user_input, re.IGNORECASE)
        if match:
            lead_data["company"] = match.group(1).strip()
            st.toast(f"🏢 Company captured: {lead_data['company']}")
            updated = True
            
    # Industry Extraction (New)
    if not lead_data["industry"]:
        industry_patterns = [
            r"(?:in\s+the|work\s+in|industry\s+is)\s+([\w\s]+?)\s+(?:industry|sector|field)",
            r"(?:from|in)\s+the\s+([\w\s]+?)\s+(?:industry|sector|field)"
        ]
        for pattern in industry_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                lead_data["industry"] = match.group(1).strip().capitalize()
                st.toast(f"🏭 Industry captured: {lead_data['industry']}")
                updated = True
                break
    
    # Buying Signals (New)
    buying_signal_patterns = [
        r"(?:how\s+much|pricing|cost|price|quote|demo|trial|purchase|buy|subscribe)",
        r"(?:when\s+can\s+we\s+start|implementation|onboarding|setup)",
        r"(?:decision\s+maker|approve|budget|timeline|roadmap)"
    ]
    
    for pattern in buying_signal_patterns:
        if re.search(pattern, user_input_lower):
            signal = re.search(pattern, user_input_lower).group(0)
            if signal not in lead_data["buying_signals"]:
                lead_data["buying_signals"].append(signal)
                updated = True
    
    if updated:
        # Update timestamp
        lead_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.lead_data = lead_data
        # Calculate lead score after update
        calculate_lead_score()

def analyze_conversation_with_openai():
    """Uses OpenAI to analyze the conversation and extract implied information."""
    # Only run this analysis periodically to save API calls
    if len(st.session_state.messages) < 3:
        return
        
    try:
        # Prepare the conversation history
        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
        
        # Create the analysis prompt
        analysis_prompt = f"""
        Analyze this conversation between a lead and an AI assistant. Extract the following information:
        
        Conversation:
        {conversation}
        
        Extract the following (respond in JSON format):
        1. Implied interests (topics they seem interested in but didn't explicitly state)
        2. Pain points or challenges they mentioned
        3. Industry (if mentioned or implied)
        4. Company size hints (small, medium, enterprise)
        5. Buying signals (urgency, budget mentions, decision timeline)
        6. Lead qualification (how likely they are to be a qualified lead)
        
        Format your response as valid JSON with these keys: implied_interests, pain_points, industry, company_size, buying_signals, lead_qualification
        """
        
        # Call OpenAI API for analysis
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        # Extract and parse the JSON response
        response_content = completion.choices[0].message.content
        
        # Find JSON content (it might be wrapped in ```json or just be plain JSON)
        json_match = re.search(r'```json\n(.*?)\n```', response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Assume the entire response is JSON
            json_str = response_content
            
        try:
            analysis_result = json.loads(json_str)
            update_lead_data_from_analysis(analysis_result)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from OpenAI response: {e}")
            print(f"Response was: {response_content}")
            
    except Exception as e:
        print(f"Error in conversation analysis: {e}")

def update_lead_data_from_analysis(analysis):
    """Updates lead data based on OpenAI analysis results."""
    lead_data = st.session_state.lead_data
    updated = False
    
    # Update implied interests if not already set
    if not lead_data["interest"] and "implied_interests" in analysis and analysis["implied_interests"]:
        if isinstance(analysis["implied_interests"], list) and analysis["implied_interests"]:
            lead_data["interest"] = ", ".join(analysis["implied_interests"])
            st.toast(f"💡 Interest inferred: {lead_data['interest']}")
            updated = True
        elif isinstance(analysis["implied_interests"], str) and analysis["implied_interests"].strip():
            lead_data["interest"] = analysis["implied_interests"].strip()
            st.toast(f"💡 Interest inferred: {lead_data['interest']}")
            updated = True
    
    # Update industry if not already set
    if not lead_data["industry"] and "industry" in analysis and analysis["industry"]:
        lead_data["industry"] = analysis["industry"]
        st.toast(f"🏭 Industry inferred: {lead_data['industry']}")
        updated = True
    
    # Update pain points
    if "pain_points" in analysis and analysis["pain_points"]:
        if isinstance(analysis["pain_points"], list) and analysis["pain_points"]:
            pain_points = ", ".join(analysis["pain_points"])
        else:
            pain_points = analysis["pain_points"]
            
        lead_data["pain_points"] = pain_points
        updated = True
    
    # Update buying signals
    if "buying_signals" in analysis and analysis["buying_signals"]:
        if isinstance(analysis["buying_signals"], list):
            for signal in analysis["buying_signals"]:
                if signal and signal not in lead_data["buying_signals"]:
                    lead_data["buying_signals"].append(signal)
                    updated = True
        elif isinstance(analysis["buying_signals"], str) and analysis["buying_signals"].strip():
            signal = analysis["buying_signals"].strip()
            if signal not in lead_data["buying_signals"]:
                lead_data["buying_signals"].append(signal)
                updated = True
    
    if updated:
        # Update timestamp
        lead_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.lead_data = lead_data
        # Recalculate lead score
        calculate_lead_score()

def calculate_lead_score():
    """Calculates a lead score based on available information and engagement."""
    lead_data = st.session_state.lead_data
    score = 0
    
    # Basic information completeness (50 points max)
    if lead_data["name"]:
        score += 10
    if lead_data["email"]:
        score += 15
    if lead_data["phone"]:
        score += 10
    if lead_data["company"]:
        score += 10
    if lead_data["industry"]:
        score += 5
        
    # Interest and pain points (20 points max)
    if lead_data["interest"]:
        score += 10
    if lead_data["pain_points"]:
        score += 10
        
    # Buying signals (30 points max)
    signal_score = min(30, len(lead_data["buying_signals"]) * 10)
    score += signal_score
    
    # Set the lead score
    lead_data["lead_score"] = score
    
    # Determine lead status based on score
    if score >= 70:
        lead_data["lead_status"] = "Hot"
    elif score >= 40:
        lead_data["lead_status"] = "Warm"
    else:
        lead_data["lead_status"] = "Cold"
        
    # Update session state
    st.session_state.lead_data = lead_data

def get_openai_response():
    """Gets a response from OpenAI based on the current conversation history."""
    # Ensure the latest user message is in session state before calling API
    if not st.session_state.messages or st.session_state.messages[-1]["role"] != "user":
        return "Hmm, I seem to have missed what you just said. Could you please repeat that?"
        
    try:
        # Create a system prompt that includes lead data status to guide the conversation
        lead_data = st.session_state.lead_data
        missing_info = []
        
        if not lead_data["name"]:
            missing_info.append("name")
        if not lead_data["email"]:
            missing_info.append("email")
        if not lead_data["phone"]:
            missing_info.append("phone")
        if not lead_data["company"]:
            missing_info.append("company")
        if not lead_data["interest"]:
            missing_info.append("interests")
            
        # Craft a dynamic system prompt based on what information we still need
        system_prompt_content = """
        You are Lia, a friendly and helpful AI lead generation assistant for LeadPulse. Your goal is to understand the user's needs, 
        collect relevant information naturally through conversation, and qualify them as a lead. Be conversational and engaging.
        Ask clarifying questions if needed. Keep responses concise and friendly.
        """
        
        # Add guidance based on missing information
        if missing_info:
            system_prompt_content += f"\n\nIn this conversation, try to naturally collect the following missing information: {', '.join(missing_info)}. "
            system_prompt_content += "Don't ask for all at once, but weave questions naturally into the conversation."
        
        # Add guidance based on lead status
        if lead_data["lead_status"] == "Hot":
            system_prompt_content += "\n\nThis appears to be a HOT lead. Focus on next steps and moving them toward a decision."
        elif lead_data["lead_status"] == "Warm":
            system_prompt_content += "\n\nThis appears to be a WARM lead. Focus on understanding their needs better and building interest."
        
        system_prompt = {"role": "system", "content": system_prompt_content}
        messages_for_api = [system_prompt] + st.session_state.messages
        
        # Call OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_api,
            temperature=0.7,
            max_tokens=150
        )
        response_content = completion.choices[0].message.content
        
        return response_content

    except Exception as e:
        print(f"ERROR: OpenAI API call failed: {e}")
        st.error(f"Error communicating with OpenAI: {e}")
        return "Sorry, I encountered a technical glitch. Please give me a moment and try again."

# --- Main Chat Interface Logic --- 

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What can Lia help you with?"):
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Increment message counter
    st.session_state.message_counter += 1

    # Extract lead info using regex
    extract_lead_info_regex(prompt)
    
    # Periodically analyze the conversation with OpenAI
    # Do this every 3 messages to avoid excessive API calls
    if st.session_state.message_counter % 3 == 0:
        analyze_conversation_with_openai()

    # Get response from OpenAI
    assistant_response = get_openai_response()

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    # Rerun to update the chat display smoothly
    st.rerun()

# --- Sidebar for Lead Data Display --- 
st.sidebar.header("Lead Intelligence")

# Display lead score with color coding
score = st.session_state.lead_data["lead_score"]
status = st.session_state.lead_data["lead_status"]
score_class = f"score-{status.lower()}"

st.sidebar.markdown(f"""
<div class="lead-score {score_class}">
    Lead Score: {score}/100<br>
    Status: {status}
</div>
""", unsafe_allow_html=True)

# Display collected lead data
st.sidebar.subheader("Collected Lead Data")
lead_display = {
    "Name": st.session_state.lead_data["name"] or "Not captured",
    "Email": st.session_state.lead_data["email"] or "Not captured",
    "Phone": st.session_state.lead_data["phone"] or "Not captured",
    "Company": st.session_state.lead_data["company"] or "Not captured",
    "Industry": st.session_state.lead_data["industry"] or "Not captured",
    "Interest": st.session_state.lead_data["interest"] or "Not captured",
    "Pain Points": st.session_state.lead_data["pain_points"] or "Not captured",
    "Buying Signals": ", ".join(st.session_state.lead_data["buying_signals"]) if st.session_state.lead_data["buying_signals"] else "None detected",
    "Last Updated": st.session_state.lead_data["last_updated"]
}

for key, value in lead_display.items():
    st.sidebar.text(f"{key}: {value}")

# --- Footer --- 
st.markdown("<div class='footer'>Powered by LeadPulse & Manus</div>", unsafe_allow_html=True)