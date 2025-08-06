import streamlit as st
from typing import Dict, List
import re
import os
from openai import OpenAI

# Translation dictionaries for UI elements
TRANSLATIONS = {
    "en": {
        "welcome": "Hi! I'm Lia, your AI assistant from LeadPulse. How can I help you today?",
        "input_placeholder": "Type your message here...",
        "send_button": "Send",
        "lead_captured": "Thank you for providing your information!",
        "email_prompt": "Could you share your email address?",
        "name_prompt": "What's your name?",
        "phone_prompt": "What's your phone number?",
        "interest_prompt": "What are you interested in?",
        "company_prompt": "What company are you with?",
        "budget_prompt": "What's your budget range for this project?",
        "timeline_prompt": "When are you looking to get started?",
        "error_message": "I'm having trouble connecting right now. Please try again in a moment.",
        "lead_score": "Lead Score",
        "contact_info": "Contact Information",
        "qualification_info": "Qualification Details",
        "next_steps": "Recommended Next Steps",
        "high_priority": "High Priority Lead",
        "medium_priority": "Medium Priority Lead",
        "low_priority": "Low Priority Lead"
    },
    "zh": {
        "welcome": "你好！我是Lia，您的LeadPulse AI助手。今天我能帮您什么？",
        "input_placeholder": "在这里输入您的消息...",
        "send_button": "发送",
        "lead_captured": "感谢您提供信息！",
        "email_prompt": "您能分享您的电子邮件地址吗？",
        "name_prompt": "您叫什么名字？",
        "phone_prompt": "您的电话号码是多少？",
        "interest_prompt": "您对什么感兴趣？",
        "company_prompt": "您在哪家公司工作？",
        "budget_prompt": "这个项目的预算范围是多少？",
        "timeline_prompt": "您计划什么时候开始？",
        "error_message": "我现在连接有问题。请稍后再试。",
        "lead_score": "潜在客户评分",
        "contact_info": "联系信息",
        "qualification_info": "资格详情",
        "next_steps": "建议的下一步",
        "high_priority": "高优先级潜在客户",
        "medium_priority": "中等优先级潜在客户",
        "low_priority": "低优先级潜在客户"
    },
    "es": {
        "welcome": "¡Hola! Soy Lia, tu asistente de IA de LeadPulse. ¿Cómo puedo ayudarte hoy?",
        "input_placeholder": "Escribe tu mensaje aquí...",
        "send_button": "Enviar",
        "lead_captured": "¡Gracias por proporcionar tu información!",
        "email_prompt": "¿Podrías compartir tu dirección de correo electrónico?",
        "name_prompt": "¿Cómo te llamas?",
        "phone_prompt": "¿Cuál es tu número de teléfono?",
        "interest_prompt": "¿En qué estás interesado?",
        "company_prompt": "¿Con qué empresa estás?",
        "budget_prompt": "¿Cuál es tu rango de presupuesto para este proyecto?",
        "timeline_prompt": "¿Cuándo estás buscando comenzar?",
        "error_message": "Tengo problemas de conexión ahora. Por favor, inténtalo de nuevo en un momento.",
        "lead_score": "Puntuación de Lead",
        "contact_info": "Información de Contacto",
        "qualification_info": "Detalles de Calificación",
        "next_steps": "Próximos Pasos Recomendados",
        "high_priority": "Lead de Alta Prioridad",
        "medium_priority": "Lead de Prioridad Media",
        "low_priority": "Lead de Baja Prioridad"
    }
}

# Regular expressions for lead extraction in different languages
LEAD_EXTRACTION_PATTERNS = {
    # ... unchanged ...
}

@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Provide it in Streamlit secrets or environment variables.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

def get_ui_text(key: str, language: str = "en") -> str:
    """Get UI text in the target language."""
    return TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))

def detect_language(text: str) -> str:
    """Detect language from user input using heuristics, fallback to OpenAI."""
    if not text:
        return "en"
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    if chinese_chars > len(text) * 0.3:
        return "zh"
    spanish_chars = len(re.findall(r'[ñáéíóúü]', text.lower()))
    spanish_words = ['el', 'la', 'es', 'en', 'de', 'que', 'y', 'con', 'por', 'para', 'hola', 'soy', 'estoy']
    words = re.findall(r'\w+', text.lower())
    if spanish_chars > 0 or any(w in words for w in spanish_words):
        return "es"
    # Fallback to OpenAI language detection
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Detect the language of the text. Respond only with 'en', 'zh', or 'es'."},
                {"role": "user", "content": f"Language of: {text[:200]}"}
            ],
            max_tokens=5,
            temperature=0
        )
        detected = response.choices[0].message.content.strip().lower()
        if detected in ("en", "zh", "es"):
            return detected
    except Exception as e:
        st.warning(f"Language detection failed: {e}")
    return "en"

def extract_lead_info_multilingual(user_input: str, language: str, lead_data: Dict) -> Dict:
    """Extract lead info from user input based on language-specific patterns."""
    if not user_input:
        return lead_data
    updated = False
    # EMAIL extraction (same pattern for all)
    if not lead_data.get("email"):
        pattern = LEAD_EXTRACTION_PATTERNS["email"].get(language, LEAD_EXTRACTION_PATTERNS["email"]["en"])
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            lead_data["email"] = match.group().lower()
            st.success(f"📧 {get_ui_text('email_prompt', language)}: {lead_data['email']}")
            updated = True

    # NAME extraction
    if not lead_data.get("name"):
        patterns = LEAD_EXTRACTION_PATTERNS["name"].get(language, LEAD_EXTRACTION_PATTERNS["name"]["en"])
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 1 and not any(word in name.lower() for word in ['email', 'phone', 'number', 'address']):
                    lead_data["name"] = name
                    st.success(f"👤 {get_ui_text('name_prompt', language)}: {lead_data['name']}")
                    updated = True
                    break

    # PHONE extraction
    if not lead_data.get("phone"):
        pattern = LEAD_EXTRACTION_PATTERNS["phone"].get(language, LEAD_EXTRACTION_PATTERNS["phone"]["en"])
        match = re.search(pattern, user_input)
        if match:
            phone = re.sub(r'[()\s-]', '', match.group())
            if len(phone) >= 10:  # basic validation
                lead_data["phone"] = phone
                st.success(f"📞 {get_ui_text('phone_prompt', language)}: {lead_data['phone']}")
                updated = True

    # COMPANY extraction
    if not lead_data.get("company"):
        patterns = LEAD_EXTRACTION_PATTERNS["company"].get(language, LEAD_EXTRACTION_PATTERNS["company"]["en"])
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                company = match.group(1).strip().title()
                if len(company) > 2 and not any(word in company.lower() for word in ['email', 'phone', 'number']):
                    lead_data["company"] = company
                    st.success(f"🏢 {get_ui_text('company_prompt', language)}: {lead_data['company']}")
                    updated = True
                    break

    # INTEREST extraction
    if not lead_data.get("interest"):
        patterns = LEAD_EXTRACTION_PATTERNS["interest"].get(language, LEAD_EXTRACTION_PATTERNS["interest"]["en"])
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                interest = match.group(1).strip()
                if 5 <= len(interest) <= 100:
                    lead_data["interest"] = interest
                    st.success(f"💡 {get_ui_text('interest_prompt', language)}: {lead_data['interest']}")
                    updated = True
                    break

    # BUDGET extraction
    if not lead_data.get("budget"):
        patterns = LEAD_EXTRACTION_PATTERNS["budget"].get(language, LEAD_EXTRACTION_PATTERNS["budget"]["en"])
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                budget = match.group(1)
                currency = "$" if language == "en" else "¥" if language == "zh" else "€" if language == "es" else "$"
                lead_data["budget"] = budget
                st.success(f"💰 {get_ui_text('budget_prompt', language)}: {currency}{budget}")
                updated = True
                break

    return lead_data


def calculate_lead_score(lead_data: Dict) -> int:
    """Calculate lead score based on presence of fields."""
    score = 0
    if lead_data.get("email"):
        score += 30
    if lead_data.get("phone"):
        score += 20
    if lead_data.get("company"):
        score += 15
    if lead_data.get("budget"):
        score += 15
    if lead_data.get("interest"):
        score += 10
    if lead_data.get("name"):
        score += 10
    return min(score, 100)


def get_lead_priority(score: int, language: str = "en") -> tuple:
    """Return priority label and emoji based on lead score."""
    if score >= 70:
        return ("high", get_ui_text("high_priority", language), "🔥")
    elif score >= 40:
        return ("medium", get_ui_text("medium_priority", language), "⚡")
    else:
        return ("low", get_ui_text("low_priority", language), "📝")


def format_lead_summary(lead_data: Dict, language: str = "en") -> str:
    """Format lead info summary string."""
    parts = []
    if lead_data.get("name"):
        parts.append(f"👤 **{get_ui_text('name_prompt', language)[:-1]}:** {lead_data['name']}")
    if lead_data.get("email"):
        parts.append(f"📧 **Email:** {lead_data['email']}")
    if lead_data.get("phone"):
        parts.append(f"📞 **{get_ui_text('phone_prompt', language)[:-1]}:** {lead_data['phone']}")
    if lead_data.get("company"):
        parts.append(f"🏢 **{get_ui_text('company_prompt', language)[:-1]}:** {lead_data['company']}")
    if lead_data.get("interest"):
        parts.append(f"💡 **{get_ui_text('interest_prompt', language)[:-1]}:** {lead_data['interest']}")
    if lead_data.get("budget"):
        parts.append(f"💰 **{get_ui_text('budget_prompt', language)[:-1]}:** ${lead_data['budget']}")
    if not parts:
        return f"*{get_ui_text('lead_captured', language)}*"
    return "\n".join(parts)


# Main Streamlit app UI
def main():
    st.title("LeadPulse Multilingual Lead Capture AI")

    if 'lead_data' not in st.session_state:
        st.session_state.lead_data = {}

    user_text = st.text_area(get_ui_text('input_placeholder'), height=100)
    if st.button(get_ui_text('send_button')):
        if not user_text.strip():
            st.warning("Please enter a message.")
            return
        language = detect_language(user_text)
        st.write(f"Detected language: {language}")

        # Extract lead info from input and update session state
        st.session_state.lead_data = extract_lead_info_multilingual(user_text, language, st.session_state.lead_data)

        # Show lead summary
        summary = format_lead_summary(st.session_state.lead_data, language)
        st.markdown("### Lead Summary")
        st.markdown(summary)

        # Calculate and show lead score and priority
        score = calculate_lead_score(st.session_state.lead_data)
        priority_key, priority_label, emoji = get_lead_priority(score, language)
        st.markdown(f"**{get_ui_text('lead_score', language)}:** {score}")
        st.markdown(f"**{priority_label}** {emoji}")


if __name__ == "__main__":
    main()