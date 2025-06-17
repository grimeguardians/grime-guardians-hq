/**
 * Ava Training System
 * 
 * Allows Brandon and Lena to correct Ava's mistakes and improve her performance
 * Handles Discord-based training interface and learning feedback
 */

const MessageClassifier = require('./messageClassifier');

class AvaTrainingSystem {
  constructor(discordClient) {
    this.discordClient = discordClient;
    this.messageClassifier = new MessageClassifier();
    this.pendingTraining = new Map(); // Store messages awaiting correction
    
    console.log('🎓 Ava Training System initialized');
  }

  // When Ava makes a classification, store it for potential correction
  async logClassification(messageId, originalMessage, classification, context = {}) {
    this.pendingTraining.set(messageId, {
      timestamp: new Date().toISOString(),
      originalMessage,
      classification,
      context,
      corrected: false
    });

    // Clean up old entries (keep last 100)
    if (this.pendingTraining.size > 100) {
      const entries = Array.from(this.pendingTraining.entries());
      const toDelete = entries.slice(0, entries.length - 100);
      toDelete.forEach(([key]) => this.pendingTraining.delete(key));
    }
  }

  // Handle training corrections via Discord
  async handleTrainingCommand(message, args) {
    const command = args[0]?.toLowerCase();
    
    switch (command) {
      case 'correct':
        return await this.handleCorrection(message, args.slice(1));
        
      case 'review':
        return await this.showRecentClassifications(message);
        
      case 'stats':
        return await this.showTrainingStats(message);
        
      case 'help':
        return await this.showTrainingHelp(message);
        
      default:
        return await this.showTrainingHelp(message);
    }
  }

  // NEW: Handle natural language training
  async handleNaturalLanguageTraining(message) {
    // Check if this looks like training feedback
    const text = message.content.toLowerCase();
    const trainingIndicators = [
      'ava', 'this is', 'this should be', 'actually', 'correction',
      'not a', 'this is a', 'you got', 'mistake', 'wrong',
      'should have classified', 'this is actually', 'not for'
    ];

    const hasTrainingLanguage = trainingIndicators.some(indicator => 
      text.includes(indicator)
    );

    if (!hasTrainingLanguage) return false;

    // Extract the correction using GPT
    const correction = await this.extractCorrectionFromNaturalLanguage(message.content);
    
    if (correction) {
      await this.processNaturalLanguageCorrection(message, correction);
      return true;
    }

    return false;
  }

  async extractCorrectionFromNaturalLanguage(feedbackText) {
    try {
      const OpenAI = require('openai');
      const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

      const prompt = `Extract training correction from this natural language feedback:

"${feedbackText}"

Categories: new_prospect, schedule_change, complaint, general, spam

Extract:
1. What category should it be?
2. Why/reasoning
3. Key indicators mentioned

Respond with JSON only:
{
  "isCorrection": true/false,
  "correctCategory": "category_name",
  "reasoning": "explanation",
  "keyIndicators": ["word1", "word2"]
}

If this is not training feedback, return {"isCorrection": false}`;

      const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.2,
        max_tokens: 200
      });

      const result = JSON.parse(response.choices[0].message.content);
      return result.isCorrection ? result : null;

    } catch (error) {
      console.error('❌ Error extracting natural language correction:', error.message);
      return null;
    }
  }

  async processNaturalLanguageCorrection(message, correction) {
    // Find the most recent pending classification
    const recentClassifications = Array.from(this.pendingTraining.entries())
      .filter(([_, data]) => !data.corrected)
      .slice(-5); // Last 5 uncorrected

    if (recentClassifications.length === 0) {
      return message.reply('🤔 I don\'t see any recent classifications to correct. Could you be more specific about which message?');
    }

    // Use the most recent one (likely what they're referring to)
    const [messageId, pendingItem] = recentClassifications[recentClassifications.length - 1];

    // Record the correction
    const correctionId = await this.messageClassifier.recordCorrection(
      pendingItem.originalMessage,
      pendingItem.classification,
      { 
        category: correction.correctCategory, 
        notes: correction.reasoning,
        keyIndicators: correction.keyIndicators 
      },
      message.author.username
    );

    // Mark as corrected
    pendingItem.corrected = true;
    pendingItem.correctionId = correctionId;

    // Send natural confirmation
    const embed = {
      title: '✅ Got it! Training correction recorded',
      color: 0x00ff00,
      fields: [
        { name: '📝 Your Feedback', value: `"${message.content}"`, inline: false },
        { name: '🎯 What I Learned', value: `This should be classified as **${correction.correctCategory}**`, inline: false },
        { name: '🧠 Key Indicators', value: correction.keyIndicators.map(i => `"${i}"`).join(', '), inline: false },
        { name: '💡 Reasoning', value: correction.reasoning, inline: false }
      ],
      footer: { text: `Thanks ${message.author.username}! I'll remember this for next time.` },
      timestamp: new Date().toISOString()
    };

    return message.reply({ embeds: [embed] });
  }

  async handleCorrection(message, args) {
    // Expected format: !train correct <messageId> <correctCategory> [notes]
    const messageId = args[0];
    const correctCategory = args[1];
    const notes = args.slice(2).join(' ');

    if (!messageId || !correctCategory) {
      return message.reply('❌ Usage: `!train correct <messageId> <category> [notes]`\nCategories: new_prospect, schedule_change, complaint, general, spam');
    }

    const pendingItem = this.pendingTraining.get(messageId);
    if (!pendingItem) {
      return message.reply('❌ Message ID not found. Use `!train review` to see recent classifications.');
    }

    const validCategories = ['new_prospect', 'schedule_change', 'complaint', 'general', 'spam'];
    if (!validCategories.includes(correctCategory)) {
      return message.reply(`❌ Invalid category. Valid options: ${validCategories.join(', ')}`);
    }

    // Record the correction
    const correctionId = await this.messageClassifier.recordCorrection(
      pendingItem.originalMessage,
      pendingItem.classification,
      { category: correctCategory, notes },
      message.author.username
    );

    // Mark as corrected
    pendingItem.corrected = true;
    pendingItem.correctionId = correctionId;

    // Send confirmation
    const embed = {
      title: '✅ Training Correction Recorded',
      color: 0x00ff00,
      fields: [
        { name: 'Original Message', value: `\`\`\`${pendingItem.originalMessage.substring(0, 200)}...\`\`\``, inline: false },
        { name: 'Ava\'s Classification', value: `${pendingItem.classification.category} (${Math.round(pendingItem.classification.confidence * 100)}% confidence)`, inline: true },
        { name: 'Correct Classification', value: correctCategory, inline: true },
        { name: 'Trainer', value: message.author.username, inline: true }
      ],
      timestamp: new Date().toISOString()
    };

    if (notes) {
      embed.fields.push({ name: 'Notes', value: notes, inline: false });
    }

    return message.reply({ embeds: [embed] });
  }

  async showRecentClassifications(message) {
    const recent = Array.from(this.pendingTraining.entries())
      .slice(-10)
      .reverse();

    if (recent.length === 0) {
      return message.reply('📚 No recent classifications to review.');
    }

    const embed = {
      title: '📚 Recent Ava Classifications',
      color: 0x3498db,
      description: 'Use `!train correct <messageId> <category>` to fix mistakes',
      fields: []
    };

    recent.forEach(([messageId, data], index) => {
      const status = data.corrected ? '✅ Corrected' : '⏳ Pending';
      const preview = data.originalMessage.substring(0, 100) + '...';
      
      embed.fields.push({
        name: `${index + 1}. ID: ${messageId} - ${status}`,
        value: `**Category:** ${data.classification.category} (${Math.round(data.classification.confidence * 100)}%)\n**Message:** \`${preview}\``,
        inline: false
      });
    });

    return message.reply({ embeds: [embed] });
  }

  async showTrainingStats(message) {
    const corrections = this.messageClassifier.getCorrections();
    const totalClassifications = this.pendingTraining.size;
    const correctedCount = corrections.length;
    
    const categoryStats = {};
    corrections.forEach(correction => {
      const cat = correction.correctClassification.category;
      categoryStats[cat] = (categoryStats[cat] || 0) + 1;
    });

    const embed = {
      title: '📊 Ava Training Statistics',
      color: 0x9b59b6,
      fields: [
        { name: '📈 Total Classifications', value: totalClassifications.toString(), inline: true },
        { name: '✏️ Corrections Made', value: correctedCount.toString(), inline: true },
        { name: '🎯 Accuracy Rate', value: totalClassifications > 0 ? `${Math.round((1 - correctedCount / totalClassifications) * 100)}%` : 'N/A', inline: true }
      ],
      timestamp: new Date().toISOString()
    };

    if (Object.keys(categoryStats).length > 0) {
      const categoryText = Object.entries(categoryStats)
        .map(([cat, count]) => `${cat}: ${count}`)
        .join('\n');
      
      embed.fields.push({
        name: '📝 Corrections by Category',
        value: `\`\`\`${categoryText}\`\`\``,
        inline: false
      });
    }

    return message.reply({ embeds: [embed] });
  }

  async showTrainingHelp(message) {
    const embed = {
      title: '🎓 Ava Training System Help',
      color: 0xe74c3c,
      description: 'Train Ava to better understand customer messages',
      fields: [
        {
          name: '🔧 Commands',
          value: `\`!train correct <messageId> <category> [notes]\` - Correct a classification
\`!train review\` - Show recent classifications
\`!train stats\` - Show training statistics  
\`!train help\` - Show this help`,
          inline: false
        },
        {
          name: '📂 Categories',
          value: `\`new_prospect\` - New customer inquiries
\`schedule_change\` - Reschedule/cancel requests
\`complaint\` - Customer complaints/issues
\`general\` - General questions/thanks
\`spam\` - Irrelevant messages`,
          inline: false
        },
        {
          name: '💡 Example',
          value: '`!train correct msg_123 new_prospect This is clearly a quote request`',
          inline: false
        }
      ]
    };

    return message.reply({ embeds: [embed] });
  }

  // Generate an improved response based on correct classification
  async generateImprovedResponse(message, correctClassification) {
    try {
      const OpenAI = require('openai');
      const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

      const prompt = this.buildResponsePrompt(message, correctClassification);
      
      const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.7,
        max_tokens: 300
      });

      return response.choices[0].message.content;
      
    } catch (error) {
      console.error('❌ Error generating improved response:', error.message);
      return null;
    }
  }

  buildResponsePrompt(message, classification) {
    const templates = {
      new_prospect: `Write a professional response to this new prospect inquiry for Grime Guardians cleaning service. Include:
- Thank them for their interest
- Ask for key details (square footage, number of rooms, type of cleaning)
- Mention our competitive pricing and quality service
- Provide next steps to schedule`,
      
      schedule_change: `Write a helpful response to this schedule change request. Include:
- Acknowledge their request professionally
- Show flexibility and understanding
- Ask for their preferred new time/date
- Confirm we'll accommodate their needs`,
      
      complaint: `Write an empathetic response to this customer complaint. Include:
- Sincere apology for their experience
- Request for specific details about the issue
- Assurance that we'll make it right
- Next steps to resolve the problem`,
      
      general: `Write a friendly, helpful response to this general inquiry. Keep it professional but warm.`
    };

    const template = templates[classification.category] || templates.general;

    return `${template}

CUSTOMER MESSAGE: "${message}"

RESPONSE GUIDELINES:
- Professional tone for Grime Guardians cleaning service
- Keep response under 150 words
- End with clear next steps or call to action
- Use first person (we/our) representing the company

Write only the response text, no explanations:`;
  }
}

module.exports = AvaTrainingSystem;
