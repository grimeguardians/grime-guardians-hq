"""
Tests for Dean's Email Agent Integration
Validates email campaign creation and management functionality
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from src.core.email_agent import EmailAgent, EmailCampaign, EmailLead, EmailTemplate
from src.core.dean_conversation import DeanConversationEngine


class TestEmailAgent:
    """Test Dean's Email Agent functionality."""
    
    @pytest.fixture
    def email_agent(self):
        """Create Email Agent instance for testing."""
        return EmailAgent()
    
    @pytest.fixture
    def sample_lead(self):
        """Create sample lead for testing."""
        return EmailLead(
            email="manager@propertyco.com",
            name="Sarah Johnson", 
            company="Metro Property Management",
            segment="property_managers",
            status="new"
        )
    
    def test_email_agent_initialization(self, email_agent):
        """Test Email Agent initializes correctly."""
        assert email_agent is not None
        assert len(email_agent.templates) > 0
        assert 'pm_value_first' in email_agent.templates
        assert 'realtor_pain_point' in email_agent.templates
        assert 'investor_roi_focus' in email_agent.templates
    
    def test_hormozi_frameworks_loaded(self, email_agent):
        """Test Hormozi methodology frameworks are loaded."""
        frameworks = email_agent.hormozi_frameworks
        
        assert 'value_equation' in frameworks
        assert 'email_frameworks' in frameworks
        assert 'response_triggers' in frameworks
        
        # Check value equation components
        value_eq = frameworks['value_equation']['application']
        assert 'dream_outcome' in value_eq
        assert 'perceived_likelihood' in value_eq
        assert 'time_delay' in value_eq
        assert 'effort_sacrifice' in value_eq
    
    @pytest.mark.asyncio
    async def test_create_campaign(self, email_agent):
        """Test campaign creation."""
        campaign_config = {
            'name': 'Property Manager Outreach Q1',
            'segment': 'property_managers',
            'template_type': 'pm_value_first'
        }
        
        campaign_id = await email_agent.create_campaign(campaign_config)
        
        assert campaign_id is not None
        assert campaign_id in email_agent.active_campaigns
        
        campaign = email_agent.active_campaigns[campaign_id]
        assert campaign.name == 'Property Manager Outreach Q1'
        assert campaign.target_segment == 'property_managers'
        assert campaign.status == 'draft'
        assert campaign.send_count == 0
    
    @pytest.mark.asyncio
    async def test_send_campaign_email(self, email_agent, sample_lead):
        """Test sending campaign email."""
        # Create campaign first
        campaign_config = {
            'name': 'Test Campaign',
            'segment': 'property_managers', 
            'template_type': 'pm_value_first'
        }
        campaign_id = await email_agent.create_campaign(campaign_config)
        
        # Send email
        result = await email_agent.send_campaign_email(campaign_id, sample_lead)
        
        assert result is True
        assert len(email_agent.pending_approvals) == 1
        
        # Check approval queue
        approval = email_agent.pending_approvals[0]
        assert approval['to'] == sample_lead.email
        assert approval['campaign_id'] == campaign_id
        assert 'template_id' in approval
    
    @pytest.mark.asyncio
    async def test_personalize_email(self, email_agent, sample_lead):
        """Test email personalization."""
        template = email_agent.templates['pm_value_first']
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            # Mock OpenAI response
            mock_response = Mock()
            mock_response.choices[0].message.content = "Hi Sarah, Quick insight from our work with Metro Properties..."
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            
            personalized = await email_agent._personalize_email(template, sample_lead)
            
            assert personalized is not None
            assert len(personalized) > 0
    
    @pytest.mark.asyncio
    async def test_monitor_inbox(self, email_agent):
        """Test inbox monitoring."""
        responses = await email_agent.monitor_inbox()
        
        assert isinstance(responses, list)
        # Should return mock data for testing
        assert len(responses) >= 0
    
    @pytest.mark.asyncio
    async def test_get_campaign_metrics(self, email_agent):
        """Test campaign metrics retrieval."""
        # Create campaign
        campaign_config = {
            'name': 'Test Metrics Campaign',
            'segment': 'realtors',
            'template_type': 'realtor_pain_point'
        }
        campaign_id = await email_agent.create_campaign(campaign_config)
        
        # Get metrics
        metrics = await email_agent.get_campaign_metrics(campaign_id)
        
        assert 'campaign_id' in metrics
        assert 'name' in metrics
        assert 'emails_sent' in metrics
        assert 'open_rate' in metrics
        assert 'response_rate' in metrics
        assert metrics['emails_sent'] == 0  # New campaign


class TestDeanEmailIntegration:
    """Test Dean's integration with Email Agent."""
    
    @pytest.fixture
    def dean_engine(self):
        """Create Dean conversation engine for testing."""
        return DeanConversationEngine()
    
    @pytest.mark.asyncio
    async def test_dean_email_agent_coordination(self, dean_engine):
        """Test Dean can coordinate with Email Agent."""
        task = {
            'type': 'create_campaign',
            'name': 'Strategic Property Manager Outreach',
            'segment': 'property_managers',
            'template_type': 'pm_value_first'
        }
        
        result = await dean_engine._coordinate_email_agent(task)
        
        assert result is not None
        assert 'Email campaign created:' in result or 'Email Agent' in result
    
    @pytest.mark.asyncio
    async def test_dean_monitor_inbox_coordination(self, dean_engine):
        """Test Dean can coordinate inbox monitoring."""
        task = {'type': 'monitor_inbox'}
        
        result = await dean_engine._coordinate_email_agent(task)
        
        assert result is not None
        assert 'Inbox monitored:' in result or 'Email Agent' in result
    
    @pytest.mark.asyncio
    async def test_dean_get_metrics_coordination(self, dean_engine):
        """Test Dean can get campaign metrics."""
        task = {
            'type': 'get_metrics',
            'campaign_id': 'test_campaign_123'
        }
        
        result = await dean_engine._coordinate_email_agent(task)
        
        assert result is not None
        assert 'Campaign metrics:' in result or 'Email Agent' in result


class TestEmailTemplates:
    """Test email template functionality."""
    
    @pytest.fixture
    def email_agent(self):
        """Create Email Agent instance for testing."""
        return EmailAgent()
    
    def test_property_manager_templates(self, email_agent):
        """Test property manager email templates."""
        pm_template = email_agent.templates['pm_value_first']
        
        assert pm_template.segment == 'property_managers'
        assert pm_template.hormozi_framework == 'value_first'
        assert '{name}' in pm_template.content
        assert 'turnover' in pm_template.content.lower()
        assert 'documentation' in pm_template.content.lower()
    
    def test_realtor_templates(self, email_agent):
        """Test realtor email templates."""
        realtor_template = email_agent.templates['realtor_pain_point']
        
        assert realtor_template.segment == 'realtors'
        assert realtor_template.hormozi_framework == 'pain_point'
        assert 'listing' in realtor_template.content.lower()
        assert 'photo' in realtor_template.content.lower()
    
    def test_investor_templates(self, email_agent):
        """Test investor email templates."""
        investor_template = email_agent.templates['investor_roi_focus']
        
        assert investor_template.segment == 'real_estate_investors'
        assert investor_template.hormozi_framework == 'value_first'
        assert 'roi' in investor_template.content.lower()
        assert '$300' in investor_template.content or '$400' in investor_template.content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])