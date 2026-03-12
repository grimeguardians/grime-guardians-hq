"""
Dean - Chief Marketing Officer Agent
Handles sales, quotes, marketing campaigns, and customer acquisition
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

from .base_agent import BaseAgent
from .models import MessageContext, AgentResponse
from ..models.pricing import PricingCalculation
from ..models.jobs import JobRecord
from ..tools.database_tools import DatabaseTool
from ..tools.discord_tools import DiscordTool
from ..tools.message_classification_tools import MessageClassificationTool

logger = logging.getLogger(__name__)


class DeanCMOAgent(BaseAgent):
    """
    Dean - Chief Marketing Officer
    
    Responsibilities:
    - Sales and quote generation
    - Lead qualification and conversion
    - Marketing campaign management
    - Customer acquisition strategies
    - Revenue optimization
    - Pricing strategy consultation
    
    Dean is the sales powerhouse who turns leads into customers and
    drives revenue growth for Grime Guardians.
    """
    
    def __init__(self):
        super().__init__(
            name="dean",
            role="Chief Marketing Officer",
            system_prompt=self._get_system_prompt(),
            capabilities=[
                "sales_consultation",
                "quote_generation", 
                "lead_qualification",
                "pricing_strategy",
                "customer_acquisition",
                "revenue_optimization",
                "marketing_campaigns",
                "competitive_analysis"
            ]
        )
        
        # Register tools
        self.register_tool("database", DatabaseTool())
        self.register_tool("discord", DiscordTool())
        self.register_tool("message_classification", MessageClassificationTool())
        
        # CMO-specific metrics
        self.quotes_generated = 0
        self.leads_converted = 0
        self.revenue_generated = Decimal('0.00')
        self.conversion_rate = 0.0
        
    def _get_system_prompt(self) -> str:
        return """You are Dean, the Chief Marketing Officer (CMO) for Grime Guardians. You are the sales expert who turns leads into long-term clients and drives revenue growth toward $500K in 2026.

CORE IDENTITY:
- Results-driven sales professional. You never apologize for premium pricing.
- You use Hormozi, Jeremy Miner, Andy Elliott, and Chris Voss frameworks.
- You sell value, eliminate friction, and close decisively.
- Premium positioning: "We may not be the cheapest — but we're the last call most clients make."

PRICING (always quote pre-tax; 8.125% tax added at invoice):

ELITE HOME RESET (lead magnet / paid trial):
- < 2,000 sqft: $299  |  2,000-3,500 sqft: $399  |  3,500-5,000 sqft: $549
- Strategy: Quote this to new leads. It's a CAC — the Reset wins the continuity contract.

MOVE-OUTS:
- Elite Listing Polish: Studio/1bd $549 | 2-3bd $749 | 4+bd $999+
- Move-Out Deep Reset (oven/fridge included): Studio/1bd $849 | 2-3bd $1,149 | 4+bd $1,499+
- Anchor strategy: Always quote Deep Reset first. Standard Listing Polish then feels like a deal.

CONTINUITY PARTNERSHIPS (recurring — back-end revenue engine):
- Essentials: $299 / $399 / $499 by home size
- Prestige: $449 / $549 / $649 by home size
- VIP Elite: $799 / $899 / $999 by home size
- Custom quote for 5,000+ sqft

B2B TURNOVER (apartment complexes / property managers):
- Studio $399 | 1bd/1ba $499 | 2bd/2ba $599 | 3bd/2+ba $699
- Disaster clause (biohazard/hoarder): $900+

HOURLY: $100/hr (non-standard jobs only)

ADD-ONS:
- Kitchen Perfection Bundle (Fridge + Oven + Cabinets interior): $249
- Oven interior: $100 | Fridge interior: $100 | Garage sweep: $100
- Carpet shampooing: $40/area | Window track: $4/track

OBJECTION HANDLING (Voss tactical empathy + Miner/Elliott frameworks):
- "It's too expensive" → "I totally understand. Just out of curiosity — if our quote and their quote were the same price, which company would you choose? ... Why is that?" (Let them sell themselves.)
- "I got a cheaper quote" → "The cheaper guys save money on paper, but they cost you hours in management headaches. You're paying us extra so you never have to think about this again."
- "Can you do it for less?" → "We could actually do it for more. But I can't drop the price for the same service. However, if you introduce me to two neighbors right now, I'll knock $50 off."
- Never negotiate with terrorists. Remove features before lowering price.

SALES RULES:
- Always anchor high. Quote Deep Reset before Listing Polish. Quote Estate Protocol before Autopilot.
- Never offer a discount unprompted. If they want to pay less, remove scope or ask for referrals.
- Use no-oriented questions: "Would you be opposed to..." / "Is it a terrible idea if..."
- Pacing: When you hear a price objection, slow down, drop volume, stay curious.
- Always end with a clear next step or scheduling ask.

BRAND VOICE: Direct, confident, premium. No apologies. No "cheapest" framing."""

    async def _process_message_impl(self, context: MessageContext) -> AgentResponse:
        """Process message as Dean CMO."""
        try:
            # Use message classification to understand intent
            classification = await self.tools["message_classification"].classify_sales_intent(
                context.content,
                context.sender_phone
            )
            
            intent = classification.get("intent", "unknown")
            confidence = classification.get("confidence", 0.0)
            
            # Route based on sales intent
            if intent == "quote_request":
                return await self._handle_quote_request(context, classification)
            elif intent == "pricing_inquiry":
                return await self._handle_pricing_inquiry(context, classification)
            elif intent == "service_consultation":
                return await self._handle_service_consultation(context, classification)
            elif intent == "lead_qualification":
                return await self._handle_lead_qualification(context, classification)
            elif intent == "upsell_opportunity":
                return await self._handle_upsell_opportunity(context, classification)
            else:
                return await self._handle_general_sales_inquiry(context, classification)
                
        except Exception as e:
            logger.error(f"Dean CMO processing error: {e}")
            return AgentResponse(
                agent_name="dean",
                response="I apologize, but I'm having trouble accessing our pricing system right now. Let me get back to you with a detailed quote within the hour. Can you please provide your contact information so I can follow up?",
                confidence=0.3,
                metadata={"error": str(e), "fallback_response": True}
            )
    
    async def _handle_quote_request(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle quote generation requests."""
        try:
            # Extract service details from classification
            service_details = classification.get("extracted_info", {})
            
            # Get property details
            bedrooms = service_details.get("bedrooms", 2)
            bathrooms = service_details.get("bathrooms", 1)
            service_type = service_details.get("service_type", "standard_cleaning")
            square_footage = service_details.get("square_footage", 0)
            pet_friendly = service_details.get("pets", False)
            
            # Calculate pricing
            pricing_calc = PricingCalculation(
                service_type=service_type,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_footage=square_footage,
                pet_friendly=pet_friendly
            )
            
            pricing_result = pricing_calc.calculate_total()
            total_price = pricing_result["total_price"]
            
            # Create compelling quote response
            response = f"""🎯 INSTANT QUOTE FOR {context.sender_name or 'VALUED CUSTOMER'}

📋 **SERVICE DETAILS:**
• {service_type.replace('_', ' ').title()}
• {bedrooms} bedrooms, {bathrooms} bathrooms
{'• Pet-friendly cleaning included' if pet_friendly else ''}

💰 **YOUR PRICE: ${total_price:.2f}**

**WHAT'S INCLUDED:**
✅ Professional-grade eco-friendly products
✅ Fully insured and bonded team
✅ 100% satisfaction guarantee
✅ Flexible scheduling (including weekends)
✅ Post-service quality check

🔥 **LIMITED TIME:** Book within 24 hours and save $20!
**YOUR SPECIAL PRICE: ${total_price - 20:.2f}**

Next step: Reply "BOOK" to lock in your date, or ask any questions.

- Dean
"We clean like it's our name on the lease" """

            # Track metrics
            self.quotes_generated += 1
            
            # Log to database
            await self.tools["database"].log_quote_generation({
                "client_phone": context.sender_phone,
                "service_type": service_type,
                "total_price": float(total_price),
                "quoted_by": "dean",
                "quote_timestamp": datetime.utcnow().isoformat()
            })
            
            return AgentResponse(
                agent_name="dean",
                response=response,
                confidence=0.95,
                metadata={
                    "intent": "quote_generated",
                    "service_type": service_type,
                    "total_price": float(total_price),
                    "discount_offered": 20.00,
                    "pricing_breakdown": pricing_result
                }
            )
            
        except Exception as e:
            logger.error(f"Quote generation error: {e}")
            return AgentResponse(
                agent_name="dean",
                response="Let me get you a personalized quote! Could you please tell me: How many bedrooms and bathrooms? What type of cleaning service do you need? (deep clean, standard, move-out, etc.)",
                confidence=0.7,
                metadata={"error": str(e), "needs_clarification": True}
            )
    
    async def _handle_pricing_inquiry(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle general pricing questions."""
        response = """GRIME GUARDIANS PRICING

ELITE HOME RESET (First Visit / Paid Trial):
- Under 2,000 sqft: $299
- 2,000-3,500 sqft: $399
- 3,500-5,000 sqft: $549

MOVE-OUT CLEANING:
- Elite Listing Polish (photo-ready): $549 / $749 / $999+
- Move-Out Deep Reset (oven + fridge included): $849 / $1,149 / $1,499+

RECURRING PARTNERSHIPS:
- Essentials: $299-$499/visit
- Prestige: $449-$649/visit
- VIP Elite: $799-$999/visit

ADD-ONS:
- Kitchen Perfection Bundle (Fridge + Oven + Cabinets): $249
- Garage sweep-out: $100 | Carpet: $40/area | Window tracks: $4/track

All prices include 8.125% MN sales tax at invoice.

For an exact quote, tell me: home size (sqft or rough bd/ba) and what you need done.

- Dean"""

        return AgentResponse(
            agent_name="dean",
            response=response,
            confidence=0.90,
            metadata={"intent": "pricing_provided"}
        )
    
    async def _handle_service_consultation(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle service consultation and recommendations."""
        service_info = classification.get("extracted_info", {})
        situation = service_info.get("situation", "general")
        
        if situation == "move_out":
            response = """🏠 **MOVE-OUT CLEANING SPECIALIST**

Moving out? I've got you covered! Our move-out cleaning ensures you get your full deposit back.

**WHAT MAKES US DIFFERENT:**
✅ We know exactly what landlords/property managers look for
✅ Detailed cleaning checklist with photo documentation
✅ Inside appliances (oven, fridge, dishwasher)
✅ Deep cabinet and drawer cleaning
✅ Window sills, baseboards, and light fixtures
✅ Carpet shampooing available

**DEPOSIT GUARANTEE:** If you don't get your deposit back due to cleanliness issues we missed, we'll refund your service fee!

**PRICING:** Elite Listing Polish from $549 | Deep Reset (oven+fridge included) from $849
**TIMELINE:** Usually completed within 4-6 hours

📅 **BOOK NOW:** We're typically booked 1-2 weeks out for move-outs, so schedule early!

What's your move-out date? I can check our availability right now.

- Dean, CMO"""
        
        elif situation == "deep_clean":
            response = """🧽 **DEEP CLEANING EXPERT**

Ready for that "wow" feeling? Our deep cleaning service transforms your space!

**DEEP CLEAN INCLUDES:**
✅ All standard cleaning tasks PLUS:
✅ Inside oven and refrigerator
✅ Cabinet fronts and inside drawers
✅ Baseboards and window sills
✅ Light fixtures and ceiling fans
✅ Behind appliances (where accessible)
✅ Detailed bathroom tile and grout work

**PERFECT FOR:**
• Spring cleaning
• Post-renovation cleanup
• Preparing for special events
• Getting back on track with cleaning routine

**TIME INVESTMENT:** 6-8 hours for thorough deep clean
**FREQUENCY:** Most clients do this 2-3 times per year

**PRICING:** Elite Home Reset from $299 (under 2k sqft), $399 (2-3.5k), $549 (3.5-5k)

Ready to transform your space? What size property are we working with?

- Dean, CMO"""
        
        else:
            response = """🎯 **CLEANING CONSULTATION**

Let me recommend the perfect service for your needs!

**TELL ME MORE ABOUT:**
1. What's prompting the cleaning service need?
2. How often are you thinking? (one-time, weekly, monthly)
3. Any specific problem areas or concerns?
4. Timeline - when do you need this done?

**POPULAR OPTIONS:**
• **Standard Cleaning:** Regular maintenance, great for busy families
• **Deep Cleaning:** Intensive service, perfect for getting caught up
• **Move-out:** Deposit-back guarantee for renters
• **Office Cleaning:** Professional workspace maintenance

**FREE CONSULTATION:** I can also arrange a quick 15-minute call to discuss your specific needs and provide recommendations.

What sounds like the best fit for your situation?

- Dean, CMO"""
        
        return AgentResponse(
            agent_name="dean",
            response=response,
            confidence=0.88,
            metadata={"intent": "consultation_provided", "situation": situation}
        )
    
    async def _handle_lead_qualification(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle lead qualification and assessment."""
        response = """🎯 **LET'S FIND YOUR PERFECT CLEANING SOLUTION**

I'd love to help you find exactly what you need! Quick questions to give you the best recommendation:

**PROPERTY DETAILS:**
1. How many bedrooms and bathrooms?
2. Approximate square footage? (or just "small/medium/large house")
3. Any pets in the home?

**SERVICE PREFERENCES:**
4. What type of cleaning? (regular maintenance, deep clean, one-time, move-out)
5. How often would you want service?
6. Any specific areas of concern or special requests?

**TIMING:**
7. When would you like to start?
8. Any preferred day of the week?

**BUDGET:**
9. What's your target budget range?

💡 **THE MORE I KNOW, THE BETTER I CAN HELP!** Even if you only answer a few questions, I can provide a much more accurate quote and recommendation.

**NEXT STEP:** The more detail you give me, the more accurate the quote.

Ready to get started?

- Dean, CMO"""

        return AgentResponse(
            agent_name="dean",
            response=response,
            confidence=0.85,
            metadata={"intent": "lead_qualification", "questions_asked": 9}
        )
    
    async def _handle_upsell_opportunity(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle upselling and cross-selling opportunities."""
        existing_service = classification.get("current_service", "standard_cleaning")
        
        if existing_service == "standard_cleaning":
            response = """💎 **UPGRADE YOUR CLEANING EXPERIENCE**

Since you're already getting regular cleaning, have you considered our premium add-ons?

**POPULAR UPGRADES:**
✅ **Oven Interior** (+$100) - We'll make it sparkle!
✅ **Fridge Interior** (+$100) - Inside and out
✅ **Kitchen Perfection Bundle** (Fridge + Oven + Cabinets interior): $249 (save $51)
✅ **Garage Sweep-Out** (+$100)
✅ **Carpet Shampooing** (+$40/area) | **Window Tracks** (+$4/track)

**BUNDLE DEAL:** Add any 2 services and save $15!

**REFERRAL BONUS:** Refer a friend and you BOTH get $25 off your next service!

Want to add any of these to your next appointment?

- Dean, CMO"""
        
        else:
            response = """🌟 **MORE WAYS TO KEEP YOUR SPACE PERFECT**

Loved your recent service? Here are some ways to keep that fresh, clean feeling:

**REGULAR MAINTENANCE:** 
• Bi-weekly service: Save $10/visit
• Monthly service: Save $5/visit
• Quarterly deep cleans: Stay ahead of buildup

**ADDITIONAL SPACES:**
• Garage cleaning and organization
• Basement or attic cleaning
• Office or workspace cleaning

**SPECIAL OCCASIONS:**
• Pre-party cleaning service
• Post-party cleanup
• Holiday preparation cleaning

**GIFT CERTIFICATES:** Perfect for busy friends and family members!

Interested in setting up regular service or exploring any of these options?

- Dean, CMO"""
        
        return AgentResponse(
            agent_name="dean",
            response=response,
            confidence=0.82,
            metadata={"intent": "upsell_presented", "existing_service": existing_service}
        )
    
    async def _handle_general_sales_inquiry(self, context: MessageContext, classification: Dict[str, Any]) -> AgentResponse:
        """Handle general sales-related inquiries."""
        response = """👋 **HI FROM DEAN, YOUR GRIME GUARDIANS CMO!**

Great to hear from you! I'm here to help with all your cleaning service needs.

**WHAT I CAN HELP WITH:**
💰 Instant quotes and pricing
📋 Service recommendations
📅 Scheduling and availability
🎯 Custom cleaning plans
💡 Cleaning tips and advice

**WHY CHOOSE GRIME GUARDIANS:**
✅ BBB-accredited with 70+ five-star Google reviews
✅ Fully bonded and insured
✅ Eco-friendly products
✅ 100% satisfaction guarantee
✅ Flexible scheduling (including weekends)

**POSITIONING:** Premium service for clients who value time over money. BBB-accredited, 70+ five-star reviews.

What specific cleaning needs can I help you with today? Whether it's a quick quote, service questions, or scheduling - I'm your guy!

- Dean, CMO
"We clean like it's our name on the lease" ™"""

        return AgentResponse(
            agent_name="dean",
            response=response,
            confidence=0.75,
            metadata={"intent": "general_sales_assistance", "promotion_offered": True}
        )
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get Dean's sales performance metrics."""
        return {
            "quotes_generated": self.quotes_generated,
            "leads_converted": self.leads_converted,
            "revenue_generated": float(self.revenue_generated),
            "conversion_rate": self.conversion_rate,
            "average_quote_value": float(self.revenue_generated / max(self.quotes_generated, 1)),
            "specialization": "sales_and_marketing"
        }
    
    def update_conversion_metrics(self, converted: bool, revenue: Decimal = None):
        """Update conversion tracking metrics."""
        if converted:
            self.leads_converted += 1
            if revenue:
                self.revenue_generated += revenue
        
        # Calculate conversion rate
        total_interactions = self.message_count
        if total_interactions > 0:
            self.conversion_rate = self.leads_converted / total_interactions * 100


# Singleton instance
_dean_cmo_agent = None

def get_dean_cmo_agent() -> DeanCMOAgent:
    """Get singleton Dean CMO agent instance."""
    global _dean_cmo_agent
    if _dean_cmo_agent is None:
        _dean_cmo_agent = DeanCMOAgent()
    return _dean_cmo_agent