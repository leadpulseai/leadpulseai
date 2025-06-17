import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import get_db_manager
from multilanguage import get_ui_text
import json

class AdvancedDashboard:
    """Advanced lead dashboard with analytics and management features."""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def render_dashboard(self, language: str = "en"):
        """Render the complete advanced dashboard."""
        st.title(get_ui_text("dashboard_title", language, "📊 Advanced Lead Dashboard"))
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            get_ui_text("overview", language, "Overview"),
            get_ui_text("leads", language, "Leads"),
            get_ui_text("analytics", language, "Analytics"),
            get_ui_text("export", language, "Export"),
            get_ui_text("settings", language, "Settings")
        ])
        
        with tab1:
            self.render_overview_tab(language)
        
        with tab2:
            self.render_leads_management_tab(language)
        
        with tab3:
            self.render_analytics_tab(language)
        
        with tab4:
            self.render_export_tab(language)
        
        with tab5:
            self.render_settings_tab(language)
    
    def render_overview_tab(self, language: str):
        """Render overview dashboard with key metrics."""
        st.subheader(get_ui_text("overview_title", language, "📈 Overview"))
        
        # Time period selector
        col1, col2 = st.columns([2, 1])
        with col1:
            period = st.selectbox(
                get_ui_text("time_period", language, "Time Period"),
                options=[7, 14, 30, 60, 90],
                format_func=lambda x: f"Last {x} days",
                index=2  # Default to 30 days
            )
        
        with col2:
            if st.button(get_ui_text("refresh", language, "🔄 Refresh")):
                st.rerun()
        
        # Get analytics data
        analytics = self.db.get_analytics_summary(days=period)
        
        # Key metrics cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label=get_ui_text("total_leads", language, "Total Leads"),
                value=analytics['total_leads'],
                delta=self._calculate_delta(analytics['total_leads'], period)
            )
        
        with col2:
            st.metric(
                label=get_ui_text("avg_score", language, "Avg Score"),
                value=f"{analytics['average_score']}/100",
                delta=None
            )
        
        with col3:
            high_priority = analytics['leads_by_priority'].get('high', 0)
            st.metric(
                label=get_ui_text("high_priority", language, "High Priority"),
                value=high_priority,
                delta=None
            )
        
        with col4:
            conversion_rate = self._calculate_conversion_rate(period)
            st.metric(
                label=get_ui_text("conversion_rate", language, "Conversion Rate"),
                value=f"{conversion_rate}%",
                delta=None
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_leads_by_priority_chart(analytics, language)
        
        with col2:
            self.render_leads_by_language_chart(analytics, language)
        
        # Recent activity
        st.subheader(get_ui_text("recent_activity", language, "🕒 Recent Activity"))
        self.render_recent_leads_table(language, limit=10)
    
    def render_leads_management_tab(self, language: str):
        """Render leads management interface."""
        st.subheader(get_ui_text("lead_management", language, "👥 Lead Management"))
        
        # Filters
        with st.expander(get_ui_text("filters", language, "🔍 Filters"), expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                priority_filter = st.selectbox(
                    get_ui_text("priority", language, "Priority"),
                    options=["all", "high", "medium", "low"],
                    format_func=lambda x: get_ui_text(x, language, x.title()) if x != "all" else get_ui_text("all", language, "All")
                )
            
            with col2:
                status_filter = st.selectbox(
                    get_ui_text("status", language, "Status"),
                    options=["all", "new", "contacted", "qualified", "converted", "lost"],
                    format_func=lambda x: get_ui_text(x, language, x.title()) if x != "all" else get_ui_text("all", language, "All")
                )
            
            with col3:
                language_filter = st.selectbox(
                    get_ui_text("language", language, "Language"),
                    options=["all", "en", "zh", "es"],
                    format_func=lambda x: {"all": "All", "en": "English", "zh": "中文", "es": "Español"}.get(x, x)
                )
            
            with col4:
                date_range = st.date_input(
                    get_ui_text("date_range", language, "Date Range"),
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    max_value=datetime.now()
                )
        
        # Build filters dict
        filters = {}
        if priority_filter != "all":
            filters['priority'] = priority_filter
        if status_filter != "all":
            filters['status'] = status_filter
        if language_filter != "all":
            filters['language'] = language_filter
        if len(date_range) == 2:
            filters['date_from'] = date_range[0].isoformat()
            filters['date_to'] = date_range[1].isoformat()
        
        # Pagination
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page_size = st.selectbox("Leads per page", [10, 25, 50, 100], index=1)
            page_number = st.number_input("Page", min_value=1, value=1)
        
        # Get filtered leads
        offset = (page_number - 1) * page_size
        leads = self.db.get_all_leads(limit=page_size, offset=offset, filters=filters)
        
        if leads:
            # Leads table with actions
            self.render_leads_table_with_actions(leads, language)
        else:
            st.info(get_ui_text("no_leads_found", language, "No leads found with the current filters."))
        
        # Bulk actions
        if leads:
            st.subheader(get_ui_text("bulk_actions", language, "⚡ Bulk Actions"))
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(get_ui_text("mark_contacted", language, "Mark as Contacted")):
                    self._bulk_update_status(leads, "contacted")
                    st.success(get_ui_text("bulk_update_success", language, "Bulk update completed!"))
                    st.rerun()
            
            with col2:
                if st.button(get_ui_text("mark_qualified", language, "Mark as Qualified")):
                    self._bulk_update_status(leads, "qualified")
                    st.success(get_ui_text("bulk_update_success", language, "Bulk update completed!"))
                    st.rerun()
            
            with col3:
                if st.button(get_ui_text("export_filtered", language, "Export Filtered")):
                    csv_data = self._export_leads_to_csv(leads)
                    st.download_button(
                        label=get_ui_text("download_csv", language, "Download CSV"),
                        data=csv_data,
                        file_name=f"filtered_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    
    def render_analytics_tab(self, language: str):
        """Render detailed analytics."""
        st.subheader(get_ui_text("analytics_title", language, "📊 Detailed Analytics"))
        
        # Time series analysis
        st.subheader(get_ui_text("lead_trends", language, "📈 Lead Generation Trends"))
        self.render_lead_trends_chart(language)
        
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(get_ui_text("score_distribution", language, "📊 Score Distribution"))
            self.render_score_distribution_chart(language)
        
        with col2:
            st.subheader(get_ui_text("conversion_funnel", language, "🔄 Conversion Funnel"))
            self.render_conversion_funnel_chart(language)
        
        # Geographic analysis (if available)
        st.subheader(get_ui_text("language_analysis", language, "🌍 Language Analysis"))
        self.render_language_performance_chart(language)
    
    def render_export_tab(self, language: str):
        """Render export functionality."""
        st.subheader(get_ui_text("export_title", language, "📤 Export Data"))
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                get_ui_text("export_format", language, "Export Format"),
                options=["csv", "json", "excel"],
                format_func=lambda x: x.upper()
            )
        
        with col2:
            export_period = st.selectbox(
                get_ui_text("export_period", language, "Time Period"),
                options=[7, 30, 90, 365, "all"],
                format_func=lambda x: f"Last {x} days" if x != "all" else "All time"
            )
        
        # Export buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(get_ui_text("export_leads", language, "📋 Export Leads")):
                self._handle_export("leads", export_format, export_period, language)
        
        with col2:
            if st.button(get_ui_text("export_conversations", language, "💬 Export Conversations")):
                self._handle_export("conversations", export_format, export_period, language)
        
        with col3:
            if st.button(get_ui_text("export_analytics", language, "📊 Export Analytics")):
                self._handle_export("analytics", export_format, export_period, language)
        
        # Scheduled exports
        st.subheader(get_ui_text("scheduled_exports", language, "⏰ Scheduled Exports"))
        st.info(get_ui_text("scheduled_exports_info", language, "Scheduled export functionality coming soon!"))
    
    def render_settings_tab(self, language: str):
        """Render dashboard settings."""
        st.subheader(get_ui_text("dashboard_settings", language, "⚙️ Dashboard Settings"))
        
        # Dashboard preferences
        with st.expander(get_ui_text("preferences", language, "Preferences"), expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                auto_refresh = st.checkbox(
                    get_ui_text("auto_refresh", language, "Auto-refresh dashboard"),
                    value=st.session_state.get("dashboard_auto_refresh", False)
                )
                st.session_state.dashboard_auto_refresh = auto_refresh
                
                default_period = st.selectbox(
                    get_ui_text("default_period", language, "Default time period"),
                    options=[7, 14, 30, 60, 90],
                    format_func=lambda x: f"{x} days",
                    index=2
                )
            
            with col2:
                show_scores = st.checkbox(
                    get_ui_text("show_scores", language, "Show lead scores"),
                    value=st.session_state.get("dashboard_show_scores", True)
                )
                st.session_state.dashboard_show_scores = show_scores
                
                compact_view = st.checkbox(
                    get_ui_text("compact_view", language, "Compact table view"),
                    value=st.session_state.get("dashboard_compact_view", False)
                )
                st.session_state.dashboard_compact_view = compact_view
        
        # Data management
        with st.expander(get_ui_text("data_management", language, "Data Management")):
            st.warning(get_ui_text("data_warning", language, "⚠️ These actions cannot be undone!"))
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(get_ui_text("cleanup_old_sessions", language, "🧹 Cleanup Old Sessions")):
                    self.db.cleanup_old_sessions(days=30)
                    st.success(get_ui_text("cleanup_success", language, "Old sessions cleaned up!"))
            
            with col2:
                if st.button(get_ui_text("backup_data", language, "💾 Backup Data")):
                    st.info(get_ui_text("backup_info", language, "Backup functionality coming soon!"))
    
    def render_leads_by_priority_chart(self, analytics: Dict, language: str):
        """Render leads by priority pie chart."""
        if analytics['leads_by_priority']:
            fig = px.pie(
                values=list(analytics['leads_by_priority'].values()),
                names=list(analytics['leads_by_priority'].keys()),
                title=get_ui_text("leads_by_priority", language, "Leads by Priority"),
                color_discrete_map={
                    'high': '#ff4444',
                    'medium': '#ffaa00',
                    'low': '#44ff44'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(get_ui_text("no_data", language, "No data available"))
    
    def render_leads_by_language_chart(self, analytics: Dict, language: str):
        """Render leads by language bar chart."""
        if analytics['leads_by_language']:
            fig = px.bar(
                x=list(analytics['leads_by_language'].keys()),
                y=list(analytics['leads_by_language'].values()),
                title=get_ui_text("leads_by_language", language, "Leads by Language"),
                labels={'x': 'Language', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(get_ui_text("no_data", language, "No data available"))
    
    def render_recent_leads_table(self, language: str, limit: int = 10):
        """Render recent leads table."""
        leads = self.db.get_all_leads(limit=limit)
        
        if leads:
            df = pd.DataFrame(leads)
            df = df[['name', 'email', 'company', 'priority', 'score', 'created_at']]
            df.columns = [
                get_ui_text("name", language, "Name"),
                get_ui_text("email", language, "Email"),
                get_ui_text("company", language, "Company"),
                get_ui_text("priority", language, "Priority"),
                get_ui_text("score", language, "Score"),
                get_ui_text("created", language, "Created")
            ]
            st.dataframe(df, use_container_width=True)
        else:
            st.info(get_ui_text("no_recent_leads", language, "No recent leads"))
    
    def render_leads_table_with_actions(self, leads: List[Dict], language: str):
        """Render leads table with action buttons."""
        for i, lead in enumerate(leads):
            with st.expander(f"👤 {lead.get('name', 'Unknown')} - {lead.get('email', 'No email')}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{get_ui_text('company', language, 'Company')}:** {lead.get('company', 'N/A')}")
                    st.write(f"**{get_ui_text('phone', language, 'Phone')}:** {lead.get('phone', 'N/A')}")
                    st.write(f"**{get_ui_text('interest', language, 'Interest')}:** {lead.get('interest', 'N/A')}")
                    st.write(f"**{get_ui_text('budget', language, 'Budget')}:** {lead.get('budget', 'N/A')}")
                    st.write(f"**{get_ui_text('score', language, 'Score')}:** {lead.get('score', 0)}/100")
                    st.write(f"**{get_ui_text('created', language, 'Created')}:** {lead.get('created_at', 'N/A')}")
                
                with col2:
                    new_status = st.selectbox(
                        get_ui_text("status", language, "Status"),
                        options=["new", "contacted", "qualified", "converted", "lost"],
                        value=lead.get('status', 'new'),
                        key=f"status_{lead['id']}"
                    )
                    
                    if st.button(get_ui_text("update_status", language, "Update"), key=f"update_{lead['id']}"):
                        self.db.update_lead_status(lead['id'], new_status)
                        st.success(get_ui_text("status_updated", language, "Status updated!"))
                        st.rerun()
                
                with col3:
                    notes = st.text_area(
                        get_ui_text("notes", language, "Notes"),
                        value=lead.get('notes', ''),
                        key=f"notes_{lead['id']}",
                        height=100
                    )
                    
                    if st.button(get_ui_text("save_notes", language, "Save Notes"), key=f"save_notes_{lead['id']}"):
                        self.db.update_lead_status(lead['id'], lead.get('status', 'new'), notes)
                        st.success(get_ui_text("notes_saved", language, "Notes saved!"))
                        st.rerun()
    
    def render_lead_trends_chart(self, language: str):
        """Render lead generation trends over time."""
        # This would require more complex database queries
        # For now, showing a placeholder
        st.info(get_ui_text("trends_coming_soon", language, "Trend analysis coming soon!"))
    
    def render_score_distribution_chart(self, language: str):
        """Render score distribution histogram."""
        # This would require score data from database
        st.info(get_ui_text("score_dist_coming_soon", language, "Score distribution coming soon!"))
    
    def render_conversion_funnel_chart(self, language: str):
        """Render conversion funnel."""
        # This would require status transition data
        st.info(get_ui_text("funnel_coming_soon", language, "Conversion funnel coming soon!"))
    
    def render_language_performance_chart(self, language: str):
        """Render language performance analysis."""
        analytics = self.db.get_analytics_summary(days=30)
        
        if analytics['leads_by_language']:
            # Calculate performance metrics by language
            lang_data = []
            for lang, count in analytics['leads_by_language'].items():
                lang_data.append({
                    'Language': {'en': 'English', 'zh': '中文', 'es': 'Español'}.get(lang, lang),
                    'Leads': count,
                    'Percentage': round(count / analytics['total_leads'] * 100, 1)
                })
            
            df = pd.DataFrame(lang_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info(get_ui_text("no_language_data", language, "No language data available"))
    
    def _calculate_delta(self, current_value: int, period: int) -> Optional[str]:
        """Calculate delta for metrics."""
        # This would require historical data comparison
        return None
    
    def _calculate_conversion_rate(self, period: int) -> float:
        """Calculate conversion rate."""
        # This would require conversion tracking
        return 0.0
    
    def _bulk_update_status(self, leads: List[Dict], status: str):
        """Bulk update lead status."""
        for lead in leads:
            self.db.update_lead_status(lead['id'], status)
    
    def _export_leads_to_csv(self, leads: List[Dict]) -> str:
        """Export leads to CSV format."""
        df = pd.DataFrame(leads)
        return df.to_csv(index=False)
    
    def _handle_export(self, data_type: str, format_type: str, period, language: str):
        """Handle data export."""
        st.info(get_ui_text("export_processing", language, f"Exporting {data_type} in {format_type} format..."))
        # Implementation would depend on the specific export requirements

# Singleton instance
_dashboard = None

def get_dashboard() -> AdvancedDashboard:
    """Get the dashboard singleton instance."""
    global _dashboard
    if _dashboard is None:
        _dashboard = AdvancedDashboard()
    return _dashboard

