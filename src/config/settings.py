"""
Grime Guardians Agentic Suite Configuration
Environment-based configuration following 12-factor methodology
Enhanced to work with your existing .env file
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import lru_cache
from decimal import Decimal

# Try to load python-dotenv if available
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")


class Settings:
    """Application settings with environment variable support."""
    
    def __init__(self):
        # Application
        self.app_name: str = os.getenv("APP_NAME", "Grime Guardians Agentic Suite")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.environment: str = os.getenv("NODE_ENV", "development")
        self.production_mode: bool = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Database - Use your database or fallback to SQLite
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///./grime_guardians.db")
        self.database_pool_size: int = int(os.getenv("DB_POOL_MIN", "5"))
        self.database_max_overflow: int = int(os.getenv("DB_POOL_MAX", "20"))
        self.db_timeout: int = int(os.getenv("DB_TIMEOUT", "30"))
        
        # AI Services - Using your existing OpenAI key
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_timeout: int = int(os.getenv("OPENAI_TIMEOUT", "30"))
        self.openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        self.openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
        
        # Message Classification
        self.target_classification_accuracy: float = float(os.getenv("TARGET_CLASSIFICATION_ACCURACY", "0.90"))
        self.classification_confidence_threshold: float = float(os.getenv("CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.80"))
        
        # Discord Integration - Using your existing token
        self.discord_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
        self.discord_bot_token: str = self.discord_token  # Alias for compatibility
        self.discord_guild_id: Optional[str] = os.getenv("DISCORD_GUILD_ID")
        self.discord_client_id: Optional[str] = os.getenv("DISCORD_CLIENT_ID")
        
        # Your existing Discord IDs
        self.discord_ops_lead_id: Optional[int] = int(os.getenv("DISCORD_OPS_LEAD_ID", "0")) or None
        self.discord_checkin_channel_id: Optional[int] = int(os.getenv("DISCORD_CHECKIN_CHANNEL_ID", "0")) or None
        self.ops_lead_discord_id: Optional[int] = int(os.getenv("OPS_LEAD_DISCORD_ID", "0")) or None
        
        # Enhanced Discord Channels for Agentic Suite
        self.discord_channel_jobs: str = os.getenv("DISCORD_JOBS_CHANNEL", "🪧-job-board")
        self.discord_channel_alerts: str = os.getenv("DISCORD_ALERTS_CHANNEL", "🚨-alerts")
        self.discord_strikes_channel: str = os.getenv("DISCORD_STRIKES_CHANNEL", "❌-strikes")
        self.discord_checkins_channel: str = os.getenv("DISCORD_CHECKINS_CHANNEL", "✔️-job-check-ins")
        self.discord_photos_channel: str = os.getenv("DISCORD_PHOTOS_CHANNEL", "📸-photo-submissions")
        
        # GoHighLevel CRM - Using your existing credentials
        self.gohighlevel_api_key: str = os.getenv("HIGHLEVEL_API_KEY", "")
        self.gohighlevel_location_id: str = os.getenv("HIGHLEVEL_LOCATION_ID", "")
        self.gohighlevel_webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
        self.highlevel_calendar_id: str = os.getenv("HIGHLEVEL_CALENDAR_ID", "")
        self.highlevel_oauth_client_id: str = os.getenv("HIGHLEVEL_OAUTH_CLIENT_ID", "")
        self.highlevel_oauth_client_secret: str = os.getenv("HIGHLEVEL_OAUTH_CLIENT_SECRET", "")
        self.highlevel_oauth_access_token: str = os.getenv("HIGHLEVEL_OAUTH_ACCESS_TOKEN", "")
        self.highlevel_oauth_refresh_token: str = os.getenv("HIGHLEVEL_OAUTH_REFRESH_TOKEN", "")
        self.highlevel_pit_token: str = os.getenv("HIGHLEVEL_PIT_TOKEN", "")
        self.disable_highlevel: bool = os.getenv("DISABLE_HIGHLEVEL", "false").lower() == "true"
        
        # Notion Integration - Using your existing credentials
        self.notion_token: str = os.getenv("NOTION_SECRET", "")
        self.notion_secret: str = self.notion_token  # Alias for compatibility
        self.notion_database_contractors: str = os.getenv("NOTION_ATTENDANCE_DB_ID", "")
        self.notion_database_jobs: str = os.getenv("NOTION_JOBS_DB_ID", "")
        self.notion_database_performance: str = os.getenv("NOTION_PERFORMANCE_DB_ID", "")
        
        # Gmail API - Using your existing credentials
        self.gmail_client_id: str = os.getenv("GMAIL_CLIENT_ID", "")
        self.gmail_client_secret: str = os.getenv("GMAIL_CLIENT_SECRET", "")
        self.gmail_refresh_token: str = os.getenv("GMAIL_REFRESH_TOKEN", "")
        self.gmail_emails: List[str] = os.getenv("GMAIL_EMAILS", "").split(",") if os.getenv("GMAIL_EMAILS") else []
        
        # Google Services
        self.google_service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
        self.google_drive_folder_id: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
        
        # File Storage
        self.local_storage_path: str = os.getenv("LOCAL_STORAGE_PATH", "./data/files")
        self.use_s3_storage: bool = os.getenv("USE_S3_STORAGE", "false").lower() == "true"
        self.max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        
        # AWS S3 Configuration
        self.aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region: str = os.getenv("AWS_REGION", "us-east-1")
        self.aws_s3_bucket: str = os.getenv("AWS_S3_BUCKET", "")
        
        # Email Configuration
        self.smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user: str = os.getenv("SMTP_USER", "")
        self.smtp_password: str = os.getenv("SMTP_PASSWORD", "")
        self.from_email: str = os.getenv("FROM_EMAIL", "noreply@grimeguardians.com")
        
        # Agent Configuration
        self.agent_timeout: int = int(os.getenv("AGENT_TIMEOUT", "30"))
        self.agent_max_retries: int = int(os.getenv("AGENT_MAX_RETRIES", "3"))
        self.agent_backoff_factor: float = float(os.getenv("AGENT_BACKOFF_FACTOR", "1.5"))
        self.max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "3"))
        
        # Business Rules
        self.tax_multiplier: Decimal = Decimal(os.getenv("TAX_MULTIPLIER", "1.08125"))
        self.max_strike_count: int = int(os.getenv("MAX_STRIKE_COUNT", "3"))
        self.checkin_buffer_minutes: int = int(os.getenv("CHECKIN_BUFFER_MINUTES", "15"))
        self.violation_penalty: Decimal = Decimal(os.getenv("VIOLATION_PENALTY", "50.00"))
        self.photo_quality_threshold: float = float(os.getenv("PHOTO_QUALITY_THRESHOLD", "6.0"))
        self.strike_reset_days: int = int(os.getenv("STRIKE_RESET_DAYS", "90"))
        
        # Security
        self.secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.jwt_secret: str = os.getenv("JWT_SECRET", "your-jwt-secret")
        self.webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
        self.webhook_port: int = int(os.getenv("WEBHOOK_PORT", "3000"))
        
        # Feature Flags
        self.enable_ai_classification: bool = os.getenv("ENABLE_AI_CLASSIFICATION", "true").lower() == "true"
        self.enable_photo_validation: bool = os.getenv("ENABLE_PHOTO_VALIDATION", "true").lower() == "true"
        self.enable_quality_enforcement: bool = os.getenv("ENABLE_QUALITY_ENFORCEMENT", "true").lower() == "true"
        self.enable_performance_scoring: bool = os.getenv("ENABLE_PERFORMANCE_SCORING", "true").lower() == "true"
        self.enable_discord_integration: bool = os.getenv("ENABLE_DISCORD_INTEGRATION", "true").lower() == "true"
        self.enable_database_operations: bool = os.getenv("ENABLE_DATABASE_OPERATIONS", "true").lower() == "true"
        
        # Monitoring & Cost Control - Using your existing settings
        self.cost_monitoring_enabled: bool = os.getenv("COST_MONITORING_ENABLED", "false").lower() == "true"
        self.enable_debug_logs: bool = os.getenv("ENABLE_DEBUG_LOGS", "false").lower() == "true"
        self.mock_external_apis: bool = os.getenv("MOCK_EXTERNAL_APIS", "false").lower() == "true"
        self.test_mode: bool = os.getenv("TEST_MODE", "false").lower() == "true"
        
        # Rate Limiting
        self.rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # Validate critical settings
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate that critical settings are present."""
        warnings = []
        errors = []
        
        # Critical for core functionality
        if not self.openai_api_key and not self.test_mode:
            errors.append("OPENAI_API_KEY is required for AI classification")
        
        # Important for Discord integration
        if self.enable_discord_integration and not self.discord_token and not self.mock_external_apis:
            warnings.append("DISCORD_BOT_TOKEN missing - Discord features will be disabled")
        
        # Important for CRM integration
        if not self.disable_highlevel and not self.gohighlevel_api_key:
            warnings.append("HIGHLEVEL_API_KEY missing - CRM integration will be limited")
        
        # Database validation
        if self.enable_database_operations and "postgresql" in self.database_url.lower():
            if not os.getenv("DB_USER") or not os.getenv("DB_PASSWORD"):
                warnings.append("PostgreSQL credentials missing - falling back to SQLite")
                self.database_url = "sqlite:///./grime_guardians.db"
        
        # Log warnings and errors
        if warnings:
            print("⚠️  Configuration Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
        
        if errors and not self.test_mode:
            print("❌ Configuration Errors:")
            for error in errors:
                print(f"   • {error}")
            print("   Set TEST_MODE=true to bypass validation for testing")
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL."""
        if self.test_mode:
            return "sqlite:///./test_grime_guardians.db"
        return self.database_url
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled."""
        feature_map = {
            "ai_classification": self.enable_ai_classification,
            "photo_validation": self.enable_photo_validation,
            "quality_enforcement": self.enable_quality_enforcement,
            "performance_scoring": self.enable_performance_scoring,
            "discord_integration": self.enable_discord_integration,
            "database_operations": self.enable_database_operations,
        }
        return feature_map.get(feature, False)


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# ============================================================
# BUSINESS CONSTANTS — Source of truth: GG Operating Manual
# ============================================================

# Revenue Targets (2026)
REVENUE_TARGETS = {
    "annual": 500_000,       # $500K gross by EOY 2026
    "monthly": 42_000,       # ~$42K/month run-rate
    "weekly": 9_615,         # ~$9,615/week
    "daily_jobs_min": 6,
    "daily_jobs_max": 10,
    "cleaner_efficiency_min": 7_500,  # $/month per cleaner
}

# Tiered Pricing Structure — flat rates by home size or unit type
# All prices are pre-tax. Tax (8.125%) applied at invoice generation.
PRICING_STRUCTURE = {
    # --- LEAD MAGNET / PAID TRIAL ---
    "elite_reset": {
        "description": "Elite Home Reset (CAC offer — break-even or slight loss)",
        "tiers": [
            {"label": "small",  "max_sqft": 2000, "price": 299,  "cleaner_pay": 150},
            {"label": "medium", "max_sqft": 3500, "price": 399,  "cleaner_pay": 200},
            {"label": "large",  "max_sqft": 5000, "price": 549,  "cleaner_pay": 275},
        ],
        "cleaner_pct": 0.50,
        "note": "Cleaner earns ~$40-50/hr effective. Company recovers via continuity.",
    },

    # --- MOVE-OUT (primary profit center) ---
    "listing_polish": {
        "description": "Elite Listing Polish — surface/photo-ready move-out",
        "tiers": [
            {"label": "studio_1bed", "max_sqft": 1200, "price": 549,  "cleaner_pay": 165},
            {"label": "2_3bed",      "max_sqft": 2500, "price": 749,  "cleaner_pay": 225},
            {"label": "4plus_estate","max_sqft": 99999,"price": 999,  "cleaner_pay": 300},
        ],
        "cleaner_pct": 0.30,
    },
    "deep_reset": {
        "description": "Move-Out Deep Reset — includes inside oven/fridge + deposit guarantee",
        "tiers": [
            {"label": "studio_1bed", "max_sqft": 1200, "price": 849,  "cleaner_pay": 255},
            {"label": "2_3bed",      "max_sqft": 2500, "price": 1149, "cleaner_pay": 345},
            {"label": "4plus_estate","max_sqft": 99999,"price": 1499, "cleaner_pay": 450},
        ],
        "cleaner_pct": 0.30,
    },

    # --- CONTINUITY PARTNERSHIPS (back-end revenue engine) ---
    "essentials": {
        "description": "Essentials Partnership — Maintenance Core Checklist",
        "tiers": [
            {"label": "small",  "max_sqft": 2000, "price": 299, "cleaner_pay": 120},
            {"label": "medium", "max_sqft": 3500, "price": 399, "cleaner_pay": 160},
            {"label": "large",  "max_sqft": 5000, "price": 499, "cleaner_pay": 200},
            {"label": "custom", "max_sqft": 99999,"price": None,"cleaner_pay": None},
        ],
        "cleaner_pct": 0.40,
    },
    "prestige": {
        "description": "Prestige Partnership — Maintenance + Detail Enhancers",
        "tiers": [
            {"label": "small",  "max_sqft": 2000, "price": 449, "cleaner_pay": 180},
            {"label": "medium", "max_sqft": 3500, "price": 549, "cleaner_pay": 220},
            {"label": "large",  "max_sqft": 5000, "price": 649, "cleaner_pay": 260},
            {"label": "custom", "max_sqft": 99999,"price": None,"cleaner_pay": None},
        ],
        "cleaner_pct": 0.40,
    },
    "vip_elite": {
        "description": "VIP Elite Partnership — Full 13-Point Elite Checklist + account notes",
        "tiers": [
            {"label": "small",  "max_sqft": 2000, "price": 799, "cleaner_pay": 320},
            {"label": "medium", "max_sqft": 3500, "price": 899, "cleaner_pay": 360},
            {"label": "large",  "max_sqft": 5000, "price": 999, "cleaner_pay": 400},
            {"label": "custom", "max_sqft": 99999,"price": None,"cleaner_pay": None},
        ],
        "cleaner_pct": 0.40,
    },

    # --- B2B TURNOVER (apartments / property managers) ---
    "b2b_turnover": {
        "description": "B2B Premium Turnover — exclusive volume rate for property managers",
        "tiers": [
            {"label": "studio",    "price": 399, "cleaner_pay": 120},
            {"label": "1bed_1bath","price": 499, "cleaner_pay": 150},
            {"label": "2bed_2bath","price": 599, "cleaner_pay": 180},
            {"label": "3bed_2bath","price": 699, "cleaner_pay": 210},
        ],
        "disaster_min": 900,
        "cleaner_pct": 0.30,
        "note": "Disaster clause (biohazard/hoarder) = $900+ with photo approval before work.",
    },

    # --- POST-CONSTRUCTION ---
    "post_construction": {
        "description": "Post-Construction Cleaning — per square foot",
        "rate_min": 0.25,
        "rate_max": 0.60,
        "rate_standard": 0.40,
        "cleaner_pct": 0.30,
    },

    # --- COMMERCIAL ---
    "commercial": {
        "description": "Commercial — monthly flat retainer (never bill hourly)",
        "target_effective_rate_min": 80,   # $/hr target
        "target_effective_rate_max": 100,
        "note": "Use A-Player Trial to determine time, then set flat monthly rate.",
        "cleaner_pct": 0.30,
    },

    # --- HOURLY (non-standard / specialty only) ---
    "hourly": {
        "description": "Hourly Rate — non-standard jobs only",
        "rate": 100,  # $100/hr customer-facing
    },

    # --- AFFLUENT CLIENT PACKAGES ---
    "quarterly_deep_reset": {
        "description": "Quarterly Deep Reset — high-margin one-time",
        "price_min": 600,
        "price_max": 900,
        "cleaner_pct": 0.40,
    },
    "autopilot_monthly": {
        "description": "Autopilot Home Maintenance — weekly deep cleans, multi-person crew",
        "price_min": 1000,
        "price_max": 1500,
        "cleaner_pct": 0.40,
    },
    "estate_protocol": {
        "description": "Zero-Bandwidth Estate Protocol — fractional house manager",
        "price_min": 3000,
        "price_max": 5000,
        "cleaner_pct": 0.40,
        "note": "Anchor price. Makes $1,500 autopilot feel like a deal.",
    },
}

# Add-Ons (margin boosters)
ADD_ONS = {
    "kitchen_perfection_bundle": 249,  # Fridge + Oven + Cabinets interior
    "oven_interior": 100,
    "fridge_interior": 100,
    "garage_sweep": 100,         # Cobwebs + shelves
    "carpet_shampooing": 40,     # Per area (room, hallway, staircase)
    "window_track": 4,           # Per track
}

# Modifiers applied to base price before tax
MODIFIERS = {
    "pet_homes": 1.10,   # +10%
    "buildup": 1.20,     # +20%
}

# Pay structure by job type
PAY_STRUCTURE = {
    "elite_reset":      {"cleaner_pct": 0.50, "company_pct": 0.50},
    "listing_polish":   {"cleaner_pct": 0.30, "company_pct": 0.70},
    "deep_reset":       {"cleaner_pct": 0.30, "company_pct": 0.70},
    "essentials":       {"cleaner_pct": 0.40, "company_pct": 0.60},
    "prestige":         {"cleaner_pct": 0.40, "company_pct": 0.60},
    "vip_elite":        {"cleaner_pct": 0.40, "company_pct": 0.60},
    "b2b_turnover":     {"cleaner_pct": 0.30, "company_pct": 0.70},
    "post_construction":{"cleaner_pct": 0.30, "company_pct": 0.70},
    "commercial":       {"cleaner_pct": 0.30, "company_pct": 0.70},
    "hourly_ranges": [
        {"label": "new_recruit_training", "min": 20, "max": 23},
        {"label": "standard_cleans",      "min": 23, "max": 26},
        {"label": "heavy_grime_lead",     "min": 26, "max": 30},
    ],
    "violation_penalty": 10,  # $ deduction per violation (after warning)
}

# Active contractor teams
CONTRACTOR_TEAMS = {
    "katy_crew": {
        "name": "Katy + Crew",
        "type": "subcontractor",
        "serves": ["south", "central", "west", "east"],
        "excludes": ["north"],
        "best_fit": ["move_out", "high_volume", "large_scope"],
        "notes": "Plug-and-play. Clear scope + strong job notes = best results.",
    },
    "anna_oksana": {
        "name": "Anna + Oksana",
        "type": "duo",
        "serves": ["south", "central", "west", "east", "north"],
        "excludes": [],
        "best_fit": ["move_out", "deep_clean", "post_construction"],
        "notes": "Strong speed + coverage. Must follow photo/checklist standards.",
    },
    "kateryna": {
        "name": "Kateryna",
        "type": "solo",
        "serves": ["north", "eagan", "minnetonka", "eden_prairie", "edina"],
        "excludes": ["minneapolis", "saint_paul", "woodbury", "east_metro"],
        "best_fit": ["recurring", "reset", "detail_work"],
        "notes": "High-standard recurring homes. Will NOT do Mpls/St. Paul or Woodbury+.",
    },
    "liuda": {
        "name": "Liuda",
        "type": "solo",
        "serves": ["north"],
        "excludes": ["south", "central", "west", "east"],
        "best_fit": ["recurring_north", "small_one_off"],
        "notes": "Northern region only.",
    },
}

# Territory dispatch priority (ordered: first = highest priority)
TERRITORY_DISPATCH = {
    "north":        ["liuda", "kateryna"],
    "eagan":        ["kateryna", "anna_oksana", "katy_crew"],
    "minnetonka":   ["kateryna", "anna_oksana", "katy_crew"],
    "eden_prairie": ["kateryna", "anna_oksana", "katy_crew"],
    "edina":        ["kateryna", "anna_oksana", "katy_crew"],
    "central":      ["kateryna", "anna_oksana", "katy_crew"],
    "west_sw":      ["kateryna", "anna_oksana", "katy_crew"],
    "minneapolis":  ["anna_oksana", "katy_crew"],
    "saint_paul":   ["anna_oksana", "katy_crew"],
    "east_metro":   ["anna_oksana", "katy_crew"],
    "south":        ["anna_oksana", "katy_crew"],
}

# Dispatch priority rules (in order)
DISPATCH_PRIORITY = [
    "territory_match",   # 1. Reduce drive time, increase acceptance
    "job_type_match",    # 2. Right team for the scope
    "consistency",       # 3. Same crew for recurring when possible
    "quality_risk",      # 4. No unproven recruits on high-stakes work
]

# Agent definitions
AGENT_CONFIG = {
    "ava":    {"name": "Ava",    "role": "COO / Master Orchestrator",       "priority": 1},
    "dean":   {"name": "Dean",   "role": "CMO / Sales & Marketing",         "priority": 1},
    "emma":   {"name": "Emma",   "role": "CXO / Customer Experience",       "priority": 2},
    "sophia": {"name": "Sophia", "role": "Booking Coordinator",             "priority": 2},
    "keith":  {"name": "Keith",  "role": "Check-in Tracker",                "priority": 2},
    "maya":   {"name": "Maya",   "role": "Performance Coach",               "priority": 3},
    "iris":   {"name": "Iris",   "role": "Contractor Onboarding",           "priority": 3},
    "dmitri": {"name": "Dmitri", "role": "Escalation & Issue Resolution",   "priority": 2},
    "bruno":  {"name": "Bruno",  "role": "Bonus & Referral Tracker",        "priority": 4},
    "aiden":  {"name": "Aiden",  "role": "Analytics & Financial Reporting", "priority": 3},
}

# Photo validation requirements
QUALITY_REQUIREMENTS = {
    "photos_required_for": [
        "elite_reset", "listing_polish", "deep_reset",
        "post_construction", "b2b_turnover", "vip_elite",
    ],
    "minimum_photos": ["kitchen_before", "kitchen_after", "bathroom_before",
                       "bathroom_after", "floors", "problem_areas"],
    "min_resolution": {"width": 800, "height": 600},
    "max_file_size_mb": 10,
    "allowed_formats": [".jpg", ".jpeg", ".png", ".webp"],
}

# Backward-compat alias (referenced by pricing_engine.py)
CONTRACTOR_PAY_RATES: dict = {}  # No individual hourly rates — use CONTRACTOR_TEAMS + PAY_STRUCTURE

# ─── GoHighLevel Calendar Configuration ──────────────────────────────────────
# Three calendars in GHL, queried in priority order.
# IDs sourced from the working agent-system project.
# To override a calendar ID, set HIGHLEVEL_CALENDAR_ID_<KEY> in .env
import os as _os

GHL_CALENDARS = {
    "cleaning_service": {
        "id": _os.getenv("HIGHLEVEL_CALENDAR_ID_CLEANING", "sb6IQR2sx5JXOQqMgtf5"),
        "name": "Cleaning service appointment",
        "priority": 1,
        "focus": "residential_commercial_cleaning",
        "responsible_agent": "ava",
    },
    "walkthrough": {
        "id": _os.getenv("HIGHLEVEL_CALENDAR_ID_WALKTHROUGH", "mhrQNqycH11jLZah5sJ6"),
        "name": "Walkthrough appointment",
        "priority": 2,
        "focus": "lead_qualification",
        "responsible_agent": "sophia",
    },
    "commercial_walkthrough": {
        "id": _os.getenv("HIGHLEVEL_CALENDAR_ID_COMMERCIAL", "qXm41YUW2Cxc0stYERn8"),
        "name": "Commercial Cleaning Walkthrough",
        "priority": 3,
        "focus": "commercial_lead_generation",
        "responsible_agent": "dean",
    },
}