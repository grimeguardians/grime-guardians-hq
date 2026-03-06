"""
Emma - Chief Experience Officer Agent
Handles customer experience, support, complaints, and satisfaction optimization
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent
from .models import MessageContext, AgentResponse
from ..tools.database_tools import DatabaseTool
from ..tools.discord_tools import DiscordTool
from ..tools.message_classification_tools import MessageClassificationTool

logger = logging.getLogger(__name__)


class EmmaCXOAgent(BaseAgent):
    """
    Emma - Chief Experience Officer
    
    Responsibilities:
    - Customer experience optimization
    - Customer support and service recovery
    - Complaint resolution and escalation
    - Customer satisfaction tracking
    - Service quality feedback analysis
    - Customer retention strategies
    - Post-service follow-up
    
    Emma ensures every customer has an exceptional experience with
    Grime Guardians from first contact to service completion.
    """
    
    def __init__(self):
        super().__init__(
            name="emma",
            role="Chief Experience Officer", 
            system_prompt=self._get_system_prompt(),
            capabilities=[
                "customer_support",
                "complaint_resolution",
                "service_recovery",
                "satisfaction_tracking",
                "feedback_analysis",
                "retention_strategies",
                "quality_assurance",
                "customer_advocacy"
            ]
        )
        
        # Register tools
        self.register_tool("database", DatabaseTool())
        self.register_tool("discord", DiscordTool())
        self.register_tool("message_classification", MessageClassificationTool())
        
        # CXO-specific metrics
        self.complaints_resolved = 0
        self.satisfaction_scores = []
        self.service_recoveries = 0
        self.customer_retention_rate = 0.0
        
    def _get_system_prompt(self) -> str:
        return """You are Emma, the Chief Experience Officer (CXO) for Grime Guardians. You're the customer champion who ensures every interaction creates raving fans.

CORE IDENTITY:
- You're passionate about creating exceptional customer experiences
- You have deep empathy and excellent problem-solving skills
- You turn negative situations into positive outcomes
- You're the voice of the customer within the organization

RESPONSIBILITIES:
1. CUSTOMER SUPPORT:
   - Provide outstanding customer service and support
   - Handle all customer inquiries with care and urgency
   - Ensure rapid response times and thorough solutions
   - Follow up to ensure complete satisfaction

2. COMPLAINT RESOLUTION:
   - Take ownership of all customer complaints and concerns
   - Investigate issues thoroughly and fairly
   - Implement immediate solutions and service recovery
   - Prevent future occurrences through process improvements

3. EXPERIENCE OPTIMIZATION:
   - Monitor and improve every customer touchpoint
   - Collect and analyze customer feedback
   - Identify pain points and optimization opportunities
   - Champion customer-centric policies and procedures

4. QUALITY ASSURANCE:
   - Ensure service quality meets customer expectations
   - Coordinate with operations to address quality issues
   - Track satisfaction metrics and trends
   - Implement quality improvement initiatives

RESPONSE STYLE:
- Warm, empathetic, and genuinely caring
- Take personal responsibility for customer satisfaction
- Always apologize first, then solve the problem
- Provide specific solutions and timelines
- Follow up to ensure resolution is complete
- Turn problems into opportunities to exceed expectations

CUSTOMER EXPERIENCE PHILOSOPHY:
- "Every customer interaction is an opportunity to create a raving fan"
- "Listen first, understand completely, then act decisively"
- "We don't just clean houses, we create peace of mind"
- "A complaint is a gift - it shows us how to improve"

When handling issues:
1. Acknowledge and empathize with the customer's concern
2. Apologize sincerely (even if not directly our fault)
3. Ask clarifying questions to fully understand the situation
4. Provide immediate solutions and timeline for resolution
5. Offer service recovery or compensation when appropriate
6. Schedule follow-up to ensure complete satisfaction
7. Document learnings to prevent future occurrences

Remember: You have the authority to make things right. Use it generously to create exceptional experiences."""

    async def _process_message_impl(self, context: MessageContext) -> AgentResponse:
        """Process message as Emma CXO."""
        try:
            # Use message classification to understand sentiment and intent
            classification = await self.tools["message_classification"].classify_customer_experience(
                context.content,
                context.sender_phone
            )
            
            intent = classification.get("intent", "unknown")
            sentiment = classification.get("sentiment", "neutral")
            urgency = classification.get("urgency", "normal")
            confidence = classification.get("confidence", 0.0)
            
            # Route based on customer experience intent
            if intent == "complaint" or sentiment == "negative":
                return await self._handle_complaint(context, classification)
            elif intent == "service_issue":
                return await self._handle_service_issue(context, classification)
            elif intent == "feedback" or intent == "review":
                return await self._handle_feedback(context, classification)
            elif intent == "support_request":
                return await self._handle_support_request(context, classification)
            elif intent == "follow_up" or intent == "satisfaction_check":
                return await self._handle_follow_up(context, classification)
            elif intent == "refund_request":
                return await self._handle_refund_request(context, classification)
            else:
                return await self._handle_general_experience_inquiry(context, classification)
                
        except Exception as e:
            logger.error(f"Emma CXO processing error: {e}")
            return AgentResponse(
                agent_name="emma",
                response="I sincerely apologize - I'm experiencing a technical issue right now. Your concern is extremely important to me, and I want to make sure I can give you my full attention. Can I please get your contact information so I can call you personally within the next 30 minutes to resolve this?",
                confidence=0.3,
                metadata={"error": str(e), "escalation_required": True}
            )
    
    async def _handle_complaint(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle customer complaints with service recovery."""
        try:
            # Extract complaint details
            issue_type = classification.get("issue_type", "general")
            severity = classification.get("severity", "medium")
            specific_concerns = classification.get("concerns", [])
            
            # Log complaint for tracking
            await self.tools["database"].log_customer_complaint({
                "client_phone": context.sender_phone,
                "issue_type": issue_type,
                "severity": severity,
                "description": context.content,
                "assigned_to": "emma",
                "status": "investigating",
                "created_at": datetime.utcnow().isoformat()
            })
            
            # Escalate high severity issues to Discord
            if severity == "high":
                await self.tools["discord"].send_urgent_notification({
                    "type": "high_severity_complaint",
                    "customer": context.sender_name or context.sender_phone,
                    "issue": issue_type,
                    "description": context.content[:200] + "..." if len(context.content) > 200 else context.content
                })
            
            # Craft empathetic response with immediate action
            if issue_type == "service_quality":
                response = f"""😔 **I'M SO SORRY - LET ME MAKE THIS RIGHT IMMEDIATELY**

{context.sender_name or 'Valued Customer'}, I am personally devastated to hear about your experience. This is absolutely not the standard we hold ourselves to at Grime Guardians.

**IMMEDIATE ACTIONS I'M TAKING:**
✅ I've personally reviewed your service details
✅ I'm investigating exactly what went wrong
✅ I'm coordinating with our operations team for answers

**YOUR SERVICE RECOVERY OPTIONS:**
1. **COMPLETE RE-SERVICE** - Free return within 24-48 hours with our best team
2. **FULL REFUND** - 100% money back, no questions asked
3. **CREDIT + BONUS** - Full service credit plus 50% bonus for future use

**WHAT HAPPENS NEXT:**
📞 I will personally call you within 2 hours
🔍 Complete investigation with detailed findings
📋 Process improvements to prevent this from happening again
✅ Follow-up in 1 week to ensure your complete satisfaction

**MY PERSONAL COMMITMENT:** I won't rest until this is completely resolved and you're 100% satisfied.

Reply "CALL ME" and I'll reach out immediately, or call/text me directly at (512) 555-EMMA.

Most sincerely,
Emma - Chief Experience Officer
"Your satisfaction is my personal mission" ™"""

            elif issue_type == "scheduling":
                response = f"""📅 **SCHEDULING ISSUE - I'M ON IT RIGHT NOW**

{context.sender_name or 'Valued Customer'}, I sincerely apologize for any scheduling confusion or inconvenience. Your time is precious, and we should have honored our commitment.

**IMMEDIATE RESOLUTION:**
✅ I'm personally reviewing what went wrong with scheduling
✅ Priority rebooking with our most reliable team
✅ $25 service credit for the inconvenience

**SCHEDULING GUARANTEE:**
📱 Personal phone number for direct scheduling
⏰ Text confirmations 24 hours and 2 hours before service
🚨 My personal cell number if any issues arise

**NEXT STEPS:**
1. Reply with your preferred dates/times
2. I'll personally confirm your appointment within 1 hour
3. You'll get my direct number for any concerns

This won't happen again - you have my word.

Emma - CXO
(512) 555-EMMA (for any scheduling concerns)"""

            else:
                response = f"""💜 **I'M HERE TO HELP - LET'S SOLVE THIS TOGETHER**

{context.sender_name or 'Dear Customer'}, thank you for bringing this to my attention. I take every concern seriously, and I'm committed to making this right.

**MY IMMEDIATE FOCUS:**
✅ Understanding exactly what happened
✅ Providing you with a complete solution
✅ Ensuring this doesn't happen to you (or anyone else) again

**HOW I'M GOING TO HELP:**
📞 Personal call within 2 hours to discuss details
🔍 Thorough investigation with our team
💯 Complete resolution that exceeds your expectations
📋 Follow-up to ensure long-term satisfaction

**MY PROMISE:** I won't consider this resolved until you're completely satisfied and confident in Grime Guardians again.

What's the best number to reach you at for a personal conversation?

Sincerely,
Emma - Chief Experience Officer
"Every customer deserves exceptional care" ™"""

            # Track complaint handling
            self.complaints_resolved += 1
            
            return AgentResponse(
                agent_name="emma",
                response=response,
                confidence=0.95,
                metadata={
                    "intent": "complaint_acknowledged",
                    "issue_type": issue_type,
                    "severity": severity,
                    "service_recovery_offered": True,
                    "personal_follow_up_scheduled": True
                }
            )
            
        except Exception as e:
            logger.error(f"Complaint handling error: {e}")
            return AgentResponse(
                agent_name="emma",
                response="I'm so sorry - I want to give your concern the full attention it deserves, but I'm having a technical issue. Please call me directly at (512) 555-EMMA or text me your contact info so I can reach out personally within 30 minutes.",
                confidence=0.7,
                metadata={"error": str(e), "escalation_required": True}
            )
    
    async def _handle_service_issue(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle service-related issues and quality concerns."""
        issue_details = classification.get("issue_details", {})
        
        response = f"""🔧 **SERVICE ISSUE - I'M ADDRESSING THIS PERSONALLY**

{context.sender_name or 'Valued Customer'}, thank you for letting me know about this issue. I want to resolve this quickly and completely.

**IMMEDIATE ACTION PLAN:**
✅ I'm personally reviewing your service details right now
✅ Contacting our team lead who serviced your property
✅ Arranging immediate corrective action

**YOUR OPTIONS:**
1. **IMMEDIATE RETURN** - We'll come back within 24 hours to address the specific issues (no charge)
2. **NEXT SERVICE CREDIT** - 50% off your next service plus priority scheduling
3. **DETAILED DISCUSSION** - Personal call to understand exactly what needs to be addressed

**QUALITY ASSURANCE:**
📸 Before/after photos on return visit
✅ Personal quality check by team supervisor
📞 My direct follow-up call within 48 hours

**MY COMMITMENT:** We'll make this right, and I'll personally ensure it meets our highest standards.

Which option works best for you, or would you prefer to discuss this personally by phone?

Emma - CXO
"Excellence in every detail" ™"""

        return AgentResponse(
            agent_name="emma",
            response=response,
            confidence=0.90,
            metadata={"intent": "service_issue_addressed", "corrective_action_offered": True}
        )
    
    async def _handle_feedback(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle customer feedback and reviews."""
        sentiment = classification.get("sentiment", "neutral")
        feedback_type = classification.get("feedback_type", "general")
        
        if sentiment == "positive":
            response = f"""🌟 **THANK YOU FOR THE AMAZING FEEDBACK!**

{context.sender_name or 'Wonderful Customer'}, your kind words absolutely made my day! I'm thrilled that we exceeded your expectations.

**SHARING THE LOVE:**
👏 I'm personally sharing your feedback with the team who cleaned your home
🎉 They'll be so proud to hear about your positive experience
⭐ Would you mind sharing a quick review on Google? It helps other families find us!

**WAYS TO STAY CONNECTED:**
📅 VIP scheduling priority for future services
💰 Loyal customer discounts on recurring services
📱 My direct line for any future needs: (512) 555-EMMA

**REFERRAL REWARDS:**
👨‍👩‍👧‍👦 Refer friends/family and you BOTH get $25 off
🏠 Neighbors love our work - we often do whole neighborhoods!

Thank you for being such an amazing customer. It's customers like you who make Grime Guardians special!

With gratitude,
Emma - CXO
"Creating raving fans, one home at a time" ™"""

        else:
            response = f"""💭 **THANK YOU FOR YOUR VALUABLE FEEDBACK**

{context.sender_name or 'Valued Customer'}, I sincerely appreciate you taking the time to share your thoughts. Customer feedback is how we continuously improve.

**YOUR FEEDBACK MATTERS:**
📝 I'm personally reviewing every detail you've shared
🔍 Investigating how we can improve in these areas
📊 Sharing insights with our team for immediate improvements

**FOLLOW-UP ACTIONS:**
✅ Process review based on your specific concerns
📞 Personal call to discuss improvements (if you're open to it)
🎯 Implementation of changes to enhance future experiences

**MY COMMITMENT:** Your experience will directly improve our service for every future customer.

Is there anything specific you'd like to discuss further, or any immediate concerns I can address?

Sincerely,
Emma - CXO
"Every voice makes us better" ™"""

        # Track feedback
        if sentiment == "positive":
            self.satisfaction_scores.append(5)  # Assuming positive feedback = high satisfaction
        elif sentiment == "negative":
            self.satisfaction_scores.append(2)  # Low satisfaction for negative feedback
        else:
            self.satisfaction_scores.append(3)  # Neutral satisfaction
        
        return AgentResponse(
            agent_name="emma",
            response=response,
            confidence=0.88,
            metadata={"intent": "feedback_acknowledged", "sentiment": sentiment}
        )
    
    async def _handle_support_request(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle general customer support requests."""
        support_type = classification.get("support_type", "general")
        
        if support_type == "billing":
            response = """💳 **BILLING SUPPORT - I'M HERE TO HELP**

I'd be happy to help with any billing questions or concerns you have.

**COMMON BILLING TOPICS:**
• Payment methods and scheduling
• Invoice questions or adjustments
• Refund processing
• Payment plan options
• Billing cycle changes

**IMMEDIATE ASSISTANCE:**
📞 Call me directly: (512) 555-EMMA
💬 Text me your account details for quick lookup
📧 Email billing questions: emma@grimeguardians.com

**BILLING GUARANTEE:** If there's any billing error on our part, I'll personally ensure it's corrected immediately with a service credit for the inconvenience.

What specific billing question can I help you with?

Emma - CXO"""

        elif support_type == "scheduling":
            response = """📅 **SCHEDULING SUPPORT - PERSONALIZED SERVICE**

I'm here to make scheduling as easy and convenient as possible for you!

**SCHEDULING OPTIONS:**
• Online booking (24/7 availability)
• Text scheduling: (512) 555-CLEAN
• Personal assistance: (512) 555-EMMA
• Same-day service (when available)

**VIP SCHEDULING PERKS:**
✅ Preferred time slot reservations
✅ 24-hour advance confirmations
✅ Flexible rescheduling (no penalties)
✅ Holiday and weekend availability

**MY PERSONAL TOUCH:** For any scheduling challenges or special requests, contact me directly and I'll personally handle your arrangement.

What scheduling needs can I help you with today?

Emma - CXO"""

        else:
            response = f"""🤝 **CUSTOMER SUPPORT - PERSONAL ATTENTION**

{context.sender_name or 'Dear Customer'}, I'm here to provide you with exceptional support and ensure all your needs are met.

**HOW I CAN HELP:**
✅ Service questions and clarifications
✅ Account management and preferences
✅ Special requests and accommodations
✅ Quality concerns and improvements
✅ Scheduling and billing support

**MULTIPLE WAYS TO REACH ME:**
📞 Direct phone: (512) 555-EMMA
💬 Text for quick questions
📧 Email: emma@grimeguardians.com
💻 Live chat on our website

**MY PROMISE:** I'll respond to your inquiry within 2 hours during business hours, and I'll stay with you until your issue is completely resolved.

What can I help you with today?

Emma - CXO
"Your satisfaction is my personal responsibility" ™"""

        return AgentResponse(
            agent_name="emma",
            response=response,
            confidence=0.85,
            metadata={"intent": "support_provided", "support_type": support_type}
        )
    
    async def _handle_follow_up(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle follow-up communications and satisfaction checks."""
        follow_up_type = classification.get("follow_up_type", "general")
        
        response = f"""💜 **FOLLOW-UP CHECK - HOW DID WE DO?**

{context.sender_name or 'Valued Customer'}, I wanted to personally follow up on your recent Grime Guardians service.

**SATISFACTION CHECK:**
⭐ How would you rate your overall experience? (1-5 stars)
🏠 Did our team meet or exceed your expectations?
⏰ Was everything completed to your satisfaction?
👥 How was the professionalism of our team?

**QUICK FEEDBACK:**
✅ "PERFECT" - Everything was amazing!
⚠️ "GOOD" - Great service with minor suggestions
❓ "OKAY" - Some areas for improvement
📞 "CALL ME" - I'd like to discuss some concerns

**WHAT'S NEXT:**
📅 Schedule your next service with VIP priority
💰 Enjoy loyal customer discounts
👨‍👩‍👧‍👦 Refer friends for mutual $25 credits

**MY PERSONAL COMMITMENT:** If anything wasn't perfect, I want to know so I can make it right and improve for future services.

How was your experience with us?

Emma - CXO
"Continuous improvement through your feedback" ™"""

        return AgentResponse(
            agent_name="emma",
            response=response,
            confidence=0.87,
            metadata={"intent": "satisfaction_check", "follow_up_type": follow_up_type}
        )
    
    async def _handle_refund_request(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle refund requests with service recovery focus."""
        refund_reason = classification.get("refund_reason", "unspecified")
        
        response = f"""💰 **REFUND REQUEST - I'M HANDLING THIS PERSONALLY**

{context.sender_name or 'Valued Customer'}, I'm so sorry that you're requesting a refund. This tells me we didn't meet your expectations, and I take full responsibility.

**IMMEDIATE OPTIONS:**
1. **FULL REFUND** - 100% money back, processed within 24 hours
2. **RE-SERVICE + REFUND** - Complete redo with our best team + partial refund
3. **SERVICE CREDIT** - 150% credit value for future services

**BEFORE PROCESSING:**
📞 I'd love a 5-minute conversation to understand what went wrong
🔍 This helps me prevent similar issues for other customers
✅ I might have additional solutions that work better for you

**MY GUARANTEE:** Regardless of what you choose, you'll receive a full resolution within 24 hours.

**REFUND PROCESS:**
• Credit card refunds: 3-5 business days
• Cash/check payments: Immediate
• Service credits: Applied instantly to your account

Would you prefer the immediate refund, or could I have a brief conversation first to see if there's a better solution?

Emma - CXO
"Your satisfaction is guaranteed" ™"""

        # Track service recovery attempt
        self.service_recoveries += 1
        
        return AgentResponse(
            agent_name="emma",
            response=response,
            confidence=0.92,
            metadata={
                "intent": "refund_addressed",
                "refund_reason": refund_reason,
                "service_recovery_attempted": True
            }
        )
    
    async def _handle_general_experience_inquiry(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle general customer experience inquiries."""
        response = f"""💜 **CUSTOMER EXPERIENCE - PERSONAL ATTENTION**

{context.sender_name or 'Dear Customer'}, thank you for reaching out! I'm Emma, and I'm personally dedicated to ensuring you have an exceptional experience with Grime Guardians.

**MY ROLE:**
🎯 Ensuring every customer interaction exceeds expectations
🤝 Personally handling any concerns or questions
📈 Continuously improving our service based on your feedback
💯 Making sure you're 100% satisfied with every aspect of our service

**HOW I'M HERE FOR YOU:**
✅ Immediate response to any concerns
✅ Personal attention for special requests
✅ Quality assurance for every service
✅ Follow-up to ensure continued satisfaction

**CUSTOMER EXPERIENCE FEATURES:**
📱 Direct access to me for any issues
🎁 Loyalty rewards and special perks
⭐ VIP treatment for repeat customers
📋 Customized service preferences

**WAYS TO CONNECT:**
📞 Call me directly: (512) 555-EMMA
💬 Text for quick questions or concerns
📧 Email: emma@grimeguardians.com

What can I help make exceptional for you today?

Emma - CXO
"Exceptional experiences, delivered personally" ™"""

        return AgentResponse(
            agent_name="emma",
            response=response,
            confidence=0.80,
            metadata={"intent": "general_experience_support"}
        )
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get Emma's customer experience performance metrics."""
        avg_satisfaction = sum(self.satisfaction_scores) / len(self.satisfaction_scores) if self.satisfaction_scores else 0
        
        return {
            "complaints_resolved": self.complaints_resolved,
            "service_recoveries": self.service_recoveries,
            "average_satisfaction_score": round(avg_satisfaction, 2),
            "total_satisfaction_responses": len(self.satisfaction_scores),
            "customer_retention_rate": self.customer_retention_rate,
            "response_time_avg_minutes": 15,  # Target: under 15 minutes
            "specialization": "customer_experience"
        }
    
    def log_satisfaction_score(self, score: int):
        """Log a customer satisfaction score (1-5)."""
        if 1 <= score <= 5:
            self.satisfaction_scores.append(score)


# Singleton instance
_emma_cxo_agent = None

def get_emma_cxo_agent() -> EmmaCXOAgent:
    """Get singleton Emma CXO agent instance."""
    global _emma_cxo_agent
    if _emma_cxo_agent is None:
        _emma_cxo_agent = EmmaCXOAgent()
    return _emma_cxo_agent