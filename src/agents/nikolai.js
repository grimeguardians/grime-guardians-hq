// Nikolai Agent - Compliance Enforcer & SOP Validator
// Monitors checklist submissions, photo uploads, and SOP adherence

const Agent = require('./agent');
const OpenAI = require('openai');
const { logToNotion, getSOPRequirements } = require('../utils/notion');
const { sendDiscordPing, createMentionFromUsername } = require('../utils/discord');
const { getUserIdFromUsername } = require('../utils/discordUserMapping');

class Nikolai extends Agent {
  constructor(client) {
    super({ agentId: 'nikolai', role: 'Compliance Enforcer & SOP Validator' });
    this.client = client;
    this.openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    this.violationTracking = new Map();
    this.violationHistory = new Map(); // Add for test compatibility
    this.sopRequirements = new Map();
    this.photoAnalysisHistory = new Map();
  }

  onReady() {
    console.log('🛡️ Nikolai agent is ready to enforce compliance and validate SOPs!');
    
    // Check for missing submissions every 30 minutes
    setInterval(() => {
      this.checkMissingSOP();
    }, 30 * 60 * 1000);
    
    // Load SOP requirements from Notion
    this.loadSOPRequirements();
  }

  async getContext(event) {
    const username = event.author?.username;
    if (!username) return event;

    return {
      event,
      sopRequirements: await this.getSOPForJobType(event.content),
      cleanerHistory: await this.getComplianceHistory(username),
      jobDetails: await this.extractJobDetails(event.content)
    };
  }

  async handleEvent(event, context) {
    const content = event.content.toLowerCase();
    const username = event.author.username;

    // Monitor for checklist submissions
    if (this.isChecklistSubmission(content)) {
      return await this.validateChecklist(event, context);
    }

    // Monitor for photo uploads
    if (event.attachments && event.attachments.size > 0) {
      return await this.validatePhotos(event, context);
    }

    // Monitor for job completion claims
    if (content.includes('finished') || content.includes('completed') || content.includes('🏁')) {
      return await this.validateJobCompletion(event, context);
    }

    return null;
  }

  isChecklistSubmission(content) {
    const indicators = [
      'checklist', 'checked off', 'completed tasks', 'all done',
      '✅', '☑️', 'task list', 'sop completed'
    ];
    return indicators.some(indicator => content.includes(indicator));
  }

  async validateChecklist(event, context) {
    const username = event.author.username;
    const { sopRequirements, jobDetails } = context;
    
    try {
      // Extract checklist items from message
      const submittedItems = await this.extractChecklistItems(event.content);
      
      // Compare against SOP requirements
      const validation = await this.compareAgainstSOP(submittedItems, sopRequirements, jobDetails);
      
      if (validation.missing.length > 0) {
        // Missing items - flag for follow-up
        await this.flagMissingSOPItems(username, validation.missing, event);
        
        return {
          agent_id: 'nikolai',
          task: 'sop_validation',
          action_required: true,
          confidence: 0.9,
          violations: validation.missing,
          message: `Missing SOP items detected for ${username}`
        };
      } else {
        // All good - log compliance
        await this.logSOPCompliance(username, submittedItems, event);
        
        return {
          agent_id: 'nikolai',
          task: 'sop_validation',
          action_required: false,
          confidence: 0.95,
          status: 'compliant',
          message: `${username} submitted complete SOP checklist`
        };
      }
    } catch (error) {
      console.error('[Nikolai] Error validating checklist:', error);
      return null;
    }
  }

  async validatePhotos(event, context) {
    const username = event.author.username;
    const { jobDetails } = context;
    
    try {
      const photos = Array.from(event.attachments.values());
      const requiredPhotos = await this.getRequiredPhotos(jobDetails);
      
      // Basic photo count validation
      if (photos.length < requiredPhotos.minimum) {
        await this.flagInsufficientPhotos(username, photos.length, requiredPhotos.minimum, event);
        
        return {
          agent_id: 'nikolai',
          task: 'photo_validation',
          action_required: true,
          confidence: 0.85,
          issue: 'insufficient_photos',
          message: `${username} submitted ${photos.length}/${requiredPhotos.minimum} required photos`
        };
      }

      // Advanced photo analysis using GPT-4 Vision (if critical job)
      if (jobDetails?.priority === 'high' || jobDetails?.clientType === 'premium') {
        const analysis = await this.analyzePhotoQuality(photos, requiredPhotos.types);
        
        if (analysis.issues.length > 0) {
          await this.flagPhotoQualityIssues(username, analysis.issues, event);
          
          return {
            agent_id: 'nikolai',
            task: 'photo_quality_validation',
            action_required: true,
            confidence: analysis.confidence,
            issues: analysis.issues,
            message: `Photo quality issues detected for ${username}`
          };
        }
      }

      // Photos approved
      await this.logPhotoCompliance(username, photos.length, event);
      
      return {
        agent_id: 'nikolai',
        task: 'photo_validation',
        action_required: false,
        confidence: 0.9,
        status: 'approved',
        message: `${username} submitted compliant photos`
      };
      
    } catch (error) {
      console.error('[Nikolai] Error validating photos:', error);
      return null;
    }
  }

  async validateJobCompletion(event, context) {
    const username = event.author.username;
    const { jobDetails } = context;
    
    try {
      // Check if required elements are present
      const completionValidation = await this.validateCompletionRequirements(event, jobDetails);
      
      if (!completionValidation.valid) {
        await this.flagIncompleteSubmission(username, completionValidation.missing, event);
        
        return {
          agent_id: 'nikolai',
          task: 'completion_validation',
          action_required: true,
          confidence: 0.9,
          missing_requirements: completionValidation.missing,
          message: `Incomplete job submission from ${username}`
        };
      }

      // Job completion looks good
      await this.logJobCompletion(username, jobDetails, event);
      
      return {
        agent_id: 'nikolai',
        task: 'completion_validation',
        action_required: false,
        confidence: 0.95,
        status: 'validated',
        message: `${username} job completion validated`
      };
      
    } catch (error) {
      console.error('[Nikolai] Error validating job completion:', error);
      return null;
    }
  }

  async extractChecklistItems(content) {
    // Extract checklist items using GPT-4
    try {
      const response = await this.openai.chat.completions.create({
        model: 'gpt-4',
        messages: [{
          role: 'user',
          content: `Extract all completed tasks/checklist items from this message. Return as JSON array of strings:
          
          Message: "${content}"
          
          Format: ["task1", "task2", "task3"]`
        }],
        temperature: 0.1,
        max_tokens: 300
      });

      return JSON.parse(response.choices[0].message.content);
    } catch (error) {
      console.error('[Nikolai] Error extracting checklist items:', error);
      return [];
    }
  }

  async compareAgainstSOP(submittedItems, sopRequirements, jobDetails) {
    // Use GPT-4 to intelligently compare submitted items against SOP
    try {
      const response = await this.openai.chat.completions.create({
        model: 'gpt-4',
        messages: [{
          role: 'user',
          content: `Compare submitted checklist items against SOP requirements and identify missing items.

          Submitted Items: ${JSON.stringify(submittedItems)}
          SOP Requirements: ${JSON.stringify(sopRequirements)}
          Job Details: ${JSON.stringify(jobDetails)}
          
          Return JSON with:
          {
            "missing": ["missing item 1", "missing item 2"],
            "satisfied": ["satisfied item 1", "satisfied item 2"],
            "confidence": 0.95
          }`
        }],
        temperature: 0.1,
        max_tokens: 400
      });

      return JSON.parse(response.choices[0].message.content);
    } catch (error) {
      console.error('[Nikolai] Error comparing against SOP:', error);
      return { missing: [], satisfied: submittedItems, confidence: 0.5 };
    }
  }

  async analyzePhotoQuality(photos, requiredTypes) {
    // Advanced photo analysis using GPT-4 Vision for critical jobs
    try {
      const analysis = {
        issues: [],
        confidence: 0.85,
        approved: []
      };

      // For now, implement basic validation
      // TODO: Implement GPT-4 Vision analysis for advanced photo validation
      
      return analysis;
    } catch (error) {
      console.error('[Nikolai] Error analyzing photo quality:', error);
      return { issues: [], confidence: 0.5, approved: [] };
    }
  }

  async flagMissingSOPItems(username, missingItems, originalEvent) {
    const userId = await getUserIdFromUsername(username);
    const mention = createMentionFromUsername(username);
    
    const message = `🚨 **SOP Compliance Issue**\n\n` +
      `${mention}, your checklist is missing the following required items:\n\n` +
      missingItems.map(item => `• ${item}`).join('\n') + '\n\n' +
      `Please complete these items and resubmit your checklist.`;

    await sendDiscordPing(this.client, originalEvent.channel.id, message);
    
    // Log to Notion
    await logToNotion('sop_violations', {
      agent: 'nikolai',
      cleaner: username,
      violation_type: 'missing_sop_items',
      missing_items: missingItems,
      timestamp: new Date().toISOString(),
      channel_id: originalEvent.channel.id
    });
  }

  async flagInsufficientPhotos(username, submitted, required, originalEvent) {
    const userId = await getUserIdFromUsername(username);
    const mention = createMentionFromUsername(username);
    
    const message = `📸 **Photo Submission Issue**\n\n` +
      `${mention}, you submitted ${submitted} photos but ${required} are required.\n\n` +
      `Please upload the remaining ${required - submitted} photos to complete your job submission.`;

    await sendDiscordPing(this.client, originalEvent.channel.id, message);
    
    // Log to Notion
    await logToNotion('photo_violations', {
      agent: 'nikolai',
      cleaner: username,
      violation_type: 'insufficient_photos',
      submitted_count: submitted,
      required_count: required,
      timestamp: new Date().toISOString(),
      channel_id: originalEvent.channel.id
    });
  }

  async flagIncompleteSubmission(username, missingRequirements, originalEvent) {
    const userId = await getUserIdFromUsername(username);
    const mention = createMentionFromUsername(username);
    
    const message = `⚠️ **Incomplete Job Submission**\n\n` +
      `${mention}, your job completion is missing:\n\n` +
      missingRequirements.map(req => `• ${req}`).join('\n') + '\n\n' +
      `Please provide the missing information to complete your submission.`;

    await sendDiscordPing(this.client, originalEvent.channel.id, message);
    
    // Log to Notion
    await logToNotion('completion_violations', {
      agent: 'nikolai',
      cleaner: username,
      violation_type: 'incomplete_submission',
      missing_requirements: missingRequirements,
      timestamp: new Date().toISOString(),
      channel_id: originalEvent.channel.id
    });
  }

  async getSOPForJobType(content) {
    // Extract job type and return relevant SOP requirements
    // This would integrate with your Notion SOP database
    return {
      minimum_tasks: ['bathroom_cleaning', 'kitchen_cleaning', 'dusting', 'vacuuming'],
      required_photos: 4,
      special_instructions: []
    };
  }

  async getRequiredPhotos(jobDetails) {
    // Determine required photos based on job type
    return {
      minimum: 4,
      types: ['before', 'after', 'problem_areas', 'completion_proof']
    };
  }

  async validateCompletionRequirements(event, jobDetails) {
    const content = event.content.toLowerCase();
    const hasPhotos = event.attachments && event.attachments.size > 0;
    const hasChecklist = this.isChecklistSubmission(content);
    
    const missing = [];
    
    if (!hasPhotos) missing.push('completion_photos');
    if (!hasChecklist) missing.push('task_checklist');
    
    return {
      valid: missing.length === 0,
      missing
    };
  }

  async loadSOPRequirements() {
    // Load SOP requirements from Notion database
    console.log('[Nikolai] Loading SOP requirements from Notion...');
    // TODO: Implement Notion SOP database integration
  }

  async checkMissingSOP() {
    // Scheduled check for cleaners who haven't submitted SOPs
    console.log('[Nikolai] Running scheduled SOP compliance check...');
    // TODO: Implement scheduled compliance monitoring
  }

  async logSOPCompliance(username, items, event) {
    await logToNotion('sop_compliance', {
      agent: 'nikolai',
      cleaner: username,
      status: 'compliant',
      submitted_items: items,
      timestamp: new Date().toISOString(),
      channel_id: event.channel.id
    });
  }

  async logPhotoCompliance(username, photoCount, event) {
    await logToNotion('photo_compliance', {
      agent: 'nikolai',
      cleaner: username,
      status: 'compliant',
      photo_count: photoCount,
      timestamp: new Date().toISOString(),
      channel_id: event.channel.id
    });
  }

  async logJobCompletion(username, jobDetails, event) {
    await logToNotion('job_completions', {
      agent: 'nikolai',
      cleaner: username,
      status: 'validated',
      job_details: jobDetails,
      timestamp: new Date().toISOString(),
      channel_id: event.channel.id
    });
  }
}

module.exports = Nikolai;
