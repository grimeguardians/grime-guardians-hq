"""
Brandon - Chief Executive Officer Agent
Handles strategic decisions, company vision, partnerships, and high-level escalations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

from .base_agent import BaseAgent
from .models import MessageContext, AgentResponse
from ..tools.database_tools import DatabaseTool
from ..tools.discord_tools import DiscordTool
from ..tools.message_classification_tools import MessageClassificationTool

logger = logging.getLogger(__name__)


class BrandonCEOAgent(BaseAgent):
    """
    Brandon - Chief Executive Officer
    
    Responsibilities:
    - Strategic business decisions and company vision
    - High-level customer escalations and VIP accounts
    - Partnership and business development opportunities
    - Crisis management and reputation protection
    - Company culture and values enforcement
    - Major operational decisions and policy changes
    - Investor relations and stakeholder communications
    
    Brandon is the ultimate decision-maker who handles the most important
    business matters and ensures Grime Guardians maintains its mission.
    """
    
    def __init__(self):
        super().__init__(
            name="brandon",
            role="Chief Executive Officer",
            system_prompt=self._get_system_prompt(),
            capabilities=[
                "strategic_decisions",
                "executive_escalations",
                "partnership_development",
                "crisis_management",
                "vision_setting",
                "policy_decisions",
                "vip_account_management",
                "reputation_management"
            ]
        )
        
        # Register tools
        self.register_tool("database", DatabaseTool())
        self.register_tool("discord", DiscordTool())
        self.register_tool("message_classification", MessageClassificationTool())
        
        # CEO-specific metrics
        self.strategic_decisions_made = 0
        self.crisis_situations_handled = 0
        self.partnerships_developed = 0
        self.vip_accounts_managed = 0
        
    def _get_system_prompt(self) -> str:
        return """You are Brandon, the Chief Executive Officer (CEO) and founder of Grime Guardians. You embody the company's vision, values, and commitment to excellence.

CORE IDENTITY:
- You're the visionary leader who founded Grime Guardians with a mission
- You have ultimate accountability for every customer experience
- You personally care about each customer and team member
- You make decisions that align with long-term success and values

COMPANY MISSION:
"We clean like it's our name on the lease" - This means we treat every home with the same care as if we lived there ourselves.

CORE VALUES:
1. Excellence in everything we do
2. Integrity and transparency
3. Respect for customers and team members
4. Continuous improvement
5. Community responsibility

RESPONSIBILITIES:
1. EXECUTIVE ESCALATIONS:
   - Handle the most serious customer issues personally
   - Make executive decisions to resolve complex situations
   - Ensure company reputation and values are protected
   - Turn crisis situations into opportunities for excellence

2. STRATEGIC LEADERSHIP:
   - Guide company vision and strategic direction
   - Make policy decisions that affect operations
   - Evaluate partnership and growth opportunities
   - Ensure sustainable business practices

3. VIP ACCOUNT MANAGEMENT:
   - Personally manage high-value and strategic accounts
   - Build relationships with key customers and partners
   - Represent the company in important negotiations
   - Ensure VIP customers receive exceptional treatment

4. CULTURE & VALUES:
   - Reinforce company culture and values
   - Lead by example in customer service excellence
   - Support team development and growth
   - Maintain the highest ethical standards

RESPONSE STYLE:
- Professional yet personal and approachable
- Take personal ownership and accountability
- Focus on long-term relationships over short-term gains
- Demonstrate genuine care for customers and team
- Speak with authority but remain humble and service-oriented
- Always align decisions with company mission and values

ESCALATION TRIGGERS:
- Crisis situations affecting company reputation
- High-value customer concerns
- Legal or regulatory issues
- Major operational decisions
- Partnership opportunities
- Team conflict requiring executive intervention

When handling escalations:
1. Take personal ownership immediately
2. Investigate thoroughly and fairly
3. Make decisions aligned with company values
4. Communicate transparently about actions taken
5. Follow up personally to ensure resolution
6. Use situations as learning opportunities for the organization

Remember: You're not just running a business - you're building a legacy of service excellence that reflects your personal integrity and commitment to customers."""

    async def _process_message_impl(self, context: MessageContext) -> AgentResponse:
        """Process message as Brandon CEO."""
        try:
            # Use message classification to understand the escalation level and type
            classification = await self.tools["message_classification"].classify_executive_matter(
                context.content,
                context.sender_phone
            )
            
            matter_type = classification.get("matter_type", "general")
            escalation_level = classification.get("escalation_level", "low")
            urgency = classification.get("urgency", "normal")
            confidence = classification.get("confidence", 0.0)
            
            # Route based on executive matter type
            if matter_type == "crisis" or escalation_level == "critical":
                return await self._handle_crisis_situation(context, classification)
            elif matter_type == "vip_account" or escalation_level == "high":
                return await self._handle_vip_account(context, classification)
            elif matter_type == "partnership":
                return await self._handle_partnership_inquiry(context, classification)
            elif matter_type == "legal" or matter_type == "regulatory":
                return await self._handle_legal_matter(context, classification)
            elif matter_type == "executive_escalation":
                return await self._handle_executive_escalation(context, classification)
            elif matter_type == "strategic_decision":
                return await self._handle_strategic_matter(context, classification)
            else:
                return await self._handle_general_executive_inquiry(context, classification)
                
        except Exception as e:
            logger.error(f"Brandon CEO processing error: {e}")
            return AgentResponse(
                agent_name="brandon",
                response="Thank you for reaching out. I want to give your matter the executive attention it deserves. Please provide your direct contact information, and I will personally reach out within the next hour to discuss this further.",
                confidence=0.3,
                metadata={"error": str(e), "personal_follow_up_required": True}
            )
    
    async def _handle_crisis_situation(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle crisis situations requiring immediate CEO attention."""
        try:
            crisis_type = classification.get("crisis_type", "general")
            severity = classification.get("severity", "high")
            
            # Immediately alert leadership team
            await self.tools["discord"].send_crisis_alert({
                "type": "ceo_crisis_intervention",
                "customer": context.sender_name or context.sender_phone,
                "crisis_type": crisis_type,
                "severity": severity,
                "description": context.content[:300] + "..." if len(context.content) > 300 else context.content
            })
            
            # Log crisis for executive tracking
            await self.tools["database"].log_crisis_situation({
                "client_phone": context.sender_phone,
                "crisis_type": crisis_type,
                "severity": severity,
                "description": context.content,
                "handled_by": "brandon",
                "status": "active_intervention",
                "created_at": datetime.utcnow().isoformat()
            })
            
            response = f"""🚨 **IMMEDIATE CEO INTERVENTION - BRANDON SPEAKING**

{context.sender_name or 'Dear Customer'}, I am Brandon, the CEO and founder of Grime Guardians. I am personally taking immediate ownership of this situation.

**MY IMMEDIATE ACTIONS:**
✅ I am personally investigating this matter right now
✅ I have activated our executive response team
✅ I am reviewing all details of your account and service history
✅ I am implementing immediate corrective measures

**MY PERSONAL COMMITMENT TO YOU:**
📞 I will call you personally within the next 30 minutes
🔍 I will conduct a thorough investigation of what went wrong
💯 I will implement a complete solution that exceeds your expectations
📋 I will personally ensure this never happens again to anyone

**EXECUTIVE RESOLUTION OPTIONS:**
1. **COMPLETE SERVICE RECOVERY** - Full re-service with our absolute best team at no charge
2. **COMPREHENSIVE COMPENSATION** - Full refund plus additional compensation for your trouble
3. **ONGOING RELATIONSHIP** - Personal service guarantee with my direct oversight

**MY DIRECT CONTACT:**
📱 CEO Direct Line: (512) 555-CEO1
📧 brandon@grimeguardians.com
💬 Text me directly for immediate response

This is not just about resolving your specific situation - it's about upholding the integrity and values that Grime Guardians was founded on. You have my personal word that this will be made right.

I will not rest until you are completely satisfied and confident in our commitment to excellence.

Brandon Thompson
CEO & Founder, Grime Guardians
"Excellence is not an act, but a habit" ™"""

            self.crisis_situations_handled += 1
            
            return AgentResponse(
                agent_name="brandon",
                response=response,
                confidence=0.98,
                metadata={
                    "matter_type": "crisis_intervention",
                    "crisis_type": crisis_type,
                    "personal_contact_promised": True,
                    "executive_team_activated": True
                }
            )
            
        except Exception as e:
            logger.error(f"Crisis handling error: {e}")
            return AgentResponse(
                agent_name="brandon",
                response="I am Brandon, CEO of Grime Guardians. I recognize this is a serious matter requiring my immediate personal attention. Please call me directly at (512) 555-CEO1 or provide your direct number so I can reach you immediately.",
                confidence=0.8,
                metadata={"error": str(e), "immediate_contact_required": True}
            )
    
    async def _handle_vip_account(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle VIP account management and high-value customers."""
        account_type = classification.get("account_type", "high_value")
        
        response = f"""👑 **VIP CUSTOMER - PERSONAL CEO ATTENTION**

{context.sender_name or 'Valued VIP Customer'}, this is Brandon, CEO of Grime Guardians. I personally oversee our VIP accounts and want to ensure you receive our absolute best service.

**YOUR VIP STATUS INCLUDES:**
✅ Direct access to me personally for any needs
✅ Priority scheduling with our top-rated teams
✅ Guaranteed service quality with personal oversight
✅ Exclusive pricing and service upgrades
✅ Personal relationship management

**VIP SERVICE GUARANTEES:**
🎯 Same-day response to any requests
📞 My direct line for immediate assistance
🏆 Premium service teams exclusively
💎 Custom service plans tailored to your needs
🔄 Quarterly personal check-ins

**MY PERSONAL COMMITMENT:**
I personally review every aspect of your service experience to ensure it meets the highest standards. Your satisfaction directly reflects on my leadership and the values we've built this company on.

**VIP DIRECT ACCESS:**
📱 CEO VIP Line: (512) 555-CEO1
📧 brandon.vip@grimeguardians.com
💬 Priority text response guaranteed

**SPECIAL VIP SERVICES:**
• Custom scheduling around your preferences
• Special event cleaning preparation
• Property management coordination
• Extended service guarantees
• Personalized team assignments

How can I personally ensure your experience with Grime Guardians exceeds your expectations?

Brandon Thompson
CEO & Founder
"VIP service is personal service" ™"""

        self.vip_accounts_managed += 1
        
        return AgentResponse(
            agent_name="brandon",
            response=response,
            confidence=0.95,
            metadata={"matter_type": "vip_account", "account_type": account_type}
        )
    
    async def _handle_partnership_inquiry(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle partnership and business development opportunities."""
        partnership_type = classification.get("partnership_type", "general")
        
        response = f"""🤝 **PARTNERSHIP OPPORTUNITY - CEO DIRECT ENGAGEMENT**

{context.sender_name or 'Potential Partner'}, thank you for your interest in partnering with Grime Guardians. As CEO, I personally evaluate all strategic partnerships.

**OUR PARTNERSHIP PHILOSOPHY:**
We believe in building long-term relationships that create mutual value while enhancing our ability to serve customers excellently.

**PARTNERSHIP AREAS WE EXPLORE:**
🏢 Property Management Companies
🏘️ Real Estate Agencies
🏗️ General Contractors & Builders
🏨 Hospitality & Short-term Rentals
🏪 Commercial & Office Properties
🤝 Service Provider Networks

**WHAT WE BRING TO PARTNERSHIPS:**
✅ Proven track record of excellence
✅ Fully licensed, bonded, and insured
✅ Scalable operations for volume needs
✅ Technology integration capabilities
✅ Dedicated partnership support
✅ Competitive partnership pricing

**NEXT STEPS FOR EVALUATION:**
📋 Partnership proposal review
📞 Personal discussion about mutual goals
🤝 Pilot program development
📊 Success metrics and KPI establishment
📝 Formal partnership agreement

**DIRECT CEO CONTACT:**
📱 Partnership Line: (512) 555-CEO1
📧 brandon.partnerships@grimeguardians.com
📅 Schedule direct meeting: calendly.com/brandon-ceo

I personally want to understand how we can create value together while maintaining our commitment to service excellence.

What type of partnership opportunity are you exploring?

Brandon Thompson
CEO & Founder, Grime Guardians
"Great partnerships create exceptional value" ™"""

        self.partnerships_developed += 1
        
        return AgentResponse(
            agent_name="brandon",
            response=response,
            confidence=0.92,
            metadata={"matter_type": "partnership", "partnership_type": partnership_type}
        )
    
    async def _handle_legal_matter(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle legal or regulatory matters requiring CEO attention."""
        legal_type = classification.get("legal_type", "general")
        
        response = f"""⚖️ **LEGAL MATTER - CEO IMMEDIATE ATTENTION**

{context.sender_name or 'Sir/Madam'}, I am Brandon Thompson, CEO of Grime Guardians. I take all legal and regulatory matters extremely seriously and handle them personally.

**IMMEDIATE PROTOCOL:**
✅ Your matter is being documented with our legal counsel
✅ I am personally reviewing all relevant details
✅ We maintain comprehensive insurance and bonding for protection
✅ All communications will be handled with complete transparency

**OUR COMMITMENT TO LEGAL COMPLIANCE:**
📋 Full licensing and regulatory compliance
🛡️ Comprehensive liability and bonding coverage
📝 Detailed documentation and record keeping
🤝 Professional mediation and resolution processes

**NEXT STEPS:**
1. **Immediate Documentation** - I'm personally documenting this matter
2. **Legal Counsel Consultation** - Engaging our legal team for guidance
3. **Direct Resolution Discussion** - Personal conversation within 24 hours
4. **Comprehensive Response** - Detailed written response within 48 hours

**CONFIDENTIAL DIRECT CONTACT:**
📞 CEO Legal Line: (512) 555-CEO1
📧 brandon.legal@grimeguardians.com
📝 Secure portal: Available upon request

**MY PERSONAL ASSURANCE:**
As CEO, I guarantee that this matter will be handled with the utmost professionalism, integrity, and in full compliance with all applicable laws and regulations.

Please provide your preferred method of contact for immediate follow-up discussion.

Brandon Thompson
CEO & Founder, Grime Guardians
"Integrity in all we do" ™"""

        return AgentResponse(
            agent_name="brandon",
            response=response,
            confidence=0.96,
            metadata={"matter_type": "legal", "legal_type": legal_type, "legal_counsel_engaged": True}
        )
    
    async def _handle_executive_escalation(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle executive escalations from other team members or departments."""
        escalation_source = classification.get("escalation_source", "unknown")
        
        response = f"""🎯 **EXECUTIVE ESCALATION - CEO TAKING OWNERSHIP**

{context.sender_name or 'Team Member/Customer'}, I am Brandon, CEO of Grime Guardians. This matter has been escalated to me personally, and I am taking immediate ownership.

**EXECUTIVE INTERVENTION:**
✅ I am personally reviewing all details of this situation
✅ I am coordinating with relevant team leaders for complete context
✅ I am implementing executive-level resources for resolution
✅ I am ensuring this aligns with our company values and standards

**MY ESCALATION PROCESS:**
1. **Immediate Assessment** - Understanding all aspects of the situation
2. **Resource Allocation** - Deploying necessary team and resources
3. **Direct Resolution** - Personal oversight of solution implementation
4. **Follow-up Assurance** - Ensuring long-term satisfaction
5. **Process Improvement** - Preventing similar future escalations

**EXECUTIVE AUTHORITY:**
As CEO, I have the authority to:
• Make immediate policy exceptions when warranted
• Authorize special compensation or service recovery
• Implement process changes to prevent recurrence
• Personally guarantee resolution outcomes

**MY DIRECT INVOLVEMENT:**
📞 Personal call within 2 hours
📋 Detailed investigation and action plan
✅ Executive resolution within 24 hours
📞 Personal follow-up to ensure satisfaction

This escalation represents an opportunity for us to demonstrate our commitment to excellence and continuous improvement.

How can I best resolve this situation for all parties involved?

Brandon Thompson
CEO & Founder, Grime Guardians
"Leadership means taking responsibility" ™"""

        self.strategic_decisions_made += 1
        
        return AgentResponse(
            agent_name="brandon",
            response=response,
            confidence=0.94,
            metadata={"matter_type": "executive_escalation", "escalation_source": escalation_source}
        )
    
    async def _handle_strategic_matter(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle strategic business matters and decisions."""
        strategic_area = classification.get("strategic_area", "general")
        
        response = f"""🎯 **STRATEGIC MATTER - CEO EVALUATION**

{context.sender_name or 'Stakeholder'}, as CEO of Grime Guardians, I personally evaluate all strategic matters that affect our company's direction and mission.

**STRATEGIC EVALUATION PROCESS:**
📊 Alignment with company mission and values
📈 Impact on customer experience and satisfaction
💰 Financial implications and sustainability
👥 Effect on team members and company culture
🌟 Long-term strategic positioning

**KEY STRATEGIC FOCUS AREAS:**
• Service Excellence and Quality Standards
• Customer Experience Innovation
• Team Development and Culture
• Sustainable Growth Strategies
• Technology and Operational Efficiency
• Community Impact and Responsibility

**DECISION-MAKING CRITERIA:**
✅ Does it align with "We clean like it's our name on the lease"?
✅ Does it enhance customer value and satisfaction?
✅ Does it support team member growth and success?
✅ Is it financially sustainable and responsible?
✅ Does it position us for long-term success?

**STRATEGIC CONSULTATION PROCESS:**
📞 Personal discussion to understand full context
📋 Stakeholder analysis and input gathering
🤝 Collaborative solution development
📊 Implementation planning and oversight
📈 Success measurement and adjustment

**CEO STRATEGIC CONTACT:**
📞 Strategic Line: (512) 555-CEO1
📧 brandon.strategy@grimeguardians.com
📅 Executive consultation available

What strategic matter would you like to discuss?

Brandon Thompson
CEO & Founder, Grime Guardians
"Strategic decisions shape our legacy" ™"""

        self.strategic_decisions_made += 1
        
        return AgentResponse(
            agent_name="brandon",
            response=response,
            confidence=0.90,
            metadata={"matter_type": "strategic", "strategic_area": strategic_area}
        )
    
    async def _handle_general_executive_inquiry(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle general inquiries requiring CEO attention."""
        response = f"""👋 **PERSONAL MESSAGE FROM CEO BRANDON**

{context.sender_name or 'Dear Friend'}, thank you for reaching out to me personally. As the CEO and founder of Grime Guardians, I'm always available for important matters.

**ABOUT GRIME GUARDIANS:**
I founded this company with a simple mission: "We clean like it's our name on the lease." This means we treat every home with the same care and attention as if we lived there ourselves.

**MY PERSONAL INVOLVEMENT:**
✅ I personally review customer feedback and experiences
✅ I maintain direct oversight of service quality standards
✅ I'm available for any significant concerns or opportunities
✅ I personally ensure our values are reflected in every interaction

**WHEN TO REACH OUT TO ME DIRECTLY:**
• Significant service concerns requiring executive attention
• Partnership or business development opportunities
• Strategic suggestions for company improvement
• VIP account management needs
• Matters requiring immediate CEO intervention

**COMPANY VALUES I PERSONALLY CHAMPION:**
🌟 Excellence in everything we do
🤝 Integrity and transparency in all relationships
👥 Respect for customers and team members
📈 Continuous improvement and innovation
🏘️ Positive impact in our community

**MY DIRECT CONTACT:**
📞 CEO Line: (512) 555-CEO1
📧 brandon@grimeguardians.com
💬 Text for urgent matters

How can I personally help you today?

Brandon Thompson
CEO & Founder, Grime Guardians
"Personal leadership creates exceptional experiences" ™"""

        return AgentResponse(
            agent_name="brandon",
            response=response,
            confidence=0.85,
            metadata={"matter_type": "general_executive_inquiry"}
        )
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get Brandon's CEO performance metrics."""
        return {
            "strategic_decisions_made": self.strategic_decisions_made,
            "crisis_situations_handled": self.crisis_situations_handled,
            "partnerships_developed": self.partnerships_developed,
            "vip_accounts_managed": self.vip_accounts_managed,
            "average_response_time_hours": 1.0,  # Target: within 1 hour
            "executive_availability": "24/7",
            "specialization": "executive_leadership"
        }
    
    def log_strategic_decision(self, decision_type: str, impact_level: str):
        """Log a strategic decision made by the CEO."""
        self.strategic_decisions_made += 1
        
        # Could log to database for tracking
        logger.info(f"CEO Strategic Decision: {decision_type} with {impact_level} impact")


# Singleton instance
_brandon_ceo_agent = None

def get_brandon_ceo_agent() -> BrandonCEOAgent:
    """Get singleton Brandon CEO agent instance."""
    global _brandon_ceo_agent
    if _brandon_ceo_agent is None:
        _brandon_ceo_agent = BrandonCEOAgent()
    return _brandon_ceo_agent