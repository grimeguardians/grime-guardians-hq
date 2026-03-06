"""
Message Classification Tools for C-Suite Agents
Advanced classification methods for sales, customer experience, and executive matters
"""

import logging
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class MessageClassificationTool(BaseTool):
    """Enhanced message classification tool for C-Suite agent specializations."""
    
    def __init__(self):
        super().__init__(
            name="message_classification",
            description="Advanced message classification for sales, CX, and executive matters"
        )
        
        # Sales intent patterns for Dean CMO
        self.sales_patterns = {
            "quote_request": [
                r"quote", r"price", r"cost", r"how much", r"estimate", r"pricing",
                r"what would it cost", r"can you give me a price", r"ballpark"
            ],
            "pricing_inquiry": [
                r"rates", r"pricing guide", r"price list", r"what do you charge",
                r"standard rates", r"typical cost", r"average price"
            ],
            "service_consultation": [
                r"what service", r"which cleaning", r"recommend", r"best option",
                r"deep clean", r"move out", r"office clean", r"what type"
            ],
            "lead_qualification": [
                r"interested in", r"looking for", r"need cleaning", r"first time",
                r"new customer", r"tell me about", r"how does this work"
            ],
            "upsell_opportunity": [
                r"additional", r"extra", r"more", r"also need", r"what else",
                r"upgrade", r"premium", r"add on"
            ]
        }
        
        # Customer experience patterns for Emma CXO
        self.experience_patterns = {
            "complaint": [
                r"disappointed", r"unhappy", r"terrible", r"awful", r"horrible",
                r"not satisfied", r"poor", r"bad", r"worst", r"problem"
            ],
            "service_issue": [
                r"missed", r"didn't clean", r"not done", r"incomplete", r"forgot",
                r"left out", r"quality", r"not good", r"issue with"
            ],
            "feedback": [
                r"feedback", r"comment", r"suggestion", r"review", r"rating",
                r"thoughts", r"opinion", r"experience"
            ],
            "support_request": [
                r"help", r"question", r"support", r"assistance", r"clarify",
                r"explain", r"understand", r"confused"
            ],
            "follow_up": [
                r"how was", r"satisfaction", r"follow up", r"check in",
                r"everything ok", r"went well"
            ],
            "refund_request": [
                r"refund", r"money back", r"return", r"cancel", r"undo payment",
                r"charge back", r"dispute"
            ]
        }
        
        # Executive matter patterns for Brandon CEO
        self.executive_patterns = {
            "crisis": [
                r"emergency", r"urgent", r"crisis", r"serious problem", r"major issue",
                r"lawsuit", r"legal action", r"media", r"reputation", r"scandal"
            ],
            "vip_account": [
                r"property management", r"corporate account", r"bulk", r"commercial",
                r"high value", r"important client", r"regular customer"
            ],
            "partnership": [
                r"partnership", r"business opportunity", r"collaboration", r"work together",
                r"referral program", r"corporate", r"vendor"
            ],
            "legal": [
                r"legal", r"lawyer", r"attorney", r"court", r"lawsuit", r"liability",
                r"insurance claim", r"damages", r"compensation"
            ],
            "executive_escalation": [
                r"escalate", r"manager", r"supervisor", r"complaint", r"unresolved",
                r"speak to someone in charge", r"higher up"
            ],
            "strategic_decision": [
                r"policy", r"company decision", r"strategic", r"direction", r"vision",
                r"future", r"expansion", r"growth"
            ]
        }
        
        # Sentiment indicators
        self.sentiment_patterns = {
            "positive": [
                r"great", r"excellent", r"amazing", r"wonderful", r"fantastic",
                r"love", r"perfect", r"outstanding", r"impressed", r"happy"
            ],
            "negative": [
                r"terrible", r"awful", r"horrible", r"hate", r"disgusted",
                r"angry", r"frustrated", r"disappointed", r"worst", r"never again"
            ],
            "neutral": [
                r"ok", r"fine", r"average", r"decent", r"alright", r"normal"
            ]
        }
        
        # Urgency indicators
        self.urgency_patterns = {
            "high": [
                r"urgent", r"emergency", r"asap", r"immediately", r"right now",
                r"today", r"crisis", r"critical"
            ],
            "medium": [
                r"soon", r"this week", r"quickly", r"priority", r"important"
            ],
            "low": [
                r"whenever", r"no rush", r"eventually", r"when convenient"
            ]
        }

    async def classify_sales_intent(self, message: str, sender_phone: str = None) -> Dict[str, Any]:
        """Classify message for sales intent (Dean CMO)."""
        try:
            message_lower = message.lower()
            
            # Detect sales intent
            intent = "general"
            max_confidence = 0.0
            
            for intent_type, patterns in self.sales_patterns.items():
                confidence = self._calculate_pattern_confidence(message_lower, patterns)
                if confidence > max_confidence:
                    max_confidence = confidence
                    intent = intent_type
            
            # Extract service details
            extracted_info = self._extract_service_details(message_lower)
            
            # Determine urgency
            urgency = self._detect_urgency(message_lower)
            
            return {
                "intent": intent,
                "confidence": max_confidence,
                "extracted_info": extracted_info,
                "urgency": urgency,
                "classification_type": "sales"
            }
            
        except Exception as e:
            logger.error(f"Sales intent classification error: {e}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "extracted_info": {},
                "urgency": "normal",
                "error": str(e)
            }

    async def classify_customer_experience(self, message: str, sender_phone: str = None) -> Dict[str, Any]:
        """Classify message for customer experience (Emma CXO)."""
        try:
            message_lower = message.lower()
            
            # Detect CX intent
            intent = "general"
            max_confidence = 0.0
            
            for intent_type, patterns in self.experience_patterns.items():
                confidence = self._calculate_pattern_confidence(message_lower, patterns)
                if confidence > max_confidence:
                    max_confidence = confidence
                    intent = intent_type
            
            # Detect sentiment
            sentiment = self._detect_sentiment(message_lower)
            
            # Determine urgency
            urgency = self._detect_urgency(message_lower)
            
            # Extract issue details
            issue_details = self._extract_issue_details(message_lower)
            
            return {
                "intent": intent,
                "confidence": max_confidence,
                "sentiment": sentiment,
                "urgency": urgency,
                "issue_details": issue_details,
                "classification_type": "customer_experience"
            }
            
        except Exception as e:
            logger.error(f"Customer experience classification error: {e}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "sentiment": "neutral",
                "urgency": "normal",
                "error": str(e)
            }

    async def classify_executive_matter(self, message: str, sender_phone: str = None) -> Dict[str, Any]:
        """Classify message for executive matters (Brandon CEO)."""
        try:
            message_lower = message.lower()
            
            # Detect executive matter type
            matter_type = "general"
            max_confidence = 0.0
            
            for matter_type_key, patterns in self.executive_patterns.items():
                confidence = self._calculate_pattern_confidence(message_lower, patterns)
                if confidence > max_confidence:
                    max_confidence = confidence
                    matter_type = matter_type_key
            
            # Determine escalation level
            escalation_level = self._determine_escalation_level(message_lower, matter_type)
            
            # Determine urgency
            urgency = self._detect_urgency(message_lower)
            
            # Extract strategic details
            strategic_details = self._extract_strategic_details(message_lower)
            
            return {
                "matter_type": matter_type,
                "confidence": max_confidence,
                "escalation_level": escalation_level,
                "urgency": urgency,
                "strategic_details": strategic_details,
                "classification_type": "executive"
            }
            
        except Exception as e:
            logger.error(f"Executive matter classification error: {e}")
            return {
                "matter_type": "unknown",
                "confidence": 0.0,
                "escalation_level": "low",
                "urgency": "normal",
                "error": str(e)
            }

    def _calculate_pattern_confidence(self, message: str, patterns: List[str]) -> float:
        """Calculate confidence score based on pattern matching."""
        matches = 0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                matches += 1
        
        # Base confidence on match ratio
        base_confidence = matches / total_patterns if total_patterns > 0 else 0.0
        
        # Boost confidence if multiple patterns match
        if matches > 1:
            base_confidence = min(base_confidence + 0.2, 1.0)
        
        return round(base_confidence, 2)

    def _extract_service_details(self, message: str) -> Dict[str, Any]:
        """Extract service details from sales messages."""
        details = {}
        
        # Extract bedrooms
        bedroom_match = re.search(r'(\d+)\s*bed', message)
        if bedroom_match:
            details["bedrooms"] = int(bedroom_match.group(1))
        
        # Extract bathrooms
        bathroom_match = re.search(r'(\d+)\s*bath', message)
        if bathroom_match:
            details["bathrooms"] = int(bathroom_match.group(1))
        
        # Extract square footage
        sqft_match = re.search(r'(\d+)\s*sq\s*ft|(\d+)\s*square\s*feet', message)
        if sqft_match:
            details["square_footage"] = int(sqft_match.group(1) or sqft_match.group(2))
        
        # Detect service types
        if any(word in message for word in ["deep", "spring", "thorough"]):
            details["service_type"] = "deep_cleaning"
        elif any(word in message for word in ["move", "moving", "move-out"]):
            details["service_type"] = "move_out"
        elif any(word in message for word in ["office", "commercial", "business"]):
            details["service_type"] = "office_cleaning"
        else:
            details["service_type"] = "standard_cleaning"
        
        # Detect pets
        if any(word in message for word in ["pet", "dog", "cat", "animal"]):
            details["pets"] = True
        
        return details

    def _extract_issue_details(self, message: str) -> Dict[str, Any]:
        """Extract issue details from customer experience messages."""
        details = {}
        
        # Determine issue type
        if any(word in message for word in ["quality", "clean", "dirty", "missed"]):
            details["issue_type"] = "service_quality"
        elif any(word in message for word in ["schedule", "time", "late", "early"]):
            details["issue_type"] = "scheduling"
        elif any(word in message for word in ["billing", "charge", "payment", "cost"]):
            details["issue_type"] = "billing"
        elif any(word in message for word in ["staff", "team", "rude", "unprofessional"]):
            details["issue_type"] = "staff_behavior"
        else:
            details["issue_type"] = "general"
        
        # Determine severity
        if any(word in message for word in ["terrible", "awful", "worst", "horrible"]):
            details["severity"] = "high"
        elif any(word in message for word in ["disappointing", "poor", "bad"]):
            details["severity"] = "medium"
        else:
            details["severity"] = "low"
        
        return details

    def _extract_strategic_details(self, message: str) -> Dict[str, Any]:
        """Extract strategic details from executive messages."""
        details = {}
        
        # Detect partnership type
        if any(word in message for word in ["property", "management", "real estate"]):
            details["partnership_type"] = "property_management"
        elif any(word in message for word in ["commercial", "business", "corporate"]):
            details["partnership_type"] = "commercial"
        elif any(word in message for word in ["referral", "network", "vendor"]):
            details["partnership_type"] = "referral_network"
        
        # Detect crisis type
        if any(word in message for word in ["legal", "lawsuit", "court"]):
            details["crisis_type"] = "legal"
        elif any(word in message for word in ["media", "reputation", "public"]):
            details["crisis_type"] = "reputation"
        elif any(word in message for word in ["emergency", "urgent", "critical"]):
            details["crisis_type"] = "operational"
        
        return details

    def _detect_sentiment(self, message: str) -> str:
        """Detect sentiment in message."""
        sentiment_scores = {}
        
        for sentiment, patterns in self.sentiment_patterns.items():
            score = self._calculate_pattern_confidence(message, patterns)
            sentiment_scores[sentiment] = score
        
        # Return sentiment with highest score
        max_sentiment = max(sentiment_scores.items(), key=lambda x: x[1])
        return max_sentiment[0] if max_sentiment[1] > 0 else "neutral"

    def _detect_urgency(self, message: str) -> str:
        """Detect urgency level in message."""
        urgency_scores = {}
        
        for urgency, patterns in self.urgency_patterns.items():
            score = self._calculate_pattern_confidence(message, patterns)
            urgency_scores[urgency] = score
        
        # Return urgency with highest score
        max_urgency = max(urgency_scores.items(), key=lambda x: x[1])
        return max_urgency[0] if max_urgency[1] > 0 else "normal"

    def _determine_escalation_level(self, message: str, matter_type: str) -> str:
        """Determine escalation level for executive matters."""
        if matter_type == "crisis":
            return "critical"
        elif matter_type in ["legal", "vip_account"]:
            return "high"
        elif matter_type in ["partnership", "executive_escalation"]:
            return "medium"
        else:
            return "low"