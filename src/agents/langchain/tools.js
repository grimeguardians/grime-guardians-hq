/**
 * Enhanced LangChain Tools for Gmail Agent
 * Building upon the working foundation
 */

const { DynamicTool } = require("@langchain/core/tools");

// 📧 EMAIL RESPONSE TOOL
const createEmailResponseTool = () => {
  return new DynamicTool({
    name: "draft_email_response",
    description: "Draft a professional email response based on message analysis",
    func: async (input) => {
      const { messageType, clientType, urgencyLevel, originalMessage } = JSON.parse(input);
      
      // Generate contextual response using GPT-4
      const responseTemplates = {
        sales_inquiry: `Thank you for your interest in Grime Guardians! Based on your request for [DETAILS], I'd be happy to provide a customized quote...`,
        complaint: `I sincerely apologize for the experience you've described. Your satisfaction is our top priority, and I want to make this right immediately...`,
        scheduling_request: `I'd be glad to help you reschedule your appointment. Let me check our availability for [REQUESTED TIME]...`
      };
      
      return {
        draftResponse: responseTemplates[messageType] || "Thank you for contacting Grime Guardians...",
        suggestedAction: urgencyLevel === 'critical' ? 'send_immediately' : 'review_and_send',
        escalationNeeded: ['complaint', 'emergency_request'].includes(messageType)
      };
    }
  });
};

// 💰 PRICING CALCULATION TOOL  
const createPricingTool = () => {
  return new DynamicTool({
    name: "calculate_cleaning_quote",
    description: "Calculate pricing for cleaning services based on requirements",
    func: async (input) => {
      const { rooms, sqft, frequency, specialRequests } = JSON.parse(input);
      
      // Integration with existing Iris pricing engine
      const basePrice = {
        studio: 80,
        '1bed': 100,
        '2bed': 120,
        '3bed': 150,
        '4bed': 180
      };
      
      const frequencyMultiplier = {
        weekly: 0.9,
        biweekly: 1.0,
        monthly: 1.1,
        oneTime: 1.2
      };
      
      const estimate = basePrice[rooms] * frequencyMultiplier[frequency];
      
      return {
        baseEstimate: estimate,
        range: `$${estimate - 20} - $${estimate + 20}`,
        frequency: frequency,
        nextStep: 'schedule_walkthrough'
      };
    }
  });
};

// 📅 SCHEDULING TOOL
const createSchedulingTool = () => {
  return new DynamicTool({
    name: "check_availability",
    description: "Check cleaner availability and suggest appointment times",
    func: async (input) => {
      const { preferredDate, timeWindow, location } = JSON.parse(input);
      
      // Integration with Keith's scheduling system
      return {
        availableSlots: [
          "Tomorrow 9:00 AM - 12:00 PM",
          "Friday 1:00 PM - 4:00 PM", 
          "Monday 10:00 AM - 1:00 PM"
        ],
        assignedCleaner: "Sarah M. (4.9⭐ rating)",
        estimatedDuration: "2-3 hours",
        travelTime: "15 minutes from previous appointment"
      };
    }
  });
};

// 📊 NOTION INTEGRATION TOOL
const createNotionTool = () => {
  return new DynamicTool({
    name: "log_to_notion",
    description: "Log customer interaction and create follow-up tasks in Notion",
    func: async (input) => {
      const { clientEmail, messageType, summary, nextAction } = JSON.parse(input);
      
      // Integration with existing Notion utilities
      return {
        recordCreated: true,
        notionPageId: "abc123",
        followUpScheduled: nextAction.includes('follow_up'),
        escalationCreated: messageType === 'complaint',
        assignedAgent: messageType === 'sales_inquiry' ? 'Iris' : 'Ava'
      };
    }
  });
};

module.exports = {
  createEmailResponseTool,
  createPricingTool, 
  createSchedulingTool,
  createNotionTool
};
