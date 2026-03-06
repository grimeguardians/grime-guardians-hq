"""
Message Classification System
CRITICAL: Preserve 90-95% accuracy from existing JavaScript system
Based on GPT-4o-mini integration patterns with context understanding
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from openai import AsyncOpenAI
import json

from ..models.types import MessageType, ServiceType, JobStatus, ViolationType
from ..models.schemas import AgentMessageSchema, AgentResponse
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MessageClassifier:
    """
    Message classification system preserving JavaScript accuracy.
    Uses GPT-4o-mini for cost-effective, high-accuracy classification.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Cost-effective while maintaining accuracy
        self.classification_cache = {}  # Simple in-memory cache
        
        # Business context for classification
        self.business_context = self._build_business_context()
        
    def _build_business_context(self) -> str:
        """Build business context for accurate classification."""
        return """
        BUSINESS CONTEXT - Grime Guardians Cleaning Service:
        
        SERVICES:
        - Move-out/Move-in cleaning ($300 base)
        - Deep cleaning ($180 base) 
        - Recurring maintenance ($120 base)
        - Post-construction ($0.35/sq ft)
        - Commercial cleaning (requires walkthrough)
        
        CONTRACTORS (1099 Independent):
        - Jennifer: South metro, $28/hr, reliable
        - Olga: East metro, $25/hr, deep clean specialist
        - Zhanna: Central metro, $25/hr, recurring clients
        - Liuda: North metro only, $30/hr, part-time
        
        QUALITY REQUIREMENTS:
        - Before/after photos (kitchen, bathrooms, entry, impacted rooms)
        - Checklist completion (move-in/out, deep cleaning, recurring)
        - 15-minute arrival buffer
        - 3-strike system for violations
        
        BUSINESS RULES:
        - All pricing includes 8.125% tax
        - Pet homes: +10%, Buildup: +20%
        - Contractor independence must be maintained (1099 status)
        - Premium service positioning - never apologize for pricing
        """
        
    async def classify_message(
        self,
        content: str,
        sender_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[MessageType, float, Dict[str, Any]]:
        """
        Classify message with high accuracy.
        
        Returns:
            Tuple of (message_type, confidence_score, extracted_data)
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(content, sender_info)
            if cache_key in self.classification_cache:
                cached_result = self.classification_cache[cache_key]
                logger.debug(f"Using cached classification for: {content[:50]}...")
                return cached_result
            
            # Build classification prompt
            classification_prompt = self._build_classification_prompt(content, sender_info, context)
            
            # Call GPT-4o-mini for classification
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=500,
                timeout=settings.openai_timeout
            )
            
            # Parse classification result
            result = self._parse_classification_response(response.choices[0].message.content)
            
            # Cache result
            self.classification_cache[cache_key] = result
            
            # Log classification for accuracy tracking
            logger.info(f"Message classified: {result[0].value} (confidence: {result[1]:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Message classification error: {e}")
            # Fallback to generic classification
            return MessageType.STATUS_UPDATE, 0.5, {"error": str(e)}
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for message classification."""
        return f"""
        You are an expert message classifier for Grime Guardians cleaning service.
        Your job is to accurately classify incoming messages and extract relevant data.
        
        {self.business_context}
        
        CLASSIFICATION TYPES:
        1. JOB_ASSIGNMENT - New cleaning job assignments
        2. STATUS_UPDATE - Check-ins, arrivals, completions
        3. QUALITY_VIOLATION - Missing photos, incomplete checklists, complaints
        4. PERFORMANCE_FEEDBACK - Coaching, training, skill development
        5. ESCALATION - Problems requiring immediate attention
        6. COMPLIANCE_CHECK - Contractor independence validation
        7. BONUS_CALCULATION - Referral bonuses, performance incentives
        8. ANALYTICS_REPORT - Performance data, KPI updates
        
        RESPONSE FORMAT (JSON):
        {{
            "message_type": "JOB_ASSIGNMENT",
            "confidence": 0.95,
            "extracted_data": {{
                "service_type": "move_out_in",
                "client_name": "John Smith",
                "address": "123 Main St",
                "contractor": "jennifer",
                "urgency": "normal"
            }}
        }}
        
        ACCURACY REQUIREMENTS:
        - Confidence must be 0.90+ for automatic processing
        - Extract all relevant business data
        - Consider context and sender information
        - Maintain 90-95% classification accuracy
        """
    
    def _build_classification_prompt(
        self,
        content: str,
        sender_info: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build classification prompt with context."""
        prompt_parts = [
            f"MESSAGE TO CLASSIFY: {content}",
        ]
        
        if sender_info:
            prompt_parts.append(f"SENDER INFO: {json.dumps(sender_info)}")
        
        if context:
            prompt_parts.append(f"CONTEXT: {json.dumps(context)}")
        
        prompt_parts.append("""
        INSTRUCTIONS:
        1. Classify the message type with high confidence
        2. Extract all relevant business data
        3. Consider the sender's role and context
        4. Maintain contractor independence in analysis
        5. Flag any compliance or quality issues
        6. Return valid JSON format only
        """)
        
        return "\n\n".join(prompt_parts)
    
    def _parse_classification_response(self, response_content: str) -> Tuple[MessageType, float, Dict[str, Any]]:
        """Parse GPT response into classification result."""
        try:
            # Extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_content = response_content[json_start:json_end]
            result = json.loads(json_content)
            
            # Validate required fields
            message_type = MessageType(result.get("message_type"))
            confidence = float(result.get("confidence", 0.0))
            extracted_data = result.get("extracted_data", {})
            
            # Validate confidence score
            if confidence < 0.0 or confidence > 1.0:
                logger.warning(f"Invalid confidence score: {confidence}")
                confidence = max(0.0, min(1.0, confidence))
            
            return message_type, confidence, extracted_data
            
        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
            # Return fallback classification
            return MessageType.STATUS_UPDATE, 0.5, {"parse_error": str(e)}
    
    def _generate_cache_key(self, content: str, sender_info: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for message."""
        import hashlib
        
        key_parts = [content]
        if sender_info:
            key_parts.append(json.dumps(sender_info, sort_keys=True))
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def classify_batch(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Tuple[MessageType, float, Dict[str, Any]]]:
        """Classify multiple messages efficiently."""
        tasks = []
        for msg in messages:
            task = self.classify_message(
                content=msg.get("content", ""),
                sender_info=msg.get("sender_info"),
                context=msg.get("context")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch classification error for message {i}: {result}")
                processed_results.append((MessageType.STATUS_UPDATE, 0.5, {"error": str(result)}))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def validate_classification_accuracy(
        self,
        test_messages: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Validate classification accuracy against known test set."""
        correct_predictions = 0
        total_predictions = 0
        confidence_sum = 0.0
        
        for test_msg in test_messages:
            expected_type = MessageType(test_msg["expected_type"])
            content = test_msg["content"]
            
            predicted_type, confidence, _ = await self.classify_message(content)
            
            total_predictions += 1
            confidence_sum += confidence
            
            if predicted_type == expected_type:
                correct_predictions += 1
            else:
                logger.warning(f"Misclassification: expected {expected_type}, got {predicted_type}")
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
        avg_confidence = confidence_sum / total_predictions if total_predictions > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "total_tested": total_predictions,
            "correct_predictions": correct_predictions,
            "average_confidence": avg_confidence,
            "meets_target": accuracy >= settings.target_classification_accuracy
        }
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        return {
            "cache_size": len(self.classification_cache),
            "model_used": self.model,
            "target_accuracy": settings.target_classification_accuracy,
            "business_context_length": len(self.business_context)
        }
    
    def clear_cache(self) -> None:
        """Clear classification cache."""
        self.classification_cache.clear()
        logger.info("Classification cache cleared")


class ContextThreadingManager:
    """
    Manage conversation context and threading.
    Preserves context understanding from JavaScript system.
    """
    
    def __init__(self):
        self.conversation_threads = {}  # thread_id -> messages
        self.max_thread_length = 50  # Limit thread length
        
    def add_message_to_thread(
        self,
        thread_id: str,
        message: AgentMessageSchema,
        classification: Tuple[MessageType, float, Dict[str, Any]]
    ) -> None:
        """Add message to conversation thread."""
        if thread_id not in self.conversation_threads:
            self.conversation_threads[thread_id] = []
        
        thread_message = {
            "timestamp": datetime.utcnow(),
            "message": message,
            "classification": classification,
            "agent_id": message.agent_id
        }
        
        self.conversation_threads[thread_id].append(thread_message)
        
        # Trim thread if too long
        if len(self.conversation_threads[thread_id]) > self.max_thread_length:
            self.conversation_threads[thread_id] = self.conversation_threads[thread_id][-self.max_thread_length:]
    
    def get_thread_context(self, thread_id: str, last_n: int = 10) -> List[Dict[str, Any]]:
        """Get recent thread context for classification."""
        if thread_id not in self.conversation_threads:
            return []
        
        return self.conversation_threads[thread_id][-last_n:]
    
    def get_thread_summary(self, thread_id: str) -> Dict[str, Any]:
        """Get thread summary for context."""
        if thread_id not in self.conversation_threads:
            return {}
        
        messages = self.conversation_threads[thread_id]
        
        return {
            "message_count": len(messages),
            "participants": list(set(msg["agent_id"] for msg in messages)),
            "message_types": list(set(msg["classification"][0] for msg in messages)),
            "first_message": messages[0]["timestamp"] if messages else None,
            "last_message": messages[-1]["timestamp"] if messages else None
        }


# Natural Language Feedback System
class NaturalLanguageFeedback:
    """
    Process natural language feedback for system improvement.
    Preserves adaptive learning from JavaScript system.
    """
    
    def __init__(self, classifier: MessageClassifier):
        self.classifier = classifier
        self.feedback_log = []
    
    async def process_feedback(
        self,
        message_content: str,
        actual_classification: MessageType,
        expected_classification: MessageType,
        feedback_text: str
    ) -> Dict[str, Any]:
        """Process natural language feedback for classification improvement."""
        feedback_entry = {
            "timestamp": datetime.utcnow(),
            "message_content": message_content,
            "actual_classification": actual_classification.value,
            "expected_classification": expected_classification.value,
            "feedback_text": feedback_text,
            "processed": False
        }
        
        self.feedback_log.append(feedback_entry)
        
        # Analyze feedback with AI
        analysis = await self._analyze_feedback(feedback_entry)
        feedback_entry["analysis"] = analysis
        feedback_entry["processed"] = True
        
        logger.info(f"Processed feedback for classification improvement: {feedback_text[:100]}...")
        
        return feedback_entry
    
    async def _analyze_feedback(self, feedback_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feedback to improve classification."""
        try:
            prompt = f"""
            Analyze this classification feedback and suggest improvements:
            
            MESSAGE: {feedback_entry['message_content']}
            ACTUAL: {feedback_entry['actual_classification']}
            EXPECTED: {feedback_entry['expected_classification']}
            FEEDBACK: {feedback_entry['feedback_text']}
            
            Provide specific suggestions for improving classification accuracy.
            """
            
            response = await self.classifier.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a classification system improvement analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return {
                "suggestions": response.choices[0].message.content,
                "analyzed_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Feedback analysis error: {e}")
            return {"error": str(e)}
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of feedback received."""
        if not self.feedback_log:
            return {"total_feedback": 0}
        
        processed_count = sum(1 for entry in self.feedback_log if entry["processed"])
        
        return {
            "total_feedback": len(self.feedback_log),
            "processed_feedback": processed_count,
            "latest_feedback": self.feedback_log[-1]["timestamp"] if self.feedback_log else None,
            "common_misclassifications": self._get_common_misclassifications()
        }
    
    def _get_common_misclassifications(self) -> List[Dict[str, Any]]:
        """Identify common misclassification patterns."""
        misclassification_counts = {}
        
        for entry in self.feedback_log:
            if entry["actual_classification"] != entry["expected_classification"]:
                key = f"{entry['actual_classification']}->{entry['expected_classification']}"
                misclassification_counts[key] = misclassification_counts.get(key, 0) + 1
        
        # Return top 5 most common misclassifications
        sorted_misclassifications = sorted(
            misclassification_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return [
            {"pattern": pattern, "count": count}
            for pattern, count in sorted_misclassifications
        ]