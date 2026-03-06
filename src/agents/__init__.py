"""
Grime Guardians Agentic Suite - Agent Implementations
Complete 8-agent system following 12-factor methodology
"""

from .base_agent import BaseAgent, AgentTool, AgentManager
from .ava_orchestrator import AvaOrchestrator
from .sophia_booking_coordinator import SophiaBookingCoordinator
from .keith_checkin_tracker import KeithCheckinTracker
from .maya_coaching_agent import MayaCoachingAgent
from .dmitri_escalation_agent import DmitriEscalationAgent
from .remaining_specialists import (
    IrisOnboardingAgent,
    BrunoBonusTracker,
    AidenAnalyticsAgent
)
from .dean_cmo_agent import DeanCMOAgent
from .emma_cxo_agent import EmmaCXOAgent
from .brandon_ceo_agent import BrandonCEOAgent

__all__ = [
    # Base framework
    "BaseAgent",
    "AgentTool", 
    "AgentManager",
    
    # COO Operations Team (Ava + 5 specialists)
    "AvaOrchestrator",           # COO - Master coordination and business rule enforcement
    "SophiaBookingCoordinator",  # Operations scheduling and logistics coordination
    "KeithCheckinTracker",       # Contractor status monitoring and geographic optimization
    "MayaCoachingAgent",         # Performance coaching and skill development
    "DmitriEscalationAgent",     # Operations escalation and quality enforcement
    "IrisOnboardingAgent",       # New contractor onboarding and training
    "BrunoBonusTracker",         # Referral bonuses and recognition system
    
    # CFO Analytics (separate from operations)
    "AidenAnalyticsAgent",       # CFO - Financial analytics and revenue reporting
    
    # C-Suite Executive Leadership
    "DeanCMOAgent",             # CMO - Sales, quotes, marketing, customer acquisition
    "EmmaCXOAgent",             # CXO - Customer experience, support, complaints, satisfaction
    "BrandonCEOAgent"           # CEO - Strategic decisions, escalations, partnerships, vision
]

# Agent factory for easy instantiation
def create_agent(agent_id: str, business_context=None):
    """
    Factory function to create agents by ID.
    
    Args:
        agent_id: One of 'ava', 'sophia', 'keith', 'maya', 'dmitri', 'iris', 'bruno', 'aiden', 'dean', 'emma', 'brandon'
        business_context: Optional BusinessContext for agent initialization
    
    Returns:
        Instantiated agent of the specified type
    """
    agent_classes = {
        # COO Operations Team
        "ava": AvaOrchestrator,
        "sophia": SophiaBookingCoordinator,
        "keith": KeithCheckinTracker,
        "maya": MayaCoachingAgent,
        "dmitri": DmitriEscalationAgent,
        "iris": IrisOnboardingAgent,
        "bruno": BrunoBonusTracker,
        # CFO Analytics
        "aiden": AidenAnalyticsAgent,
        # C-Suite Leadership
        "dean": DeanCMOAgent,
        "emma": EmmaCXOAgent,
        "brandon": BrandonCEOAgent
    }
    
    if agent_id not in agent_classes:
        raise ValueError(f"Unknown agent_id: {agent_id}. Available: {list(agent_classes.keys())}")
    
    return agent_classes[agent_id](business_context)

# Agent system initialization
async def initialize_agent_system(business_context=None):
    """
    Initialize the complete 11-agent system with C-Suite leadership.
    
    Args:
        business_context: Optional BusinessContext for all agents
    
    Returns:
        AgentManager with all agents registered and ready
    """
    manager = AgentManager()
    
    # Create and register all agents
    agent_ids = [
        # COO Operations Team
        "ava", "sophia", "keith", "maya", "dmitri", "iris", "bruno",
        # CFO Analytics
        "aiden",
        # C-Suite Leadership
        "dean", "emma", "brandon"
    ]
    
    for agent_id in agent_ids:
        agent = create_agent(agent_id, business_context)
        manager.register_agent(agent)
    
    return manager

# Singleton getters for direct agent access
def get_agent_manager():
    """Get singleton agent manager instance."""
    # This would typically maintain a global singleton
    # For now, return None to indicate initialization required
    return None

# Individual agent getters for the new C-Suite agents
from .dean_cmo_agent import get_dean_cmo_agent
from .emma_cxo_agent import get_emma_cxo_agent  
from .brandon_ceo_agent import get_brandon_ceo_agent

__all__.extend([
    "get_dean_cmo_agent",
    "get_emma_cxo_agent", 
    "get_brandon_ceo_agent",
    "get_agent_manager"
])