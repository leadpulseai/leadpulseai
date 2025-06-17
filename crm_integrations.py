import requests
import json
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from database import get_db_manager
from email_notifications import get_email_manager

class CRMIntegrationManager:
    """Manages integrations with various CRM and messaging platforms."""
    
    def __init__(self):
        self.db = get_db_manager()
        self.email_manager = get_email_manager()
        self.integrations = {
            'hubspot': HubSpotIntegration(),
            'salesforce': SalesforceIntegration(),
            'airtable': AirtableIntegration(),
            'notion': NotionIntegration(),
            'slack': SlackIntegration(),
            'discord': DiscordIntegration(),
            'webhook': WebhookIntegration()
        }
    
    def get_available_integrations(self) -> List[Dict]:
        """Get list of available integrations."""
        return [
            {
                'id': 'hubspot',
                'name': 'HubSpot CRM',
                'description': 'Sync leads to HubSpot CRM automatically',
                'icon': '🔗',
                'category': 'CRM',
                'status': self._get_integration_status('hubspot')
            },
            {
                'id': 'salesforce',
                'name': 'Salesforce',
                'description': 'Push leads to Salesforce CRM',
                'icon': '☁️',
                'category': 'CRM',
                'status': self._get_integration_status('salesforce')
            },
            {
                'id': 'airtable',
                'name': 'Airtable',
                'description': 'Store leads in Airtable database',
                'icon': '📊',
                'category': 'Database',
                'status': self._get_integration_status('airtable')
            },
            {
                'id': 'notion',
                'name': 'Notion',
                'description': 'Create lead pages in Notion workspace',
                'icon': '📝',
                'category': 'Productivity',
                'status': self._get_integration_status('notion')
            },
            {
                'id': 'slack',
                'name': 'Slack',
                'description': 'Send lead notifications to Slack channels',
                'icon': '💬',
                'category': 'Messaging',
                'status': self._get_integration_status('slack')
            },
            {
                'id': 'discord',
                'name': 'Discord',
                'description': 'Send lead notifications to Discord channels',
                'icon': '🎮',
                'category': 'Messaging',
                'status': self._get_integration_status('discord')
            },
            {
                'id': 'webhook',
                'name': 'Custom Webhook',
                'description': 'Send lead data to custom webhook URL',
                'icon': '🔌',
                'category': 'Custom',
                'status': self._get_integration_status('webhook')
            }
        ]
    
    def configure_integration(self, integration_id: str, config: Dict) -> bool:
        """Configure an integration with provided settings."""
        try:
            if integration_id in self.integrations:
                success = self.integrations[integration_id].configure(config)
                if success:
                    # Save configuration to session state
                    if 'integrations_config' not in st.session_state:
                        st.session_state.integrations_config = {}
                    st.session_state.integrations_config[integration_id] = config
                    
                    # Log configuration
                    self.db.log_analytics_event(
                        event_type="integration_configured",
                        data={"integration": integration_id, "success": True}
                    )
                return success
            return False
        except Exception as e:
            logging.error(f"Failed to configure {integration_id}: {e}")
            return False
    
    def test_integration(self, integration_id: str) -> bool:
        """Test an integration connection."""
        try:
            if integration_id in self.integrations:
                return self.integrations[integration_id].test_connection()
            return False
        except Exception as e:
            logging.error(f"Failed to test {integration_id}: {e}")
            return False
    
    def sync_lead_to_integrations(self, lead_data: Dict, session_id: str) -> Dict[str, bool]:
        """Sync lead data to all configured integrations."""
        results = {}
        
        for integration_id, integration in self.integrations.items():
            if self._is_integration_enabled(integration_id):
                try:
                    success = integration.sync_lead(lead_data)
                    results[integration_id] = success
                    
                    # Log sync result
                    self.db.log_analytics_event(
                        event_type="lead_synced",
                        session_id=session_id,
                        data={
                            "integration": integration_id,
                            "success": success,
                            "lead_name": lead_data.get('name', 'Unknown')
                        }
                    )
                except Exception as e:
                    logging.error(f"Failed to sync lead to {integration_id}: {e}")
                    results[integration_id] = False
        
        return results
    
    def send_lead_notification(self, lead_data: Dict, session_id: str) -> Dict[str, bool]:
        """Send lead notifications to messaging integrations."""
        results = {}
        
        messaging_integrations = ['slack', 'discord', 'webhook']
        
        for integration_id in messaging_integrations:
            if self._is_integration_enabled(integration_id):
                try:
                    integration = self.integrations[integration_id]
                    success = integration.send_notification(lead_data)
                    results[integration_id] = success
                except Exception as e:
                    logging.error(f"Failed to send notification to {integration_id}: {e}")
                    results[integration_id] = False
        
        return results
    
    def _get_integration_status(self, integration_id: str) -> str:
        """Get integration status (configured, enabled, disabled)."""
        if 'integrations_config' in st.session_state:
            config = st.session_state.integrations_config.get(integration_id)
            if config and config.get('enabled', False):
                return 'enabled'
            elif config:
                return 'configured'
        return 'disabled'
    
    def _is_integration_enabled(self, integration_id: str) -> bool:
        """Check if integration is enabled."""
        return self._get_integration_status(integration_id) == 'enabled'

class BaseIntegration:
    """Base class for all integrations."""
    
    def __init__(self):
        self.config = {}
        self.is_configured = False
    
    def configure(self, config: Dict) -> bool:
        """Configure the integration."""
        self.config = config
        self.is_configured = True
        return True
    
    def test_connection(self) -> bool:
        """Test the integration connection."""
        return self.is_configured
    
    def sync_lead(self, lead_data: Dict) -> bool:
        """Sync lead data to the platform."""
        raise NotImplementedError
    
    def send_notification(self, lead_data: Dict) -> bool:
        """Send notification about new lead."""
        raise NotImplementedError

class HubSpotIntegration(BaseIntegration):
    """HubSpot CRM integration."""
    
    def configure(self, config: Dict) -> bool:
        """Configure HubSpot integration."""
        required_fields = ['api_key', 'portal_id']
        if all(field in config for field in required_fields):
            self.config = config
            self.is_configured = True
            return True
        return False
    
    def test_connection(self) -> bool:
        """Test HubSpot API connection."""
        if not self.is_configured:
            return False
        
        try:
            headers = {
                'Authorization': f"Bearer {self.config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"https://api.hubapi.com/contacts/v1/lists/all/contacts/all",
                headers=headers,
                params={'count': 1}
            )
            
            return response.status_code == 200
        except Exception as e:
            logging.error(f"HubSpot connection test failed: {e}")
            return False
    
    def sync_lead(self, lead_data: Dict) -> bool:
        """Sync lead to HubSpot."""
        if not self.is_configured:
            return False
        
        try:
            headers = {
                'Authorization': f"Bearer {self.config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            # Prepare contact data for HubSpot
            contact_data = {
                'properties': [
                    {'property': 'email', 'value': lead_data.get('email', '')},
                    {'property': 'firstname', 'value': lead_data.get('name', '').split(' ')[0] if lead_data.get('name') else ''},
                    {'property': 'lastname', 'value': ' '.join(lead_data.get('name', '').split(' ')[1:]) if lead_data.get('name') and len(lead_data.get('name', '').split(' ')) > 1 else ''},
                    {'property': 'phone', 'value': lead_data.get('phone', '')},
                    {'property': 'company', 'value': lead_data.get('company', '')},
                    {'property': 'hs_lead_status', 'value': 'NEW'},
                    {'property': 'lead_source', 'value': 'Lia AI Assistant'},
                    {'property': 'notes_last_contacted', 'value': f"Interest: {lead_data.get('interest', 'N/A')}, Budget: {lead_data.get('budget', 'N/A')}"}
                ]
            }
            
            response = requests.post(
                'https://api.hubapi.com/contacts/v1/contact',
                headers=headers,
                json=contact_data
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            logging.error(f"Failed to sync lead to HubSpot: {e}")
            return False

class SalesforceIntegration(BaseIntegration):
    """Salesforce CRM integration."""
    
    def configure(self, config: Dict) -> bool:
        """Configure Salesforce integration."""
        required_fields = ['instance_url', 'access_token']
        if all(field in config for field in required_fields):
            self.config = config
            self.is_configured = True
            return True
        return False
    
    def sync_lead(self, lead_data: Dict) -> bool:
        """Sync lead to Salesforce."""
        if not self.is_configured:
            return False
        
        try:
            headers = {
                'Authorization': f"Bearer {self.config['access_token']}",
                'Content-Type': 'application/json'
            }
            
            # Prepare lead data for Salesforce
            sf_lead_data = {
                'FirstName': lead_data.get('name', '').split(' ')[0] if lead_data.get('name') else '',
                'LastName': ' '.join(lead_data.get('name', '').split(' ')[1:]) if lead_data.get('name') and len(lead_data.get('name', '').split(' ')) > 1 else 'Unknown',
                'Email': lead_data.get('email', ''),
                'Phone': lead_data.get('phone', ''),
                'Company': lead_data.get('company', 'Unknown Company'),
                'LeadSource': 'Lia AI Assistant',
                'Status': 'Open - Not Contacted',
                'Description': f"Interest: {lead_data.get('interest', 'N/A')}, Budget: {lead_data.get('budget', 'N/A')}"
            }
            
            response = requests.post(
                f"{self.config['instance_url']}/services/data/v52.0/sobjects/Lead/",
                headers=headers,
                json=sf_lead_data
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            logging.error(f"Failed to sync lead to Salesforce: {e}")
            return False

class AirtableIntegration(BaseIntegration):
    """Airtable integration."""
    
    def configure(self, config: Dict) -> bool:
        """Configure Airtable integration."""
        required_fields = ['api_key', 'base_id', 'table_name']
        if all(field in config for field in required_fields):
            self.config = config
            self.is_configured = True
            return True
        return False
    
    def sync_lead(self, lead_data: Dict) -> bool:
        """Sync lead to Airtable."""
        if not self.is_configured:
            return False
        
        try:
            headers = {
                'Authorization': f"Bearer {self.config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            # Prepare record data for Airtable
            record_data = {
                'records': [
                    {
                        'fields': {
                            'Name': lead_data.get('name', ''),
                            'Email': lead_data.get('email', ''),
                            'Phone': lead_data.get('phone', ''),
                            'Company': lead_data.get('company', ''),
                            'Interest': lead_data.get('interest', ''),
                            'Budget': lead_data.get('budget', ''),
                            'Priority': lead_data.get('priority', 'low'),
                            'Score': lead_data.get('score', 0),
                            'Source': 'Lia AI Assistant',
                            'Created': datetime.now().isoformat()
                        }
                    }
                ]
            }
            
            response = requests.post(
                f"https://api.airtable.com/v0/{self.config['base_id']}/{self.config['table_name']}",
                headers=headers,
                json=record_data
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            logging.error(f"Failed to sync lead to Airtable: {e}")
            return False

class NotionIntegration(BaseIntegration):
    """Notion integration."""
    
    def configure(self, config: Dict) -> bool:
        """Configure Notion integration."""
        required_fields = ['api_key', 'database_id']
        if all(field in config for field in required_fields):
            self.config = config
            self.is_configured = True
            return True
        return False
    
    def sync_lead(self, lead_data: Dict) -> bool:
        """Sync lead to Notion."""
        if not self.is_configured:
            return False
        
        try:
            headers = {
                'Authorization': f"Bearer {self.config['api_key']}",
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }
            
            # Prepare page data for Notion
            page_data = {
                'parent': {'database_id': self.config['database_id']},
                'properties': {
                    'Name': {
                        'title': [
                            {
                                'text': {
                                    'content': lead_data.get('name', 'Unknown Lead')
                                }
                            }
                        ]
                    },
                    'Email': {
                        'email': lead_data.get('email', '')
                    },
                    'Company': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': lead_data.get('company', '')
                                }
                            }
                        ]
                    },
                    'Priority': {
                        'select': {
                            'name': lead_data.get('priority', 'low').title()
                        }
                    },
                    'Score': {
                        'number': lead_data.get('score', 0)
                    }
                }
            }
            
            response = requests.post(
                'https://api.notion.com/v1/pages',
                headers=headers,
                json=page_data
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            logging.error(f"Failed to sync lead to Notion: {e}")
            return False

class SlackIntegration(BaseIntegration):
    """Slack messaging integration."""
    
    def configure(self, config: Dict) -> bool:
        """Configure Slack integration."""
        required_fields = ['webhook_url']
        if all(field in config for field in required_fields):
            self.config = config
            self.is_configured = True
            return True
        return False
    
    def send_notification(self, lead_data: Dict) -> bool:
        """Send lead notification to Slack."""
        if not self.is_configured:
            return False
        
        try:
            # Prepare Slack message
            message = {
                'text': f"🚀 New Lead Captured!",
                'attachments': [
                    {
                        'color': 'good',
                        'fields': [
                            {'title': 'Name', 'value': lead_data.get('name', 'N/A'), 'short': True},
                            {'title': 'Email', 'value': lead_data.get('email', 'N/A'), 'short': True},
                            {'title': 'Company', 'value': lead_data.get('company', 'N/A'), 'short': True},
                            {'title': 'Priority', 'value': lead_data.get('priority', 'low').title(), 'short': True},
                            {'title': 'Score', 'value': f"{lead_data.get('score', 0)}/100", 'short': True},
                            {'title': 'Interest', 'value': lead_data.get('interest', 'N/A'), 'short': False}
                        ],
                        'footer': 'Lia AI Assistant',
                        'ts': int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.config['webhook_url'],
                json=message
            )
            
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to send Slack notification: {e}")
            return False

class DiscordIntegration(BaseIntegration):
    """Discord messaging integration."""
    
    def configure(self, config: Dict) -> bool:
        """Configure Discord integration."""
        required_fields = ['webhook_url']
        if all(field in config for field in required_fields):
            self.config = config
            self.is_configured = True
            return True
        return False
    
    def send_notification(self, lead_data: Dict) -> bool:
        """Send lead notification to Discord."""
        if not self.is_configured:
            return False
        
        try:
            # Prepare Discord embed
            embed = {
                'title': '🚀 New Lead Captured!',
                'color': 0x3B82F6,
                'fields': [
                    {'name': 'Name', 'value': lead_data.get('name', 'N/A'), 'inline': True},
                    {'name': 'Email', 'value': lead_data.get('email', 'N/A'), 'inline': True},
                    {'name': 'Company', 'value': lead_data.get('company', 'N/A'), 'inline': True},
                    {'name': 'Priority', 'value': lead_data.get('priority', 'low').title(), 'inline': True},
                    {'name': 'Score', 'value': f"{lead_data.get('score', 0)}/100", 'inline': True},
                    {'name': 'Interest', 'value': lead_data.get('interest', 'N/A'), 'inline': False}
                ],
                'footer': {'text': 'Lia AI Assistant'},
                'timestamp': datetime.now().isoformat()
            }
            
            message = {'embeds': [embed]}
            
            response = requests.post(
                self.config['webhook_url'],
                json=message
            )
            
            return response.status_code == 204
        except Exception as e:
            logging.error(f"Failed to send Discord notification: {e}")
            return False

class WebhookIntegration(BaseIntegration):
    """Custom webhook integration."""
    
    def configure(self, config: Dict) -> bool:
        """Configure webhook integration."""
        required_fields = ['webhook_url']
        if all(field in config for field in required_fields):
            self.config = config
            self.is_configured = True
            return True
        return False
    
    def sync_lead(self, lead_data: Dict) -> bool:
        """Send lead data to webhook."""
        return self.send_notification(lead_data)
    
    def send_notification(self, lead_data: Dict) -> bool:
        """Send lead data to custom webhook."""
        if not self.is_configured:
            return False
        
        try:
            # Prepare webhook payload
            payload = {
                'event': 'new_lead',
                'timestamp': datetime.now().isoformat(),
                'source': 'lia_ai_assistant',
                'data': lead_data
            }
            
            headers = {'Content-Type': 'application/json'}
            
            # Add custom headers if configured
            if 'headers' in self.config:
                headers.update(self.config['headers'])
            
            response = requests.post(
                self.config['webhook_url'],
                json=payload,
                headers=headers,
                timeout=10
            )
            
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logging.error(f"Failed to send webhook notification: {e}")
            return False

# Singleton instance
_crm_manager = None

def get_crm_manager() -> CRMIntegrationManager:
    """Get the CRM integration manager singleton instance."""
    global _crm_manager
    if _crm_manager is None:
        _crm_manager = CRMIntegrationManager()
    return _crm_manager

