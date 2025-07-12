"""
Dean's Strategic Sales & Marketing Conversation Implementation
Master agent coordinating Email Agent, Funnel Agent, Research Agent, and Monitoring Agent
Infused with Alex Hormozi methodologies and premium sales strategies
"""

from typing import Dict, Any, List
from datetime import datetime
from .conversation_engine import ConversationEngine, ConversationContext
from ..config import settings
import structlog

logger = structlog.get_logger()


class DeanConversationEngine(ConversationEngine):
    """
    Dean's specialized conversation engine for strategic sales & marketing.
    
    Master coordinator focusing on:
    - Strategic sales direction and Hormozi methodology
    - Lead generation and conversion optimization  
    - Market positioning and competitive advantage
    - Revenue growth and pipeline management
    - Subagent coordination and decision-making
    """
    
    def __init__(self):
        # Dean's persona configuration
        persona_config = {
            'name': 'Dean',
            'role': 'Strategic Sales Director',
            'model': 'gpt-4-turbo-preview',
            'max_tokens': 150,  # Ultra-concise responses
            'temperature': 0.8,  # Slightly higher for strategic creativity
            'max_messages': 30,  # Longer conversations for strategy
            'context_timeout_hours': 12,  # Extended for ongoing strategy sessions
            'system_prompt': self._build_dean_system_prompt(),
            'error_message': "Strategic systems temporarily offline. Critical sales decisions pending your input."
        }
        
        super().__init__(persona_config)
        
        # Dean's strategic knowledge base
        self.sales_methodology = self._load_hormozi_methodology()
        self.market_intelligence = self._load_market_intelligence()
        self.subagents_status = {
            'email_agent': {'active': False, 'last_campaign': None},
            'funnel_agent': {'active': False, 'last_optimization': None},
            'research_agent': {'active': False, 'last_analysis': None},
            'monitoring_agent': {'active': False, 'last_scan': None}
        }
    
    def _build_dean_system_prompt(self) -> str:
        """Build Dean's comprehensive strategic system prompt."""
        return f"""You are Dean, Strategic Sales Director for Grime Guardians, Twin Cities' premium cleaning service targeting $300K annual revenue.

ROLE & STRATEGIC FOCUS:
- Strategic sales leadership with Alex Hormozi methodology expertise
- Revenue optimization and conversion mastery
- Market positioning and competitive dominance
- Subagent coordination and tactical oversight
- CRITICAL: Maximum 2 sentences - ultra-concise strategic insights only

HORMOZI METHODOLOGY INTEGRATION:
✅ $100M OFFERS FRAMEWORK:
- Value equation: (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort & Sacrifice)
- Price anchoring on value, not cost
- Irresistible offer stacking with premium positioning

✅ $100M LEADS PRINCIPLES:
- Lead magnet strategy for property managers/realtors
- Outbound cadences with valuable content first
- Social proof leveraging 70+ five-star reviews

✅ STRATEGIC SALES FOCUS:
- Premium positioning: "Last call most clients make"
- Value-first conversations, not pitch-first
- ROI justification for property management efficiency

YOUR DOMAIN:
✅ STRATEGIC SALES: Revenue strategy, conversion optimization, Hormozi frameworks
✅ MARKET POSITIONING: Competitive advantage, premium justification, value communication
✅ LEAD GENERATION: Outbound strategy, lead qualification, pipeline optimization
✅ SUBAGENT COORDINATION: Email Agent, Funnel Agent, Research Agent oversight

❌ NOT YOUR DOMAIN: Daily operations (Ava), finances (CFO), execution details (subagents)

CURRENT BUSINESS CONTEXT:
- Target Market: Property managers, realtors, real estate investors (Twin Cities focus)
- Service Area: Eagan → South suburbs → Minneapolis/St. Paul expansion
- Competitive Advantage: 70+ five-star reviews, professional network, premium results
- Pricing Strategy: Range quoting ($584-$706) based on condition assessment
- Response Protocol: Immediate acknowledgment, 5-minute follow-up, human conversation detection

SUBAGENT COORDINATION:
- Email Agent: Campaign strategy, inbox management, outbound sequences
- Funnel Agent: Landing page optimization, SEO strategy, conversion tracking
- Research Agent: Lead qualification, market analysis, competitor intelligence
- Monitoring Agent: GHL/Gmail/Social monitoring, response recommendations

RESPONSE STYLE:
- Maximum 2 sentences - strategic insights only
- Hormozi-style direct value communication
- ROI-focused recommendations
- Subagent task delegation when appropriate
- Escalation identification for critical decisions

Current date: {datetime.now().strftime('%A, %B %d, %Y')}
Current priority: Revenue acceleration through systematic lead generation and conversion optimization."""

    def _load_hormozi_methodology(self) -> Dict[str, Any]:
        """Load Alex Hormozi strategic frameworks."""
        return {
            'value_equation': {
                'dream_outcome': 'Stress-free property management with reliable, premium cleaning',
                'perceived_likelihood': 'Proven by 70+ five-star reviews and professional track record',
                'time_delay': 'Immediate service availability with 15-minute response times',
                'effort_sacrifice': 'Zero effort required - we handle everything including damage protection'
            },
            'offer_stacking': {
                'core_service': 'Premium move-out/move-in cleaning',
                'value_adds': [
                    'Professional vendor network access',
                    'Damage claim protection through documentation',
                    'Same-day emergency coverage capability',
                    'Direct realtor/property manager communication',
                    'Photo documentation for tenant disputes'
                ],
                'risk_reversal': '100% satisfaction guarantee with documented quality standards',
                'urgency': 'Limited capacity - premium clients only'
            },
            'lead_magnets': {
                'property_managers': 'Property Turnover Efficiency Guide + Tenant Damage Documentation System',
                'realtors': 'Listing Preparation Checklist + Move-in Ready Standards',
                'investors': 'ROI Maximization through Professional Property Presentation'
            },
            'outbound_strategy': {
                'value_first': 'Lead with industry insights and efficiency improvements',
                'social_proof': 'Reference specific satisfied clients in similar situations',
                'pain_point_focus': 'Address tenant turnover delays and quality inconsistencies',
                'premium_justification': 'ROI calculation: time saved × hourly rate + tenant acquisition speed'
            }
        }
    
    def _load_market_intelligence(self) -> Dict[str, Any]:
        """Load current market intelligence and competitive positioning."""
        return {
            'target_segments': {
                'property_management_companies': {
                    'pain_points': ['tenant turnover delays', 'quality inconsistency', 'coordination headaches'],
                    'value_proposition': 'Streamlined turnover with professional documentation',
                    'decision_makers': ['operations managers', 'regional managers'],
                    'buying_cycle': '30-60 days evaluation period'
                },
                'individual_realtors': {
                    'pain_points': ['listing preparation delays', 'cleaning quality concerns', 'vendor reliability'],
                    'value_proposition': 'Listing-ready results with professional presentation',
                    'decision_makers': ['listing agents', 'team leaders'],
                    'buying_cycle': 'Immediate need basis'
                },
                'real_estate_investors': {
                    'pain_points': ['renovation timeline delays', 'cost optimization', 'quality standards'],
                    'value_proposition': 'Investment-grade cleaning with ROI optimization',
                    'decision_makers': ['portfolio managers', 'individual investors'],
                    'buying_cycle': '90+ days relationship building'
                }
            },
            'competitive_landscape': {
                'mass_market_cleaners': 'Positioning: Unreliable, inconsistent, no professional focus',
                'franchise_operations': 'Positioning: Corporate overhead, limited local expertise, cookie-cutter approach',
                'independent_competitors': 'Positioning: Limited capacity, no systematic approach, poor documentation'
            },
            'geographic_expansion': {
                'tier_1_focus': 'Eagan, Apple Valley, Burnsville (established network)',
                'tier_2_expansion': 'Bloomington, Edina, Lakeville (premium target)',
                'tier_3_opportunity': 'Minneapolis, St. Paul (market penetration phase)'
            }
        }
    
    def get_business_context(self, conversation: ConversationContext) -> str:
        """Get current strategic context for Dean."""
        context_parts = []
        
        # Current strategic priorities
        context_parts.append("STRATEGIC PRIORITIES:")
        context_parts.append("- Outbound sales acceleration (currently stalled)")
        context_parts.append("- Lead generation system optimization") 
        context_parts.append("- Sales funnel completion and conversion tracking")
        context_parts.append("- GoHighLevel CRM integration active")
        
        # Market opportunity assessment
        if self._conversation_mentions_leads(conversation):
            context_parts.append("\nLEAD GENERATION STATUS:")
            context_parts.append("- Property manager outreach: Needs systematic approach")
            context_parts.append("- Realtor network: Strong foundation, expansion opportunity")
            context_parts.append("- Geographic expansion: Ready for tier-2 markets")
            context_parts.append("- Live conversation monitoring available")
        
        # Revenue acceleration focus
        if self._conversation_mentions_revenue(conversation):
            context_parts.append("\nREVENUE OPTIMIZATION:")
            context_parts.append("- Target: $300K annual ($25K/month minimum)")
            context_parts.append("- Current: Strong reputation foundation, pipeline gaps")
            context_parts.append("- Opportunity: Systematic outbound + funnel completion")
            context_parts.append("- Real-time lead analytics and pipeline tracking")
        
        # Sales intelligence context
        if self._conversation_mentions_sales_intelligence(conversation):
            context_parts.append("\nSALES INTELLIGENCE:")
            context_parts.append("- GoHighLevel conversation monitoring active")
            context_parts.append("- Lead source analytics and conversion tracking")
            context_parts.append("- Email campaign performance and response rates")
        
        return "\n".join(context_parts)
    
    def _conversation_mentions_leads(self, conversation: ConversationContext) -> bool:
        """Check if conversation involves lead generation topics."""
        lead_keywords = ['lead', 'prospect', 'outbound', 'sales', 'pipeline', 'outreach', 'conversion']
        recent_messages = conversation.messages[-5:]
        
        for message in recent_messages:
            if any(keyword in message.content.lower() for keyword in lead_keywords):
                return True
        return False
    
    def _conversation_mentions_revenue(self, conversation: ConversationContext) -> bool:
        """Check if conversation involves revenue/growth topics."""
        revenue_keywords = ['revenue', 'growth', 'target', '300k', 'expansion', 'scale', 'income']
        recent_messages = conversation.messages[-5:]
        
        for message in recent_messages:
            if any(keyword in message.content.lower() for keyword in revenue_keywords):
                return True
        return False
    
    def _conversation_mentions_sales_intelligence(self, conversation: ConversationContext) -> bool:
        """Check if conversation involves sales intelligence/analytics topics."""
        intelligence_keywords = ['analytics', 'performance', 'metrics', 'conversation', 'monitoring', 'intelligence', 'tracking']
        recent_messages = conversation.messages[-5:]
        
        for message in recent_messages:
            if any(keyword in message.content.lower() for keyword in intelligence_keywords):
                return True
        return False
    
    async def coordinate_subagent(self, agent_type: str, task: Dict[str, Any]) -> str:
        """Coordinate tasks with subagents."""
        try:
            if agent_type == 'email_agent':
                return await self._coordinate_email_agent(task)
            elif agent_type == 'funnel_agent':
                return await self._coordinate_funnel_agent(task)
            elif agent_type == 'research_agent':
                return await self._coordinate_research_agent(task)
            elif agent_type == 'monitoring_agent':
                return await self._coordinate_monitoring_agent(task)
            else:
                return f"Unknown subagent type: {agent_type}"
        except Exception as e:
            logger.error(f"Error coordinating with {agent_type}: {e}")
            return f"Subagent coordination failed: {agent_type}"
    
    async def _coordinate_email_agent(self, task: Dict[str, Any]) -> str:
        """Coordinate with Email Agent for campaign and inbox management."""
        from .email_agent import email_agent
        
        try:
            task_type = task.get('type', 'unknown')
            
            if task_type == 'create_campaign':
                campaign_id = await email_agent.create_campaign(task)
                return f"Email campaign created: {campaign_id}"
            
            elif task_type == 'monitor_inbox':
                responses = await email_agent.monitor_inbox()
                return f"Inbox monitored: {len(responses)} new responses detected"
            
            elif task_type == 'get_metrics':
                campaign_id = task.get('campaign_id')
                metrics = await email_agent.get_campaign_metrics(campaign_id)
                return f"Campaign metrics: {metrics.get('emails_sent', 0)} sent, {metrics.get('response_rate', 0)}% response rate"
            
            elif task_type == 'approve_email':
                approval_id = task.get('approval_id')
                success = await email_agent.approve_email(approval_id)
                return f"Email approval: {'Sent' if success else 'Failed'}"
            
            else:
                return f"Email Agent active: {len(email_agent.get_pending_approvals())} emails pending approval"
                
        except Exception as e:
            logger.error(f"Error coordinating with Email Agent: {e}")
            return "Email Agent coordination failed - manual intervention required"
    
    async def _coordinate_funnel_agent(self, task: Dict[str, Any]) -> str:
        """Coordinate with Funnel Agent for landing page and SEO optimization."""
        # Placeholder for Funnel Agent coordination
        return "Funnel Agent task queued: Landing page optimization analysis"
    
    async def _coordinate_research_agent(self, task: Dict[str, Any]) -> str:
        """Coordinate with Research Agent for lead qualification and market analysis."""
        # Placeholder for Research Agent coordination
        return "Research Agent task queued: Market analysis and lead qualification"
    
    async def _coordinate_monitoring_agent(self, task: Dict[str, Any]) -> str:
        """Coordinate with Monitoring Agent for multi-channel surveillance."""
        # Placeholder for Monitoring Agent coordination
        return "Monitoring Agent task queued: Multi-channel lead monitoring"
    
    async def generate_hormozi_strategy(self, context: str) -> str:
        """Generate strategic recommendations using Hormozi methodology."""
        try:
            if 'lead' in context.lower() or 'prospect' in context.lower():
                return "Value-first outreach: Lead with efficiency insights, anchor on ROI, stack social proof."
            elif 'offer' in context.lower() or 'pricing' in context.lower():
                return "Premium positioning: Range quote with condition assessment, value-stack professional network access."
            elif 'conversion' in context.lower() or 'funnel' in context.lower():
                return "Irresistible offer: Risk reversal with satisfaction guarantee plus vendor network value-add."
            else:
                return "Strategic focus: Systematic outbound cadence with premium positioning and Hormozi value equation."
        except Exception as e:
            logger.error(f"Error generating Hormozi strategy: {e}")
            return "Strategic analysis pending - coordinate with subagents for tactical execution."
    
    async def get_lead_analytics(self, days_back: int = 7) -> str:
        """Get lead generation analytics from GoHighLevel."""
        try:
            from ..integrations.gohighlevel_service import ghl_service
            analytics = await ghl_service.get_lead_analytics(days_back)
            
            if not analytics:
                return "Unable to retrieve lead analytics from GoHighLevel."
            
            summary = f"LEAD ANALYTICS ({days_back} days):\n"
            summary += f"• Total Leads: {analytics.get('total_leads', 0)}\n"
            summary += f"• Active Conversations: {analytics.get('active_conversations', 0)}\n"
            summary += f"• Scheduled Appointments: {analytics.get('scheduled_appointments', 0)}\n"
            
            # Lead sources breakdown
            sources = analytics.get('lead_sources', {})
            if sources:
                summary += f"\nTOP SOURCES:\n"
                for source, count in list(sources.items())[:3]:
                    summary += f"• {source}: {count} leads\n"
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error getting lead analytics: {e}")
            return "Analytics temporarily unavailable - monitoring systems reconnecting."
    
    async def monitor_conversations(self, limit: int = 10) -> str:
        """Monitor recent conversations from GoHighLevel."""
        try:
            from ..integrations.gohighlevel_service import ghl_service
            conversations = await ghl_service.get_conversations(limit)
            
            if not conversations:
                return "No recent conversations to monitor."
            
            # Filter for unread/active conversations
            active_convs = [c for c in conversations if c.unread_count > 0 or c.status == 'open']
            
            if not active_convs:
                return f"All {len(conversations)} recent conversations handled - no urgent responses needed."
            
            summary = f"ACTIVE CONVERSATIONS ({len(active_convs)} need attention):\n"
            
            for conv in active_convs[:5]:  # Show top 5
                time_ago = self._time_since(conv.last_message_time)
                summary += f"• {conv.contact_name} ({conv.type})\n"
                summary += f"  Last: {conv.last_message[:60]}{'...' if len(conv.last_message) > 60 else ''}\n"
                summary += f"  Status: {conv.status} | {time_ago}\n\n"
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error monitoring conversations: {e}")
            return "Conversation monitoring temporarily offline - manual review recommended."
    
    async def get_pipeline_status(self) -> str:
        """Get sales pipeline status from GoHighLevel."""
        try:
            from ..integrations.gohighlevel_service import ghl_service
            
            # Get recent data
            appointments = await ghl_service.get_upcoming_appointments(168)  # Next 7 days
            conversations = await ghl_service.get_conversations(50)
            analytics = await ghl_service.get_lead_analytics(30)
            
            pipeline_summary = "SALES PIPELINE STATUS:\n"
            
            # Appointments pipeline
            scheduled_count = len(appointments)
            pipeline_summary += f"• Scheduled Jobs: {scheduled_count} (next 7 days)\n"
            
            # Conversation pipeline
            active_convs = len([c for c in conversations if c.unread_count > 0])
            pipeline_summary += f"• Active Conversations: {active_convs}\n"
            
            # Lead generation rate
            leads_30d = analytics.get('total_leads', 0)
            pipeline_summary += f"• New Leads (30d): {leads_30d}\n"
            
            # Conversion insights
            if scheduled_count > 0 and leads_30d > 0:
                conversion_rate = (scheduled_count / leads_30d) * 100
                pipeline_summary += f"• Lead-to-Appointment: {conversion_rate:.1f}%\n"
            
            # Strategic recommendation
            if scheduled_count < 20:  # Target threshold
                pipeline_summary += f"\n⚡ OPPORTUNITY: Pipeline below capacity - accelerate outbound campaigns."
            else:
                pipeline_summary += f"\n✅ PIPELINE: Strong appointment flow - optimize conversion focus."
            
            return pipeline_summary
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return "Pipeline monitoring temporarily offline - manual CRM review recommended."
    
    def _time_since(self, timestamp: datetime) -> str:
        """Calculate human-readable time since timestamp."""
        try:
            now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
            delta = now - timestamp
            
            if delta.days > 0:
                return f"{delta.days}d ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours}h ago"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes}m ago"
            else:
                return "Just now"
        except Exception:
            return "Recently"


# Global Dean conversation instance
dean_conversation = DeanConversationEngine()