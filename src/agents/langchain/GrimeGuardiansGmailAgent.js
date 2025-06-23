/**
 * Grime Guardians Gmail Agent - LangChain Integration
 */

const { ChatOpenAI } = require("@langchain/openai");
const { AgentExecutor, createOpenAIFunctionsAgent } = require("langchain/agents");
const { ChatPromptTemplate, MessagesPlaceholder } = require("@langchain/core/prompts");
const { DynamicTool } = require("@langchain/core/tools");
require('dotenv').config();

class GrimeGuardiansGmailAgent {
  constructor() {
    this.model = null;
    this.agent = null;
    this.agentExecutor = null;
    this.isInitialized = false;
    console.log('🤖 GrimeGuardiansGmailAgent instance created');
  }

  async initialize() {
    try {
      console.log('🚀 Initializing LangChain Gmail Agent...');
      
      if (!process.env.OPENAI_API_KEY) {
        throw new Error('OPENAI_API_KEY not found in environment variables');
      }

      this.model = new ChatOpenAI({
        modelName: "gpt-4",
        temperature: 0.3,
        openAIApiKey: process.env.OPENAI_API_KEY,
      });

      const tools = this.createTools();
      const prompt = ChatPromptTemplate.fromMessages([
        [
          "system",
          `You are Ava, the COO agent for Grime Guardians cleaning service. 

ANALYZE emails and classify them accurately:

MESSAGE TYPES:
- customer_service: Scheduling, rescheduling, service questions
- sales_inquiry: Pricing, quotes, new customer requests  
- complaint: Dissatisfied customers, service issues
- operational: Staff check-ins, supply questions, job updates
- payment: Billing questions, payment issues
- spam: Promotional, irrelevant messages

URGENCY LEVELS:
- high: Complaints, emergencies, urgent reschedules
- medium: Normal requests, questions  
- low: General inquiries, non-urgent items

CLIENT TYPES:
- existing_customer: Has email domain or mentions past service
- new_prospect: Asking for quotes/pricing
- employee: From @grimeguardians.com domain
- unknown: Cannot determine

Provide detailed analysis with specific reasoning.`
        ],
        ["user", "Analyze this email:\n\nSubject: {subject}\nFrom: {from}\nBody: {body}"],
        new MessagesPlaceholder("agent_scratchpad"),
      ]);

      this.agent = await createOpenAIFunctionsAgent({
        llm: this.model,
        tools,
        prompt,
      });

      this.agentExecutor = new AgentExecutor({
        agent: this.agent,
        tools,
        verbose: false,
        returnIntermediateSteps: false,
      });

      this.isInitialized = true;
      console.log('✅ LangChain Gmail Agent initialized successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize LangChain Gmail Agent:', error);
      this.isInitialized = false;
      return false;
    }
  }

  createTools() {
    return [
      new DynamicTool({
        name: "classify_message",
        description: "Classify message type",
        func: async (messageContent) => {
          return "Available types: new_inquiry, booking_request, schedule_change, complaint, compliment, payment_question, service_question, spam, other";
        },
      }),

      new DynamicTool({
        name: "assess_urgency",
        description: "Assess urgency level",
        func: async (messageContent) => {
          return "Urgency levels: critical, high, medium, low";
        },
      }),
    ];
  }

  async analyzeMessage(messageData) {
    if (!this.isInitialized) {
      console.log('⚠️ Agent not initialized, attempting to initialize...');
      const initialized = await this.initialize();
      if (!initialized) {
        throw new Error('Failed to initialize LangChain agent');
      }
    }

    try {
      const { subject, from, body, timestamp } = messageData;
      
      // Use direct GPT-4 call for better results
      const prompt = `You are Ava, the COO agent for Grime Guardians cleaning service.

Analyze this email and classify it:

FROM: ${from}
SUBJECT: ${subject}
BODY: ${body}

Provide your analysis in this exact JSON format:
{
  "message_type": "customer_service|sales_inquiry|complaint|operational|payment|spam",
  "urgency_level": "critical|high|medium|low", 
  "client_type": "existing_customer|new_prospect|employee|unknown",
  "requires_response": true/false,
  "reasoning": "Brief explanation of classification",
  "suggested_action": "immediate_response|standard_queue|escalate|no_action"
}

Be specific in your classification based on the content.`;

      const result = await this.model.invoke(prompt);
      
      console.log('🔍 LangChain Raw Output:', result.content);
      
      return this.parseAgentResponse(result.content, messageData);

    } catch (error) {
      console.error('❌ Error analyzing message:', error);
      return {
        agent_id: 'ava_langchain_error',
        timestamp: new Date().toISOString(),
        confidence: 0.1,
        message_type: 'unknown',
        urgency_level: 'medium',
        client_type: 'unknown',
        requires_response: true,
        response_draft: 'Thank you for contacting Grime Guardians. We will respond within 24 hours.',
        action_required: 'manual_review',
        original_message: messageData,
        error: error.message
      };
    }
  }

  parseAgentResponse(agentOutput, originalMessage) {
    try {
      // Try to parse JSON response from GPT-4
      const jsonMatch = agentOutput.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          agent_id: 'ava_langchain',
          timestamp: new Date().toISOString(),
          confidence: 0.95,
          message_type: parsed.message_type || 'other',
          urgency_level: parsed.urgency_level || 'medium',
          client_type: parsed.client_type || 'unknown',
          requires_response: parsed.requires_response !== false,
          response_draft: null,
          action_required: parsed.suggested_action || 'standard_processing',
          follow_up_needed: false,
          original_message: originalMessage,
          raw_analysis: agentOutput,
          reasoning: parsed.reasoning || 'No reasoning provided'
        };
      }
    } catch (error) {
      console.log('⚠️ Failed to parse JSON, falling back to text analysis');
    }
    
    // Fallback to text parsing
    return {
      agent_id: 'ava_langchain',
      timestamp: new Date().toISOString(),
      confidence: 0.75,
      message_type: this.extractMessageType(agentOutput),
      urgency_level: this.extractUrgencyLevel(agentOutput),
      client_type: 'unknown',
      requires_response: this.extractResponseRequirement(agentOutput),
      response_draft: this.extractResponseDraft(agentOutput),
      action_required: 'standard_processing',
      follow_up_needed: false,
      original_message: originalMessage,
      raw_analysis: agentOutput
    };
  }

  extractMessageType(text) {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('inquiry') || lowerText.includes('quote')) return 'new_inquiry';
    if (lowerText.includes('book') || lowerText.includes('schedule')) return 'booking_request';
    if (lowerText.includes('complaint') || lowerText.includes('problem')) return 'complaint';
    if (lowerText.includes('reschedule') || lowerText.includes('change')) return 'schedule_change';
    return 'other';
  }

  extractUrgencyLevel(text) {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('critical') || lowerText.includes('emergency')) return 'critical';
    if (lowerText.includes('high') || lowerText.includes('urgent')) return 'high';
    if (lowerText.includes('low')) return 'low';
    return 'medium';
  }

  extractResponseRequirement(text) {
    return !text.toLowerCase().includes('no response needed');
  }

  extractResponseDraft(text) {
    const quotedMatch = text.match(/"([^"]{30,})"/);
    if (quotedMatch) return quotedMatch[1];
    return null;
  }

  async testConnection() {
    try {
      if (!this.isInitialized) await this.initialize();
      
      const testResult = await this.analyzeMessage({
        from: 'test@example.com',
        subject: 'Test Message',
        body: 'This is a test message.',
        timestamp: new Date().toISOString()
      });
      
      console.log('✅ LangChain agent test successful');
      return testResult;
    } catch (error) {
      console.error('❌ LangChain agent test failed:', error);
      throw error;
    }
  }
}

module.exports = GrimeGuardiansGmailAgent;
