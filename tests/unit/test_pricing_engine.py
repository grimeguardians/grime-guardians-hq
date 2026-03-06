"""
Unit tests for Pricing Engine
CRITICAL: These tests verify exact JavaScript logic preservation
"""

import pytest
from decimal import Decimal
from src.core.pricing_engine import PricingEngine, calculate_service_price, calculate_contractor_pay
from src.models.types import ServiceType
from src.models.schemas import PricingRequest


class TestPricingEngine:
    """Test exact pricing calculations against business rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = PricingEngine()
    
    def test_move_out_in_basic_pricing(self):
        """Test basic move-out/move-in pricing calculation."""
        result = self.engine.calculate_service_price(
            service_type=ServiceType.MOVE_OUT_IN,
            rooms=3,
            full_baths=2,
            half_baths=1
        )
        
        # Expected calculation:
        # Base: $300
        # Rooms: 3 × $30 = $90
        # Full baths: 2 × $60 = $120
        # Half baths: 1 × $30 = $30
        # Subtotal: $540
        # Tax (8.125%): $540 × 1.08125 = $583.88 (rounded)
        
        assert result.base_price == Decimal("300.00")
        assert result.room_charges == Decimal("90.00")
        assert result.bathroom_charges == Decimal("150.00")  # 120 + 30
        assert result.add_on_charges == Decimal("0.00")
        assert result.modifier_multiplier == Decimal("1.0")
        assert result.subtotal == Decimal("540.00")
        assert result.tax_amount == Decimal("43.88")  # 540 × 0.08125
        assert result.final_price == Decimal("583.88")
    
    def test_deep_cleaning_with_modifiers(self):
        """Test deep cleaning with pet homes and buildup modifiers."""
        result = self.engine.calculate_service_price(
            service_type=ServiceType.DEEP_CLEANING,
            rooms=2,
            full_baths=1,
            half_baths=0,
            modifiers={"pet_homes": True, "buildup": True}
        )
        
        # Expected calculation:
        # Base: $180
        # Rooms: 2 × $30 = $60
        # Full baths: 1 × $60 = $60
        # Subtotal before modifiers: $300
        # Pet modifier: ×1.10 = $330
        # Buildup modifier: ×1.20 = $396
        # Tax: $396 × 1.08125 = $428.18 (rounded)
        
        assert result.base_price == Decimal("180.00")
        assert result.room_charges == Decimal("60.00")
        assert result.bathroom_charges == Decimal("60.00")
        assert result.modifier_multiplier == Decimal("1.32")  # 1.10 × 1.20
        assert result.subtotal == Decimal("396.00")
        assert result.final_price == Decimal("428.18")
    
    def test_recurring_with_add_ons(self):
        """Test recurring service with add-ons."""
        result = self.engine.calculate_service_price(
            service_type=ServiceType.RECURRING,
            rooms=4,
            full_baths=2,
            half_baths=1,
            add_ons=["fridge_interior", "oven_interior", "carpet_shampooing"]
        )
        
        # Expected calculation:
        # Base: $120
        # Rooms: 4 × $30 = $120
        # Full baths: 2 × $60 = $120
        # Half baths: 1 × $30 = $30
        # Fridge: $60
        # Oven: $60
        # Carpet (4 rooms): 4 × $40 = $160
        # Subtotal: $670
        # Tax: $670 × 1.08125 = $724.44 (rounded)
        
        assert result.base_price == Decimal("120.00")
        assert result.room_charges == Decimal("120.00")
        assert result.bathroom_charges == Decimal("150.00")
        assert result.add_on_charges == Decimal("280.00")  # 60 + 60 + 160
        assert result.subtotal == Decimal("670.00")
        assert result.final_price == Decimal("724.44")
    
    def test_post_construction_square_footage(self):
        """Test post-construction pricing by square footage."""
        result = self.engine.calculate_service_price(
            service_type=ServiceType.POST_CONSTRUCTION,
            square_footage=2000
        )
        
        # Expected calculation:
        # Rate: $0.35/sq ft
        # Base: 2000 × $0.35 = $700
        # Tax: $700 × 1.08125 = $756.88 (rounded)
        
        assert result.base_price == Decimal("700.00")
        assert result.room_charges == Decimal("0.00")
        assert result.bathroom_charges == Decimal("0.00")
        assert result.final_price == Decimal("756.88")
    
    def test_hourly_rate_calculation(self):
        """Test hourly rate calculation."""
        result = self.engine.calculate_service_price(
            service_type=ServiceType.HOURLY,
            square_footage=5  # Using as hours
        )
        
        # Expected calculation:
        # Rate: $60/hour
        # Base: 5 × $60 = $300
        # Tax: $300 × 1.08125 = $324.38 (rounded)
        
        assert result.base_price == Decimal("300.00")
        assert result.final_price == Decimal("324.38")
    
    def test_commercial_requires_walkthrough(self):
        """Test that commercial pricing requires walkthrough."""
        with pytest.raises(ValueError, match="Commercial pricing requires walkthrough"):
            self.engine.calculate_service_price(
                service_type=ServiceType.COMMERCIAL,
                rooms=10
            )
    
    def test_tax_calculation_precision(self):
        """Test tax calculation precision with various amounts."""
        # Test edge cases for rounding
        test_cases = [
            (Decimal("100.00"), Decimal("108.13")),  # 100 × 1.08125
            (Decimal("50.00"), Decimal("54.06")),    # 50 × 1.08125
            (Decimal("33.33"), Decimal("36.04")),    # 33.33 × 1.08125
        ]
        
        for subtotal, expected_final in test_cases:
            result = self.engine.calculate_service_price(
                service_type=ServiceType.RECURRING,
                rooms=0,
                full_baths=0,
                half_baths=0
            )
            # Override base price for testing
            calculated_final = subtotal * self.engine.tax_multiplier
            calculated_final = calculated_final.quantize(Decimal("0.01"))
            assert calculated_final == expected_final
    
    def test_contractor_pay_calculations(self):
        """Test contractor pay split calculations."""
        final_price = Decimal("583.88")
        
        # Test base split (45/55)
        base_pay = calculate_contractor_pay(final_price, "jennifer", "base")
        assert base_pay["cleaner_pay"] == Decimal("262.75")  # 583.88 × 0.45
        assert base_pay["business_revenue"] == Decimal("321.13")  # 583.88 × 0.55
        assert base_pay["total_verified"] is True
        
        # Test top performer split (50/50)
        top_pay = calculate_contractor_pay(final_price, "jennifer", "top_performer")
        assert top_pay["cleaner_pay"] == Decimal("291.94")  # 583.88 × 0.50
        assert top_pay["business_revenue"] == Decimal("291.94")  # 583.88 × 0.50
        assert top_pay["total_verified"] is True
    
    def test_pricing_request_validation(self):
        """Test pricing request validation."""
        # Valid request
        valid_request = PricingRequest(
            service_type=ServiceType.MOVE_OUT_IN,
            rooms=3,
            full_baths=2,
            half_baths=1,
            add_ons=["fridge_interior"]
        )
        assert self.engine.validate_pricing_request(valid_request) is True
        
        # Invalid add-on
        invalid_request = PricingRequest(
            service_type=ServiceType.MOVE_OUT_IN,
            rooms=3,
            full_baths=2,
            half_baths=1,
            add_ons=["invalid_addon"]
        )
        assert self.engine.validate_pricing_request(invalid_request) is False
        
        # Post-construction without square footage
        invalid_post_construction = PricingRequest(
            service_type=ServiceType.POST_CONSTRUCTION,
            rooms=0,
            full_baths=0,
            half_baths=0
        )
        assert self.engine.validate_pricing_request(invalid_post_construction) is False
    
    def test_convenience_function(self):
        """Test convenience function wrapper."""
        result = calculate_service_price(
            service_type=ServiceType.MOVE_OUT_IN,
            rooms=2,
            full_baths=1,
            half_baths=0
        )
        
        # Should match engine calculation
        expected = self.engine.calculate_service_price(
            service_type=ServiceType.MOVE_OUT_IN,
            rooms=2,
            full_baths=1,
            half_baths=0
        )
        
        assert result.final_price == expected.final_price
        assert result.breakdown == expected.breakdown
    
    def test_pricing_estimate_ranges(self):
        """Test pricing estimate ranges."""
        # Commercial range
        commercial_range = self.engine.get_pricing_estimate_range(ServiceType.COMMERCIAL)
        assert commercial_range["min_hourly"] == 40
        assert commercial_range["max_hourly"] == 80
        
        # Standard service estimate
        move_out_estimate = self.engine.get_pricing_estimate_range(ServiceType.MOVE_OUT_IN)
        expected_base_with_tax = Decimal("300") * Decimal("1.08125")
        assert move_out_estimate["base_price_with_tax"] == float(expected_base_with_tax)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Zero rooms/baths
        result = self.engine.calculate_service_price(
            service_type=ServiceType.DEEP_CLEANING,
            rooms=0,
            full_baths=0,
            half_baths=0
        )
        assert result.base_price == Decimal("180.00")
        assert result.room_charges == Decimal("0.00")
        assert result.bathroom_charges == Decimal("0.00")
        
        # Maximum realistic values
        result = self.engine.calculate_service_price(
            service_type=ServiceType.MOVE_OUT_IN,
            rooms=20,
            full_baths=10,
            half_baths=10
        )
        # Should calculate without error
        assert result.final_price > Decimal("0")
        
        # Single carpet shampooing room
        result = self.engine.calculate_service_price(
            service_type=ServiceType.RECURRING,
            rooms=1,
            full_baths=0,
            half_baths=0,
            add_ons=["carpet_shampooing"]
        )
        # Should charge for at least 1 room of carpet shampooing
        assert result.add_on_charges == Decimal("40.00")


class TestPricingEngineIntegration:
    """Integration tests for pricing engine with business rules."""
    
    def test_real_world_scenarios(self):
        """Test real-world pricing scenarios from business."""
        engine = PricingEngine()
        
        # Scenario 1: Jennifer's typical south metro job
        jennifer_job = engine.calculate_service_price(
            service_type=ServiceType.MOVE_OUT_IN,
            rooms=3,
            full_baths=2,
            half_baths=1,
            add_ons=["fridge_interior", "oven_interior"],
            modifiers={"pet_homes": True}
        )
        
        # Verify calculation breakdown is detailed
        assert "service_type" in jennifer_job.breakdown
        assert "modifier_multiplier" in jennifer_job.breakdown
        assert jennifer_job.breakdown["tax_rate"] == "8.125%"
        
        # Scenario 2: Commercial estimate request
        with pytest.raises(ValueError):
            engine.calculate_service_price(
                service_type=ServiceType.COMMERCIAL,
                rooms=50
            )
        
        # Should use estimate range instead
        estimate = engine.get_pricing_estimate_range(ServiceType.COMMERCIAL)
        assert estimate["note"] == "Requires walkthrough for exact quote"