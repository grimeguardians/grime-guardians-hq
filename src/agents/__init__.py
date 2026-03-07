"""
Grime Guardians Agentic Suite - Agent Implementations
Complete agent system following 12-factor methodology.

All imports are lazy to avoid pulling in optional heavy dependencies
(cv2, PIL, etc.) unless those agents are explicitly used.
"""

__all__ = [
    # Base framework
    "BaseAgent",
    "AgentTool",
    "AgentManager",
    # COO Operations Team
    "AvaOrchestrator",
    "SophiaBookingCoordinator",
    "KeithCheckinTracker",
    "MayaCoachingAgent",
    "DmitriEscalationAgent",
    "IrisOnboardingAgent",
    "BrunoBonusTracker",
    # CFO Analytics
    "AidenAnalyticsAgent",
    # C-Suite Executive Leadership
    "DeanCMOAgent",
    "EmmaCXOAgent",
    "BrandonCEOAgent",
    # Getters
    "get_dean_cmo_agent",
    "get_emma_cxo_agent",
    "get_brandon_ceo_agent",
    "get_agent_manager",
    "create_agent",
    "initialize_agent_system",
]


def __getattr__(name):
    """Lazy-load agent classes and functions on first access."""
    _lazy_map = {
        "BaseAgent":               ("base_agent",                "BaseAgent"),
        "AgentTool":               ("base_agent",                "AgentTool"),
        "AgentManager":            ("base_agent",                "AgentManager"),
        "AvaOrchestrator":         ("ava_orchestrator",          "AvaOrchestrator"),
        "SophiaBookingCoordinator":("sophia_booking_coordinator","SophiaBookingCoordinator"),
        "KeithCheckinTracker":     ("keith_checkin_tracker",     "KeithCheckinTracker"),
        "MayaCoachingAgent":       ("maya_coaching_agent",       "MayaCoachingAgent"),
        "DmitriEscalationAgent":   ("dmitri_escalation_agent",   "DmitriEscalationAgent"),
        "IrisOnboardingAgent":     ("remaining_specialists",     "IrisOnboardingAgent"),
        "BrunoBonusTracker":       ("remaining_specialists",     "BrunoBonusTracker"),
        "AidenAnalyticsAgent":     ("remaining_specialists",     "AidenAnalyticsAgent"),
        "DeanCMOAgent":            ("dean_cmo_agent",            "DeanCMOAgent"),
        "EmmaCXOAgent":            ("emma_cxo_agent",            "EmmaCXOAgent"),
        "BrandonCEOAgent":         ("brandon_ceo_agent",         "BrandonCEOAgent"),
        "get_dean_cmo_agent":      ("dean_cmo_agent",            "get_dean_cmo_agent"),
        "get_emma_cxo_agent":      ("emma_cxo_agent",            "get_emma_cxo_agent"),
        "get_brandon_ceo_agent":   ("brandon_ceo_agent",         "get_brandon_ceo_agent"),
    }
    if name in _lazy_map:
        module_name, attr = _lazy_map[name]
        import importlib
        mod = importlib.import_module(f".{module_name}", package=__name__)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_agent_manager():
    """Get singleton agent manager instance (initialization required)."""
    return None


def create_agent(agent_id: str, business_context=None):
    """
    Factory function to create agents by ID.

    Args:
        agent_id: One of 'ava', 'sophia', 'keith', 'maya', 'dmitri',
                  'iris', 'bruno', 'aiden', 'dean', 'emma', 'brandon'
        business_context: Optional BusinessContext for agent initialization

    Returns:
        Instantiated agent of the specified type
    """
    _id_map = {
        "ava":     ("ava_orchestrator",           "AvaOrchestrator"),
        "sophia":  ("sophia_booking_coordinator", "SophiaBookingCoordinator"),
        "keith":   ("keith_checkin_tracker",      "KeithCheckinTracker"),
        "maya":    ("maya_coaching_agent",         "MayaCoachingAgent"),
        "dmitri":  ("dmitri_escalation_agent",    "DmitriEscalationAgent"),
        "iris":    ("remaining_specialists",       "IrisOnboardingAgent"),
        "bruno":   ("remaining_specialists",       "BrunoBonusTracker"),
        "aiden":   ("remaining_specialists",       "AidenAnalyticsAgent"),
        "dean":    ("dean_cmo_agent",              "DeanCMOAgent"),
        "emma":    ("emma_cxo_agent",              "EmmaCXOAgent"),
        "brandon": ("brandon_ceo_agent",           "BrandonCEOAgent"),
    }
    if agent_id not in _id_map:
        raise ValueError(
            f"Unknown agent_id: {agent_id!r}. Available: {list(_id_map)}"
        )
    import importlib
    module_name, cls_name = _id_map[agent_id]
    mod = importlib.import_module(f".{module_name}", package=__name__)
    cls = getattr(mod, cls_name)
    return cls(business_context)


async def initialize_agent_system(business_context=None):
    """
    Initialize the complete 11-agent system with C-Suite leadership.

    Args:
        business_context: Optional BusinessContext for all agents

    Returns:
        AgentManager with all agents registered and ready
    """
    from .base_agent import AgentManager
    manager = AgentManager()
    agent_ids = [
        "ava", "sophia", "keith", "maya", "dmitri", "iris", "bruno",
        "aiden", "dean", "emma", "brandon",
    ]
    for agent_id in agent_ids:
        agent = create_agent(agent_id, business_context)
        manager.register_agent(agent)
    return manager