import pytest
from decimal import Decimal
from src.core.pricing_engine import PricingEngine
from src.models.schemas import ServiceType, PricingRequest


class TestPricingEngine:
    """Test suite for pricing engine accuracy and business rule compliance."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = PricingEngine()
    
    def test_move_out_in_pricing_basic(self):
        """Test basic move-out/move-in pricing calculation."""
        # Test case: 3 rooms, 2 full baths, 1 half bath
        result = self.engine.calculate_service_price(
            ServiceType.MOVE_OUT_IN,
            rooms=3,
            full_baths=2,
            half_baths=1
        )
        
        # Expected calculation:
        # Base: $300 + Rooms: 3×$30 + Full baths: 2×$60 + Half baths: 1×$30
        # = $300 + $90 + $120 + $30 = $540
        # Tax: $540 × 1.08125 = $583.88
        expected_subtotal = Decimal("540.00")
        expected_total = Decimal("583.88")  # With 8.125% tax
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
        assert result.service_type == ServiceType.MOVE_OUT_IN
    
    def test_deep_cleaning_pricing(self):
        """Test deep cleaning pricing calculation."""
        result = self.engine.calculate_service_price(
            ServiceType.DEEP_CLEANING,
            rooms=2,
            full_baths=1,
            half_baths=0
        )
        
        # Expected: $180 + 2×$30 + 1×$60 = $300
        # Tax: $300 × 1.08125 = $324.38
        expected_subtotal = Decimal("300.00")
        expected_total = Decimal("324.38")
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_recurring_pricing(self):
        """Test recurring maintenance pricing."""
        result = self.engine.calculate_service_price(
            ServiceType.RECURRING,
            rooms=4,
            full_baths=2,
            half_baths=1
        )
        
        # Expected: $120 + 4×$30 + 2×$60 + 1×$30 = $390
        # Tax: $390 × 1.08125 = $421.69
        expected_subtotal = Decimal("390.00")
        expected_total = Decimal("421.69")
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_pet_homes_modifier(self):
        """Test pet homes modifier (+10%)."""
        result = self.engine.calculate_service_price(
            ServiceType.MOVE_OUT_IN,
            rooms=2,
            full_baths=1,
            half_baths=0,
            modifiers={"pet_homes": True}
        )
        
        # Base calculation: $300 + 2×$30 + 1×$60 = $420
        # Pet modifier: $420 × 1.10 = $462
        # Tax: $462 × 1.08125 = $499.38
        expected_subtotal = Decimal("462.00")
        expected_total = Decimal("499.38")
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_buildup_modifier(self):
        """Test buildup modifier (+20%)."""
        result = self.engine.calculate_service_price(
            ServiceType.DEEP_CLEANING,
            rooms=1,
            full_baths=1,
            half_baths=0,
            modifiers={"buildup": True}
        )
        
        # Base calculation: $180 + 1×$30 + 1×$60 = $270
        # Buildup modifier: $270 × 1.20 = $324
        # Tax: $324 × 1.08125 = $350.25
        expected_subtotal = Decimal("324.00")
        expected_total = Decimal("350.25")
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_combined_modifiers(self):
        """Test both pet homes and buildup modifiers."""
        result = self.engine.calculate_service_price(
            ServiceType.MOVE_OUT_IN,
            rooms=2,
            full_baths=1,
            half_baths=0,
            modifiers={"pet_homes": True, "buildup": True}
        )
        
        # Base calculation: $300 + 2×$30 + 1×$60 = $420
        # Pet modifier: $420 × 1.10 = $462
        # Buildup modifier: $462 × 1.20 = $554.40
        # Tax: $554.40 × 1.08125 = $599.51
        expected_subtotal = Decimal("554.40")
        expected_total = Decimal("599.51")
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_add_ons_basic(self):
        """Test basic add-on services."""
        result = self.engine.calculate_service_price(
            ServiceType.DEEP_CLEANING,
            rooms=1,
            full_baths=1,
            half_baths=0,
            add_ons=["fridge_interior", "oven_interior"]
        )
        
        # Base: $180 + 1×$30 + 1×$60 = $270
        # Add-ons: $60 + $60 = $120
        # Subtotal: $270 + $120 = $390
        # Tax: $390 × 1.08125 = $421.69
        expected_subtotal = Decimal("390.00")
        expected_total = Decimal("421.69")
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
        assert result.addon_charges == Decimal("120.00")
    
    def test_carpet_shampooing_addon(self):
        """Test carpet shampooing add-on (per room)."""
        result = self.engine.calculate_service_price(
            ServiceType.DEEP_CLEANING,
            rooms=3,
            full_baths=1,
            half_baths=0,
            add_ons=["carpet_shampooing"]
        )
        
        # Base: $180 + 3×$30 + 1×$60 = $330
        # Carpet shampooing: 3 rooms × $40 = $120
        # Subtotal: $330 + $120 = $450
        # Tax: $450 × 1.08125 = $486.56
        expected_addon_charges = Decimal("120.00")  # 3 rooms × $40
        expected_subtotal = Decimal("450.00")
        expected_total = Decimal("486.56")
        
        assert result.addon_charges == expected_addon_charges
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_post_construction_pricing(self):
        """Test post-construction pricing (per square foot)."""
        result = self.engine.calculate_service_price(
            ServiceType.POST_CONSTRUCTION,
            rooms=0,  # Not used for post-construction
            full_baths=0,
            half_baths=0,
            square_footage=1200
        )
        
        # Expected: 1200 sq ft × $0.35 = $420
        # Tax: $420 × 1.08125 = $454.13
        expected_subtotal = Decimal("420.00")
        expected_total = Decimal("454.13")
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_post_construction_with_buildup(self):
        """Test post-construction with buildup modifier."""
        result = self.engine.calculate_service_price(
            ServiceType.POST_CONSTRUCTION,
            rooms=0,
            full_baths=0,
            half_baths=0,
            square_footage=1000,
            modifiers={"buildup": True}
        )
        
        # Base: 1000 sq ft × $0.35 = $350
        # Buildup: $350 × 1.20 = $420
        # Tax: $420 × 1.08125 = $454.13
        expected_subtotal = Decimal("420.00")
        expected_total = Decimal("454.13")
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_commercial_estimate(self):
        """Test commercial pricing estimate."""
        result = self.engine.calculate_service_price(
            ServiceType.COMMERCIAL,
            rooms=0,
            full_baths=0,
            half_baths=0
        )
        
        # Commercial returns minimum hourly rate as estimate
        assert result.base_price == Decimal("40.00")  # Minimum hourly rate
        assert "walkthrough" in result.breakdown["note"].lower()
    
    def test_hourly_pricing(self):
        """Test hourly rate pricing."""
        result = self.engine.calculate_service_price(
            ServiceType.HOURLY,
            rooms=0,
            full_baths=0,
            half_baths=0
        )
        
        # Hourly rate is $60/hour
        assert result.base_price == Decimal("60.00")
        assert "hourly_rate" in result.breakdown["pricing_type"]
    
    def test_discount_calculation(self):
        """Test new client discount calculation."""
        original_price = Decimal("400.00")
        discount_percentage = Decimal("0.15")  # 15%
        
        discounted_price = self.engine.calculate_discount(original_price, discount_percentage)
        expected_price = Decimal("340.00")  # $400 - 15% = $340
        
        assert discounted_price == expected_price
    
    def test_pricing_request_validation(self):
        """Test pricing request validation."""
        # Valid request
        valid_request = PricingRequest(
            service_type=ServiceType.MOVE_OUT_IN,
            rooms=3,
            full_baths=2,
            half_baths=1
        )
        
        assert self.engine.validate_pricing_request(valid_request) is True
        
        # Invalid request - post-construction without square footage
        invalid_request = PricingRequest(
            service_type=ServiceType.POST_CONSTRUCTION,
            rooms=0,
            full_baths=0,
            half_baths=0
            # Missing square_footage
        )
        
        with pytest.raises(ValueError, match="Square footage required"):
            self.engine.validate_pricing_request(invalid_request)
    
    def test_tax_application_consistency(self):
        """Test that tax is consistently applied to all pricing scenarios."""
        test_cases = [
            (ServiceType.MOVE_OUT_IN, {"rooms": 2, "full_baths": 1, "half_baths": 0}),
            (ServiceType.DEEP_CLEANING, {"rooms": 3, "full_baths": 2, "half_baths": 1}),
            (ServiceType.RECURRING, {"rooms": 1, "full_baths": 1, "half_baths": 0}),
        ]
        
        for service_type, params in test_cases:
            result = self.engine.calculate_service_price(
                service_type,
                **params
            )
            
            # Verify tax calculation
            expected_tax = result.subtotal * (Decimal("1.08125") - Decimal("1"))
            assert result.tax_amount == expected_tax
            
            # Verify total calculation
            expected_total = result.subtotal * Decimal("1.08125")
            assert result.total_price == expected_total
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Zero rooms, zero baths (minimum service)
        result = self.engine.calculate_service_price(
            ServiceType.RECURRING,
            rooms=0,
            full_baths=0,
            half_baths=0
        )
        
        # Should be base price + tax
        expected_subtotal = Decimal("120.00")  # Base recurring price
        expected_total = Decimal("129.75")  # With tax
        
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total
    
    def test_precision_and_rounding(self):
        """Test decimal precision and rounding consistency."""
        result = self.engine.calculate_service_price(
            ServiceType.MOVE_OUT_IN,
            rooms=3,
            full_baths=2,
            half_baths=1,
            modifiers={"pet_homes": True}
        )
        
        # All monetary values should be rounded to 2 decimal places
        assert result.total_price % Decimal("0.01") == 0
        assert result.subtotal % Decimal("0.01") == 0
        assert result.tax_amount % Decimal("0.01") == 0
    
    def test_complex_scenario(self):
        """Test complex pricing scenario with multiple modifiers and add-ons."""
        result = self.engine.calculate_service_price(
            ServiceType.MOVE_OUT_IN,
            rooms=4,
            full_baths=3,
            half_baths=2,
            add_ons=["fridge_interior", "oven_interior", "garage_cleaning", "carpet_shampooing"],
            modifiers={"pet_homes": True, "buildup": True}
        )
        
        # Base calculation: $300 + 4×$30 + 3×$60 + 2×$30 = $660
        # Add-ons: $60 + $60 + $100 + (4×$40) = $380
        # Subtotal before modifiers: $660 + $380 = $1040
        # Pet homes (+10%): $1040 × 1.10 = $1144
        # Buildup (+20%): $1144 × 1.20 = $1372.80
        # Tax: $1372.80 × 1.08125 = $1484.73
        
        expected_base = Decimal("300.00")
        expected_room_charges = Decimal("120.00")  # 4 × $30
        expected_bathroom_charges = Decimal("240.00")  # 3×$60 + 2×$30
        expected_addon_charges = Decimal("380.00")  # $60+$60+$100+(4×$40)
        expected_subtotal = Decimal("1372.80")
        expected_total = Decimal("1484.73")
        
        assert result.base_price == expected_base
        assert result.room_charges == expected_room_charges
        assert result.bathroom_charges == expected_bathroom_charges
        assert result.addon_charges == expected_addon_charges
        assert result.subtotal == expected_subtotal
        assert result.total_price == expected_total