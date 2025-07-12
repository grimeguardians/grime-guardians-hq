from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any
from ..models.schemas import ServiceType, PricingRequest, PricingResponse
from ..config import PRICING_STRUCTURE, ADD_ONS, MODIFIERS, TAX_MULTIPLIER


class PricingEngine:
    """
    Exact migration of JavaScript pricing logic for Grime Guardians.
    
    CRITICAL: All calculations must preserve exact business logic.
    Tax multiplier (8.125%) must be applied to ALL quotes.
    """
    
    def __init__(self):
        self.pricing_structure = PRICING_STRUCTURE
        self.add_ons = ADD_ONS
        self.modifiers = MODIFIERS
        self.tax_multiplier = TAX_MULTIPLIER
    
    def calculate_service_price(
        self,
        service_type: ServiceType,
        rooms: int,
        full_baths: int,
        half_baths: int,
        square_footage: Optional[int] = None,
        add_ons: Optional[List[str]] = None,
        modifiers: Optional[Dict[str, bool]] = None
    ) -> PricingResponse:
        """
        Calculate total service price with exact business logic.
        
        Args:
            service_type: Type of cleaning service
            rooms: Number of rooms to clean
            full_baths: Number of full bathrooms
            half_baths: Number of half bathrooms
            square_footage: Square footage (for post-construction only)
            add_ons: List of additional services
            modifiers: Dictionary of pricing modifiers (pet_homes, buildup)
            
        Returns:
            PricingResponse with detailed breakdown
            
        Raises:
            ValueError: If invalid service type or parameters
        """
        if add_ons is None:
            add_ons = []
        if modifiers is None:
            modifiers = {}
            
        # Validate service type
        if service_type not in [st.value for st in ServiceType]:
            raise ValueError(f"Invalid service type: {service_type}")
            
        # Handle post-construction pricing (per square foot)
        if service_type == ServiceType.POST_CONSTRUCTION:
            if not square_footage:
                raise ValueError("Square footage required for post-construction pricing")
            return self._calculate_post_construction_price(square_footage, add_ons, modifiers)
            
        # Handle commercial pricing (requires walkthrough)
        if service_type == ServiceType.COMMERCIAL:
            return self._calculate_commercial_estimate(add_ons)
            
        # Handle hourly rate pricing
        if service_type == ServiceType.HOURLY:
            return self._calculate_hourly_estimate(add_ons)
            
        # Standard pricing calculation (move_out_in, deep_cleaning, recurring)
        return self._calculate_standard_price(
            service_type, rooms, full_baths, half_baths, add_ons, modifiers
        )
    
    def _calculate_standard_price(
        self,
        service_type: ServiceType,
        rooms: int,
        full_baths: int,
        half_baths: int,
        add_ons: List[str],
        modifiers: Dict[str, bool]
    ) -> PricingResponse:
        """Calculate pricing for standard services (move_out_in, deep_cleaning, recurring)."""
        
        # Get base pricing structure
        pricing = self.pricing_structure[service_type.value]
        
        # Base price calculation
        base_price = pricing["base"]
        room_charges = Decimal(str(rooms)) * pricing["room"]
        
        # Bathroom charges
        full_bath_charges = Decimal(str(full_baths)) * pricing["full_bath"]
        half_bath_charges = Decimal(str(half_baths)) * pricing["half_bath"]
        bathroom_charges = full_bath_charges + half_bath_charges
        
        # Calculate subtotal before add-ons and modifiers
        subtotal_before_addons = base_price + room_charges + bathroom_charges
        
        # Add-on charges
        addon_charges = self._calculate_addon_charges(add_ons, rooms)
        
        # Subtotal before modifiers
        subtotal_before_modifiers = subtotal_before_addons + addon_charges
        
        # Apply modifiers (percentage increases)
        modifier_adjustments = Decimal("0")
        modifier_multiplier = Decimal("1")
        
        if modifiers.get("pet_homes", False):
            pet_adjustment = subtotal_before_modifiers * (self.modifiers["pet_homes"] - Decimal("1"))
            modifier_adjustments += pet_adjustment
            modifier_multiplier *= self.modifiers["pet_homes"]
            
        if modifiers.get("buildup", False):
            buildup_adjustment = subtotal_before_modifiers * (self.modifiers["buildup"] - Decimal("1"))
            modifier_adjustments += buildup_adjustment
            modifier_multiplier *= self.modifiers["buildup"]
        
        # Subtotal after modifiers but before tax
        subtotal = subtotal_before_modifiers + modifier_adjustments
        
        # CRITICAL: Apply tax (8.125% = 1.08125 multiplier)
        tax_amount = subtotal * (self.tax_multiplier - Decimal("1"))
        total_price = subtotal * self.tax_multiplier
        
        # Round to 2 decimal places
        total_price = total_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Create detailed breakdown
        breakdown = {
            "base_price": float(base_price),
            "room_count": rooms,
            "room_rate": float(pricing["room"]),
            "room_charges": float(room_charges),
            "full_baths": full_baths,
            "half_baths": half_baths,
            "full_bath_rate": float(pricing["full_bath"]),
            "half_bath_rate": float(pricing["half_bath"]),
            "bathroom_charges": float(bathroom_charges),
            "add_ons": add_ons,
            "addon_charges": float(addon_charges),
            "modifiers_applied": modifiers,
            "modifier_adjustments": float(modifier_adjustments),
            "subtotal_before_tax": float(subtotal),
            "tax_rate": float(self.tax_multiplier - Decimal("1")),
            "tax_amount": float(tax_amount),
            "total_with_tax": float(total_price)
        }
        
        return PricingResponse(
            service_type=service_type,
            base_price=base_price,
            room_charges=room_charges,
            bathroom_charges=bathroom_charges,
            addon_charges=addon_charges,
            modifier_adjustments=modifier_adjustments,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_price=total_price,
            breakdown=breakdown
        )
    
    def _calculate_addon_charges(self, add_ons: List[str], rooms: int) -> Decimal:
        """Calculate charges for add-on services."""
        total_addon_charges = Decimal("0")
        
        for addon in add_ons:
            if addon not in self.add_ons:
                raise ValueError(f"Invalid add-on service: {addon}")
                
            addon_price = self.add_ons[addon]
            
            # Special handling for carpet shampooing (per room)
            if addon == "carpet_shampooing":
                total_addon_charges += addon_price * Decimal(str(rooms))
            else:
                total_addon_charges += addon_price
                
        return total_addon_charges
    
    def _calculate_post_construction_price(
        self,
        square_footage: int,
        add_ons: List[str],
        modifiers: Dict[str, bool]
    ) -> PricingResponse:
        """Calculate pricing for post-construction cleaning (per sq ft)."""
        
        rate_per_sqft = self.pricing_structure["post_construction"]["rate"]
        base_price = Decimal(str(square_footage)) * rate_per_sqft
        
        # Add-ons are not typically room-based for post-construction
        addon_charges = Decimal("0")
        for addon in add_ons:
            if addon in self.add_ons:
                addon_charges += self.add_ons[addon]
        
        # Apply modifiers
        modifier_adjustments = Decimal("0")
        subtotal_before_modifiers = base_price + addon_charges
        
        if modifiers.get("buildup", False):
            modifier_adjustments = subtotal_before_modifiers * (self.modifiers["buildup"] - Decimal("1"))
        
        subtotal = subtotal_before_modifiers + modifier_adjustments
        tax_amount = subtotal * (self.tax_multiplier - Decimal("1"))
        total_price = subtotal * self.tax_multiplier
        
        breakdown = {
            "square_footage": square_footage,
            "rate_per_sqft": float(rate_per_sqft),
            "base_calculation": f"{square_footage} sq ft × ${rate_per_sqft}/sq ft",
            "add_ons": add_ons,
            "addon_charges": float(addon_charges),
            "modifiers_applied": modifiers,
            "modifier_adjustments": float(modifier_adjustments),
            "subtotal_before_tax": float(subtotal),
            "tax_amount": float(tax_amount),
            "total_with_tax": float(total_price)
        }
        
        return PricingResponse(
            service_type=ServiceType.POST_CONSTRUCTION,
            base_price=base_price,
            room_charges=Decimal("0"),
            bathroom_charges=Decimal("0"),
            addon_charges=addon_charges,
            modifier_adjustments=modifier_adjustments,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_price=total_price,
            breakdown=breakdown
        )
    
    def _calculate_commercial_estimate(self, add_ons: List[str]) -> PricingResponse:
        """Generate estimate for commercial cleaning (requires walkthrough)."""
        
        # Commercial pricing requires walkthrough - provide range estimate
        hourly_min = self.pricing_structure["commercial"]["hourly_min"]
        hourly_max = self.pricing_structure["commercial"]["hourly_max"]
        
        breakdown = {
            "pricing_type": "estimate_range",
            "hourly_rate_range": f"${hourly_min}-${hourly_max}/hour",
            "note": "Requires on-site walkthrough for accurate quote",
            "add_ons_available": add_ons,
            "contact_required": True
        }
        
        return PricingResponse(
            service_type=ServiceType.COMMERCIAL,
            base_price=hourly_min,  # Show minimum as base
            room_charges=Decimal("0"),
            bathroom_charges=Decimal("0"),
            addon_charges=Decimal("0"),
            modifier_adjustments=Decimal("0"),
            subtotal=hourly_min,
            tax_amount=Decimal("0"),
            total_price=hourly_min,  # Minimum estimate
            breakdown=breakdown
        )
    
    def _calculate_hourly_estimate(self, add_ons: List[str]) -> PricingResponse:
        """Calculate hourly rate pricing for non-standard jobs."""
        
        hourly_rate = self.pricing_structure["hourly_rate"]
        
        breakdown = {
            "pricing_type": "hourly_rate",
            "hourly_rate": float(hourly_rate),
            "note": "Final price depends on actual time spent",
            "add_ons_available": add_ons,
            "minimum_charge": "1 hour"
        }
        
        return PricingResponse(
            service_type=ServiceType.HOURLY,
            base_price=hourly_rate,
            room_charges=Decimal("0"),
            bathroom_charges=Decimal("0"),
            addon_charges=Decimal("0"),
            modifier_adjustments=Decimal("0"),
            subtotal=hourly_rate,
            tax_amount=Decimal("0"),
            total_price=hourly_rate,
            breakdown=breakdown
        )
    
    def calculate_discount(self, total_price: Decimal, discount_percentage: Decimal) -> Decimal:
        """
        Calculate new client discount (15% - last resort only).
        
        Args:
            total_price: Original total price
            discount_percentage: Discount as decimal (0.15 for 15%)
            
        Returns:
            Discounted price
        """
        if discount_percentage < 0 or discount_percentage > Decimal("0.20"):
            raise ValueError("Discount percentage must be between 0 and 20%")
            
        discount_amount = total_price * discount_percentage
        discounted_price = total_price - discount_amount
        
        return discounted_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def validate_pricing_request(self, request: PricingRequest) -> bool:
        """
        Validate pricing request parameters.
        
        Args:
            request: PricingRequest to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        # Service-specific validations
        if request.service_type == ServiceType.POST_CONSTRUCTION:
            if not request.square_footage or request.square_footage <= 0:
                raise ValueError("Square footage required and must be > 0 for post-construction")
                
        if request.rooms < 0 or request.full_baths < 0 or request.half_baths < 0:
            raise ValueError("Room and bathroom counts must be >= 0")
            
        # Validate add-ons
        if request.add_ons:
            for addon in request.add_ons:
                if addon not in self.add_ons:
                    raise ValueError(f"Invalid add-on: {addon}")
                    
        # Validate modifiers
        if request.modifiers:
            for modifier in request.modifiers.keys():
                if modifier not in self.modifiers:
                    raise ValueError(f"Invalid modifier: {modifier}")
                    
        return True


# Global pricing engine instance
pricing_engine = PricingEngine()