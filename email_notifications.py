import smtplib
import ssl
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import streamlit as st
from typing import Dict, List, Optional
import json
from datetime import datetime
import logging
from database import get_db_manager
from multilanguage import get_ui_text

class EmailNotificationManager:
    """Manages email notifications for lead generation events."""
    
    def __init__(self):
        self.db = get_db_manager()
        self.smtp_config = self._load_smtp_config()
        
    def _load_smtp_config(self) -> Dict:
        """Load SMTP configuration from Streamlit secrets or config."""
        try:
            # Try to load from Streamlit secrets first
            if hasattr(st, 'secrets') and 'email' in st.secrets:
                return {
                    'smtp_server': st.secrets.email.get('smtp_server', 'smtp.gmail.com'),
                    'smtp_port': st.secrets.email.get('smtp_port', 587),
                    'username': st.secrets.email.get('username', ''),
                    'password': st.secrets.email.get('password', ''),
                    'from_email': st.secrets.email.get('from_email', ''),
                    'from_name': st.secrets.email.get('from_name', 'Lia - LeadPulse')
                }
        except:
            pass
        
        # Fallback to default configuration
        return {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': '',
            'password': '',
            'from_email': '',
            'from_name': 'Lia - LeadPulse'
        }
    
    def configure_smtp(self, smtp_server: str, smtp_port: int, username: str, 
                      password: str, from_email: str, from_name: str = "Lia"):
        """Configure SMTP settings."""
        self.smtp_config = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'username': username,
            'password': password,
            'from_email': from_email,
            'from_name': from_name
        }
        
        # Save to session state for persistence during session
        st.session_state.email_config = self.smtp_config
    
    def test_smtp_connection(self) -> bool:
        """Test SMTP connection and authentication."""
        try:
            if not self.smtp_config.get('username') or not self.smtp_config.get('password'):
                return False
            
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            server.starttls(context=context)
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.quit()
            return True
        except Exception as e:
            logging.error(f"SMTP connection test failed: {e}")
            return False
    
    def send_new_lead_notification(self, lead_data: Dict, recipient_emails: List[str], 
                                  language: str = "en") -> bool:
        """Send notification email for new lead."""
        try:
            subject = self._get_email_subject("new_lead", language, lead_data)
            body = self._generate_new_lead_email_body(lead_data, language)
            
            return self._send_email(
                recipients=recipient_emails,
                subject=subject,
                body=body,
                is_html=True
            )
        except Exception as e:
            logging.error(f"Failed to send new lead notification: {e}")
            return False
    
    def send_lead_status_update(self, lead_data: Dict, old_status: str, new_status: str,
                               recipient_emails: List[str], language: str = "en") -> bool:
        """Send notification email for lead status update."""
        try:
            subject = self._get_email_subject("status_update", language, lead_data)
            body = self._generate_status_update_email_body(lead_data, old_status, new_status, language)
            
            return self._send_email(
                recipients=recipient_emails,
                subject=subject,
                body=body,
                is_html=True
            )
        except Exception as e:
            logging.error(f"Failed to send status update notification: {e}")
            return False
    
    def send_daily_summary(self, recipient_emails: List[str], language: str = "en") -> bool:
        """Send daily lead summary email."""
        try:
            # Get today's analytics
            analytics = self.db.get_analytics_summary(days=1)
            recent_leads = self.db.get_all_leads(limit=10)
            
            subject = self._get_email_subject("daily_summary", language)
            body = self._generate_daily_summary_email_body(analytics, recent_leads, language)
            
            return self._send_email(
                recipients=recipient_emails,
                subject=subject,
                body=body,
                is_html=True
            )
        except Exception as e:
            logging.error(f"Failed to send daily summary: {e}")
            return False
    
    def send_weekly_report(self, recipient_emails: List[str], language: str = "en") -> bool:
        """Send weekly lead report email."""
        try:
            # Get weekly analytics
            analytics = self.db.get_analytics_summary(days=7)
            top_leads = self.db.get_all_leads(limit=20, filters={'priority': 'high'})
            
            subject = self._get_email_subject("weekly_report", language)
            body = self._generate_weekly_report_email_body(analytics, top_leads, language)
            
            return self._send_email(
                recipients=recipient_emails,
                subject=subject,
                body=body,
                is_html=True
            )
        except Exception as e:
            logging.error(f"Failed to send weekly report: {e}")
            return False
    
    def send_lead_follow_up_reminder(self, lead_data: Dict, recipient_emails: List[str],
                                   language: str = "en") -> bool:
        """Send follow-up reminder for a lead."""
        try:
            subject = self._get_email_subject("follow_up_reminder", language, lead_data)
            body = self._generate_follow_up_reminder_email_body(lead_data, language)
            
            return self._send_email(
                recipients=recipient_emails,
                subject=subject,
                body=body,
                is_html=True
            )
        except Exception as e:
            logging.error(f"Failed to send follow-up reminder: {e}")
            return False
    
    def _send_email(self, recipients: List[str], subject: str, body: str, 
                   is_html: bool = False, attachments: List[str] = None) -> bool:
        """Send email using configured SMTP settings."""
        try:
            if not self.smtp_config.get('username') or not self.smtp_config.get('password'):
                logging.error("SMTP credentials not configured")
                return False
            
            # Create message
            message = MimeMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            message["To"] = ", ".join(recipients)
            
            # Add body
            if is_html:
                part = MimeText(body, "html")
            else:
                part = MimeText(body, "plain")
            message.attach(part)
            
            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, "rb") as attachment:
                            part = MimeBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {file_path.split("/")[-1]}'
                        )
                        message.attach(part)
                    except Exception as e:
                        logging.error(f"Failed to attach file {file_path}: {e}")
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                server.starttls(context=context)
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.sendmail(self.smtp_config['from_email'], recipients, message.as_string())
            
            # Log successful send
            self.db.log_analytics_event(
                event_type="email_sent",
                data={
                    "recipients": recipients,
                    "subject": subject,
                    "type": "notification"
                }
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            return False
    
    def _get_email_subject(self, email_type: str, language: str, lead_data: Dict = None) -> str:
        """Generate email subject based on type and language."""
        subjects = {
            "new_lead": {
                "en": f"🚀 New Lead: {lead_data.get('name', 'Unknown')} from {lead_data.get('company', 'Unknown Company')}",
                "zh": f"🚀 新潜在客户：{lead_data.get('name', '未知')} 来自 {lead_data.get('company', '未知公司')}",
                "es": f"🚀 Nuevo Lead: {lead_data.get('name', 'Desconocido')} de {lead_data.get('company', 'Empresa Desconocida')}"
            },
            "status_update": {
                "en": f"📋 Lead Status Update: {lead_data.get('name', 'Unknown')}",
                "zh": f"📋 潜在客户状态更新：{lead_data.get('name', '未知')}",
                "es": f"📋 Actualización de Estado: {lead_data.get('name', 'Desconocido')}"
            },
            "daily_summary": {
                "en": "📊 Daily Lead Summary - LeadPulse",
                "zh": "📊 每日潜在客户摘要 - LeadPulse",
                "es": "📊 Resumen Diario de Leads - LeadPulse"
            },
            "weekly_report": {
                "en": "📈 Weekly Lead Report - LeadPulse",
                "zh": "📈 每周潜在客户报告 - LeadPulse",
                "es": "📈 Reporte Semanal de Leads - LeadPulse"
            },
            "follow_up_reminder": {
                "en": f"⏰ Follow-up Reminder: {lead_data.get('name', 'Unknown')}",
                "zh": f"⏰ 跟进提醒：{lead_data.get('name', '未知')}",
                "es": f"⏰ Recordatorio de Seguimiento: {lead_data.get('name', 'Desconocido')}"
            }
        }
        
        return subjects.get(email_type, {}).get(language, subjects.get(email_type, {}).get("en", "LeadPulse Notification"))
    
    def _generate_new_lead_email_body(self, lead_data: Dict, language: str) -> str:
        """Generate HTML email body for new lead notification."""
        templates = {
            "en": f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #3B82F6;">🚀 New Lead Captured!</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Lead Information:</h3>
                        <p><strong>Name:</strong> {lead_data.get('name', 'Not provided')}</p>
                        <p><strong>Email:</strong> {lead_data.get('email', 'Not provided')}</p>
                        <p><strong>Phone:</strong> {lead_data.get('phone', 'Not provided')}</p>
                        <p><strong>Company:</strong> {lead_data.get('company', 'Not provided')}</p>
                        <p><strong>Interest:</strong> {lead_data.get('interest', 'Not provided')}</p>
                        <p><strong>Budget:</strong> {lead_data.get('budget', 'Not provided')}</p>
                        <p><strong>Priority:</strong> <span style="color: {'#ff4444' if lead_data.get('priority') == 'high' else '#ffaa00' if lead_data.get('priority') == 'medium' else '#44ff44'};">{lead_data.get('priority', 'low').title()}</span></p>
                        <p><strong>Score:</strong> {lead_data.get('score', 0)}/100</p>
                    </div>
                    
                    <p>This lead was captured on {datetime.now().strftime('%Y-%m-%d at %H:%M')} via Lia AI Assistant.</p>
                    
                    <div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
                        <p style="margin: 0;"><strong>Next Steps:</strong></p>
                        <ul style="margin: 10px 0;">
                            <li>Review the lead information</li>
                            <li>Reach out within 24 hours for best results</li>
                            <li>Update lead status in the dashboard</li>
                        </ul>
                    </div>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        This email was sent automatically by Lia AI Assistant.<br>
                        Powered by LeadPulse - AI Lead Generation Platform
                    </p>
                </div>
            </body>
            </html>
            """,
            "zh": f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #3B82F6;">🚀 捕获新的潜在客户！</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">潜在客户信息：</h3>
                        <p><strong>姓名：</strong> {lead_data.get('name', '未提供')}</p>
                        <p><strong>邮箱：</strong> {lead_data.get('email', '未提供')}</p>
                        <p><strong>电话：</strong> {lead_data.get('phone', '未提供')}</p>
                        <p><strong>公司：</strong> {lead_data.get('company', '未提供')}</p>
                        <p><strong>兴趣：</strong> {lead_data.get('interest', '未提供')}</p>
                        <p><strong>预算：</strong> {lead_data.get('budget', '未提供')}</p>
                        <p><strong>优先级：</strong> <span style="color: {'#ff4444' if lead_data.get('priority') == 'high' else '#ffaa00' if lead_data.get('priority') == 'medium' else '#44ff44'};">{'高' if lead_data.get('priority') == 'high' else '中' if lead_data.get('priority') == 'medium' else '低'}</span></p>
                        <p><strong>评分：</strong> {lead_data.get('score', 0)}/100</p>
                    </div>
                    
                    <p>此潜在客户于 {datetime.now().strftime('%Y-%m-%d %H:%M')} 通过 Lia AI 助手捕获。</p>
                    
                    <div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
                        <p style="margin: 0;"><strong>下一步：</strong></p>
                        <ul style="margin: 10px 0;">
                            <li>查看潜在客户信息</li>
                            <li>在24小时内联系以获得最佳效果</li>
                            <li>在仪表板中更新潜在客户状态</li>
                        </ul>
                    </div>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        此邮件由 Lia AI 助手自动发送。<br>
                        由 LeadPulse - AI 潜在客户生成平台提供支持
                    </p>
                </div>
            </body>
            </html>
            """,
            "es": f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #3B82F6;">🚀 ¡Nuevo Lead Capturado!</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Información del Lead:</h3>
                        <p><strong>Nombre:</strong> {lead_data.get('name', 'No proporcionado')}</p>
                        <p><strong>Email:</strong> {lead_data.get('email', 'No proporcionado')}</p>
                        <p><strong>Teléfono:</strong> {lead_data.get('phone', 'No proporcionado')}</p>
                        <p><strong>Empresa:</strong> {lead_data.get('company', 'No proporcionado')}</p>
                        <p><strong>Interés:</strong> {lead_data.get('interest', 'No proporcionado')}</p>
                        <p><strong>Presupuesto:</strong> {lead_data.get('budget', 'No proporcionado')}</p>
                        <p><strong>Prioridad:</strong> <span style="color: {'#ff4444' if lead_data.get('priority') == 'high' else '#ffaa00' if lead_data.get('priority') == 'medium' else '#44ff44'};">{'Alta' if lead_data.get('priority') == 'high' else 'Media' if lead_data.get('priority') == 'medium' else 'Baja'}</span></p>
                        <p><strong>Puntuación:</strong> {lead_data.get('score', 0)}/100</p>
                    </div>
                    
                    <p>Este lead fue capturado el {datetime.now().strftime('%Y-%m-%d a las %H:%M')} a través del Asistente AI Lia.</p>
                    
                    <div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
                        <p style="margin: 0;"><strong>Próximos Pasos:</strong></p>
                        <ul style="margin: 10px 0;">
                            <li>Revisar la información del lead</li>
                            <li>Contactar dentro de 24 horas para mejores resultados</li>
                            <li>Actualizar el estado del lead en el dashboard</li>
                        </ul>
                    </div>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        Este email fue enviado automáticamente por el Asistente AI Lia.<br>
                        Powered by LeadPulse - Plataforma de Generación de Leads AI
                    </p>
                </div>
            </body>
            </html>
            """
        }
        
        return templates.get(language, templates["en"])
    
    def _generate_status_update_email_body(self, lead_data: Dict, old_status: str, 
                                          new_status: str, language: str) -> str:
        """Generate HTML email body for status update notification."""
        # Simplified version - would be expanded with full templates
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Lead Status Update</h2>
            <p><strong>Lead:</strong> {lead_data.get('name', 'Unknown')}</p>
            <p><strong>Status changed from:</strong> {old_status} → {new_status}</p>
            <p><strong>Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </body>
        </html>
        """
    
    def _generate_daily_summary_email_body(self, analytics: Dict, recent_leads: List[Dict], 
                                          language: str) -> str:
        """Generate HTML email body