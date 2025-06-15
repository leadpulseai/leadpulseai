import streamlit as st
from typing import Dict, List, Optional
import json
import re
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
    "email": {
        "en": r"[\w.\-+%]+@[\w.-]+\.[a-zA-Z]{2,}",
        "zh": r"[\w.\-+%]+@[\w.-]+\.[a-zA-Z]{2,}",  # Email format is universal
        "es": r"[\w.\-+%]+@[\w.-]+\.[a-zA-Z]{2,}"
    },
    "name": {
        "en": [
            r"(?:my name is|I am|I'm|call me|this is)\s+([A-Za-z\s]{2,30})",
            r"(?:I'm|I am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:name|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ],
        "zh": [
            r"(?:我叫|我是|我的名字是|叫我)\s*([\u4e00-\u9fa5A-Za-z\s]{1,20})",
            r"(?:姓名|名字)(?:是|叫)?\s*([\u4e00-\u9fa5A-Za-z\s]{1,20})"
        ],
        "es": [
            r"(?:me llamo|soy|mi nombre es|llámame|esto es)\s+([A-Za-zÀ-ÿ\s]{2,30})",
            r"(?:nombre|llamado)\s+([A-Za-zÀ-ÿ\s]{2,30})"
        ]
    },
    "phone": {
        "en": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "zh": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "es": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    },
    "company": {
        "en": [
            r"(?:work at|work for|employed by|company is|from)\s+([A-Za-z0-9\s&.,'-]{2,50})",
            r"(?:at|@)\s+([A-Z][A-Za-z0-9\s&.,'-]{1,49})\s*(?:company|corp|inc|ltd|llc)?"
        ],
        "zh": [
            r"(?:在|工作在|公司是|来自)\s*([\u4e00-\u9fa5A-Za-z0-9\s&.,'-]{2,30})",
            r"(?:公司|企业|单位)(?:是|叫)?\s*([\u4e00-\u9fa5A-Za-z0-9\s&.,'-]{2,30})"
        ],
        "es": [
            r"(?:trabajo en|trabajo para|empleado por|empresa es|de la empresa)\s+([A-Za-zÀ-ÿ0-9\s&.,'-]{2,50})",
            r"(?:en|@)\s+([A-Za-zÀ-ÿ0-9\s&.,'-]{2,50})\s*(?:empresa|corp|inc|ltd)?"
        ]
    },
    "interest": {
        "en": [
            r"(?:interested in|looking for|need|want|seeking)\s+([^.,;!?]{5,100})",
            r"(?:help with|assistance with|support for)\s+([^.,;!?]{5,100})"
        ],
        "zh": [
            r"(?:对|感兴趣|寻找|需要|想要|寻求)\s*([^.,;!?]{3,50})",
            r"(?:帮助|协助|支持)(?:关于|在)?\s*([^.,;!?]{3,50})"
        ],
        "es": [
            r"(?:interesado en|buscando|necesito|quiero|buscando)\s+([^.,;!?]{5,100})",
            r"(?:ayuda con|asistencia con|apoyo para)\s+([^.,;!?]{5,100})"
        ]
    },
    "budget": {
        "en": [
            r"(?:budget|spend|invest|pay)\s*(?:is|of|around|about)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:budget|range|limit)"
        ],
        "zh": [
            r"(?:预算|花费|投资|支付)\s*(?:是|大约|左右)?\s*¥?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"¥(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:预算|范围|限制)"
        ],
        "es": [
            r"(?:presupuesto|gastar|invertir|pagar)\s*(?:es|de|alrededor|sobre)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:presupuesto|rango|límite)"
        ]
    }
}

def detect_language(text: str) -> str:
    """Detect language from user input using simple heuristics and OpenAI fallback."""
    if not text:
        return "en"
    
    # Simple heuristic detection first (faster)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    spanish_chars = len(re.findall(r'[ñáéíóúü]', text.lower()))
    
    # If significant Chinese characters, likely Chinese
    if chinese_chars > len(text) * 0.3:
        return "zh"
    
    # If Spanish characters or common Spanish words
    spanish_words = ['el', 'la', 'es', 'en', 'de', 'que', 'y', 'con', 'por', 'para', 'hola', 'soy', 'estoy']
    if spanish_chars > 0 or any(word in text.lower().split() for word in spanish_words):
        return "es"
    
    # Try OpenAI detection for ambiguous cases
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Detect the language of the text. Respond with only 'en' for English, 'zh' for Chinese, or 'es' for Spanish."},
                {"role": "user", "content": f"Language of: '{text[:200]}'"}  # Limit text length
            ],
            max_tokens=5,
            temperature=0
        )
        detected = response.choices[0].message.content.strip().lower()
        
        if detected in ["en", "zh", "es"]:
            return detected
    except Exception as e:
        print(f"Language detection error: {e}")
    
    return "en"  # Default to English

def translate_text(text: str, target_language: str, source_language: str = "auto") -> str:
    """Translate text to target language using OpenAI."""
    if not text or target_language == "en":
        return text
    
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        language_names = {"en": "English", "zh": "Chinese", "es": "Spanish"}
        target_lang_name = language_names.get(target_language, "English")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a professional translator. Translate the following text to {target_lang_name}. Maintain the tone and context. Only return the translation, no explanations."
                },
                {"role": "user", "content": text}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text on error

def get_ui_text(key: str, language: str = "en") -> str:
    """Get UI text in the specified language."""
    if language in TRANSLATIONS and key in TRANSLATIONS[language]:
        return TRANSLATIONS[language][key]
    return TRANSLATIONS["en"].get(key, key)  # Fallback to English or key itself

def extract_lead_info_multilingual(user_input: str, language: str, lead_data: Dict) -> Dict:
    """Extract lead information using language-specific patterns."""
    if not user_input:
        return lead_data
    
    updated = False
    
    # Email extraction (universal format)
    if not lead_data.get("email"):
        email_pattern = LEAD_EXTRACTION_PATTERNS["email"].get(language, LEAD_EXTRACTION_PATTERNS["email"]["en"])
        email_match = re.search(email_pattern, user_input, re.IGNORECASE)
        if email_match:
            lead_data["email"] = email_match.group().lower()
            st.toast(f"📧 {get_ui_text('email_prompt', language)}: {lead_data['email']}")
            updated = True
    
    # Name extraction
    if not lead_data.get("name"):
        name_patterns = LEAD_EXTRACTION_PATTERNS["name"].get(language, LEAD_EXTRACTION_PATTERNS["name"]["en"])
        for pattern in name_patterns:
            name_match = re.search(pattern, user_input, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip().title()
                # Filter out common false positives
                if len(name) > 1 and not any(word in name.lower() for word in ['email', 'phone', 'number', 'address']):
                    lead_data["name"] = name
                    st.toast(f"👤 {get_ui_text('name_prompt', language)}: {lead_data['name']}")
                    updated = True
                    break
    
    # Phone extraction
    if not lead_data.get("phone"):
        phone_pattern = LEAD_EXTRACTION_PATTERNS["phone"].get(language, LEAD_EXTRACTION_PATTERNS["phone"]["en"])
        phone_match = re.search(phone_pattern, user_input)
        if phone_match:
            phone = re.sub(r'[()\s-]', '', phone_match.group())
            if len(phone) >= 10:  # Valid phone number length
                lead_data["phone"] = phone_match.group()
                st.toast(f"📞 {get_ui_text('phone_prompt', language)}: {lead_data['phone']}")
                updated = True
    
    # Company extraction
    if not lead_data.get("company"):
        company_patterns = LEAD_EXTRACTION_PATTERNS["company"].get(language, LEAD_EXTRACTION_PATTERNS["company"]["en"])
        for pattern in company_patterns:
            company_match = re.search(pattern, user_input, re.IGNORECASE)
            if company_match:
                company = company_match.group(1).strip().title()
                # Filter out common false positives
                if len(company) > 2 and not any(word in company.lower() for word in ['email', 'phone', 'number']):
                    lead_data["company"] = company
                    st.toast(f"🏢 {get_ui_text('company_prompt', language)}: {lead_data['company']}")
                    updated = True
                    break
    
    # Interest extraction
    if not lead_data.get("interest"):
        interest_patterns = LEAD_EXTRACTION_PATTERNS["interest"].get(language, LEAD_EXTRACTION_PATTERNS["interest"]["en"])
        for pattern in interest_patterns:
            interest_match = re.search(pattern, user_input, re.IGNORECASE)
            if interest_match:
                interest = interest_match.group(1).strip()
                # Avoid capturing overly long or short interests
                if 5 <= len(interest) <= 100:
                    lead_data["interest"] = interest
                    st.toast(f"💡 {get_ui_text('interest_prompt', language)}: {lead_data['interest']}")
                    updated = True
                    break
    
    # Budget extraction
    if not lead_data.get("budget"):
        budget_patterns = LEAD_EXTRACTION_PATTERNS["budget"].get(language, LEAD_EXTRACTION_PATTERNS["budget"]["en"])
        for pattern in budget_patterns:
            budget_match = re.search(pattern, user_input, re.IGNORECASE)
            if budget_match:
                budget = budget_match.group(1)
                lead_data["budget"] = budget
                st.toast(f"💰 {get_ui_text('budget_prompt', language)}: ${budget}")
                updated = True
                break
    
    return lead_data

def calculate_lead_score(lead_data: Dict, config: Dict) -> int:
    """Calculate lead score based on available information."""
    score = 0
    scoring_config = config.get("lead_qualification", {}).get("scoring", {})
    
    if lead_data.get("email"):
        score += scoring_config.get("email_provided", 30)
    
    if lead_data.get("phone"):
        score += scoring_config.get("phone_provided", 20)
    
    if lead_data.get("company"):
        score += scoring_config.get("company_provided", 15)
    
    if lead_data.get("budget"):
        score += scoring_config.get("budget_provided", 15)
    
    if lead_data.get("interest"):
        score += scoring_config.get("timeline_provided", 10)
    
    if lead_data.get("name"):
        score += 10  # Bonus for having name
    
    return min(score, 100)  # Cap at 100

def get_lead_priority(score: int, language: str = "en") -> tuple:
    """Get lead priority based on score."""
    if score >= 70:
        return ("high", get_ui_text("high_priority", language), "🔥")
    elif score >= 40:
        return ("medium", get_ui_text("medium_priority", language), "⚡")
    else:
        return ("low", get_ui_text("low_priority", language), "📝")

def format_lead_summary(lead_data: Dict, language: str = "en") -> str:
    """Format lead data into a readable summary."""
    summary_parts = []
    
    if lead_data.get("name"):
        summary_parts.append(f"👤 **{get_ui_text('name_prompt', language)[:-1]}:** {lead_data['name']}")
    
    if lead_data.get("email"):
        summary_parts.append(f"📧 **Email:** {lead_data['email']}")
    
    if lead_data.get("phone"):
        summary_parts.append(f"📞 **{get_ui_text('phone_prompt', language)[:-1]}:** {lead_data['phone']}")
    
    if lead_data.get("company"):
        summary_parts.append(f"🏢 **{get_ui_text('company_prompt', language)[:-1]}:** {lead_data['company']}")
    
    if lead_data.get("interest"):
        summary_parts.append(f"💡 **{get_ui_text('interest_prompt', language)[:-1]}:** {lead_data['interest']}")
    
    if lead_data.get("budget"):
        summary_parts.append(f"💰 **{get_ui_text('budget_prompt', language)[:-1]}:** ${lead_data['budget']}")
    
    return "\n".join(summary_parts) if summary_parts else f"*{get_ui_text('lead_captured', language)}*"

def get_language_specific_system_prompt(base_prompt: str, language: str) -> str:
    """Modify system prompt for specific language."""
    language_instructions = {
        "en": "Respond in English. Use natural, conversational English.",
        "zh": "用中文回复。使用自然、对话式的中文。保持友好和专业的语调。",
        "es": "Responde en español. Usa español natural y conversacional. Mantén un tono amigable y profesional."
    }
    
    lang_instruction = language_instructions.get(language, language_instructions["en"])
    
    return f"{base_prompt}\n\nIMPORTANT: {lang_instruction}"

def render_language_selector():
    """Render language selector in sidebar."""
    st.sidebar.subheader("🌍 Language / 语言 / Idioma")
    
    languages = {
        "en": "🇺🇸 English",
        "zh": "🇨🇳 中文",
        "es": "🇪🇸 Español"
    }
    
    current_language = st.session_state.get("language", "en")
    
    selected_language = st.sidebar.selectbox(
        "Select Language",
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=list(languages.keys()).index(current_language),
        key="language_selector"
    )
    
    if selected_language != current_language:
        st.session_state.language = selected_language
        st.rerun()
    
    return selected_language

def get_conversation_starters(language: str) -> List[str]:
    """Get conversation starters in the specified language."""
    starters = {
        "en": [
            "Hi! How can I help you today?",
            "What brings you here?",
            "What are you looking for?",
            "How can I assist you?",
            "What can I help you with?"
        ],
        "zh": [
            "您好！今天我能为您做些什么？",
            "是什么带您来到这里？",
            "您在寻找什么？",
            "我能为您提供什么帮助？",
            "有什么我可以帮助您的吗？"
        ],
        "es": [
            "¡Hola! ¿Cómo puedo ayudarte hoy?",
            "¿Qué te trae por aquí?",
            "¿Qué estás buscando?",
            "¿Cómo puedo asistirte?",
            "¿En qué puedo ayudarte?"
        ]
    }
    
    return starters.get(language, starters["en"])