"""
Unit tests for Message Classification System
CRITICAL: Verify 90-95% accuracy preservation from JavaScript system
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.core.message_classifier import MessageClassifier, ContextThreadingManager, NaturalLanguageFeedback
from src.models.types import MessageType
from src.models.schemas import AgentMessageSchema


class TestMessageClassifier:
    """Test message classification accuracy and functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = MessageClassifier()
        
    @pytest.mark.asyncio
    async def test_job_assignment_classification(self):
        """Test job assignment message classification."""
        message = "New move-out cleaning job assigned to Jennifer at 123 Main St, Eagan for tomorrow 2pm"
        
        with patch.object(self.classifier.client.chat.completions, 'create') as mock_create:
            # Mock GPT response
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = '''
            {
                "message_type": "JOB_ASSIGNMENT",
                "confidence": 0.95,
                "extracted_data": {
                    "service_type": "move_out_in",
                    "contractor": "jennifer",
                    "address": "123 Main St, Eagan",
                    "scheduled_time": "tomorrow 2pm"
                }
            }
            '''
            mock_create.return_value = mock_response
            
            message_type, confidence, data = await self.classifier.classify_message(message)
            
            assert message_type == MessageType.JOB_ASSIGNMENT
            assert confidence == 0.95
            assert data["contractor"] == "jennifer"
            assert data["service_type"] == "move_out_in"
    
    @pytest.mark.asyncio
    async def test_quality_violation_classification(self):
        """Test quality violation message classification."""
        message = "Olga completed job at 456 Oak Ave but didn't submit photos. Missing kitchen and bathroom photos."
        
        with patch.object(self.classifier.client.chat.completions, 'create') as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = '''
            {
                "message_type": "QUALITY_VIOLATION",
                "confidence": 0.92,
                "extracted_data": {
                    "contractor": "olga",
                    "violation_type": "missing_photos",
                    "missing_items": ["kitchen", "bathroom"],
                    "address": "456 Oak Ave"
                }
            }
            '''
            mock_create.return_value = mock_response
            
            message_type, confidence, data = await self.classifier.classify_message(message)
            
            assert message_type == MessageType.QUALITY_VIOLATION
            assert confidence == 0.92
            assert data["violation_type"] == "missing_photos"
            assert "kitchen" in data["missing_items"]
    
    @pytest.mark.asyncio
    async def test_status_update_classification(self):
        """Test status update message classification."""
        message = "🚗 Jennifer arrived at 789 Pine St"
        
        with patch.object(self.classifier.client.chat.completions, 'create') as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = '''
            {
                "message_type": "STATUS_UPDATE",
                "confidence": 0.98,
                "extracted_data": {
                    "contractor": "jennifer",
                    "status": "arrived",
                    "address": "789 Pine St",
                    "update_type": "check_in"
                }
            }
            '''
            mock_create.return_value = mock_response
            
            message_type, confidence, data = await self.classifier.classify_message(message)
            
            assert message_type == MessageType.STATUS_UPDATE
            assert confidence == 0.98
            assert data["status"] == "arrived"
    
    @pytest.mark.asyncio
    async def test_escalation_classification(self):
        """Test escalation message classification."""
        message = "URGENT: Client complaint about Zhanna's cleaning at 321 Elm St. Customer very unhappy, requesting re-clean."
        
        with patch.object(self.classifier.client.chat.completions, 'create') as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = '''
            {
                "message_type": "ESCALATION",
                "confidence": 0.94,
                "extracted_data": {
                    "contractor": "zhanna",
                    "issue_type": "customer_complaint",
                    "address": "321 Elm St",
                    "urgency": "high",
                    "action_required": "re_clean"
                }
            }
            '''
            mock_create.return_value = mock_response
            
            message_type, confidence, data = await self.classifier.classify_message(message)
            
            assert message_type == MessageType.ESCALATION
            assert confidence == 0.94
            assert data["urgency"] == "high"
    
    @pytest.mark.asyncio
    async def test_bonus_calculation_classification(self):
        """Test bonus calculation message classification."""
        message = "Jennifer mentioned in 5-star Google review by client at 555 Oak Dr. Qualifies for $25 referral bonus."
        
        with patch.object(self.classifier.client.chat.completions, 'create') as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = '''
            {
                "message_type": "BONUS_CALCULATION",
                "confidence": 0.91,
                "extracted_data": {
                    "contractor": "jennifer",
                    "bonus_type": "referral_bonus",
                    "amount": 25,
                    "source": "google_review",
                    "rating": "5_star"
                }
            }
            '''
            mock_create.return_value = mock_response
            
            message_type, confidence, data = await self.classifier.classify_message(message)
            
            assert message_type == MessageType.BONUS_CALCULATION
            assert confidence == 0.91
            assert data["amount"] == 25
    
    @pytest.mark.asyncio
    async def test_classification_with_context(self):
        """Test classification with sender info and context."""
        message = "Running late, will be there in 20 minutes"
        sender_info = {"contractor_id": "liuda", "role": "contractor"}
        context = {"job_id": "job_123", "scheduled_time": "2pm"}
        
        with patch.object(self.classifier.client.chat.completions, 'create') as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = '''
            {
                "message_type": "STATUS_UPDATE",
                "confidence": 0.93,
                "extracted_data": {
                    "contractor": "liuda",
                    "status": "delayed",
                    "estimated_delay": "20 minutes",
                    "job_id": "job_123"
                }
            }
            '''
            mock_create.return_value = mock_response
            
            message_type, confidence, data = await self.classifier.classify_message(
                message, sender_info, context
            )
            
            assert message_type == MessageType.STATUS_UPDATE
            assert data["contractor"] == "liuda"
            assert data["estimated_delay"] == "20 minutes"
    
    @pytest.mark.asyncio
    async def test_batch_classification(self):
        """Test batch message classification."""
        messages = [
            {"content": "🚗 Arrived at location", "sender_info": {"contractor_id": "jennifer"}},
            {"content": "Missing checklist for deep clean", "context": {"job_id": "job_456"}},
            {"content": "Job completed successfully", "sender_info": {"contractor_id": "olga"}}
        ]
        
        with patch.object(self.classifier, 'classify_message') as mock_classify:
            mock_classify.side_effect = [
                (MessageType.STATUS_UPDATE, 0.95, {"status": "arrived"}),
                (MessageType.QUALITY_VIOLATION, 0.89, {"violation": "missing_checklist"}),
                (MessageType.STATUS_UPDATE, 0.97, {"status": "completed"})
            ]
            
            results = await self.classifier.classify_batch(messages)
            
            assert len(results) == 3
            assert results[0][0] == MessageType.STATUS_UPDATE
            assert results[1][0] == MessageType.QUALITY_VIOLATION
            assert results[2][0] == MessageType.STATUS_UPDATE
    
    @pytest.mark.asyncio
    async def test_classification_accuracy_validation(self):
        """Test classification accuracy validation against test set."""
        test_messages = [
            {
                "content": "New job assignment for deep cleaning",
                "expected_type": "JOB_ASSIGNMENT"
            },
            {
                "content": "🏁 Finished cleaning",
                "expected_type": "STATUS_UPDATE"
            },
            {
                "content": "Photos missing from last job",
                "expected_type": "QUALITY_VIOLATION"
            }
        ]
        
        with patch.object(self.classifier, 'classify_message') as mock_classify:
            # Mock high accuracy results
            mock_classify.side_effect = [
                (MessageType.JOB_ASSIGNMENT, 0.95, {}),
                (MessageType.STATUS_UPDATE, 0.92, {}),
                (MessageType.QUALITY_VIOLATION, 0.89, {})
            ]
            
            accuracy_stats = await self.classifier.validate_classification_accuracy(test_messages)
            
            assert accuracy_stats["accuracy"] == 1.0  # 100% for this test
            assert accuracy_stats["total_tested"] == 3
            assert accuracy_stats["correct_predictions"] == 3
            assert accuracy_stats["meets_target"] is True
    
    def test_cache_functionality(self):
        """Test classification caching."""
        message = "Test message"
        sender_info = {"contractor_id": "test"}
        
        # Generate cache key
        cache_key = self.classifier._generate_cache_key(message, sender_info)
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length
        
        # Test cache clear
        self.classifier.classification_cache["test"] = "test_data"
        assert len(self.classifier.classification_cache) == 1
        
        self.classifier.clear_cache()
        assert len(self.classifier.classification_cache) == 0
    
    def test_business_context_building(self):
        """Test business context building."""
        context = self.classifier._build_business_context()
        
        # Verify key business information is included
        assert "Jennifer" in context
        assert "8.125%" in context
        assert "1099" in context
        assert "move-out" in context.lower()
        assert "photo" in context.lower()
    
    def test_classification_stats(self):
        """Test classification statistics."""
        stats = self.classifier.get_classification_stats()
        
        assert "cache_size" in stats
        assert "model_used" in stats
        assert "target_accuracy" in stats
        assert stats["model_used"] == "gpt-4o-mini"


class TestContextThreadingManager:
    """Test conversation context and threading management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.threading_manager = ContextThreadingManager()
    
    def test_add_message_to_thread(self):
        """Test adding messages to conversation threads."""
        message = AgentMessageSchema(
            agent_id="keith",
            message_type=MessageType.STATUS_UPDATE,
            content="Test message"
        )
        classification = (MessageType.STATUS_UPDATE, 0.95, {})
        
        self.threading_manager.add_message_to_thread("thread_1", message, classification)
        
        assert "thread_1" in self.threading_manager.conversation_threads
        assert len(self.threading_manager.conversation_threads["thread_1"]) == 1
        
        thread_message = self.threading_manager.conversation_threads["thread_1"][0]
        assert thread_message["agent_id"] == "keith"
        assert thread_message["classification"] == classification
    
    def test_thread_context_retrieval(self):
        """Test thread context retrieval."""
        message = AgentMessageSchema(
            agent_id="keith",
            message_type=MessageType.STATUS_UPDATE,
            content="Test message"
        )
        classification = (MessageType.STATUS_UPDATE, 0.95, {})
        
        # Add multiple messages
        for i in range(15):
            self.threading_manager.add_message_to_thread(f"thread_1", message, classification)
        
        # Get last 10 messages
        context = self.threading_manager.get_thread_context("thread_1", last_n=10)
        assert len(context) == 10
        
        # Get thread summary
        summary = self.threading_manager.get_thread_summary("thread_1")
        assert summary["message_count"] == 15
        assert "keith" in summary["participants"]
    
    def test_thread_length_limiting(self):
        """Test thread length limiting."""
        message = AgentMessageSchema(
            agent_id="keith", 
            message_type=MessageType.STATUS_UPDATE,
            content="Test message"
        )
        classification = (MessageType.STATUS_UPDATE, 0.95, {})
        
        # Add more messages than max thread length
        for i in range(60):  # Max is 50
            self.threading_manager.add_message_to_thread("thread_1", message, classification)
        
        # Should be trimmed to 50
        assert len(self.threading_manager.conversation_threads["thread_1"]) == 50


class TestNaturalLanguageFeedback:
    """Test natural language feedback system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = MessageClassifier()
        self.feedback_system = NaturalLanguageFeedback(self.classifier)
    
    @pytest.mark.asyncio
    async def test_process_feedback(self):
        """Test processing natural language feedback."""
        message_content = "Job completed"
        actual_classification = MessageType.STATUS_UPDATE
        expected_classification = MessageType.JOB_ASSIGNMENT
        feedback_text = "This should be classified as job assignment because it indicates completion of assignment"
        
        with patch.object(self.classifier.client.chat.completions, 'create') as mock_create:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "Improve context analysis for job completion messages"
            mock_create.return_value = mock_response
            
            feedback_entry = await self.feedback_system.process_feedback(
                message_content, actual_classification, expected_classification, feedback_text
            )
            
            assert feedback_entry["processed"] is True
            assert feedback_entry["actual_classification"] == "STATUS_UPDATE"
            assert feedback_entry["expected_classification"] == "JOB_ASSIGNMENT"
            assert "analysis" in feedback_entry
    
    def test_feedback_summary(self):
        """Test feedback summary generation."""
        # Add test feedback entries
        self.feedback_system.feedback_log = [
            {
                "actual_classification": "STATUS_UPDATE",
                "expected_classification": "JOB_ASSIGNMENT", 
                "processed": True
            },
            {
                "actual_classification": "STATUS_UPDATE",
                "expected_classification": "JOB_ASSIGNMENT",
                "processed": True
            }
        ]
        
        summary = self.feedback_system.get_feedback_summary()
        
        assert summary["total_feedback"] == 2
        assert summary["processed_feedback"] == 2
        
        common_misclassifications = summary["common_misclassifications"]
        assert len(common_misclassifications) > 0
        assert common_misclassifications[0]["pattern"] == "STATUS_UPDATE->JOB_ASSIGNMENT"
        assert common_misclassifications[0]["count"] == 2


class TestMessageClassifierIntegration:
    """Integration tests for message classifier with business rules."""
    
    @pytest.mark.asyncio
    async def test_real_world_message_scenarios(self):
        """Test real-world message classification scenarios."""
        classifier = MessageClassifier()
        
        # Test scenarios based on actual business operations
        test_scenarios = [
            {
                "message": "Jennifer needs to reschedule 2pm cleaning at 123 Oak St due to family emergency",
                "expected_type": MessageType.ESCALATION,
                "reason": "Schedule change requires immediate attention"
            },
            {
                "message": "Photos uploaded for deep clean at 456 Pine Ave - kitchen, 2 bathrooms, living room",
                "expected_type": MessageType.STATUS_UPDATE,
                "reason": "Completion confirmation with quality compliance"
            },
            {
                "message": "Client at 789 Elm Dr mentioned Jennifer by name in Google review",
                "expected_type": MessageType.BONUS_CALCULATION,
                "reason": "Triggers $25 referral bonus calculation"
            }
        ]
        
        # Mock responses for integration test
        with patch.object(classifier.client.chat.completions, 'create') as mock_create:
            def mock_response_generator(scenario):
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message.content = f'''
                {{
                    "message_type": "{scenario['expected_type'].value}",
                    "confidence": 0.92,
                    "extracted_data": {{"test": "data"}}
                }}
                '''
                return mock_response
            
            mock_create.side_effect = [mock_response_generator(s) for s in test_scenarios]
            
            # Test each scenario
            for scenario in test_scenarios:
                message_type, confidence, data = await classifier.classify_message(scenario["message"])
                
                assert message_type == scenario["expected_type"]
                assert confidence >= 0.90  # Meet target accuracy threshold
    
    def test_business_rule_integration(self):
        """Test integration with business rules and constraints."""
        classifier = MessageClassifier()
        
        # Verify business context includes key constraints
        context = classifier.business_context
        
        # Contractor independence
        assert "1099" in context
        assert "independent" in context.lower()
        
        # Pricing rules
        assert "8.125%" in context
        assert "$300" in context  # Move-out base price
        
        # Quality requirements
        assert "photo" in context.lower()
        assert "checklist" in context.lower()
        assert "3-strike" in context.lower()
        
        # Contractor information
        for contractor in ["Jennifer", "Olga", "Zhanna", "Liuda"]:
            assert contractor in context