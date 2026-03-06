"""
Unit tests for Base Agent Framework
Testing 12-factor methodology implementation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.agents.base_agent import BaseAgent, AgentManager, AgentState
from src.agents.ava_orchestrator import AvaOrchestrator
from src.models.schemas import AgentMessageSchema, AgentResponse
from src.models.types import MessageType, AgentStatus


class MockAgent(BaseAgent):
    """Mock agent for testing base functionality."""
    
    def __init__(self, agent_id: str = "test_agent"):
        # Mock the config lookup
        with patch('src.agents.base_agent.AGENT_CONFIG', {agent_id: {"name": "Test Agent", "role": "Testing", "priority": 1}}):
            super().__init__(agent_id)
    
    @property
    def system_prompt(self) -> str:
        return "You are a test agent for unit testing."
    
    def _register_tools(self):
        return []
    
    async def _handle_message_type(self, message_type, content, extracted_data):
        return AgentResponse(
            agent_id=self.agent_id,
            status="test_processed",
            response=f"Test response for {message_type.value}",
            actions_taken=["test_action"]
        )


class TestBaseAgent:
    """Test base agent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_agent = MockAgent()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.mock_agent.agent_id == "test_agent"
        assert self.mock_agent.status == AgentStatus.ACTIVE
        assert self.mock_agent.error_count == 0
        assert self.mock_agent.success_count == 0
        assert isinstance(self.mock_agent.last_activity, datetime)
    
    @pytest.mark.asyncio
    async def test_process_message_success(self):
        """Test successful message processing."""
        message = AgentMessageSchema(
            agent_id="test_agent",
            message_type=MessageType.STATUS_UPDATE,
            content="Test message content"
        )
        
        # Mock the message classifier
        with patch.object(self.mock_agent.message_classifier, 'classify_message') as mock_classify:
            mock_classify.return_value = (MessageType.STATUS_UPDATE, 0.95, {"test": "data"})
            
            response = await self.mock_agent.process_message(message)
            
            assert response.agent_id == "test_agent"
            assert response.status == "test_processed"
            assert response.processing_time is not None
            assert self.mock_agent.success_count == 1
            assert self.mock_agent.status == AgentStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self):
        """Test message processing error handling."""
        message = AgentMessageSchema(
            agent_id="test_agent",
            message_type=MessageType.STATUS_UPDATE,
            content="Test message content"
        )
        
        # Mock classification to raise an exception
        with patch.object(self.mock_agent.message_classifier, 'classify_message') as mock_classify:
            mock_classify.side_effect = Exception("Test error")
            
            response = await self.mock_agent.process_message(message)
            
            assert response.status == "error"
            assert "Test error" in response.response
            assert response.requires_escalation is True
            assert self.mock_agent.error_count == 1
            assert self.mock_agent.status == AgentStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_low_confidence_classification(self):
        """Test handling of low confidence classification."""
        message = AgentMessageSchema(
            agent_id="test_agent",
            message_type=MessageType.STATUS_UPDATE,
            content="Ambiguous message"
        )
        
        with patch.object(self.mock_agent.message_classifier, 'classify_message') as mock_classify:
            # Low confidence classification
            mock_classify.return_value = (MessageType.STATUS_UPDATE, 0.75, {"test": "data"})
            
            response = await self.mock_agent.process_message(message)
            
            # Should still process but log warning
            assert response.status == "test_processed"
            assert self.mock_agent.success_count == 1
    
    @pytest.mark.asyncio
    async def test_message_routing(self):
        """Test message routing to specialist agents."""
        message = AgentMessageSchema(
            agent_id="test_agent",
            message_type=MessageType.JOB_ASSIGNMENT,
            content="New job assignment"
        )
        
        # Mock should_handle_message_type to return False
        with patch.object(self.mock_agent, '_should_handle_message_type', return_value=False):
            with patch.object(self.mock_agent.message_classifier, 'classify_message') as mock_classify:
                mock_classify.return_value = (MessageType.JOB_ASSIGNMENT, 0.95, {"contractor": "jennifer"})
                
                response = await self.mock_agent.process_message(message)
                
                assert response.status == "routed"
                assert "sophia" in response.response  # Should route job assignments to Sophia
    
    @pytest.mark.asyncio
    async def test_openai_api_call(self):
        """Test OpenAI API integration."""
        messages = [
            {"role": "system", "content": "You are a test agent"},
            {"role": "user", "content": "Test message"}
        ]
        
        with patch.object(self.mock_agent.openai_client.chat.completions, 'create') as mock_create:
            # Mock OpenAI response
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "Test AI response"
            mock_response.choices[0].message.tool_calls = None
            mock_response.usage = AsyncMock()
            mock_response.usage.dict.return_value = {"total_tokens": 100}
            mock_create.return_value = mock_response
            
            response = await self.mock_agent.call_openai(messages)
            
            assert response["content"] == "Test AI response"
            assert response["tool_calls"] is None
            assert response["usage"]["total_tokens"] == 100
    
    @pytest.mark.asyncio 
    async def test_agent_pause_resume(self):
        """Test agent pause and resume functionality."""
        # Test pause
        await self.mock_agent.pause()
        assert self.mock_agent.status == AgentStatus.PAUSED
        
        # Test resume
        await self.mock_agent.resume()
        assert self.mock_agent.status == AgentStatus.ACTIVE
    
    def test_agent_state_retrieval(self):
        """Test agent state retrieval."""
        state = self.mock_agent.get_agent_state()
        
        assert isinstance(state, AgentState)
        assert state.agent_id == "test_agent"
        assert state.status == AgentStatus.ACTIVE
        assert state.error_count == 0
        assert state.success_count == 0
        assert isinstance(state.last_activity, datetime)
    
    def test_business_rule_validation(self):
        """Test business rule validation."""
        # Test contractor independence validation
        result = self.mock_agent._validate_business_rules(
            "mandate_schedule", 
            {"contractor": "jennifer"}
        )
        assert result is False  # Should violate contractor independence
        
        # Test valid action
        result = self.mock_agent._validate_business_rules(
            "notify_available_job",
            {"contractor": "jennifer"}
        )
        assert result is True
    
    def test_pricing_rule_validation(self):
        """Test pricing rule validation."""
        # Test pricing without tax
        result = self.mock_agent._validate_pricing_rules({"price": 100})
        assert result is False  # Should require tax application
        
        # Test pricing with tax
        result = self.mock_agent._validate_pricing_rules({"price": 100, "tax_applied": True})
        assert result is True
    
    def test_quality_enforcement_validation(self):
        """Test quality enforcement validation."""
        # Test 3rd strike without human approval
        result = self.mock_agent._validate_quality_enforcement({"strike_count": 3})
        assert result is False  # Should require human approval
        
        # Test 3rd strike with human approval
        result = self.mock_agent._validate_quality_enforcement({"strike_count": 3, "human_approval": True})
        assert result is True


class TestAvaOrchestrator:
    """Test Ava orchestrator specific functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the agent config
        with patch('src.agents.base_agent.AGENT_CONFIG', {"ava": {"name": "Ava Orchestrator", "role": "COO", "priority": 1}}):
            self.ava = AvaOrchestrator()
    
    def test_ava_initialization(self):
        """Test Ava initialization."""
        assert self.ava.agent_id == "ava"
        assert hasattr(self.ava, 'pricing_engine')
        assert hasattr(self.ava, 'kpi_thresholds')
        assert len(self.ava.tools) > 0
    
    def test_ava_system_prompt(self):
        """Test Ava's system prompt contains key business information."""
        prompt = self.ava.system_prompt
        
        # Check for key business elements
        assert "Master Orchestrator" in prompt
        assert "$300K" in prompt
        assert "8.125%" in prompt
        assert "Jennifer" in prompt
        assert "1099" in prompt
        assert "3-strike" in prompt
    
    def test_ava_tools_registration(self):
        """Test Ava's tools are properly registered."""
        tool_names = [tool.name for tool in self.ava.tools]
        
        expected_tools = [
            "coordinate_agents",
            "enforce_business_rules", 
            "monitor_kpis",
            "escalate_issue",
            "track_revenue_progress",
            "validate_contractor_compliance"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    def test_ava_message_type_handling(self):
        """Test which message types Ava should handle."""
        # Ava should handle coordination messages
        assert self.ava._should_handle_message_type(MessageType.ESCALATION) is True
        assert self.ava._should_handle_message_type(MessageType.COMPLIANCE_CHECK) is True
        assert self.ava._should_handle_message_type(MessageType.ANALYTICS_REPORT) is True
        
        # Ava should route specialist messages
        assert self.ava._should_handle_message_type(MessageType.JOB_ASSIGNMENT) is False
    
    @pytest.mark.asyncio
    async def test_ava_escalation_handling(self):
        """Test Ava's escalation handling."""
        content = "Quality issue with contractor Zhanna - 3rd violation"
        extracted_data = {
            "issue_type": "quality",
            "contractor_id": "zhanna",
            "severity": "high"
        }
        
        # Mock the violation count lookup
        with patch.object(self.ava, '_get_contractor_violation_count', return_value=2):
            response = await self.ava._handle_escalation(content, extracted_data)
            
            assert response.status == "escalation_handled"
            assert response.requires_escalation is True  # 3rd strike
            assert "3rd_strike_penalty_request" in response.actions_taken[0]
    
    @pytest.mark.asyncio
    async def test_ava_compliance_check(self):
        """Test Ava's compliance checking."""
        content = "Need to mandate Jennifer works specific hours tomorrow"
        extracted_data = {
            "contractor_id": "jennifer",
            "action_type": "scheduling_control"
        }
        
        response = await self.ava._handle_compliance_check(content, extracted_data)
        
        assert response.status == "compliance_checked"
        assert response.requires_escalation is True  # Should flag compliance issue
        assert "potential_employee_control_detected" in response.response
    
    @pytest.mark.asyncio
    async def test_ava_kpi_monitoring(self):
        """Test Ava's KPI monitoring."""
        # Mock KPI data with some alerts
        with patch.object(self.ava, '_get_current_kpis') as mock_kpis:
            mock_kpis.return_value = {
                "checklist_compliance": 85.0,  # Below threshold
                "photo_submission": 88.0,      # Below threshold
                "revenue_month": 18000         # Below target
            }
            
            response = await self.ava._handle_analytics_report("Weekly KPI report", {})
            
            assert response.status == "analytics_processed"
            assert response.requires_escalation is True
            assert "KPI ALERTS" in response.response
    
    @pytest.mark.asyncio
    async def test_ava_tool_coordination(self):
        """Test Ava's agent coordination tool."""
        result = await self.ava._tool_coordinate_agents(
            target_agents=["sophia", "keith"],
            coordination_type="assign",
            message="Coordinate job assignment",
            priority=2
        )
        
        assert result["coordinated_agents"] == 2
        assert len(result["results"]) == 2
        assert result["priority"] == 2
    
    @pytest.mark.asyncio
    async def test_ava_business_rule_enforcement(self):
        """Test Ava's business rule enforcement tool."""
        # Test contractor independence enforcement
        result = await self.ava._tool_enforce_business_rules(
            rule_type="contractor_independence",
            action="mandate_work_schedule",
            justification="Need coverage",
            entity_id="jennifer"
        )
        
        assert result["compliant"] is False
        assert "independence_violation_flagged" in result["enforcement_actions"]
    
    @pytest.mark.asyncio
    async def test_ava_revenue_tracking(self):
        """Test Ava's revenue tracking tool."""
        result = await self.ava._tool_track_revenue_progress(
            period="monthly",
            current_amount=20000,
            projection_needed=True
        )
        
        assert result["period"] == "monthly"
        assert result["current_amount"] == 20000
        assert result["target_amount"] == 25000
        assert result["progress_percentage"] == 80.0
        assert result["on_track"] is True  # 80% threshold
        assert "projection" in result
    
    def test_ava_kpi_thresholds(self):
        """Test Ava's KPI threshold configuration."""
        thresholds = self.ava.kpi_thresholds
        
        assert thresholds["checklist_compliance_min"] == 90.0
        assert thresholds["photo_submission_min"] == 90.0
        assert thresholds["monthly_revenue_min"] == 25000


class TestAgentManager:
    """Test agent manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = AgentManager()
        self.mock_agent = MockAgent("test_agent")
    
    def test_agent_registration(self):
        """Test agent registration."""
        self.manager.register_agent(self.mock_agent)
        
        assert "test_agent" in self.manager.agents
        assert "test_agent" in self.manager.agent_states
        assert self.manager.agent_states["test_agent"].agent_id == "test_agent"
    
    @pytest.mark.asyncio
    async def test_agent_launch_and_pause(self):
        """Test agent launch and pause functionality."""
        self.manager.register_agent(self.mock_agent)
        
        # Test launch
        result = await self.manager.launch_agent("test_agent")
        assert result is True
        assert self.manager.agents["test_agent"].status == AgentStatus.ACTIVE
        
        # Test pause
        result = await self.manager.pause_agent("test_agent")
        assert result is True
        assert self.manager.agents["test_agent"].status == AgentStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_agent_launch_nonexistent(self):
        """Test launching non-existent agent."""
        result = await self.manager.launch_agent("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_system_status(self):
        """Test system status reporting."""
        self.manager.register_agent(self.mock_agent)
        
        status = await self.manager.get_system_status()
        
        assert status["total_agents"] == 1
        assert status["active_agents"] == 1
        assert status["total_errors"] == 0
        assert status["total_successes"] == 0
        assert "agent_states" in status
        assert "test_agent" in status["agent_states"]
    
    @pytest.mark.asyncio
    async def test_message_routing(self):
        """Test message routing through manager."""
        self.manager.register_agent(self.mock_agent)
        
        message = AgentMessageSchema(
            agent_id="test_agent",
            message_type=MessageType.STATUS_UPDATE,
            content="Test message"
        )
        
        with patch.object(self.mock_agent.message_classifier, 'classify_message') as mock_classify:
            mock_classify.return_value = (MessageType.STATUS_UPDATE, 0.95, {})
            
            response = await self.manager.route_message(message)
            
            assert response.agent_id == "test_agent"
            assert response.status == "test_processed"


class TestAgentIntegration:
    """Integration tests for agent system."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self):
        """Test coordination between multiple agents."""
        manager = AgentManager()
        
        # Create multiple agents
        with patch('src.agents.base_agent.AGENT_CONFIG', {
            "ava": {"name": "Ava", "role": "COO", "priority": 1},
            "test": {"name": "Test", "role": "Test", "priority": 2}
        }):
            ava = AvaOrchestrator()
            test_agent = MockAgent("test")
            
            manager.register_agent(ava)
            manager.register_agent(test_agent)
            
            # Test system status with multiple agents
            status = await manager.get_system_status()
            assert status["total_agents"] == 2
    
    @pytest.mark.asyncio
    async def test_business_context_integration(self):
        """Test business context integration in agents."""
        from src.models.schemas import BusinessContext, KPISnapshot
        
        # Create business context
        kpi_snapshot = KPISnapshot(
            date=datetime.utcnow(),
            jobs_completed_today=5,
            active_contractors=8,
            checklist_compliance_rate=92.5,
            photo_submission_rate=88.0,
            revenue_today=1200.50,
            revenue_month_to_date=22500.75,
            violations_today=1,
            escalations_pending=0
        )
        
        business_context = BusinessContext(
            active_jobs=[],
            contractor_statuses=[],
            current_kpis=kpi_snapshot,
            pending_violations=[],
            agent_statuses=[]
        )
        
        with patch('src.agents.base_agent.AGENT_CONFIG', {"ava": {"name": "Ava", "role": "COO", "priority": 1}}):
            ava = AvaOrchestrator(business_context)
            
            assert ava.business_context is not None
            assert ava.business_context.current_kpis.jobs_completed_today == 5