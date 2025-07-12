"""
Dean's Email Agent - Campaign Management & Inbox Monitoring
Core sales engine for automated outbound campaigns and inbox management
Integrates with Gmail API and GoHighLevel for comprehensive email automation
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import openai
import structlog
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from ..config import settings
from .conversation_engine import ConversationEngine, ConversationContext

logger = structlog.get_logger()


@dataclass
class EmailCampaign:
    """Email campaign configuration and tracking."""
    campaign_id: str
    name: str
    target_segment: str  # 'property_managers', 'realtors', 'investors'
    template_type: str
    status: str  # 'draft', 'active', 'paused', 'completed'
    send_count: int
    open_rate: float
    response_rate: float
    created_at: datetime
    last_sent: Optional[datetime] = None


@dataclass
class EmailLead:
    """Lead information for email campaigns."""
    email: str
    name: str
    company: str
    segment: str
    status: str  # 'new', 'contacted', 'responded', 'qualified', 'converted'
    last_contact: Optional[datetime] = None
    response_count: int = 0
    notes: str = ""


@dataclass
class EmailTemplate:
    """Email template with Hormozi methodology."""
    template_id: str
    name: str
    segment: str
    subject_line: str
    content: str
    follow_up_sequence: int  # 1, 2, 3, etc.
    hormozi_framework: str  # 'value_first', 'social_proof', 'pain_point'


class EmailAgent:
    """
    Dean's Email Agent for comprehensive email automation.
    
    Handles:
    - Outbound campaign management with Hormozi methodology
    - Inbox monitoring and response suggestions
    - Lead qualification and follow-up sequences
    - Integration with Gmail and GoHighLevel
    """
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Email templates with Hormozi methodology
        self.templates = self._load_email_templates()
        
        # Campaign tracking
        self.active_campaigns: Dict[str, EmailCampaign] = {}
        self.leads_database: Dict[str, EmailLead] = {}
        
        # Response approval system
        self.pending_approvals: List[Dict[str, Any]] = []
        
        # Hormozi frameworks
        self.hormozi_frameworks = self._load_hormozi_frameworks()
    
    def _load_email_templates(self) -> Dict[str, EmailTemplate]:
        """Load Hormozi-optimized email templates for each segment."""
        templates = {}
        
        # Property Manager Templates
        templates['pm_value_first'] = EmailTemplate(
            template_id='pm_value_first',
            name='Property Manager - Value First',
            segment='property_managers',
            subject_line='Cut tenant turnover time by 40% (Twin Cities insight)',
            content="""Hi {name},

Quick insight from our work with {similar_company} - we helped them reduce tenant turnover time from 14 days to 8 days average.

The secret? Professional move-out documentation that prevents tenant disputes and streamlines the process.

Would a 40% reduction in turnover time be valuable for your portfolio?

Best,
Rob Robillard
Grime Guardians
"We clean like it's our name on the lease"

P.S. - Happy to share the 3-step documentation system we use if you're interested.""",
            follow_up_sequence=1,
            hormozi_framework='value_first'
        )
        
        templates['pm_social_proof'] = EmailTemplate(
            template_id='pm_social_proof',
            name='Property Manager - Social Proof',
            segment='property_managers',
            subject_line='How [Company] saved 2 weeks per turnover',
            content="""Hi {name},

Thought you'd find this interesting - just finished a project with [Property Management Company] where our documentation system saved them 2 weeks per unit turnover.

Here's what happened:
• Tenant claimed "damage was already there"
• Our before/after photos provided clear evidence
• Dispute resolved in 24 hours instead of weeks

70+ five-star reviews later, property managers tell us we're "the last call they have to make."

Worth a quick conversation about your turnover process?

Best,
Rob Robillard""",
            follow_up_sequence=2,
            hormozi_framework='social_proof'
        )
        
        # Offer stacking template
        templates['pm_offer_stacking'] = EmailTemplate(
            template_id='pm_offer_stacking',
            name='Property Manager - Offer Stacking',
            segment='property_managers',
            subject_line='Everything included: No hidden fees',
            content="""Hi {name},

Here's exactly what you get with our property management cleaning service:

✅ Premium cleaning (normally $400 elsewhere)
✅ Professional photo documentation ($100 value)
✅ Damage protection evidence (priceless during disputes)
✅ Direct communication with your office ($50/hour saved)
✅ Same-day emergency coverage (most competitors: 3-5 days)
✅ 100% satisfaction guarantee (risk-free trial)

Total value: $550+
Your investment: $300 flat rate

Plus: We're BBB-accredited with 70+ five-star reviews.

Ready to streamline your next turnover?

Best,
Rob Robillard""",
            follow_up_sequence=3,
            hormozi_framework='offer_stacking'
        )
        
        # Realtor Templates
        templates['realtor_pain_point'] = EmailTemplate(
            template_id='realtor_pain_point',
            name='Realtor - Pain Point Focus',
            segment='realtors',
            subject_line='Listing photos tomorrow? (cleaning concern)',
            content="""Hi {name},

Quick question - ever had a listing where the cleaning wasn't photo-ready and you had to delay the shoot?

We specialize in listing-ready results for realtors in the south metro. Our before/after documentation ensures every shot looks professional.

Last week helped {realtor_name} get photos done same-day instead of waiting another week for "touch-ups."

Worth a quick chat about your current cleaning process?

Best,
Rob""",
            follow_up_sequence=1,
            hormozi_framework='pain_point'
        )
        
        # Investor Templates
        templates['investor_roi_focus'] = EmailTemplate(
            template_id='investor_roi_focus',
            name='Investor - ROI Focus',
            segment='real_estate_investors',
            subject_line='ROI calculation: Professional cleaning vs. DIY',
            content="""Hi {name},

Quick ROI calculation for investors:

DIY cleaning: 8 hours × $50/hour opportunity cost = $400
+ Risk of tenant disputes over "damage already there"
+ Potential lost rent from delays

Professional cleaning: $300 flat rate
+ Photo documentation protecting deposit claims
+ Faster turnaround = faster rent collection

Net savings: $100+ plus risk protection.

Worth discussing for your next turnover?

Best,
Rob Robillard
Investment Property Specialist""",
            follow_up_sequence=1,
            hormozi_framework='value_first'
        )
        
        return templates
    
    def _load_hormozi_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Load Hormozi methodology frameworks for email optimization."""
        return {
            'value_equation': {
                'formula': '(Dream Outcome × Perceived Likelihood) / (Time Delay × Effort & Sacrifice)',
                'application': {
                    'dream_outcome': 'Stress-free property management',
                    'perceived_likelihood': '70+ five-star reviews prove reliability',
                    'time_delay': 'Same-day service available',
                    'effort_sacrifice': 'Zero effort - we handle everything'
                }
            },
            'email_frameworks': {
                'value_first': {
                    'structure': 'Lead with insight/result → Provide value → Soft ask',
                    'psychology': 'Build authority before selling'
                },
                'social_proof': {
                    'structure': 'Similar situation → Specific result → Relevance question',
                    'psychology': 'Reduce perceived risk through peer success'
                },
                'pain_point': {
                    'structure': 'Identify pain → Relate experience → Solution hint',
                    'psychology': 'Problem-aware prospects need solution awareness'
                }
            },
            'response_triggers': {
                'curiosity': ['Quick insight', 'Thought you\'d find this interesting', 'Quick question'],
                'urgency': ['Tomorrow', 'This week', 'Before Friday'],
                'specificity': ['40% reduction', '2 weeks saved', '$400 calculation'],
                'social_proof': ['[Company] saved', 'Last week helped', '70+ reviews']
            }
        }
    
    async def create_campaign(self, campaign_config: Dict[str, Any]) -> str:
        """Create new email campaign with Hormozi optimization."""
        try:
            campaign_id = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            campaign = EmailCampaign(
                campaign_id=campaign_id,
                name=campaign_config['name'],
                target_segment=campaign_config['segment'],
                template_type=campaign_config['template_type'],
                status='draft',
                send_count=0,
                open_rate=0.0,
                response_rate=0.0,
                created_at=datetime.utcnow()
            )
            
            self.active_campaigns[campaign_id] = campaign
            
            logger.info(f"Created email campaign: {campaign_id}")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise
    
    async def send_campaign_email(self, campaign_id: str, lead: EmailLead) -> bool:
        """Send individual campaign email with personalization."""
        try:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                return False
            
            template = self.templates.get(campaign.template_type)
            if not template:
                logger.error(f"Template not found: {campaign.template_type}")
                return False
            
            # Personalize email content
            personalized_content = await self._personalize_email(template, lead)
            
            # Create email payload for approval system
            email_payload = {
                'to': lead.email,
                'subject': template.subject_line.format(name=lead.name),
                'content': personalized_content,
                'campaign_id': campaign_id,
                'lead_email': lead.email,
                'template_id': template.template_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add to approval queue (green-checkmark system)
            self.pending_approvals.append(email_payload)
            
            logger.info(f"Email queued for approval: {lead.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending campaign email: {e}")
            return False
    
    async def _personalize_email(self, template: EmailTemplate, lead: EmailLead) -> str:
        """Personalize email using AI and lead data."""
        try:
            personalization_prompt = f"""
            Personalize this email template for the lead:
            
            Lead Info:
            - Name: {lead.name}
            - Company: {lead.company}
            - Segment: {lead.segment}
            
            Template:
            {template.content}
            
            Instructions:
            - Replace {name} with lead's name
            - Add relevant company context if possible
            - Keep Hormozi framework intact
            - Maintain professional but personal tone
            - Maximum 150 words
            
            Return only the personalized email content.
            """
            
            response = await self.openai_client.chat.completions.create(
                model='gpt-4-turbo-preview',
                messages=[{'role': 'user', 'content': personalization_prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error personalizing email: {e}")
            # Fallback to basic personalization
            return template.content.format(name=lead.name, similar_company="a similar company")
    
    async def monitor_inbox(self) -> List[Dict[str, Any]]:
        """Monitor inbox for new responses and generate reply suggestions."""
        try:
            # This would integrate with Gmail API
            # For now, return mock data structure
            new_responses = []
            
            # Mock response monitoring
            mock_response = {
                'from': 'prospect@propertymanagement.com',
                'subject': 'Re: Cut tenant turnover time by 40%',
                'content': 'Interested in learning more about your documentation system.',
                'timestamp': datetime.utcnow().isoformat(),
                'lead_segment': 'property_managers',
                'sentiment': 'positive',
                'response_type': 'interest'
            }
            
            # Generate response suggestion
            suggestion = await self._generate_response_suggestion(mock_response)
            mock_response['suggested_response'] = suggestion
            
            new_responses.append(mock_response)
            
            logger.info(f"Monitored inbox: {len(new_responses)} new responses")
            return new_responses
            
        except Exception as e:
            logger.error(f"Error monitoring inbox: {e}")
            return []
    
    async def _generate_response_suggestion(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response suggestion using Hormozi methodology."""
        try:
            response_prompt = f"""
            Generate a response suggestion for this email using Alex Hormozi methodology:
            
            Original Response:
            From: {response_data['from']}
            Content: {response_data['content']}
            Sentiment: {response_data['sentiment']}
            Type: {response_data['response_type']}
            
            Context: This is a response to our outbound sales email for Grime Guardians premium cleaning service.
            
            Instructions:
            - Use Hormozi principles: value-first, social proof, risk reversal
            - Keep response under 100 words
            - Include specific next step (call scheduling)
            - Maintain premium positioning
            - Professional but warm tone
            
            Return JSON with: subject, content, priority (high/medium/low), next_action
            """
            
            response = await self.openai_client.chat.completions.create(
                model='gpt-4-turbo-preview',
                messages=[{'role': 'user', 'content': response_prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            suggestion_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                suggestion = json.loads(suggestion_text)
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                suggestion = {
                    'subject': f"Re: {response_data['subject']}",
                    'content': suggestion_text,
                    'priority': 'medium',
                    'next_action': 'Schedule call'
                }
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error generating response suggestion: {e}")
            return {
                'subject': f"Re: {response_data['subject']}",
                'content': "Thanks for your interest! Let's schedule a quick call to discuss your specific needs.",
                'priority': 'medium',
                'next_action': 'Schedule call'
            }
    
    async def approve_email(self, approval_id: str) -> bool:
        """Approve email for sending (green-checkmark system)."""
        try:
            # Find email in pending approvals
            email_to_send = None
            for i, email in enumerate(self.pending_approvals):
                if email.get('approval_id') == approval_id:
                    email_to_send = self.pending_approvals.pop(i)
                    break
            
            if not email_to_send:
                logger.error(f"Email approval not found: {approval_id}")
                return False
            
            # Send the email (would integrate with actual email service)
            logger.info(f"Sending approved email to: {email_to_send['to']}")
            
            # Update campaign metrics
            campaign_id = email_to_send['campaign_id']
            if campaign_id in self.active_campaigns:
                self.active_campaigns[campaign_id].send_count += 1
                self.active_campaigns[campaign_id].last_sent = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Error approving email: {e}")
            return False
    
    async def get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign performance metrics."""
        try:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                return {}
            
            return {
                'campaign_id': campaign.campaign_id,
                'name': campaign.name,
                'status': campaign.status,
                'emails_sent': campaign.send_count,
                'open_rate': campaign.open_rate,
                'response_rate': campaign.response_rate,
                'created_at': campaign.created_at.isoformat(),
                'last_sent': campaign.last_sent.isoformat() if campaign.last_sent else None
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign metrics: {e}")
            return {}
    
    async def qualify_lead_response(self, response_content: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify lead based on email response using AI."""
        try:
            qualification_prompt = f"""
            Qualify this lead response for Grime Guardians premium cleaning service:
            
            Lead Response: {response_content}
            Lead Info: {json.dumps(lead_data, indent=2)}
            
            Analyze:
            1. Interest level (high/medium/low)
            2. Decision-making authority
            3. Budget indicators
            4. Timeline urgency
            5. Specific pain points mentioned
            
            Return JSON with: qualification_score (1-10), interest_level, authority_level, 
            budget_fit, timeline, pain_points, recommended_next_action, notes
            """
            
            response = await self.openai_client.chat.completions.create(
                model='gpt-4-turbo-preview',
                messages=[{'role': 'user', 'content': qualification_prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            qualification_text = response.choices[0].message.content.strip()
            
            try:
                qualification = json.loads(qualification_text)
            except json.JSONDecodeError:
                # Fallback qualification
                qualification = {
                    'qualification_score': 5,
                    'interest_level': 'medium',
                    'authority_level': 'unknown',
                    'budget_fit': 'unknown',
                    'timeline': 'unknown',
                    'pain_points': [],
                    'recommended_next_action': 'Follow up call',
                    'notes': qualification_text
                }
            
            return qualification
            
        except Exception as e:
            logger.error(f"Error qualifying lead: {e}")
            return {
                'qualification_score': 5,
                'interest_level': 'medium',
                'recommended_next_action': 'Follow up call'
            }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all emails pending approval."""
        return self.pending_approvals.copy()
    
    def get_active_campaigns(self) -> List[Dict[str, Any]]:
        """Get all active campaigns."""
        return [asdict(campaign) for campaign in self.active_campaigns.values()]


# Global Email Agent instance
email_agent = EmailAgent()