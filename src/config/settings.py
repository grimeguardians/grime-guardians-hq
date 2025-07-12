from decimal import Decimal
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=8000, env="SERVER_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    production_mode: bool = Field(default=False, env="PRODUCTION_MODE")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    
    # AI Model Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    
    # Optional Claude fallback
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    # Discord Integration
    discord_bot_token: str = Field(..., env="DISCORD_BOT_TOKEN")
    discord_bot_token_ava: Optional[str] = Field(None, env="DISCORD_BOT_TOKEN_AVA")
    discord_bot_token_dean: Optional[str] = Field(None, env="DISCORD_BOT_TOKEN_DEAN")
    discord_checkin_channel_id: str = Field(..., env="DISCORD_CHECKIN_CHANNEL_ID")
    discord_ops_lead_id: str = Field(..., env="DISCORD_OPS_LEAD_ID")
    ops_lead_discord_id: str = Field(..., env="OPS_LEAD_DISCORD_ID")
    
    # GoHighLevel Integration
    highlevel_api_key: str = Field(..., env="HIGHLEVEL_API_KEY")
    highlevel_location_id: str = Field(..., env="HIGHLEVEL_LOCATION_ID")
    highlevel_oauth_access_token: str = Field(..., env="HIGHLEVEL_OAUTH_ACCESS_TOKEN")
    highlevel_oauth_refresh_token: str = Field(..., env="HIGHLEVEL_OAUTH_REFRESH_TOKEN")
    highlevel_private_integration: str = Field(..., env="HIGHLEVEL_PRIVATE_INTEGRATION")
    highlevel_calendar_id: str = Field(..., env="HIGHLEVEL_CALENDAR_ID")
    highlevel_oauth_client_id: str = Field(..., env="HIGHLEVEL_OAUTH_CLIENT_ID")
    highlevel_oauth_client_secret: str = Field(..., env="HIGHLEVEL_OAUTH_CLIENT_SECRET")
    highlevel_oauth_redirect_uri: str = Field(..., env="HIGHLEVEL_OAUTH_REDIRECT_URI")
    highlevel_token_expiry: int = Field(default=0, env="HIGHLEVEL_TOKEN_EXPIRY")
    highlevel_api_v2_token: Optional[str] = Field(None, env="HIGHLEVEL_API_V2_TOKEN")
    disable_highlevel: bool = Field(default=False, env="DISABLE_HIGHLEVEL")
    demo_mode: bool = Field(default=False, env="DEMO_MODE")  # Disable mock data - use real CRM
    
    # Notion Integration
    notion_secret: str = Field(..., env="NOTION_SECRET")
    notion_attendance_db_id: str = Field(..., env="NOTION_ATTENDANCE_DB_ID")
    
    # Gmail Integration
    gmail_client_id: str = Field(..., env="GMAIL_CLIENT_ID")
    gmail_client_secret: str = Field(..., env="GMAIL_CLIENT_SECRET")
    gmail_refresh_token: str = Field(..., env="GMAIL_REFRESH_TOKEN")
    gmail_emails: str = Field(..., env="GMAIL_EMAILS")
    gmail_redirect_uri: str = Field(..., env="GMAIL_REDIRECT_URI")
    
    # Webhook Configuration
    webhook_secret: str = Field(..., env="WEBHOOK_SECRET")
    webhook_port: int = Field(default=3000, env="WEBHOOK_PORT")
    
    # Security Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    
    # Business Configuration
    business_name: str = Field(default="Grime Guardians", env="BUSINESS_NAME")
    business_email: str = Field(default="brandonr@grimeguardians.com", env="BUSINESS_EMAIL")
    business_phone: str = Field(default="", env="BUSINESS_PHONE")
    tax_rate: Decimal = Field(default=Decimal("0.08125"), env="TAX_RATE")
    annual_revenue_target: int = Field(default=300000, env="ANNUAL_REVENUE_TARGET")
    
    # Feature Flags
    enable_photo_validation: bool = Field(default=True, env="ENABLE_PHOTO_VALIDATION")
    enable_3_strike_system: bool = Field(default=True, env="ENABLE_3_STRIKE_SYSTEM")
    enable_automated_coaching: bool = Field(default=True, env="ENABLE_AUTOMATED_COACHING")
    enable_bonus_tracking: bool = Field(default=True, env="ENABLE_BONUS_TRACKING")
    enable_escalation_management: bool = Field(default=True, env="ENABLE_ESCALATION_MANAGEMENT")
    enable_performance_analytics: bool = Field(default=True, env="ENABLE_PERFORMANCE_ANALYTICS")
    
    # Agent Configuration
    agent_timeout_seconds: int = Field(default=30, env="AGENT_TIMEOUT_SECONDS")
    agent_max_retries: int = Field(default=3, env="AGENT_MAX_RETRIES")
    agent_concurrent_limit: int = Field(default=5, env="AGENT_CONCURRENT_LIMIT")
    
    # Agent-Specific Configuration
    ava_monitoring_interval: int = Field(default=300, env="AVA_MONITORING_INTERVAL")
    keith_checkin_timeout: int = Field(default=900, env="KEITH_CHECKIN_TIMEOUT")
    maya_coaching_cooldown: int = Field(default=3600, env="MAYA_COACHING_COOLDOWN")
    bruno_bonus_calc_interval: int = Field(default=86400, env="BRUNO_BONUS_CALC_INTERVAL")
    
    # Monitoring
    cost_monitoring_enabled: bool = Field(default=True, env="COST_MONITORING_ENABLED")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Business Constants
TAX_MULTIPLIER = Decimal("1.08125")  # 8.125% Minnesota tax

PRICING_STRUCTURE = {
    "move_out_in": {
        "base": Decimal("300"),
        "room": Decimal("30"),
        "full_bath": Decimal("60"),
        "half_bath": Decimal("30")
    },
    "deep_cleaning": {
        "base": Decimal("180"),
        "room": Decimal("30"),
        "full_bath": Decimal("60"),
        "half_bath": Decimal("30")
    },
    "recurring": {
        "base": Decimal("120"),
        "room": Decimal("30"),
        "full_bath": Decimal("60"),
        "half_bath": Decimal("30")
    },
    "post_construction": {
        "rate": Decimal("0.35")  # per sq ft
    },
    "commercial": {
        "hourly_min": Decimal("40"),
        "hourly_max": Decimal("80")
    },
    "hourly_rate": Decimal("60")
}

ADD_ONS = {
    "fridge_interior": Decimal("60"),
    "oven_interior": Decimal("60"),
    "cabinet_interior": Decimal("60"),
    "garage_cleaning": Decimal("100"),
    "carpet_shampooing": Decimal("40")  # per room
}

MODIFIERS = {
    "pet_homes": Decimal("1.10"),
    "buildup": Decimal("1.20")
}

PAY_STRUCTURE = {
    "base_split": {"cleaner": Decimal("0.45"), "business": Decimal("0.55")},
    "top_performer_split": {"cleaner": Decimal("0.50"), "business": Decimal("0.50")},
    "specific_rates": {
        "jennifer": Decimal("28"),
        "olga": Decimal("25"),
        "liuda": Decimal("30"),
        "zhanna": Decimal("25")
    },
    "referral_bonus": Decimal("25"),
    "violation_penalty": Decimal("10")
}

# GoHighLevel Calendar Configuration (by priority)
GOHIGHLEVEL_CALENDARS = {
    "cleaning_service": {
        "id": "sb6IQR2sx5JXOQqMgtf5",
        "name": "Cleaning service appointment",
        "priority": 1,
        "description": "Most important - main cleaning appointments",
        "responsible_agent": "ava",
        "focus": "residential_commercial_cleaning"
    },
    "walkthrough": {
        "id": "mhrQNqycH11jLZah5sJ6", 
        "name": "Walkthrough appointment",
        "priority": 2,
        "description": "Property walkthroughs and assessments",
        "responsible_agent": "sophia",
        "focus": "lead_qualification"
    },
    "commercial_walkthrough": {
        "id": "qXm41YUW2Cxc0stYERn8",
        "name": "Commercial Cleaning Walkthrough", 
        "priority": 3,
        "description": "Commercial prospects - Dean's sales focus",
        "responsible_agent": "dean",
        "focus": "commercial_lead_generation"
    }
}

QUALITY_REQUIREMENTS = {
    "photos": ["kitchen", "bathrooms", "entry_area", "impacted_rooms"],
    "checklist_types": ["move_in_out", "deep_cleaning", "recurring"],
    "enforcement": "3_strike_system"
}