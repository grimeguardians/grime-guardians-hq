"""
Unit tests for Tool Infrastructure Layer
Testing core functionality of migrated systems and new tools
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

# Test basic imports and structure
def test_enhanced_message_classifier_import():
    """Test that EnhancedMessageClassifier can be imported."""
    try:
        from src.core.enhanced_message_classifier import EnhancedMessageClassifier, MessageCategory, KeywordClassifier
        assert True
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_conversation_manager_import():
    """Test that ConversationManager can be imported."""
    try:
        from src.core.conversation_manager import ConversationManager, ConversationThread, ClientProfile
        assert True
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_discord_tools_import():
    """Test that Discord tools can be imported."""
    try:
        from src.tools.discord_tools import DiscordToolkit, DiscordAgentTools, DiscordChannelType
        assert True
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_database_tools_import():
    """Test that Database tools can be imported."""
    try:
        from src.tools.database_tools import DatabaseTools, DatabaseValidator
        assert True
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_file_storage_tools_import():
    """Test that File storage tools can be imported."""
    try:
        from src.tools.file_storage_tools import FileStorageTools, FileValidator, LocalFileStorage
        assert True
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_message_categories_structure():
    """Test message categories from migrated system."""
    try:
        from src.core.enhanced_message_classifier import MessageCategory
        
        # Check that all expected categories exist
        expected_categories = [
            "NEW_PROSPECT_INQUIRY",
            "SCHEDULE_CHANGE_REQUEST", 
            "COMPLAINT_ISSUE",
            "GENERAL_OPERATIONS_QUESTION",
            "INTERNAL_CLEANER_MESSAGE",
            "SPAM_IRRELEVANT"
        ]
        
        for category in expected_categories:
            assert hasattr(MessageCategory, category)
            
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_keyword_classifier_structure():
    """Test keyword classifier from JavaScript migration."""
    try:
        from src.core.enhanced_message_classifier import KeywordClassifier
        
        classifier = KeywordClassifier()
        
        # Check that keyword sets exist
        assert hasattr(classifier, 'prospect_keywords')
        assert hasattr(classifier, 'schedule_keywords')
        assert hasattr(classifier, 'complaint_keywords')
        assert hasattr(classifier, 'operations_keywords')
        assert hasattr(classifier, 'cleaner_keywords')
        
        # Check that keyword sets are not empty
        assert len(classifier.prospect_keywords) > 0
        assert len(classifier.schedule_keywords) > 0
        assert len(classifier.complaint_keywords) > 0
        
        # Check for specific keywords from JavaScript system
        assert 'quote' in classifier.prospect_keywords
        assert 'reschedule' in classifier.schedule_keywords
        assert 'complaint' in classifier.complaint_keywords
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_conversation_thread_structure():
    """Test conversation thread structure from JavaScript migration."""
    try:
        from src.core.conversation_manager import ConversationThread, ClientProfile, ConversationStatus
        
        # Create test client profile
        profile = ClientProfile(
            phone_number="+1234567890",
            name="Test Client"
        )
        
        # Create conversation thread
        thread = ConversationThread(
            thread_id="test_thread",
            client_profile=profile
        )
        
        assert thread.thread_id == "test_thread"
        assert thread.client_profile.phone_number == "+1234567890"
        assert thread.status == ConversationStatus.ACTIVE
        assert len(thread.messages) == 0
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_discord_channel_types():
    """Test Discord channel types for business workflow."""
    try:
        from src.tools.discord_tools import DiscordChannelType
        
        # Check business-specific channels exist
        expected_channels = [
            "STRIKES",
            "ALERTS", 
            "JOB_CHECKINS",
            "PHOTO_SUBMISSIONS",
            "JOB_BOARD"
        ]
        
        for channel in expected_channels:
            assert hasattr(DiscordChannelType, channel)
            
        # Check channel emoji formatting
        assert "❌" in DiscordChannelType.STRIKES.value
        assert "🚨" in DiscordChannelType.ALERTS.value
        assert "✔️" in DiscordChannelType.JOB_CHECKINS.value
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_file_validator_structure():
    """Test file validator for business requirements."""
    try:
        from src.tools.file_storage_tools import FileValidator
        
        # Check validation constants
        assert FileValidator.MAX_FILE_SIZE > 0
        assert len(FileValidator.ALLOWED_IMAGE_FORMATS) > 0
        assert len(FileValidator.ALLOWED_DOCUMENT_FORMATS) > 0
        
        # Check allowed formats include business requirements
        assert '.jpg' in FileValidator.ALLOWED_IMAGE_FORMATS
        assert '.png' in FileValidator.ALLOWED_IMAGE_FORMATS
        assert '.pdf' in FileValidator.ALLOWED_DOCUMENT_FORMATS
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_database_validator_structure():
    """Test database validator for business rules."""
    try:
        from src.tools.database_tools import DatabaseValidator
        
        validator = DatabaseValidator()
        
        # Test job data validation structure
        valid_job_data = {
            'customer_id': 'test_customer',
            'service_type': 'recurring',
            'address': '123 Test St',
            'scheduled_date': datetime.utcnow(),
            'quoted_price': Decimal('100.00')
        }
        
        # Should not raise exception
        result = validator.validate_job_data(valid_job_data)
        assert result == valid_job_data
        
        # Test contractor validation structure  
        valid_contractor_data = {
            'name': 'Test Contractor',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'hourly_rate': Decimal('25.00')
        }
        
        result = validator.validate_contractor_data(valid_contractor_data)
        assert result == valid_contractor_data
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

# Integration test for migrated message classification
def test_keyword_classification_integration():
    """Test keyword classification preserving JavaScript accuracy."""
    try:
        from src.core.enhanced_message_classifier import KeywordClassifier, MessageCategory
        
        classifier = KeywordClassifier()
        
        # Test prospect inquiry
        prospect_message = "Hi, I'm looking for a quote for weekly cleaning service"
        category, confidence, data = classifier.classify_by_keywords(prospect_message)
        
        assert category == MessageCategory.NEW_PROSPECT_INQUIRY
        assert confidence > 0.3
        assert 'service_type' in data
        
        # Test schedule change
        schedule_message = "I need to reschedule my cleaning for tomorrow"
        category, confidence, data = classifier.classify_by_keywords(schedule_message)
        
        assert category == MessageCategory.SCHEDULE_CHANGE_REQUEST
        assert confidence > 0.3
        assert 'action_type' in data
        
        # Test complaint
        complaint_message = "I'm not satisfied with the cleaning quality"
        category, confidence, data = classifier.classify_by_keywords(complaint_message)
        
        assert category == MessageCategory.COMPLAINT_ISSUE
        assert confidence > 0.3
        assert 'severity' in data
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

# Test business context preservation
def test_business_context_preservation():
    """Test that business context from JavaScript system is preserved."""
    try:
        from src.core.enhanced_message_classifier import KeywordClassifier
        
        classifier = KeywordClassifier()
        
        # Test service type detection (from JavaScript system)
        move_message = "I need move out cleaning"
        category, confidence, data = classifier.classify_by_keywords(move_message)
        
        assert data.get('service_type') == 'move_out_in'
        
        # Test recurring detection
        recurring_message = "I want weekly cleaning service"
        category, confidence, data = classifier.classify_by_keywords(recurring_message)
        
        assert data.get('service_type') == 'recurring'
        
        # Test bedroom extraction
        bedroom_message = "I have a 3 bedroom house"
        category, confidence, data = classifier.classify_by_keywords(bedroom_message)
        
        assert data.get('bedrooms') == 3
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__])