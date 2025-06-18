/**
 * Enhanced Message Classifier with GPT-4 Integration
 * 
 * Classifies incoming messages as:
 * - New prospect inquiry
 * - Schedule change request  
 * - Complaint/issue
 * - General question
 * - Spam/irrelevant
 * 
 * Includes learning system for corrections
 */

const OpenAI = require('openai');
require('dotenv').config();

class MessageClassifier {
  constructor() {
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
    
    // Store corrections for learning
    this.corrections = new Map();
    this.loadCorrections();
  }

  async classifyMessage(message, senderInfo = {}) {
    try {
      // First, try rule-based classification
      const quickClassification = this.quickClassify(message);
      
      // If confident, return immediately
      if (quickClassification.confidence > 0.8) {
        console.log('🎯 High confidence rule-based classification - skipping GPT');
        console.log(`   Result: ${quickClassification.type} (confidence: ${quickClassification.confidence})`);
        return quickClassification;
      }
      
      // Otherwise, try GPT for deeper analysis (if available)
      try {
        const gptClassification = await this.gptClassify(message, senderInfo);
        console.log(`🤖 GPT classification: ${gptClassification.type} (confidence: ${gptClassification.confidence})`);
        
        // Combine results
        return {
          ...gptClassification,
          quickClassification: quickClassification
        };
      } catch (error) {
        console.log('⚠️ GPT unavailable - using rule-based classification');
        console.log(`   Fallback result: ${quickClassification.type} (confidence: ${quickClassification.confidence})`);
        return quickClassification;
      }
      
    } catch (error) {
      console.error('❌ Message classification error:', error.message);
      
      // Fallback to rule-based only
      const fallback = this.quickClassify(message);
      console.log(`🔄 Emergency fallback: ${fallback.type} (confidence: ${fallback.confidence})`);
      return fallback;
    }
  }

  quickClassify(message) {
    const text = message.toLowerCase().trim();
    
    // New prospect indicators
    const prospectKeywords = [
      'interested in', 'looking for', 'need cleaning', 'cleaning service',
      'quote', 'estimate', 'price', 'cost', 'how much',
      'friend recommended', 'heard about', 'saw your',
      'move out', 'move in', 'end of lease', 'new home',
      'first time', 'never used', 'new customer',
      'bedroom', 'bathroom', 'square feet', 'sqft',
      'townhome', 'apartment', 'house', 'condo'
    ];

    // Schedule change indicators
    const scheduleKeywords = [
      'reschedule', 'change my', 'move my', 'cancel my', 'postpone',
      'different time', 'another day', 'new time',
      'sick', 'emergency', 'family', 'traveling', 'out of town',
      'push back', 'push forward', 'delay'
    ];

    // General operations/questions
    const operationsKeywords = [
      'what time', 'when is', 'appointment time', 'scheduled for',
      'add to', 'include', 'extra service', 'additional',
      'how long', 'how much time', 'duration'
    ];

    // Complaint indicators
    const complaintKeywords = [
      'unhappy', 'disappointed', 'problem', 'issue', 'complaint',
      'not satisfied', 'poor', 'terrible', 'missed', 'late',
      'damaged', 'broken', 'refund', 'money back'
    ];

    // Count matches
    const prospectMatches = prospectKeywords.filter(keyword => text.includes(keyword));
    const scheduleMatches = scheduleKeywords.filter(keyword => text.includes(keyword));
    const complaintMatches = complaintKeywords.filter(keyword => text.includes(keyword));
    const operationsMatches = operationsKeywords.filter(keyword => text.includes(keyword));

    // Determine primary category
    let category = 'general';
    let confidence = 0.3;
    let keywords = [];

    if (complaintMatches.length > 0) {
      category = 'complaint';
      confidence = Math.min(complaintMatches.length * 0.3 + 0.4, 0.9);
      keywords = complaintMatches;
    } else if (scheduleMatches.length > 0) {
      category = 'schedule_change';
      confidence = Math.min(scheduleMatches.length * 0.25 + 0.5, 0.85);
      keywords = scheduleMatches;
    } else if (operationsMatches.length > 0) {
      category = 'general'; // Will map to 'operations'
      confidence = Math.min(operationsMatches.length * 0.3 + 0.4, 0.8);
      keywords = operationsMatches;
    } else if (prospectMatches.length > 1) {
      category = 'new_prospect';
      confidence = Math.min(prospectMatches.length * 0.2 + 0.4, 0.8);
      keywords = prospectMatches;
    }

    // Boost confidence for clear phrases
    const clearPhrases = {
      new_prospect: [
        'interested in scheduling', 'need a quote', 'how much do you charge',
        'looking for cleaning service', 'move out cleaning', 'move in cleaning'
      ],
      schedule_change: [
        'reschedule my', 'change my appointment', 'cancel my cleaning',
        'move my cleaning', 'different time'
      ],
      complaint: [
        'not happy with', 'problem with', 'issue with the cleaning',
        'want a refund', 'disappointed with'
      ]
    };

    if (clearPhrases[category]) {
      const hasPhrase = clearPhrases[category].some(phrase => text.includes(phrase));
      if (hasPhrase) {
        confidence = Math.min(confidence + 0.3, 0.95);
      }
    }

    return {
      type: this.mapToOperationalTypes(category),
      confidence,
      keywords,
      method: 'rule_based'
    };
  }

  /**
   * Map legacy classification types to operational types Ava expects
   */
  mapToOperationalTypes(category) {
    const typeMapping = {
      'schedule_change': 'reschedule_request',
      'new_prospect': 'pricing_inquiry', // This will be ignored by Ava (Dean's territory)
      'complaint': 'complaint',
      'general': 'operations', // General operational questions
      'spam': 'spam'
    };

    return typeMapping[category] || 'operations';
  }

  async gptClassify(message, senderInfo = {}) {
    const prompt = this.buildClassificationPrompt(message, senderInfo);
    
    try {
      const response = await this.openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.3,
        max_tokens: 200
      });

      const result = JSON.parse(response.choices[0].message.content);
      
      // Apply type mapping to GPT results too
      return {
        type: this.mapToOperationalTypes(result.category),
        confidence: result.confidence,
        category: result.category, // Keep original for reference
        reasoning: result.reasoning,
        urgency: result.urgency,
        suggested_response_type: result.suggested_response_type,
        method: 'gpt4'
      };
      
    } catch (error) {
      console.error('❌ GPT classification error:', error.message);
      
      // Check if it's a rate limit error
      if (error.status === 429) {
        console.log('⚠️ OpenAI rate limit hit - using rule-based classification only');
        console.log('💡 Tip: Add billing method to OpenAI account to remove limits');
      }
      
      throw error;
    }
  }

  buildClassificationPrompt(message, senderInfo) {
    return `You are an AI assistant for Grime Guardians cleaning service. Classify this message into one of these categories:

CATEGORIES:
- new_prospect: Someone inquiring about cleaning services, asking for quotes, or wanting to schedule their first cleaning
- schedule_change: Existing customer wanting to reschedule, cancel, or change an existing appointment
- complaint: Customer expressing dissatisfaction, reporting problems, or requesting refunds
- general: General questions, thanks, or other non-actionable messages
- spam: Irrelevant messages or spam

MESSAGE: "${message}"

SENDER INFO: ${JSON.stringify(senderInfo)}

RESPOND ONLY WITH VALID JSON:
{
  "category": "category_name",
  "confidence": 0.85,
  "reasoning": "Brief explanation of classification",
  "urgency": "low|medium|high",
  "suggested_response_type": "quote|schedule|apology|info|ignore"
}`;
  }

  // Learning system for corrections
  async recordCorrection(originalMessage, originalClassification, correctClassification, correctedBy) {
    const correction = {
      timestamp: new Date().toISOString(),
      message: originalMessage,
      originalClassification,
      correctClassification,
      correctedBy,
      id: Date.now().toString()
    };

    this.corrections.set(correction.id, correction);
    
    // Save to file for persistence
    await this.saveCorrections();
    
    console.log(`📚 [Learning] Correction recorded by ${correctedBy}`);
    console.log(`   Original: ${originalClassification.category} (${originalClassification.confidence})`);
    console.log(`   Correct: ${correctClassification.category}`);
    
    return correction.id;
  }

  async loadCorrections() {
    try {
      const fs = require('fs').promises;
      const path = '/Users/BROB/Desktop/Grime Guardians/Grime Guardians HQ/data/corrections.json';
      
      const data = await fs.readFile(path, 'utf8');
      const corrections = JSON.parse(data);
      
      for (const correction of corrections) {
        this.corrections.set(correction.id, correction);
      }
      
      console.log(`📚 Loaded ${corrections.length} classification corrections`);
      
    } catch (error) {
      console.log('📚 No existing corrections file found - starting fresh');
    }
  }

  async saveCorrections() {
    try {
      const fs = require('fs').promises;
      const path = '/Users/BROB/Desktop/Grime Guardians/Grime Guardians HQ/data/corrections.json';
      
      // Ensure directory exists
      await fs.mkdir('/Users/BROB/Desktop/Grime Guardians/Grime Guardians HQ/data', { recursive: true });
      
      const corrections = Array.from(this.corrections.values());
      await fs.writeFile(path, JSON.stringify(corrections, null, 2));
      
    } catch (error) {
      console.error('❌ Error saving corrections:', error.message);
    }
  }

  getCorrections() {
    return Array.from(this.corrections.values());
  }

  // Generate improved classification prompt based on corrections
  buildImprovedPrompt(message, senderInfo) {
    const recentCorrections = Array.from(this.corrections.values())
      .slice(-10) // Last 10 corrections
      .map(c => `Message: "${c.message}" → Correct: ${c.correctClassification.category}`)
      .join('\n');

    const basePrompt = this.buildClassificationPrompt(message, senderInfo);
    
    if (recentCorrections.length > 0) {
      return `${basePrompt}

RECENT CORRECTIONS TO LEARN FROM:
${recentCorrections}

Consider these corrections when classifying the current message.`;
    }
    
    return basePrompt;
  }
}

module.exports = MessageClassifier;
