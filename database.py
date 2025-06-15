import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import streamlit as st
import hashlib

class DatabaseManager:
    """Manages SQLite database operations for Lia."""
    
    def __init__(self, db_path: str = "lia_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create leads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                interest TEXT,
                budget TEXT,
                language TEXT DEFAULT 'en',
                score INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'low',
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                source TEXT DEFAULT 'website'
            )
        ''')
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                lead_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                language TEXT DEFAULT 'en',
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_identifier TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                metadata TEXT
            )
        ''')
        
        # Create analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id TEXT PRIMARY KEY,
                event_type TEXT,
                session_id TEXT,
                lead_id TEXT,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def create_session(self, user_identifier: str = None, language: str = "en") -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        
        if not user_identifier:
            user_identifier = f"anonymous_{session_id[:8]}"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (id, user_identifier, language, metadata)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_identifier, language, json.dumps({})))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session information."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_identifier, language, created_at, last_active, is_active, metadata
            FROM sessions WHERE id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_identifier': row[1],
                'language': row[2],
                'created_at': row[3],
                'last_active': row[4],
                'is_active': bool(row[5]),
                'metadata': json.loads(row[6]) if row[6] else {}
            }
        return None
    
    def update_session_activity(self, session_id: str):
        """Update session last activity timestamp."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions SET last_active = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def save_lead(self, lead_data: Dict, session_id: str) -> str:
        """Save or update lead information."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if lead already exists for this session
        cursor.execute('''
            SELECT id FROM leads WHERE session_id = ?
        ''', (session_id,))
        
        existing_lead = cursor.fetchone()
        
        if existing_lead:
            # Update existing lead
            lead_id = existing_lead[0]
            cursor.execute('''
                UPDATE leads SET 
                    name = COALESCE(?, name),
                    email = COALESCE(?, email),
                    phone = COALESCE(?, phone),
                    company = COALESCE(?, company),
                    interest = COALESCE(?, interest),
                    budget = COALESCE(?, budget),
                    language = ?,
                    score = ?,
                    priority = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                lead_data.get('name'),
                lead_data.get('email'),
                lead_data.get('phone'),
                lead_data.get('company'),
                lead_data.get('interest'),
                lead_data.get('budget'),
                lead_data.get('language', 'en'),
                lead_data.get('score', 0),
                lead_data.get('priority', 'low'),
                lead_id
            ))
        else:
            # Create new lead
            lead_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO leads (
                    id, session_id, name, email, phone, company, interest, 
                    budget, language, score, priority, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead_id,
                session_id,
                lead_data.get('name'),
                lead_data.get('email'),
                lead_data.get('phone'),
                lead_data.get('company'),
                lead_data.get('interest'),
                lead_data.get('budget'),
                lead_data.get('language', 'en'),
                lead_data.get('score', 0),
                lead_data.get('priority', 'low'),
                lead_data.get('status', 'new')
            ))
        
        conn.commit()
        conn.close()
        
        return lead_id
    
    def get_lead_by_session(self, session_id: str) -> Optional[Dict]:
        """Get lead information by session ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_id, name, email, phone, company, interest, 
                   budget, language, score, priority, status, created_at, updated_at
            FROM leads WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'session_id': row[1],
                'name': row[2],
                'email': row[3],
                'phone': row[4],
                'company': row[5],
                'interest': row[6],
                'budget': row[7],
                'language': row[8],
                'score': row[9],
                'priority': row[10],
                'status': row[11],
                'created_at': row[12],
                'updated_at': row[13]
            }
        return None
    
    def save_conversation_message(self, session_id: str, role: str, content: str, 
                                 lead_id: str = None, language: str = "en") -> str:
        """Save a conversation message."""
        message_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (id, session_id, lead_id, role, content, language)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, session_id, lead_id, role, content, language))
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, role, content, timestamp, language
            FROM conversations 
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'role': row[1],
                'content': row[2],
                'timestamp': row[3],
                'language': row[4]
            }
            for row in rows
        ]
    
    def get_all_leads(self, limit: int = 100, offset: int = 0, 
                     filters: Dict = None) -> List[Dict]:
        """Get all leads with optional filtering."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, session_id, name, email, phone, company, interest, 
                   budget, language, score, priority, status, created_at, updated_at
            FROM leads
        '''
        
        params = []
        conditions = []
        
        if filters:
            if filters.get('priority'):
                conditions.append('priority = ?')
                params.append(filters['priority'])
            
            if filters.get('status'):
                conditions.append('status = ?')
                params.append(filters['status'])
            
            if filters.get('language'):
                conditions.append('language = ?')
                params.append(filters['language'])
            
            if filters.get('date_from'):
                conditions.append('created_at >= ?')
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append('created_at <= ?')
                params.append(filters['date_to'])
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'session_id': row[1],
                'name': row[2],
                'email': row[3],
                'phone': row[4],
                'company': row[5],
                'interest': row[6],
                'budget': row[7],
                'language': row[8],
                'score': row[9],
                'priority': row[10],
                'status': row[11],
                'created_at': row[12],
                'updated_at': row[13]
            }
            for row in rows
        ]
    
    def update_lead_status(self, lead_id: str, status: str, notes: str = None):
        """Update lead status and notes."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE leads SET 
                status = ?,
                notes = COALESCE(?, notes),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, notes, lead_id))
        
        conn.commit()
        conn.close()
    
    def log_analytics_event(self, event_type: str, session_id: str = None, 
                           lead_id: str = None, data: Dict = None):
        """Log analytics event."""
        event_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analytics (id, event_type, session_id, lead_id, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_id, event_type, session_id, lead_id, json.dumps(data) if data else None))
        
        conn.commit()
        conn.close()
    
    def get_analytics_summary(self, days: int = 30) -> Dict:
        """Get analytics summary for the last N days."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total leads
        cursor.execute('''
            SELECT COUNT(*) FROM leads 
            WHERE created_at >= datetime('now', '-{} days')
        '''.format(days))
        total_leads = cursor.fetchone()[0]
        
        # Leads by priority
        cursor.execute('''
            SELECT priority, COUNT(*) FROM leads 
            WHERE created_at >= datetime('now', '-{} days')
            GROUP BY priority
        '''.format(days))
        leads_by_priority = dict(cursor.fetchall())
        
        # Leads by language
        cursor.execute('''
            SELECT language, COUNT(*) FROM leads 
            WHERE created_at >= datetime('now', '-{} days')
            GROUP BY language
        '''.format(days))
        leads_by_language = dict(cursor.fetchall())
        
        # Average score
        cursor.execute('''
            SELECT AVG(score) FROM leads 
            WHERE created_at >= datetime('now', '-{} days')
        '''.format(days))
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_leads': total_leads,
            'leads_by_priority': leads_by_priority,
            'leads_by_language': leads_by_language,
            'average_score': round(avg_score, 1),
            'period_days': days
        }
    
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up old inactive sessions."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions SET is_active = 0
            WHERE last_active < datetime('now', '-{} days')
        '''.format(days))
        
        conn.commit()
        conn.close()

# Singleton instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get the database manager singleton instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager