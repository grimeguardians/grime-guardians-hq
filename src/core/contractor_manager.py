"""
Contractor Management System
Handles pay splits, performance tracking, and geographic optimization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

from ..models.schemas import (
    ContractorSchema, JobSchema, PerformanceMetrics, 
    GeographicTerritory, PaySplitCalculation
)
from ..models.types import ContractorStatus, JobStatus
from ..config.settings import get_settings, CONTRACTOR_PAY_RATES
from ..core.pricing_engine import PricingEngine

logger = logging.getLogger(__name__)
settings = get_settings()


class PerformanceScorer:
    """
    Contractor performance scoring with weighted algorithms.
    Recent performance weighted more heavily than historical.
    """
    
    def __init__(self):
        self.scoring_weights = {
            "recent_jobs": 0.4,      # Last 30 days - 40% weight
            "quality_score": 0.3,    # Photo/checklist compliance - 30% weight
            "reliability": 0.2,      # On-time arrival - 20% weight
            "customer_feedback": 0.1  # Customer ratings - 10% weight
        }
        
        # Time decay factors
        self.time_decay = {
            "last_7_days": 1.0,      # Full weight
            "last_30_days": 0.8,     # 80% weight
            "last_90_days": 0.6,     # 60% weight
            "older": 0.3             # 30% weight
        }
    
    def calculate_performance_score(
        self, 
        contractor: ContractorSchema,
        job_history: List[JobSchema],
        violation_count: int = 0
    ) -> PerformanceMetrics:
        """
        Calculate weighted performance score for contractor.
        """
        try:
            now = datetime.utcnow()
            
            # Filter jobs by time periods
            recent_jobs = self._filter_jobs_by_period(job_history, 30)  # Last 30 days
            all_jobs = job_history
            
            # Calculate component scores
            quality_score = self._calculate_quality_score(recent_jobs)
            reliability_score = self._calculate_reliability_score(recent_jobs)
            efficiency_score = self._calculate_efficiency_score(recent_jobs)
            customer_score = self._calculate_customer_score(recent_jobs)
            
            # Apply violation penalty
            violation_penalty = min(violation_count * 5, 25)  # Max 25 point penalty
            
            # Calculate weighted final score
            weighted_score = (
                quality_score * self.scoring_weights["quality_score"] +
                reliability_score * self.scoring_weights["reliability"] +
                efficiency_score * self.scoring_weights["recent_jobs"] +
                customer_score * self.scoring_weights["customer_feedback"]
            ) - violation_penalty
            
            final_score = max(0, min(100, weighted_score))
            
            # Determine performance tier
            if final_score >= 90:
                tier = "excellent"
            elif final_score >= 80:
                tier = "good"
            elif final_score >= 70:
                tier = "satisfactory"
            else:
                tier = "needs_improvement"
            
            return PerformanceMetrics(
                contractor_id=contractor.id,
                period_start=now - timedelta(days=30),
                period_end=now,
                jobs_completed=len(recent_jobs),
                quality_score=quality_score,
                reliability_score=reliability_score,
                efficiency_score=efficiency_score,
                customer_satisfaction_avg=customer_score,
                violation_count=violation_count,
                overall_score=final_score,
                performance_tier=tier,
                recommendations=self._generate_recommendations(
                    quality_score, reliability_score, efficiency_score, customer_score
                )
            )
            
        except Exception as e:
            logger.error(f"Performance calculation error for {contractor.id}: {e}")
            return PerformanceMetrics(
                contractor_id=contractor.id,
                period_start=now - timedelta(days=30),
                period_end=now,
                jobs_completed=0,
                quality_score=0,
                reliability_score=0,
                efficiency_score=0,
                customer_satisfaction_avg=0,
                violation_count=violation_count,
                overall_score=0,
                performance_tier="needs_improvement",
                recommendations=["Unable to calculate performance - insufficient data"]
            )
    
    def _filter_jobs_by_period(self, jobs: List[JobSchema], days: int) -> List[JobSchema]:
        """Filter jobs to specific time period."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return [job for job in jobs if job.completed_at and job.completed_at >= cutoff_date]
    
    def _calculate_quality_score(self, jobs: List[JobSchema]) -> float:
        """Calculate quality score based on photo/checklist compliance."""
        if not jobs:
            return 0.0
        
        quality_scores = []
        for job in jobs:
            score = 100.0  # Start with perfect score
            
            # Photo compliance (mock data - in production would check actual photos)
            if not getattr(job, 'photos_submitted', True):
                score -= 30
            elif getattr(job, 'photo_quality_issues', 0) > 0:
                score -= (getattr(job, 'photo_quality_issues', 0) * 10)
            
            # Checklist compliance
            if not getattr(job, 'checklist_complete', True):
                score -= 25
            
            # Time compliance
            if getattr(job, 'late_arrival', False):
                score -= 15
            
            quality_scores.append(max(0, score))
        
        return sum(quality_scores) / len(quality_scores)
    
    def _calculate_reliability_score(self, jobs: List[JobSchema]) -> float:
        """Calculate reliability score based on on-time performance."""
        if not jobs:
            return 0.0
        
        on_time_count = 0
        for job in jobs:
            if (job.actual_start_time and job.scheduled_date and 
                job.actual_start_time <= job.scheduled_date + timedelta(minutes=15)):
                on_time_count += 1
        
        return (on_time_count / len(jobs)) * 100
    
    def _calculate_efficiency_score(self, jobs: List[JobSchema]) -> float:
        """Calculate efficiency score based on job completion time."""
        if not jobs:
            return 0.0
        
        efficiency_scores = []
        for job in jobs:
            # Mock efficiency calculation - in production would use actual times
            expected_duration = self._get_expected_duration(job.service_type)
            actual_duration = getattr(job, 'duration_hours', expected_duration)
            
            if actual_duration <= expected_duration:
                efficiency_scores.append(100.0)
            else:
                # Penalize overtime
                overtime_penalty = ((actual_duration - expected_duration) / expected_duration) * 50
                efficiency_scores.append(max(50, 100 - overtime_penalty))
        
        return sum(efficiency_scores) / len(efficiency_scores)
    
    def _calculate_customer_score(self, jobs: List[JobSchema]) -> float:
        """Calculate customer satisfaction score."""
        if not jobs:
            return 0.0
        
        # Mock customer ratings - in production would pull from actual feedback
        ratings = [getattr(job, 'customer_rating', 9.0) for job in jobs]
        avg_rating = sum(ratings) / len(ratings)
        
        # Convert 0-10 rating to 0-100 score
        return (avg_rating / 10) * 100
    
    def _get_expected_duration(self, service_type: str) -> float:
        """Get expected duration for service type."""
        durations = {
            "recurring": 2.5,
            "deep_cleaning": 4.0,
            "move_out_in": 5.0
        }
        return durations.get(service_type, 3.0)
    
    def _generate_recommendations(
        self, 
        quality: float, 
        reliability: float, 
        efficiency: float, 
        customer: float
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        if quality < 80:
            recommendations.append("Focus on photo quality and checklist completion")
        if reliability < 90:
            recommendations.append("Improve on-time arrival consistency")
        if efficiency < 80:
            recommendations.append("Work on time management and efficiency")
        if customer < 85:
            recommendations.append("Focus on customer communication and service quality")
        
        if not recommendations:
            recommendations.append("Maintain excellent performance standards")
        
        return recommendations


class GeographicOptimizer:
    """
    Geographic assignment optimization with contractor preferences.
    """
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="grime_guardians")
        
        # Metro area boundaries (rough coordinates)
        self.metro_areas = {
            "south": {"lat": 44.8, "lon": -93.2, "radius_km": 15},
            "east": {"lat": 44.95, "lon": -92.9, "radius_km": 12},
            "central": {"lat": 44.98, "lon": -93.26, "radius_km": 10},
            "north": {"lat": 45.1, "lon": -93.3, "radius_km": 18}
        }
    
    def optimize_assignment(
        self, 
        job: JobSchema,
        available_contractors: List[ContractorSchema],
        performance_scores: Dict[str, PerformanceMetrics]
    ) -> List[Tuple[ContractorSchema, float]]:
        """
        Optimize contractor assignment based on geography and performance.
        Returns ranked list of (contractor, score) tuples.
        """
        try:
            job_coords = self._get_job_coordinates(job.address)
            if not job_coords:
                logger.warning(f"Could not geocode job address: {job.address}")
                # Fall back to territory-based assignment
                return self._territory_based_assignment(job, available_contractors, performance_scores)
            
            contractor_scores = []
            
            for contractor in available_contractors:
                # Skip if contractor is not available
                if contractor.status != ContractorStatus.AVAILABLE:
                    continue
                
                # Calculate assignment score
                score = self._calculate_assignment_score(
                    contractor, job_coords, performance_scores.get(contractor.id)
                )
                
                contractor_scores.append((contractor, score))
            
            # Sort by score (highest first)
            contractor_scores.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Optimized assignment for {job.address}: {len(contractor_scores)} candidates")
            return contractor_scores
            
        except Exception as e:
            logger.error(f"Geographic optimization error: {e}")
            return self._territory_based_assignment(job, available_contractors, performance_scores)
    
    def _get_job_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for job address."""
        try:
            location = self.geocoder.geocode(f"{address}, Twin Cities, MN")
            if location:
                return (location.latitude, location.longitude)
            return None
        except Exception as e:
            logger.warning(f"Geocoding error for {address}: {e}")
            return None
    
    def _calculate_assignment_score(
        self, 
        contractor: ContractorSchema,
        job_coords: Tuple[float, float],
        performance: Optional[PerformanceMetrics]
    ) -> float:
        """
        Calculate assignment score combining distance, territory preference, and performance.
        """
        score = 0.0
        
        # Performance component (40% weight)
        if performance:
            score += performance.overall_score * 0.4
        else:
            score += 70 * 0.4  # Default score if no performance data
        
        # Territory preference component (30% weight)
        territory_score = self._calculate_territory_score(contractor, job_coords)
        score += territory_score * 0.3
        
        # Distance component (20% weight)
        distance_score = self._calculate_distance_score(contractor, job_coords)
        score += distance_score * 0.2
        
        # Availability component (10% weight)
        availability_score = self._calculate_availability_score(contractor)
        score += availability_score * 0.1
        
        return min(100, max(0, score))
    
    def _calculate_territory_score(
        self, 
        contractor: ContractorSchema, 
        job_coords: Tuple[float, float]
    ) -> float:
        """Calculate score based on contractor's preferred territory."""
        contractor_territory = getattr(contractor, 'preferred_territory', 'central')
        
        # Check if job is in contractor's preferred territory
        for territory, bounds in self.metro_areas.items():
            territory_center = (bounds["lat"], bounds["lon"])
            distance_km = geodesic(job_coords, territory_center).kilometers
            
            if distance_km <= bounds["radius_km"]:
                if territory == contractor_territory:
                    return 100.0  # Perfect match
                else:
                    return 60.0   # Out of territory but doable
        
        return 30.0  # Outside all territories
    
    def _calculate_distance_score(
        self, 
        contractor: ContractorSchema, 
        job_coords: Tuple[float, float]
    ) -> float:
        """Calculate score based on distance from contractor's location."""
        # Mock contractor location based on territory
        contractor_territory = getattr(contractor, 'preferred_territory', 'central')
        contractor_center = self.metro_areas.get(contractor_territory, self.metro_areas['central'])
        contractor_coords = (contractor_center["lat"], contractor_center["lon"])
        
        distance_km = geodesic(job_coords, contractor_coords).kilometers
        
        # Score decreases with distance
        if distance_km <= 10:
            return 100.0
        elif distance_km <= 20:
            return 80.0
        elif distance_km <= 30:
            return 60.0
        else:
            return 30.0
    
    def _calculate_availability_score(self, contractor: ContractorSchema) -> float:
        """Calculate availability score based on current workload."""
        # Mock availability calculation
        current_jobs = getattr(contractor, 'jobs_today', 0)
        max_jobs = getattr(contractor, 'max_jobs_per_day', 3)
        
        if current_jobs >= max_jobs:
            return 0.0
        elif current_jobs >= max_jobs * 0.8:
            return 50.0
        else:
            return 100.0
    
    def _territory_based_assignment(
        self, 
        job: JobSchema,
        available_contractors: List[ContractorSchema],
        performance_scores: Dict[str, PerformanceMetrics]
    ) -> List[Tuple[ContractorSchema, float]]:
        """Fallback assignment based on territory keywords in address."""
        address_lower = job.address.lower()

        # Territory detection matching GG Operating Manual dispatch rules
        if any(k in address_lower for k in ["blaine", "coon rapids", "anoka", "fridley", "mounds view", "shoreview"]):
            preferred_territory = "north"
        elif any(k in address_lower for k in ["minneapolis", "mpls"]):
            preferred_territory = "minneapolis"
        elif any(k in address_lower for k in ["saint paul", "st paul", "st. paul"]):
            preferred_territory = "saint_paul"
        elif any(k in address_lower for k in ["woodbury", "oakdale", "cottage grove", "lake elmo"]):
            preferred_territory = "east_metro"
        elif any(k in address_lower for k in ["minnetonka", "eden prairie", "edina"]):
            preferred_territory = "west_sw"
        elif any(k in address_lower for k in ["eagan", "burnsville", "apple valley", "lakeville"]):
            preferred_territory = "eagan"
        else:
            preferred_territory = "central"
        
        contractor_scores = []
        for contractor in available_contractors:
            if contractor.status != ContractorStatus.AVAILABLE:
                continue
            
            contractor_territory = getattr(contractor, 'preferred_territory', 'central')
            performance = performance_scores.get(contractor.id)
            
            # Base score from performance
            base_score = performance.overall_score if performance else 70
            
            # Territory bonus
            if contractor_territory == preferred_territory:
                territory_bonus = 20
            else:
                territory_bonus = 0
            
            final_score = min(100, base_score + territory_bonus)
            contractor_scores.append((contractor, final_score))
        
        contractor_scores.sort(key=lambda x: x[1], reverse=True)
        return contractor_scores


class ContractorManager:
    """
    Main contractor management system combining performance tracking and optimization.
    """
    
    def __init__(self):
        self.performance_scorer = PerformanceScorer()
        self.geographic_optimizer = GeographicOptimizer()
        self.pricing_engine = PricingEngine()
        
        # Cache for performance metrics
        self.performance_cache: Dict[str, PerformanceMetrics] = {}
        self.cache_expiry = timedelta(hours=1)
        self.last_cache_update = datetime.utcnow()
    
    async def calculate_pay_split(
        self, 
        job: JobSchema, 
        contractor: ContractorSchema,
        performance_bonus: bool = False
    ) -> PaySplitCalculation:
        """
        Calculate contractor pay split with performance bonuses.
        """
        try:
            # Get base pricing from pricing engine
            pricing_result = await self.pricing_engine.calculate_pricing(
                service_type=job.service_type,
                square_footage=job.square_footage,
                bedrooms=job.bedrooms,
                bathrooms=job.bathrooms,
                add_ons=job.add_ons or []
            )
            
            # Get contractor hourly rate
            contractor_rate = CONTRACTOR_PAY_RATES.get(contractor.id, Decimal("25.00"))
            
            # Estimate job duration
            estimated_hours = self._estimate_job_duration(job)
            
            # Base contractor pay
            base_pay = contractor_rate * Decimal(str(estimated_hours))
            
            # Performance bonus calculation
            bonus_amount = Decimal("0.00")
            if performance_bonus:
                performance = await self.get_contractor_performance(contractor.id, [])
                if performance.overall_score >= 90:
                    bonus_amount = base_pay * Decimal("0.10")  # 10% bonus for excellent performance
                elif performance.overall_score >= 80:
                    bonus_amount = base_pay * Decimal("0.05")  # 5% bonus for good performance
            
            total_contractor_pay = base_pay + bonus_amount
            
            # Company profit calculation
            total_customer_price = pricing_result.final_price_with_tax
            company_profit = total_customer_price - total_contractor_pay
            profit_margin = (company_profit / total_customer_price * 100) if total_customer_price > 0 else 0
            
            return PaySplitCalculation(
                job_id=job.id,
                contractor_id=contractor.id,
                customer_total=total_customer_price,
                contractor_base_pay=base_pay,
                performance_bonus=bonus_amount,
                total_contractor_pay=total_contractor_pay,
                company_profit=company_profit,
                profit_margin_percentage=float(profit_margin),
                hourly_rate=contractor_rate,
                estimated_hours=estimated_hours,
                calculation_date=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Pay split calculation error for job {job.id}: {e}")
            raise
    
    async def get_contractor_performance(
        self, 
        contractor_id: str, 
        job_history: List[JobSchema],
        force_refresh: bool = False
    ) -> PerformanceMetrics:
        """
        Get contractor performance metrics with caching.
        """
        try:
            # Check cache first
            if (not force_refresh and 
                contractor_id in self.performance_cache and
                datetime.utcnow() - self.last_cache_update < self.cache_expiry):
                return self.performance_cache[contractor_id]
            
            # Get contractor data
            contractor = await self._get_contractor_by_id(contractor_id)
            if not contractor:
                raise ValueError(f"Contractor {contractor_id} not found")
            
            # Get violation count (would be from database in production)
            violation_count = 0  # Mock data
            
            # Calculate performance
            performance = self.performance_scorer.calculate_performance_score(
                contractor, job_history, violation_count
            )
            
            # Update cache
            self.performance_cache[contractor_id] = performance
            self.last_cache_update = datetime.utcnow()
            
            return performance
            
        except Exception as e:
            logger.error(f"Performance retrieval error for {contractor_id}: {e}")
            raise
    
    async def optimize_job_assignment(
        self, 
        job: JobSchema,
        available_contractors: List[ContractorSchema]
    ) -> List[Tuple[ContractorSchema, float]]:
        """
        Optimize job assignment using geographic and performance data.
        """
        try:
            # Get performance scores for all contractors
            performance_scores = {}
            for contractor in available_contractors:
                try:
                    performance = await self.get_contractor_performance(contractor.id, [])
                    performance_scores[contractor.id] = performance
                except Exception as e:
                    logger.warning(f"Could not get performance for {contractor.id}: {e}")
                    # Continue with default performance
            
            # Use geographic optimizer
            optimized_assignments = self.geographic_optimizer.optimize_assignment(
                job, available_contractors, performance_scores
            )
            
            logger.info(f"Job assignment optimized: {len(optimized_assignments)} candidates ranked")
            return optimized_assignments
            
        except Exception as e:
            logger.error(f"Job assignment optimization error: {e}")
            # Return simple alphabetical fallback
            return [(contractor, 50.0) for contractor in available_contractors]
    
    def _estimate_job_duration(self, job: JobSchema) -> float:
        """Estimate job duration in hours."""
        base_durations = {
            "recurring": 2.5,
            "deep_cleaning": 4.0,
            "move_out_in": 5.0
        }
        
        base_time = base_durations.get(job.service_type, 3.0)
        
        # Adjust for size
        if job.square_footage:
            if job.square_footage > 2000:
                base_time *= 1.3
            elif job.square_footage > 1500:
                base_time *= 1.2
            elif job.square_footage < 1000:
                base_time *= 0.8
        
        # Adjust for add-ons
        if job.add_ons:
            base_time += len(job.add_ons) * 0.5
        
        return round(base_time, 2)
    
    async def _get_contractor_by_id(self, contractor_id: str) -> Optional[ContractorSchema]:
        """Get contractor by ID (mock implementation)."""
        # In production, this would query the database
        # Active teams per GG Operating Manual (Team Directory)
        mock_contractors = {
            "katy_crew": ContractorSchema(
                id="katy_crew",
                name="Katy + Crew",
                email="",
                phone="",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("0.00"),  # Per-job flat rate (30-50% by service type)
                preferred_territory="central",
                max_jobs_per_day=4
            ),
            "anna_oksana": ContractorSchema(
                id="anna_oksana",
                name="Anna + Oksana",
                email="",
                phone="",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("0.00"),
                preferred_territory="central",
                max_jobs_per_day=3
            ),
            "kateryna": ContractorSchema(
                id="kateryna",
                name="Kateryna",
                email="",
                phone="",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("0.00"),
                preferred_territory="north",
                max_jobs_per_day=2
            ),
            "liuda": ContractorSchema(
                id="liuda",
                name="Liuda",
                email="",
                phone="",
                status=ContractorStatus.AVAILABLE,
                hourly_rate=Decimal("0.00"),
                preferred_territory="north",
                max_jobs_per_day=2
            ),
        }

        return mock_contractors.get(contractor_id)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide contractor management metrics."""
        return {
            "cached_performances": len(self.performance_cache),
            "cache_age_minutes": (datetime.utcnow() - self.last_cache_update).total_seconds() / 60,
            "performance_scorer_weights": self.performance_scorer.scoring_weights,
            "metro_areas_configured": len(self.geographic_optimizer.metro_areas)
        }