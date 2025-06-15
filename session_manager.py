import streamlit as st
from typing import Dict, List, Optional
import hashlib
import uuid
from datetime import datetime, timedelta
from database import get_db_manager

class SessionManager:
    """Manages user sessions and persistent memory."""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def get_or_create_session(self) -> str:
        """Get existing session or create new one."""
        # Try to get session from Streamlit session state
        if "session_id" in st.session_state:
            session_id = st.session_state.session_id
            
            # Verify session exists in database
            session_data = self.db.get_session(session_id)
            if session_data and session_data['is_active']:
                # Update activity timestamp
                self.db.update_session_activity(session_id)
                return session_id
        
        # Create new session
        session_id = self.db.create_session(
            user_identifier=self._generate_user_identifier(),
            language=st.session_state.get('language', 'en')
        )
        
        st.session_state.session_id = session_id
        
        # Log session creation
        self.db.log_analytics_event(
            event_type="session_created",
            session_id=session_id,
            data={"user_agent": self._get_user_agent()}
        )
        
        return session_id
    
    def _generate_user_identifier(self) -> str:
        """Generate a unique user identifier based on browser fingerprint."""
        # In a real implementation, you might use more sophisticated fingerprinting
        # For now, we'll use a simple approach
        user_agent = self._get_user_agent()
        timestamp = str(datetime.now().timestamp())
        
        # Create a hash of user agent + timestamp for uniqueness
        identifier = hashlib.md5(f"{user_agent}_{timestamp}".encode()).hexdigest()[:12]
        return f"user_{identifier}"
    
    def _get_user_agent(self) -> str:
        """Get user agent from headers (simplified for Streamlit)."""
        # In Streamlit, we don't have direct access to headers
        # This is a placeholder - in production, you might use JavaScript
        return "streamlit_user"
    
    def load_conversation_history(self, session_id: str) -> List[Dict]:
        """Load conversation history for session."""
        return self.db.get_conversation_history(session_id)
    
    def save_message(self, session_id: str, role: str, content: str, 
                    lead_id: str = None, language: str = "en") -> str:
        """Save a conversation message."""
        return self.db.save_conversation_message(
            session_id=session_id,
            role=role,
            content=content,
            lead_id=lead_id,
            language=language
        )
    
    def load_lead_data(self, session_id: str) -> Dict:
        """Load lead data for session."""
        lead_data = self.db.get_lead_by_session(session_id)
        
        if lead_data:
            return {
                'name': lead_data.get('name'),
                'email': lead_data.get('email'),
                'phone': lead_data.get('phone'),
                'company': lead_data.get('company'),
                'interest': lead_data.get('interest'),
                'budget': lead_data.get('budget'),
                'language': lead_data.get('language', 'en'),
                'score': lead_data.get('score', 0),
                'priority': lead_data.get('priority', 'low'),
                'status': lead_data.get('status', 'new')
            }
        
        return {
            'name': None, 'email': None, 'phone': None, 
            'company': None, 'interest': None, 'budget': None,
            'language': 'en', 'score': 0, 'priority': 'low', 'status': 'new'
        }
    
    def save_lead_data(self, session_id: str, lead_data: Dict) -> str:
        """Save lead data for session."""
        lead_id = self.db.save_lead(lead_data, session_id)
        
        # Log lead update
        self.db.log_analytics_event(
            event_type="lead_updated",
            session_id=session_id,
            lead_id=lead_id,
            data={"fields_updated": list(lead_data.keys())}
        )
        
        return lead_id
    
    def initialize_session_state(self):
        """Initialize Streamlit session state with persistent data."""
        session_id = self.get_or_create_session()
        
        # Load conversation history if not already loaded
        if "messages_loaded" not in st.session_state:
            conversation_history = self.load_conversation_history(session_id)
            
            if conversation_history:
                # Convert database format to Streamlit format
                st.session_state.messages = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in conversation_history
                ]
            else:
                # Initialize with welcome message if no history
                from multilanguage import get_ui_text
                language = st.session_state.get('language', 'en')
                welcome_msg = get_ui_text("welcome", language)
                st.session_state.messages = [
                    {"role": "assistant", "content": welcome_msg}
                ]
            
            st.session_state.messages_loaded = True
        
        # Load lead data if not already loaded
        if "lead_data_loaded" not in st.session_state:
            st.session_state.lead_data = self.load_lead_data(session_id)
            st.session_state.lead_data_loaded = True
        
        return session_id
    
    def update_lead_status(self, lead_id: str, status: str, notes: str = None):
        """Update lead status."""
        self.db.update_lead_status(lead_id, status, notes)
        
        # Log status change
        self.db.log_analytics_event(
            event_type="lead_status_changed",
            lead_id=lead_id,
            data={"new_status": status, "notes": notes}
        )
    
    def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for current session."""
        session_data = self.db.get_session(session_id)
        lead_data = self.db.get_lead_by_session(session_id)
        conversation_count = len(self.db.get_conversation_history(session_id))
        
        return {
            'session_duration': self._calculate_session_duration(session_data),
            'message_count': conversation_count,
            'lead_score': lead_data.get('score', 0) if lead_data else 0,
            'lead_priority': lead_data.get('priority', 'low') if lead_data else 'low',
            'language': session_data.get('language', 'en') if session_data else 'en'
        }
    
    def _calculate_session_duration(self, session_data: Dict) -> str:
        """Calculate session duration."""
        if not session_data:
            return "0 minutes"
        
        try:
            created_at = datetime.fromisoformat(session_data['created_at'])
            last_active = datetime.fromisoformat(session_data['last_active'])
            duration = last_active - created_at
            
            if duration.total_seconds() < 60:
                return f"{int(duration.total_seconds())} seconds"
            elif duration.total_seconds() < 3600:
                return f"{int(duration.total_seconds() / 60)} minutes"
            else:
                return f"{duration.total_seconds() / 3600:.1f} hours"
        except:
            return "Unknown"
    
    def cleanup_session(self, session_id: str):
        """Clean up session data."""
        # Mark session as inactive
        # In a real implementation, you might want to keep sessions for a while
        pass
    
    def resume_conversation_prompt(self, session_id: str) -> Optional[str]:
        """Generate a prompt for resuming conversation."""
        lead_data = self.db.get_lead_by_session(session_id)
        conversation_history = self.db.get_conversation_history(session_id, limit=5)
        
        if not conversation_history:
            return None
        
        last_message = conversation_history[-1]
        time_since_last = datetime.now() - datetime.fromisoformat(last_message['timestamp'])
        
        if time_since_last.total_seconds() > 3600:  # More than 1 hour
            name = lead_data.get('name', 'there') if lead_data else 'there'
            return f"Welcome back, {name}! I see we were chatting earlier. How can I continue helping you today?"
        
        return None

# Singleton instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get the session manager singleton instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager