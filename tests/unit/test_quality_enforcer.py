"""
Unit tests for Quality Enforcement System
Testing 3-strike system, photo validation, and Discord integration
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from src.core.quality_enforcer import QualityEnforcer, PhotoValidationResult, StrikeRecord
from src.models.schemas import JobSchema, ContractorSchema, ComplianceResult
from src.models.types import ViolationType, JobStatus, ContractorStatus


class TestQualityEnforcer:
    """Test quality enforcement system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.enforcer = QualityEnforcer()
        
        # Mock job
        self.mock_job = JobSchema(
            id="test_job_123",
            customer_id="customer_1",
            contractor_id="jennifer",
            service_type="recurring",
            address="123 Test St, Minneapolis, MN",
            scheduled_date=datetime.utcnow(),
            status=JobStatus.IN_PROGRESS,
            square_footage=1500,
            bedrooms=3,
            bathrooms=2
        )
        
        # Mock contractor
        self.mock_contractor = ContractorSchema(
            id="jennifer",
            name="Jennifer",
            email="jennifer@test.com",
            phone="+1234567890",
            status=ContractorStatus.AVAILABLE,
            hourly_rate=Decimal("28.00")
        )
    
    @pytest.mark.asyncio
    async def test_photo_validation_success(self):
        """Test successful photo validation."""
        photos = [
            {"filename": "kitchen_after.jpg", "data": "mock_data"},
            {"filename": "bathroom_after.jpg", "data": "mock_data"},
            {"filename": "entry_after.jpg", "data": "mock_data"}
        ]
        
        result = await self.enforcer._validate_photos("test_job_123", photos)
        
        assert isinstance(result, PhotoValidationResult)
        assert result.quality_score > 0
        assert len(result.required_rooms_covered) > 0
    
    @pytest.mark.asyncio
    async def test_photo_validation_missing_photos(self):
        """Test photo validation with missing photos."""
        photos = []  # No photos submitted
        
        result = await self.enforcer._validate_photos("test_job_123", photos)
        
        assert result.is_valid is False
        assert result.quality_score == 0.0
        assert "No photos submitted" in result.issues
        assert len(result.missing_rooms) > 0
    
    @pytest.mark.asyncio
    async def test_photo_validation_poor_quality(self):
        """Test photo validation with poor quality images."""
        photos = [
            {"filename": "kitchen_blur_dark.jpg", "data": "mock_data"},
            {"filename": "bathroom_missing.jpg", "data": "mock_data"}
        ]
        
        result = await self.enforcer._validate_photos("test_job_123", photos)
        
        assert result.quality_score < 6.0
        assert len(result.technical_issues) > 0
    
    def test_mock_photo_analysis(self):
        """Test mock photo analysis logic."""
        # Good quality photo
        good_photo = {"filename": "kitchen_after_clean.jpg"}
        result = self.enforcer._mock_photo_analysis(good_photo)
        
        assert result["quality_score"] == 8.0
        assert result["room_type"] == "kitchen"
        assert result["room_identified"] is True
        
        # Poor quality photo
        poor_photo = {"filename": "bathroom_blur_dark.jpg"}
        result = self.enforcer._mock_photo_analysis(poor_photo)
        
        assert result["quality_score"] < 8.0
        assert "poor image quality" in result["technical_issues"]
    
    def test_checklist_validation_complete(self):
        """Test checklist validation with complete items."""
        checklist_data = {
            "completed_items": [
                "vacuum_all_floors", "mop_hard_surfaces", "dust_all_surfaces",
                "clean_bathrooms", "clean_kitchen", "empty_trash"
            ]
        }
        
        result = self.enforcer._validate_checklist("recurring", checklist_data)
        assert result is True
    
    def test_checklist_validation_incomplete(self):
        """Test checklist validation with incomplete items."""
        checklist_data = {
            "completed_items": ["vacuum_all_floors", "clean_kitchen"]  # Only 2 items
        }
        
        result = self.enforcer._validate_checklist("recurring", checklist_data)
        assert result is False
    
    def test_get_required_checklist_items(self):
        """Test checklist items for different service types."""
        # Recurring service
        recurring_items = self.enforcer._get_required_checklist_items("recurring")
        assert len(recurring_items) == 6
        assert "vacuum_all_floors" in recurring_items
        
        # Deep cleaning
        deep_items = self.enforcer._get_required_checklist_items("deep_cleaning")
        assert len(deep_items) > 6
        assert "deep_clean_bathrooms" in deep_items
        
        # Move out/in
        move_items = self.enforcer._get_required_checklist_items("move_out_in")
        assert len(move_items) > 6
        assert "clean_inside_cabinets" in move_items
    
    @pytest.mark.asyncio
    async def test_timing_compliance_on_time(self):
        """Test timing compliance for on-time arrival."""
        # Set job times for on-time arrival
        self.mock_job.scheduled_date = datetime.utcnow() - timedelta(hours=1)
        self.mock_job.actual_start_time = self.mock_job.scheduled_date + timedelta(minutes=10)
        
        violation = await self.enforcer._check_timing_compliance(self.mock_job, self.mock_contractor)
        assert violation is None
    
    @pytest.mark.asyncio
    async def test_timing_compliance_late_arrival(self):
        """Test timing compliance for late arrival."""
        # Set job times for late arrival (beyond 15-minute buffer)
        self.mock_job.scheduled_date = datetime.utcnow() - timedelta(hours=1)
        self.mock_job.actual_start_time = self.mock_job.scheduled_date + timedelta(minutes=30)
        
        violation = await self.enforcer._check_timing_compliance(self.mock_job, self.mock_contractor)
        assert violation == ViolationType.LATE_ARRIVAL
    
    @pytest.mark.asyncio
    async def test_timing_compliance_no_show(self):
        """Test timing compliance for no-show."""
        # Set job scheduled 3 hours ago with no start time
        self.mock_job.scheduled_date = datetime.utcnow() - timedelta(hours=3)
        self.mock_job.actual_start_time = None
        
        violation = await self.enforcer._check_timing_compliance(self.mock_job, self.mock_contractor)
        assert violation == ViolationType.NO_SHOW
    
    def test_compliance_score_calculation(self):
        """Test compliance score calculation."""
        # Perfect compliance
        score = self.enforcer._calculate_compliance_score([], 10.0)
        assert score == 100.0
        
        # Single violation
        violations = [ViolationType.MISSING_PHOTOS]
        score = self.enforcer._calculate_compliance_score(violations, 8.0)
        assert score < 100.0
        assert score > 50.0
        
        # Multiple violations
        violations = [ViolationType.MISSING_PHOTOS, ViolationType.INCOMPLETE_CHECKLIST, ViolationType.LATE_ARRIVAL]
        score = self.enforcer._calculate_compliance_score(violations, 5.0)
        assert score < 50.0
        
        # No-show violation
        violations = [ViolationType.NO_SHOW]
        score = self.enforcer._calculate_compliance_score(violations, 0.0)
        assert score <= 50.0
    
    @pytest.mark.asyncio
    async def test_job_compliance_check_success(self):
        """Test successful job compliance check."""
        photos = [
            {"filename": "kitchen_after.jpg", "data": "mock_data"},
            {"filename": "bathroom_after.jpg", "data": "mock_data"},
            {"filename": "entry_after.jpg", "data": "mock_data"}
        ]
        
        checklist_data = {
            "completed_items": [
                "vacuum_all_floors", "mop_hard_surfaces", "dust_all_surfaces",
                "clean_bathrooms", "clean_kitchen", "empty_trash"
            ]
        }
        
        # Set on-time arrival
        self.mock_job.scheduled_date = datetime.utcnow() - timedelta(hours=1)
        self.mock_job.actual_start_time = self.mock_job.scheduled_date + timedelta(minutes=10)
        
        result = await self.enforcer.check_job_compliance(
            self.mock_job, self.mock_contractor, photos, checklist_data
        )
        
        assert isinstance(result, ComplianceResult)
        assert result.photos_valid is True
        assert result.checklist_complete is True
        assert result.compliance_score > 80
        assert result.requires_human_review is False
        assert len(result.violations) == 0
    
    @pytest.mark.asyncio
    async def test_job_compliance_check_violations(self):
        """Test job compliance check with violations."""
        photos = []  # No photos
        checklist_data = {"completed_items": []}  # Incomplete checklist
        
        # Set late arrival
        self.mock_job.scheduled_date = datetime.utcnow() - timedelta(hours=1)
        self.mock_job.actual_start_time = self.mock_job.scheduled_date + timedelta(minutes=30)
        
        result = await self.enforcer.check_job_compliance(
            self.mock_job, self.mock_contractor, photos, checklist_data
        )
        
        assert len(result.violations) > 0
        assert ViolationType.MISSING_PHOTOS in result.violations
        assert ViolationType.INCOMPLETE_CHECKLIST in result.violations
        assert ViolationType.LATE_ARRIVAL in result.violations
        assert result.compliance_score < 50
        assert result.requires_human_review is True
    
    @pytest.mark.asyncio
    async def test_violation_recording(self):
        """Test violation recording and strike system."""
        violations = [ViolationType.MISSING_PHOTOS, ViolationType.INCOMPLETE_CHECKLIST]
        photo_result = PhotoValidationResult(
            is_valid=False,
            quality_score=3.0,
            issues=["Missing required photos"],
            missing_rooms=["kitchen", "bathroom"]
        )
        
        await self.enforcer._record_violations(
            self.mock_job, self.mock_contractor, violations, photo_result
        )
        
        strikes = self.enforcer.get_contractor_strikes("jennifer")
        assert len(strikes) == 2  # One strike per violation
        
        # Check first strike
        first_strike = strikes[0]
        assert first_strike.contractor_id == "jennifer"
        assert first_strike.strike_number == 1
        assert first_strike.violation_type == ViolationType.MISSING_PHOTOS
        assert first_strike.job_id == "test_job_123"
    
    @pytest.mark.asyncio
    async def test_third_strike_handling(self):
        """Test third strike handling and approval requirement."""
        # Add two existing strikes
        self.enforcer.strike_records["jennifer"] = [
            StrikeRecord(
                contractor_id="jennifer",
                strike_number=1,
                violation_type=ViolationType.LATE_ARRIVAL,
                description="Previous violation 1",
                evidence={},
                timestamp=datetime.utcnow() - timedelta(days=5)
            ),
            StrikeRecord(
                contractor_id="jennifer",
                strike_number=2,
                violation_type=ViolationType.POOR_PHOTO_QUALITY,
                description="Previous violation 2",
                evidence={},
                timestamp=datetime.utcnow() - timedelta(days=2)
            )
        ]
        
        violations = [ViolationType.NO_SHOW]
        photo_result = PhotoValidationResult(
            is_valid=False,
            quality_score=0.0,
            issues=["No photos submitted"]
        )
        
        # Mock Discord message queueing
        with patch.object(self.enforcer, '_queue_discord_message') as mock_queue:
            await self.enforcer._record_violations(
                self.mock_job, self.mock_contractor, violations, photo_result
            )
            
            # Check that Discord alerts were queued
            assert mock_queue.call_count >= 2  # Strike notification + 3rd strike alert
        
        strikes = self.enforcer.get_contractor_strikes("jennifer")
        assert len(strikes) == 3
        
        third_strike = strikes[-1]
        assert third_strike.strike_number == 3
        assert third_strike.requires_approval is True
    
    @pytest.mark.asyncio
    async def test_third_strike_approval(self):
        """Test third strike penalty approval process."""
        # Add three strikes
        self.enforcer.strike_records["jennifer"] = [
            StrikeRecord(
                contractor_id="jennifer",
                strike_number=i,
                violation_type=ViolationType.LATE_ARRIVAL,
                description=f"Violation {i}",
                evidence={},
                timestamp=datetime.utcnow() - timedelta(days=5-i)
            ) for i in range(1, 4)
        ]
        
        # Test penalty approval
        result = await self.enforcer.approve_third_strike_penalty(
            "jennifer", "manager_test", apply_penalty=True
        )
        
        assert result["action"] == "penalty_applied"
        assert result["penalty_amount"] == 50.0  # Default penalty from settings
        assert result["approved_by"] == "manager_test"
        
        # Check that strike was updated
        strikes = self.enforcer.get_contractor_strikes("jennifer")
        third_strike = strikes[-1]
        assert third_strike.approved_by == "manager_test"
        assert third_strike.penalty_amount == Decimal("50.00")
    
    @pytest.mark.asyncio
    async def test_third_strike_override(self):
        """Test third strike penalty override."""
        # Add three strikes
        self.enforcer.strike_records["jennifer"] = [
            StrikeRecord(
                contractor_id="jennifer",
                strike_number=i,
                violation_type=ViolationType.LATE_ARRIVAL,
                description=f"Violation {i}",
                evidence={},
                timestamp=datetime.utcnow() - timedelta(days=5-i)
            ) for i in range(1, 4)
        ]
        
        # Test penalty override
        result = await self.enforcer.approve_third_strike_penalty(
            "jennifer", "manager_test", apply_penalty=False
        )
        
        assert result["action"] == "penalty_overridden"
        assert result["approved_by"] == "manager_test"
        
        # Check that strike was updated but no penalty applied
        strikes = self.enforcer.get_contractor_strikes("jennifer")
        third_strike = strikes[-1]
        assert third_strike.approved_by == "manager_test"
        assert third_strike.penalty_amount is None
    
    def test_violation_description_generation(self):
        """Test violation description generation."""
        photo_result = PhotoValidationResult(
            is_valid=False,
            quality_score=3.0,
            issues=["Technical issues"],
            missing_rooms=["kitchen", "bathroom"],
            technical_issues=["blurry", "dark"]
        )
        
        # Test missing photos description
        desc = self.enforcer._generate_violation_description(
            ViolationType.MISSING_PHOTOS, self.mock_job, photo_result
        )
        assert "Missing required photos" in desc
        assert "kitchen, bathroom" in desc
        
        # Test poor photo quality description
        desc = self.enforcer._generate_violation_description(
            ViolationType.POOR_PHOTO_QUALITY, self.mock_job, photo_result
        )
        assert "Poor photo quality" in desc
        assert "blurry, dark" in desc
        
        # Test late arrival description
        desc = self.enforcer._generate_violation_description(
            ViolationType.LATE_ARRIVAL, self.mock_job, photo_result
        )
        assert "Late arrival without prior communication" in desc
    
    def test_strike_summary(self):
        """Test system-wide strike summary."""
        # Add strikes for multiple contractors
        self.enforcer.strike_records = {
            "jennifer": [
                StrikeRecord(
                    contractor_id="jennifer",
                    strike_number=1,
                    violation_type=ViolationType.LATE_ARRIVAL,
                    description="Test violation",
                    evidence={},
                    timestamp=datetime.utcnow() - timedelta(days=1)
                ),
                StrikeRecord(
                    contractor_id="jennifer",
                    strike_number=2,
                    violation_type=ViolationType.MISSING_PHOTOS,
                    description="Test violation 2",
                    evidence={},
                    timestamp=datetime.utcnow() - timedelta(hours=12)
                )
            ],
            "olga": [
                StrikeRecord(
                    contractor_id="olga",
                    strike_number=1,
                    violation_type=ViolationType.INCOMPLETE_CHECKLIST,
                    description="Test violation",
                    evidence={},
                    timestamp=datetime.utcnow() - timedelta(days=10)  # Old strike
                )
            ]
        }
        
        summary = self.enforcer.get_strike_summary()
        
        assert summary["total_contractors_with_strikes"] == 2
        assert summary["total_strikes"] == 3
        assert summary["contractors_at_risk"] == 1  # Jennifer with 2 strikes
        assert summary["recent_strikes_7_days"] == 2  # Jennifer's strikes only
        assert summary["average_strikes_per_contractor"] == 1.5
    
    def test_clear_contractor_strikes(self):
        """Test clearing contractor strikes."""
        # Add strikes
        self.enforcer.strike_records["jennifer"] = [
            StrikeRecord(
                contractor_id="jennifer",
                strike_number=1,
                violation_type=ViolationType.LATE_ARRIVAL,
                description="Test violation",
                evidence={},
                timestamp=datetime.utcnow()
            )
        ]
        
        result = self.enforcer.clear_contractor_strikes("jennifer", "Reset for new period")
        assert result is True
        assert len(self.enforcer.get_contractor_strikes("jennifer")) == 0
        
        # Test clearing non-existent contractor
        result = self.enforcer.clear_contractor_strikes("nonexistent", "Test")
        assert result is False
    
    def test_discord_channel_mapping(self):
        """Test Discord channel configuration."""
        channels = self.enforcer.discord_channels
        
        assert "strikes" in channels
        assert channels["strikes"] == "❌-strikes"
        assert channels["alerts"] == "🚨-alerts"
        assert channels["job_checkins"] == "✔️-job-check-ins"
    
    @pytest.mark.asyncio
    async def test_compliance_check_error_handling(self):
        """Test error handling in compliance check."""
        # Force an error by passing invalid data
        invalid_job = None
        
        result = await self.enforcer.check_job_compliance(
            invalid_job, self.mock_contractor, [], {}
        )
        
        assert result.requires_human_review is True
        assert result.compliance_score == 0
        assert not result.photos_valid
        assert not result.checklist_complete


class TestQualityEnforcerIntegration:
    """Integration tests for quality enforcement system."""
    
    @pytest.mark.asyncio
    async def test_full_violation_workflow(self):
        """Test complete violation workflow from detection to resolution."""
        enforcer = QualityEnforcer()
        
        # Create test data
        job = JobSchema(
            id="integration_test_job",
            customer_id="customer_1",
            contractor_id="test_contractor",
            service_type="recurring",
            address="123 Integration Test St",
            scheduled_date=datetime.utcnow() - timedelta(hours=1),
            actual_start_time=datetime.utcnow() - timedelta(minutes=30),  # Late arrival
            status=JobStatus.COMPLETED
        )
        
        contractor = ContractorSchema(
            id="test_contractor",
            name="Test Contractor",
            email="test@example.com",
            phone="+1234567890",
            status=ContractorStatus.AVAILABLE,
            hourly_rate=Decimal("25.00")
        )
        
        # No photos, incomplete checklist, late arrival
        photos = []
        checklist_data = {"completed_items": ["vacuum_all_floors"]}  # Incomplete
        
        # Run compliance check
        result = await enforcer.check_job_compliance(job, contractor, photos, checklist_data)
        
        # Verify multiple violations detected
        assert len(result.violations) >= 3
        assert ViolationType.MISSING_PHOTOS in result.violations
        assert ViolationType.INCOMPLETE_CHECKLIST in result.violations
        assert ViolationType.LATE_ARRIVAL in result.violations
        
        # Verify strikes were recorded
        strikes = enforcer.get_contractor_strikes("test_contractor")
        assert len(strikes) == len(result.violations)
        
        # Verify compliance score is low
        assert result.compliance_score < 50
        assert result.requires_human_review is True
    
    @pytest.mark.asyncio
    async def test_photo_validation_caching(self):
        """Test photo validation caching functionality."""
        enforcer = QualityEnforcer()
        
        photos = [
            {"filename": "kitchen_test.jpg", "data": "test_data"}
        ]
        
        # First call - should process and cache
        result1 = await enforcer._validate_photos("cache_test_job", photos)
        
        # Second call - should return cached result
        result2 = await enforcer._validate_photos("cache_test_job", photos)
        
        # Results should be identical (from cache)
        assert result1.quality_score == result2.quality_score
        assert result1.is_valid == result2.is_valid
        
        # Cache key should exist
        cache_key = f"cache_test_job_{len(photos)}"
        assert cache_key in enforcer.photo_validation_cache