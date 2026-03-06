"""
Pricing Engine - EXACT migration from JavaScript system
Critical: All calculations must match existing system exactly
Tax multiplier: 1.08125 (8.125% tax rate)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any
import logging

from ..models.types import ServiceType
from ..models.schemas import PricingRequest, PricingResponse
from ..config.settings import PRICING_STRUCTURE, ADD_ONS, MODIFIERS, get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PricingEngine:
    """
    Exact pricing calculation engine preserving JavaScript business logic.
    All financial calculations use Decimal for precision.
    """
    
    def __init__(self):
        self.tax_multiplier = Decimal(str(settings.tax_multiplier))  # 1.08125
        
    def calculate_service_price(
        self,
        service_type: ServiceType,
        rooms: int = 0,
        full_baths: int = 0,
        half_baths: int = 0,
        square_footage: Optional[int] = None,
        add_ons: Optional[List[str]] = None,
        modifiers: Optional[Dict[str, bool]] = None
    ) -> PricingResponse:
        """
        Calculate exact service pricing following business rules.
        
        CRITICAL: This must match the JavaScript implementation exactly.
        """
        try:
            add_ons = add_ons or []
            modifiers = modifiers or {}
            
            # Get base pricing structure
            if service_type == ServiceType.POST_CONSTRUCTION:
                if not square_footage:
                    raise ValueError("Square footage required for post-construction pricing")
                base_price = Decimal(str(PRICING_STRUCTURE["post_construction"]["rate"])) * Decimal(str(square_footage))
                room_charges = Decimal("0")
                bathroom_charges = Decimal("0")
            elif service_type == ServiceType.COMMERCIAL:
                # Commercial requires walkthrough - return hourly range
                raise ValueError("Commercial pricing requires walkthrough - use hourly rate")
            elif service_type == ServiceType.HOURLY:
                # Hourly rate calculation
                if not square_footage:  # Using square_footage as hours for hourly jobs
                    raise ValueError("Hours required for hourly pricing")
                base_price = Decimal(str(PRICING_STRUCTURE["hourly_rate"])) * Decimal(str(square_footage))
                room_charges = Decimal("0")
                bathroom_charges = Decimal("0")
            else:
                # Standard service types: move_out_in, deep_cleaning, recurring
                service_config = PRICING_STRUCTURE[service_type.value]
                base_price = Decimal(str(service_config["base"]))
                
                # Room and bathroom charges
                room_modifier = Decimal(str(service_config["room"]))
                full_bath_modifier = Decimal(str(service_config["full_bath"]))
                half_bath_modifier = Decimal(str(service_config["half_bath"]))
                
                room_charges = Decimal(str(rooms)) * room_modifier
                bathroom_charges = (
                    Decimal(str(full_baths)) * full_bath_modifier +
                    Decimal(str(half_baths)) * half_bath_modifier
                )
            
            # Calculate subtotal before modifiers
            subtotal_before_modifiers = base_price + room_charges + bathroom_charges
            
            # Add-on charges
            add_on_charges = Decimal("0")
            for add_on in add_ons:
                if add_on in ADD_ONS:
                    if add_on == "carpet_shampooing":
                        # Carpet shampooing is per room
                        total_rooms = max(1, rooms)  # At least 1 room
                        add_on_charges += Decimal(str(ADD_ONS[add_on])) * Decimal(str(total_rooms))
                    else:
                        add_on_charges += Decimal(str(ADD_ONS[add_on]))
                else:
                    logger.warning(f"Unknown add-on: {add_on}")
            
            # Apply add-ons
            subtotal_with_addons = subtotal_before_modifiers + add_on_charges
            
            # Apply modifiers (BEFORE tax)
            modifier_multiplier = Decimal("1.0")
            if modifiers.get("pet_homes", False):
                modifier_multiplier *= Decimal(str(MODIFIERS["pet_homes"]))
            if modifiers.get("buildup", False):
                modifier_multiplier *= Decimal(str(MODIFIERS["buildup"]))
            
            # Subtotal after modifiers
            subtotal = subtotal_with_addons * modifier_multiplier
            
            # Apply tax (CRITICAL: Always 8.125%)
            tax_amount = subtotal * (self.tax_multiplier - Decimal("1"))
            final_price = subtotal * self.tax_multiplier
            
            # Round to 2 decimal places
            base_price = base_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            room_charges = room_charges.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            bathroom_charges = bathroom_charges.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            add_on_charges = add_on_charges.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            tax_amount = tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            final_price = final_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
            # Create detailed breakdown for audit trail
            breakdown = {
                "service_type": service_type.value,
                "base_price": float(base_price),
                "rooms": rooms,
                "room_charges": float(room_charges),
                "full_baths": full_baths,
                "half_baths": half_baths,
                "bathroom_charges": float(bathroom_charges),
                "add_ons": add_ons,
                "add_on_charges": float(add_on_charges),
                "modifiers": modifiers,
                "modifier_multiplier": float(modifier_multiplier),
                "subtotal_before_tax": float(subtotal),
                "tax_rate": "8.125%",
                "tax_amount": float(tax_amount),
                "final_price": float(final_price),
                "calculation_timestamp": None  # Will be set by caller
            }
            
            logger.info(f"Pricing calculation completed: {service_type.value} = ${final_price}")
            
            return PricingResponse(
                service_type=service_type,
                base_price=base_price,
                room_charges=room_charges,
                bathroom_charges=bathroom_charges,
                add_on_charges=add_on_charges,
                modifier_multiplier=modifier_multiplier,
                subtotal=subtotal,
                tax_amount=tax_amount,
                final_price=final_price,
                breakdown=breakdown
            )
            
        except Exception as e:
            logger.error(f"Pricing calculation error: {e}")
            raise
    
    def validate_pricing_request(self, request: PricingRequest) -> bool:
        """Validate pricing request parameters."""
        try:
            # Service type validation
            if request.service_type == ServiceType.POST_CONSTRUCTION and not request.square_footage:
                return False
            
            # Room/bath validation
            if request.rooms < 0 or request.full_baths < 0 or request.half_baths < 0:
                return False
            
            # Add-on validation
            if request.add_ons:
                valid_add_ons = set(ADD_ONS.keys())
                for add_on in request.add_ons:
                    if add_on not in valid_add_ons:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Pricing validation error: {e}")
            return False
    
    def get_pricing_estimate_range(self, service_type: ServiceType) -> Dict[str, float]:
        """Get pricing estimate ranges for service types."""
        if service_type == ServiceType.COMMERCIAL:
            return {
                "min_hourly": PRICING_STRUCTURE["commercial"]["hourly_range"][0],
                "max_hourly": PRICING_STRUCTURE["commercial"]["hourly_range"][1],
                "note": "Requires walkthrough for exact quote"
            }
        
        # Calculate base price with tax for estimate
        base_price = Decimal(str(PRICING_STRUCTURE[service_type.value]["base"]))
        base_with_tax = base_price * self.tax_multiplier
        
        return {
            "base_price_with_tax": float(base_with_tax),
            "note": "Additional charges may apply for rooms, bathrooms, and add-ons"
        }


# Convenience function for direct usage
def calculate_service_price(
    service_type: ServiceType,
    rooms: int = 0,
    full_baths: int = 0,
    half_baths: int = 0,
    square_footage: Optional[int] = None,
    add_ons: Optional[List[str]] = None,
    modifiers: Optional[Dict[str, bool]] = None
) -> PricingResponse:
    """Convenience function for pricing calculations."""
    engine = PricingEngine()
    return engine.calculate_service_price(
        service_type=service_type,
        rooms=rooms,
        full_baths=full_baths,
        half_baths=half_baths,
        square_footage=square_footage,
        add_ons=add_ons,
        modifiers=modifiers
    )


# Business rule validation functions
def validate_contractor_pricing_eligibility(contractor_id: str, service_type: ServiceType) -> bool:
    """Validate if contractor can handle specific service type pricing."""
    # Business logic for contractor service type restrictions
    # This preserves contractor independence by not controlling their work
    return True  # All contractors can handle all service types


def calculate_contractor_pay(
    final_price: Decimal,
    contractor_id: str,
    performance_tier: str = "base"
) -> Dict[str, Decimal]:
    """
    Calculate contractor pay based on split percentages.
    Preserves 1099 contractor independence.
    """
    from ..config.settings import PAY_STRUCTURE
    
    # Get pay split based on performance tier
    if performance_tier == "top_performer":
        split_config = PAY_STRUCTURE["top_performer_split"]
    else:
        split_config = PAY_STRUCTURE["base_split"]
    
    cleaner_percentage = Decimal(str(split_config["cleaner"])) / Decimal("100")
    business_percentage = Decimal(str(split_config["business"])) / Decimal("100")
    
    cleaner_pay = final_price * cleaner_percentage
    business_revenue = final_price * business_percentage
    
    return {
        "cleaner_pay": cleaner_pay.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "business_revenue": business_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "split_percentage": cleaner_percentage * Decimal("100"),
        "total_verified": cleaner_pay + business_revenue == final_price
    }