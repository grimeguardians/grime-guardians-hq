"""
Unit tests for Contractor Management System
Testing performance scoring, geographic optimization, and pay calculations
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from src.core.contractor_manager import (
    ContractorManager, PerformanceScorer, GeographicOptimizer
)
from src.models.schemas import (
    ContractorSchema, JobSchema, PerformanceMetrics, PaySplitCalculation
)
from src.models.types import ContractorStatus, JobStatus


class TestPerformanceScorer:
    """Test contractor performance scoring system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = PerformanceScorer()
        
        # Mock contractor
        self.contractor = ContractorSchema(
            id="test_contractor",
            name="Test Contractor",
            email="test@example.com",
            phone="+1234567890",
            status=ContractorStatus.AVAILABLE,
            hourly_rate=Decimal("25.00")
        )
        
        # Mock job history
        self.job_history = [
            JobSchema(
                id=f"job_{i}",
                customer_id="customer_1",
                contractor_id="test_contractor",
                service_type="recurring",
                address=f"Address {i}",
                scheduled_date=datetime.utcnow() - timedelta(days=i),
                actual_start_time=datetime.utcnow() - timedelta(days=i, minutes=-10),
                completed_at=datetime.utcnow() - timedelta(days=i, hours=-2),
                status=JobStatus.COMPLETED,
                square_footage=1500,
                bedrooms=3,
                bathrooms=2
            ) for i in range(1, 11)  # 10 jobs over 10 days
        ]
    
    def test_scoring_weights_configuration(self):
        """Test performance scoring weights are properly configured."""
        weights = self.scorer.scoring_weights
        
        assert weights["recent_jobs"] == 0.4
        assert weights["quality_score"] == 0.3
        assert weights["reliability"] == 0.2
        assert weights["customer_feedback"] == 0.1
        
        # Weights should sum to 1.0
        assert sum(weights.values()) == 1.0
    
    def test_time_decay_configuration(self):
        """Test time decay factors are properly configured."""
        decay = self.scorer.time_decay
        
        assert decay["last_7_days"] == 1.0
        assert decay["last_30_days"] == 0.8
        assert decay["last_90_days"] == 0.6
        assert decay["older"] == 0.3
    
    def test_filter_jobs_by_period(self):
        """Test job filtering by time period."""
        # Filter to last 5 days
        recent_jobs = self.scorer._filter_jobs_by_period(self.job_history, 5)
        
        # Should have 5 jobs (jobs 1-5 are within 5 days)
        assert len(recent_jobs) == 5
        
        # All jobs should be within 5 days
        cutoff = datetime.utcnow() - timedelta(days=5)
        for job in recent_jobs:
            assert job.completed_at >= cutoff
    
    def test_calculate_quality_score_perfect(self):
        """Test quality score calculation with perfect compliance."""
        # Mock jobs with perfect quality
        for job in self.job_history:
            job.photos_submitted = True
            job.photo_quality_issues = 0
            job.checklist_complete = True
            job.late_arrival = False
        
        score = self.scorer._calculate_quality_score(self.job_history)
        assert score == 100.0
    
    def test_calculate_quality_score_with_issues(self):
        """Test quality score calculation with quality issues."""
        # Mock jobs with various quality issues
        for i, job in enumerate(self.job_history):
            if i % 3 == 0:  # Every 3rd job has photo issues
                job.photos_submitted = False
            elif i % 3 == 1:  # Every 3rd job has checklist issues
                job.checklist_complete = False
            else:  # Every 3rd job has timing issues
                job.late_arrival = True
        
        score = self.scorer._calculate_quality_score(self.job_history)
        assert score < 100.0
        assert score > 0.0  # Should still have some score
    
    def test_calculate_reliability_score_perfect(self):
        """Test reliability score with perfect on-time performance."""
        # All jobs start within 15-minute buffer
        for job in self.job_history:
            job.actual_start_time = job.scheduled_date + timedelta(minutes=10)
        
        score = self.scorer._calculate_reliability_score(self.job_history)
        assert score == 100.0
    
    def test_calculate_reliability_score_with_late_arrivals(self):
        """Test reliability score with some late arrivals."""
        # Half the jobs are late
        for i, job in enumerate(self.job_history):
            if i % 2 == 0:
                job.actual_start_time = job.scheduled_date + timedelta(minutes=30)  # Late
            else:
                job.actual_start_time = job.scheduled_date + timedelta(minutes=10)  # On time
        
        score = self.scorer._calculate_reliability_score(self.job_history)
        assert score == 50.0  # 50% on-time rate
    
    def test_calculate_efficiency_score(self):
        """Test efficiency score calculation."""
        # Mock job durations
        for job in self.job_history:
            job.duration_hours = 2.0  # Faster than expected 2.5 hours for recurring
        
        score = self.scorer._calculate_efficiency_score(self.job_history)
        assert score == 100.0  # All jobs completed efficiently
    
    def test_calculate_customer_score(self):
        """Test customer satisfaction score calculation."""
        # Mock customer ratings
        for job in self.job_history:
            job.customer_rating = 9.5  # High rating
        
        score = self.scorer._calculate_customer_score(self.job_history)
        assert score == 95.0  # 9.5/10 * 100 = 95%
    
    def test_get_expected_duration(self):
        """Test expected duration lookup."""
        assert self.scorer._get_expected_duration("recurring") == 2.5
        assert self.scorer._get_expected_duration("deep_cleaning") == 4.0
        assert self.scorer._get_expected_duration("move_out_in") == 5.0
        assert self.scorer._get_expected_duration("unknown") == 3.0  # Default
    
    def test_calculate_performance_score_excellent(self):
        """Test performance score calculation for excellent contractor."""
        # Set up perfect performance
        for job in self.job_history:
            job.photos_submitted = True
            job.photo_quality_issues = 0
            job.checklist_complete = True
            job.late_arrival = False
            job.actual_start_time = job.scheduled_date + timedelta(minutes=5)
            job.duration_hours = 2.0
            job.customer_rating = 9.8
        
        performance = self.scorer.calculate_performance_score(
            self.contractor, self.job_history, violation_count=0
        )
        
        assert performance.overall_score >= 90
        assert performance.performance_tier == "excellent"
        assert performance.jobs_completed > 0
        assert "Maintain excellent performance" in performance.recommendations
    
    def test_calculate_performance_score_with_violations(self):
        """Test performance score calculation with violations."""
        # Set up good performance but with violations
        for job in self.job_history:
            job.photos_submitted = True
            job.checklist_complete = True
            job.late_arrival = False
            job.customer_rating = 9.0
        
        performance = self.scorer.calculate_performance_score(
            self.contractor, self.job_history, violation_count=3  # 3 violations
        )
        
        # Should have penalty for violations (3 * 5 = 15 points)
        assert performance.overall_score <= 85  # Max would be ~100 - 15
        assert performance.violation_count == 3
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        # Low scores in different areas
        recommendations = self.scorer._generate_recommendations(
            quality=75,      # Below 80
            reliability=85,  # Above 90
            efficiency=70,   # Below 80
            customer=80      # Below 85
        )
        
        assert "Focus on photo quality and checklist completion" in recommendations
        assert "Work on time management and efficiency" in recommendations
        assert "Focus on customer communication and service quality" in recommendations
        # Should NOT include reliability recommendation since it's above 90
        assert not any("on-time arrival" in rec for rec in recommendations)
    
    def test_calculate_performance_score_no_jobs(self):
        """Test performance score calculation with no job history."""
        performance = self.scorer.calculate_performance_score(
            self.contractor, [], violation_count=0
        )
        
        assert performance.overall_score == 0
        assert performance.performance_tier == "needs_improvement"
        assert performance.jobs_completed == 0
        assert "Unable to calculate performance" in performance.recommendations[0]


class TestGeographicOptimizer:
    """Test geographic assignment optimization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = GeographicOptimizer()
        
        # Mock contractors
        self.contractors = [
            ContractorSchema(
                id="jennifer",
                name="Jennifer",
                email="jennifer@example.com",
                phone="+1234567890",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("28.00"),
                preferred_territory="south"
            ),
            ContractorSchema(
                id="olga",
                name="Olga",
                email="olga@example.com",
                phone="+1234567891",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("25.00"),
                preferred_territory="east"
            ),
            ContractorSchema(
                id="zhanna",
                name="Zhanna",
                email="zhanna@example.com",
                phone="+1234567892",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("25.00"),
                preferred_territory="central"
            )
        ]
        
        # Mock job
        self.job = JobSchema(
            id="test_job",
            customer_id="customer_1",
            contractor_id=None,
            service_type="recurring",
            address="123 South Metro St, Burnsville, MN",
            scheduled_date=datetime.utcnow() + timedelta(hours=2),
            status=JobStatus.PENDING,
            square_footage=1500,
            bedrooms=3,
            bathrooms=2
        )
    
    def test_metro_areas_configuration(self):
        """Test metro area boundaries are properly configured."""
        areas = self.optimizer.metro_areas
        
        assert "south" in areas
        assert "east" in areas
        assert "central" in areas
        assert "north" in areas
        
        # Each area should have lat, lon, and radius
        for area in areas.values():
            assert "lat" in area
            assert "lon" in area
            assert "radius_km" in area
    
    @patch('src.core.contractor_manager.Nominatim')
    def test_get_job_coordinates_success(self, mock_geocoder):
        """Test successful job coordinate retrieval."""
        # Mock geocoder response
        mock_location = MagicMock()
        mock_location.latitude = 44.8
        mock_location.longitude = -93.2
        
        mock_geocoder_instance = MagicMock()
        mock_geocoder_instance.geocode.return_value = mock_location
        mock_geocoder.return_value = mock_geocoder_instance
        
        coords = self.optimizer._get_job_coordinates("123 Test St, Minneapolis, MN")
        
        assert coords == (44.8, -93.2)
        mock_geocoder_instance.geocode.assert_called_once()
    
    @patch('src.core.contractor_manager.Nominatim')
    def test_get_job_coordinates_failure(self, mock_geocoder):
        """Test job coordinate retrieval failure."""
        # Mock geocoder failure
        mock_geocoder_instance = MagicMock()
        mock_geocoder_instance.geocode.return_value = None
        mock_geocoder.return_value = mock_geocoder_instance
        
        coords = self.optimizer._get_job_coordinates("Invalid Address")
        assert coords is None
    
    def test_calculate_territory_score_perfect_match(self):
        """Test territory score for perfect match."""
        # Jennifer prefers south, job is in south metro
        job_coords = (44.8, -93.2)  # South metro coordinates
        
        score = self.optimizer._calculate_territory_score(self.contractors[0], job_coords)
        assert score == 100.0  # Perfect match
    
    def test_calculate_territory_score_out_of_territory(self):
        """Test territory score for out-of-territory assignment."""
        # Jennifer prefers south, job is in north metro
        job_coords = (45.1, -93.3)  # North metro coordinates
        
        score = self.optimizer._calculate_territory_score(self.contractors[0], job_coords)
        assert score == 60.0  # Out of territory but doable
    
    def test_calculate_distance_score(self):
        """Test distance score calculation."""
        # Close distance
        job_coords = (44.85, -93.15)  # Close to south metro center
        score = self.optimizer._calculate_distance_score(self.contractors[0], job_coords)
        assert score >= 80.0  # Should be high score for close distance
        
        # Far distance
        job_coords = (45.2, -93.5)  # Far from south metro
        score = self.optimizer._calculate_distance_score(self.contractors[0], job_coords)
        assert score <= 60.0  # Should be lower score for far distance
    
    def test_calculate_availability_score(self):
        """Test availability score calculation."""
        # Low workload
        contractor = self.contractors[0]
        contractor.jobs_today = 1
        contractor.max_jobs_per_day = 3
        
        score = self.optimizer._calculate_availability_score(contractor)
        assert score == 100.0  # Well below max capacity
        
        # High workload
        contractor.jobs_today = 3
        score = self.optimizer._calculate_availability_score(contractor)
        assert score == 0.0  # At max capacity
    
    def test_calculate_assignment_score(self):
        """Test overall assignment score calculation."""
        job_coords = (44.8, -93.2)  # South metro
        
        # Mock performance metrics
        mock_performance = PerformanceMetrics(
            contractor_id="jennifer",
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            jobs_completed=10,
            quality_score=95.0,
            reliability_score=90.0,
            efficiency_score=85.0,
            customer_satisfaction_avg=9.2,
            violation_count=0,
            overall_score=90.0,
            performance_tier="excellent"
        )
        
        score = self.optimizer._calculate_assignment_score(
            self.contractors[0], job_coords, mock_performance
        )
        
        # Should be high score (performance * 0.4 + territory * 0.3 + distance * 0.2 + availability * 0.1)
        assert score >= 80.0
        assert score <= 100.0
    
    def test_territory_based_assignment_south(self):
        """Test fallback territory-based assignment for south metro."""
        # Job with south metro keywords
        job = JobSchema(
            id="test_job",
            customer_id="customer_1",
            service_type="recurring",
            address="123 Burnsville Ave, Burnsville, MN",
            scheduled_date=datetime.utcnow(),
            status=JobStatus.PENDING
        )
        
        mock_performance_scores = {
            "jennifer": PerformanceMetrics(
                contractor_id="jennifer",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                jobs_completed=10,
                overall_score=90.0,
                performance_tier="excellent"
            )
        }
        
        assignments = self.optimizer._territory_based_assignment(
            job, self.contractors, mock_performance_scores
        )
        
        # Jennifer (south territory) should be ranked highest
        assert len(assignments) > 0
        top_contractor, top_score = assignments[0]
        assert top_contractor.id == "jennifer"
        assert top_score > 90.0  # Should get territory bonus
    
    @patch.object(GeographicOptimizer, '_get_job_coordinates')
    def test_optimize_assignment_success(self, mock_coords):
        """Test successful assignment optimization."""
        # Mock coordinates for south metro
        mock_coords.return_value = (44.8, -93.2)
        
        mock_performance_scores = {
            contractor.id: PerformanceMetrics(
                contractor_id=contractor.id,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                jobs_completed=10,
                overall_score=85.0,
                performance_tier="good"
            ) for contractor in self.contractors
        }
        
        assignments = self.optimizer.optimize_assignment(
            self.job, self.contractors, mock_performance_scores
        )
        
        assert len(assignments) == len(self.contractors)
        
        # Results should be sorted by score (highest first)
        scores = [score for _, score in assignments]
        assert scores == sorted(scores, reverse=True)
        
        # Jennifer (south territory) should likely be ranked highest
        top_contractor, _ = assignments[0]
        assert top_contractor.id == "jennifer"
    
    @patch.object(GeographicOptimizer, '_get_job_coordinates')
    def test_optimize_assignment_geocoding_failure(self, mock_coords):
        """Test assignment optimization when geocoding fails."""
        # Mock geocoding failure
        mock_coords.return_value = None
        
        mock_performance_scores = {
            contractor.id: PerformanceMetrics(
                contractor_id=contractor.id,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                jobs_completed=10,
                overall_score=85.0,
                performance_tier="good"
            ) for contractor in self.contractors
        }
        
        assignments = self.optimizer.optimize_assignment(
            self.job, self.contractors, mock_performance_scores
        )
        
        # Should fall back to territory-based assignment
        assert len(assignments) > 0
        
        # Since job address contains "South Metro", Jennifer should be preferred
        top_contractor, _ = assignments[0]
        assert top_contractor.id == "jennifer"
    
    def test_optimize_assignment_unavailable_contractors(self):
        """Test assignment optimization with unavailable contractors."""
        # Make some contractors unavailable
        self.contractors[1].status = ContractorStatus.BUSY
        self.contractors[2].status = ContractorStatus.UNAVAILABLE
        
        mock_performance_scores = {}
        
        assignments = self.optimizer.optimize_assignment(
            self.job, self.contractors, mock_performance_scores
        )
        
        # Only available contractors should be included
        assert len(assignments) == 1
        assert assignments[0][0].id == "jennifer"


class TestContractorManager:
    """Test main contractor manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ContractorManager()
        
        # Mock job and contractor
        self.job = JobSchema(
            id="test_job",
            customer_id="customer_1",
            contractor_id="jennifer",
            service_type="recurring",
            address="123 Test St, Minneapolis, MN",
            scheduled_date=datetime.utcnow(),
            status=JobStatus.PENDING,
            square_footage=1500,
            bedrooms=3,
            bathrooms=2,
            add_ons=["interior_oven"]
        )
        
        self.contractor = ContractorSchema(
            id="jennifer",
            name="Jennifer",
            email="jennifer@example.com",
            phone="+1234567890",
            status=ContractorStatus.AVAILABLE,
            hourly_rate=Decimal("28.00")
        )
    
    def test_estimate_job_duration_recurring(self):
        """Test job duration estimation for recurring service."""
        duration = self.manager._estimate_job_duration(self.job)
        
        # Base 2.5 hours + 0.5 for add-on + size adjustment
        assert duration >= 2.5
        assert duration <= 4.0
    
    def test_estimate_job_duration_deep_cleaning(self):
        """Test job duration estimation for deep cleaning."""
        self.job.service_type = "deep_cleaning"
        self.job.square_footage = 2500  # Large house
        
        duration = self.manager._estimate_job_duration(self.job)
        
        # Base 4.0 hours + size adjustment + add-on
        assert duration >= 5.0
        assert duration <= 7.0
    
    def test_estimate_job_duration_move_out_in(self):
        """Test job duration estimation for move out/in."""
        self.job.service_type = "move_out_in"
        self.job.square_footage = 800  # Small apartment
        self.job.add_ons = []  # No add-ons
        
        duration = self.manager._estimate_job_duration(self.job)
        
        # Base 5.0 hours * 0.8 (small size adjustment) = 4.0 hours
        assert duration == 4.0
    
    @pytest.mark.asyncio
    async def test_calculate_pay_split_base(self):
        """Test basic pay split calculation."""
        with patch.object(self.manager.pricing_engine, 'calculate_pricing') as mock_pricing:
            # Mock pricing result
            mock_pricing.return_value = MagicMock(
                final_price_with_tax=Decimal("135.00")
            )
            
            pay_split = await self.manager.calculate_pay_split(
                self.job, self.contractor, performance_bonus=False
            )
            
            assert isinstance(pay_split, PaySplitCalculation)
            assert pay_split.job_id == "test_job"
            assert pay_split.contractor_id == "jennifer"
            assert pay_split.hourly_rate == Decimal("28.00")
            assert pay_split.performance_bonus == Decimal("0.00")
            assert pay_split.customer_total == Decimal("135.00")
            
            # Verify profit calculation
            assert pay_split.company_profit > 0
            assert pay_split.profit_margin_percentage > 0
    
    @pytest.mark.asyncio
    async def test_calculate_pay_split_with_performance_bonus(self):
        """Test pay split calculation with performance bonus."""
        with patch.object(self.manager.pricing_engine, 'calculate_pricing') as mock_pricing:
            mock_pricing.return_value = MagicMock(
                final_price_with_tax=Decimal("135.00")
            )
            
            # Mock excellent performance
            with patch.object(self.manager, 'get_contractor_performance') as mock_perf:
                mock_perf.return_value = PerformanceMetrics(
                    contractor_id="jennifer",
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow(),
                    jobs_completed=10,
                    overall_score=95.0,  # Excellent performance
                    performance_tier="excellent"
                )
                
                pay_split = await self.manager.calculate_pay_split(
                    self.job, self.contractor, performance_bonus=True
                )
                
                # Should have 10% performance bonus
                assert pay_split.performance_bonus > 0
                expected_bonus = pay_split.contractor_base_pay * Decimal("0.10")
                assert pay_split.performance_bonus == expected_bonus
                assert pay_split.total_contractor_pay == pay_split.contractor_base_pay + pay_split.performance_bonus
    
    @pytest.mark.asyncio
    async def test_get_contractor_performance_caching(self):
        """Test contractor performance caching."""
        job_history = [self.job]
        
        with patch.object(self.manager, '_get_contractor_by_id') as mock_get:
            mock_get.return_value = self.contractor
            
            # First call - should calculate and cache
            perf1 = await self.manager.get_contractor_performance("jennifer", job_history)
            
            # Second call - should return cached result
            perf2 = await self.manager.get_contractor_performance("jennifer", job_history)
            
            # Results should be identical
            assert perf1.overall_score == perf2.overall_score
            assert perf1.performance_tier == perf2.performance_tier
            
            # Should be cached
            assert "jennifer" in self.manager.performance_cache
    
    @pytest.mark.asyncio
    async def test_get_contractor_performance_force_refresh(self):
        """Test forced refresh of contractor performance."""
        job_history = [self.job]
        
        with patch.object(self.manager, '_get_contractor_by_id') as mock_get:
            mock_get.return_value = self.contractor
            
            # Cache initial result
            await self.manager.get_contractor_performance("jennifer", job_history)
            
            # Force refresh should recalculate
            perf_refreshed = await self.manager.get_contractor_performance(
                "jennifer", job_history, force_refresh=True
            )
            
            assert isinstance(perf_refreshed, PerformanceMetrics)
            assert perf_refreshed.contractor_id == "jennifer"
    
    @pytest.mark.asyncio
    async def test_optimize_job_assignment(self):
        """Test job assignment optimization."""
        contractors = [
            self.contractor,
            ContractorSchema(
                id="olga",
                name="Olga",
                email="olga@example.com",
                phone="+1234567891",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("25.00")
            )
        ]
        
        with patch.object(self.manager, 'get_contractor_performance') as mock_perf:
            mock_perf.return_value = PerformanceMetrics(
                contractor_id="test",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                jobs_completed=10,
                overall_score=85.0,
                performance_tier="good"
            )
            
            assignments = await self.manager.optimize_job_assignment(self.job, contractors)
            
            assert len(assignments) == len(contractors)
            
            # Should be list of (contractor, score) tuples
            for contractor, score in assignments:
                assert isinstance(contractor, ContractorSchema)
                assert isinstance(score, float)
                assert 0 <= score <= 100
    
    @pytest.mark.asyncio
    async def test_get_contractor_by_id(self):
        """Test contractor retrieval by ID."""
        # Test existing contractor
        contractor = await self.manager._get_contractor_by_id("jennifer")
        assert contractor is not None
        assert contractor.id == "jennifer"
        assert contractor.name == "Jennifer"
        
        # Test non-existent contractor
        contractor = await self.manager._get_contractor_by_id("nonexistent")
        assert contractor is None
    
    def test_get_system_metrics(self):
        """Test system metrics retrieval."""
        # Add some cache data
        self.manager.performance_cache["test"] = PerformanceMetrics(
            contractor_id="test",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            jobs_completed=5,
            overall_score=80.0,
            performance_tier="good"
        )
        
        metrics = self.manager.get_system_metrics()
        
        assert "cached_performances" in metrics
        assert "cache_age_minutes" in metrics
        assert "performance_scorer_weights" in metrics
        assert "metro_areas_configured" in metrics
        
        assert metrics["cached_performances"] == 1
        assert isinstance(metrics["cache_age_minutes"], float)
        assert metrics["metro_areas_configured"] == 4


class TestContractorManagerIntegration:
    """Integration tests for contractor manager."""
    
    @pytest.mark.asyncio
    async def test_full_assignment_workflow(self):
        """Test complete assignment workflow."""
        manager = ContractorManager()
        
        # Create test data
        job = JobSchema(
            id="integration_job",
            customer_id="customer_1",
            service_type="deep_cleaning",
            address="123 South Metro Ave, Burnsville, MN",
            scheduled_date=datetime.utcnow() + timedelta(hours=2),
            status=JobStatus.PENDING,
            square_footage=2000,
            bedrooms=4,
            bathrooms=3,
            add_ons=["interior_oven", "interior_fridge"]
        )
        
        contractors = [
            ContractorSchema(
                id="jennifer",
                name="Jennifer",
                email="jennifer@example.com",
                phone="+1234567890",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("28.00"),
                preferred_territory="south"
            ),
            ContractorSchema(
                id="olga",
                name="Olga", 
                email="olga@example.com",
                phone="+1234567891",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("25.00"),
                preferred_territory="east"
            )
        ]
        
        # Test assignment optimization
        assignments = await manager.optimize_job_assignment(job, contractors)
        
        # Should have results for all available contractors
        assert len(assignments) == 2
        
        # Jennifer should be ranked higher due to south territory preference
        top_contractor, top_score = assignments[0]
        assert top_contractor.id == "jennifer"
        assert top_score > assignments[1][1]  # Higher than second place
        
        # Test pay calculation for assigned contractor
        with patch.object(manager.pricing_engine, 'calculate_pricing') as mock_pricing:
            mock_pricing.return_value = MagicMock(
                final_price_with_tax=Decimal("240.00")
            )
            
            pay_split = await manager.calculate_pay_split(
                job, top_contractor, performance_bonus=True
            )
            
            assert pay_split.contractor_id == "jennifer"
            assert pay_split.hourly_rate == Decimal("28.00")
            assert pay_split.customer_total == Decimal("240.00")
            
            # Verify estimated hours for deep cleaning with add-ons
            assert pay_split.estimated_hours >= 5.0  # Should be substantial for deep cleaning
            
            # Verify company profit
            assert pay_split.company_profit > 0
            assert pay_split.profit_margin_percentage > 20  # Should maintain good margin