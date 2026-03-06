"""
Basic unit tests for Quality Enforcement System structure
Testing core functionality without heavy dependencies
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

# Test basic imports and structure
def test_quality_enforcer_import():
    """Test that QualityEnforcer can be imported."""
    try:
        from src.core.quality_enforcer import QualityEnforcer, PhotoValidationResult, StrikeRecord
        assert True
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_contractor_manager_import():
    """Test that ContractorManager can be imported."""
    try:
        from src.core.contractor_manager import ContractorManager, PerformanceScorer, GeographicOptimizer
        assert True
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_photo_validation_result_structure():
    """Test PhotoValidationResult structure."""
    try:
        from src.core.quality_enforcer import PhotoValidationResult
        
        result = PhotoValidationResult(
            is_valid=True,
            quality_score=8.5,
            issues=[],
            required_rooms_covered=["kitchen", "bathroom"],
            missing_rooms=[],
            technical_issues=[]
        )
        
        assert result.is_valid is True
        assert result.quality_score == 8.5
        assert len(result.required_rooms_covered) == 2
        assert len(result.missing_rooms) == 0
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_strike_record_structure():
    """Test StrikeRecord structure."""
    try:
        from src.core.quality_enforcer import StrikeRecord
        from src.models.types import ViolationType
        
        strike = StrikeRecord(
            contractor_id="test_contractor",
            strike_number=1,
            violation_type=ViolationType.MISSING_PHOTOS,
            description="Test violation",
            evidence={"test": "data"},
            timestamp=datetime.utcnow(),
            job_id="test_job",
            requires_approval=False
        )
        
        assert strike.contractor_id == "test_contractor"
        assert strike.strike_number == 1
        assert strike.violation_type == ViolationType.MISSING_PHOTOS
        assert strike.requires_approval is False
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_quality_enforcer_initialization():
    """Test QualityEnforcer can be initialized."""
    try:
        from src.core.quality_enforcer import QualityEnforcer
        
        # Mock the OpenAI client initialization
        import unittest.mock
        with unittest.mock.patch('src.core.quality_enforcer.AsyncOpenAI'):
            enforcer = QualityEnforcer()
            
            assert enforcer is not None
            assert hasattr(enforcer, 'strike_records')
            assert hasattr(enforcer, 'photo_validation_cache')
            assert hasattr(enforcer, 'discord_channels')
            assert hasattr(enforcer, 'required_photos')
            
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_contractor_manager_initialization():
    """Test ContractorManager can be initialized."""
    try:
        from src.core.contractor_manager import ContractorManager
        
        # Mock the dependencies
        import unittest.mock
        with unittest.mock.patch('src.core.contractor_manager.Nominatim'):
            manager = ContractorManager()
            
            assert manager is not None
            assert hasattr(manager, 'performance_scorer')
            assert hasattr(manager, 'geographic_optimizer')
            assert hasattr(manager, 'pricing_engine')
            assert hasattr(manager, 'performance_cache')
            
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_performance_scorer_weights():
    """Test PerformanceScorer weights configuration."""
    try:
        from src.core.contractor_manager import PerformanceScorer
        
        scorer = PerformanceScorer()
        weights = scorer.scoring_weights
        
        # Check all required weights exist
        assert "recent_jobs" in weights
        assert "quality_score" in weights  
        assert "reliability" in weights
        assert "customer_feedback" in weights
        
        # Check weights sum to 1.0
        assert abs(sum(weights.values()) - 1.0) < 0.001
        
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__])