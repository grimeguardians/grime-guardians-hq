/**
 * Schedule Request Detection Utility
 * 
 * Analyzes client messages for schedule-related requests
 * Works with messages from both Google Voice and High Level
 */

function detectScheduleRequest(message) {
  if (!message || typeof message !== 'string') {
    return {
      isScheduleRequest: false,
      type: null,
      urgency: 'low',
      keywords: [],
      confidence: 0
    };
  }

  const text = message.toLowerCase().trim();
  
  // Define keyword categories
  const scheduleKeywords = {
    reschedule: ['reschedule', 'move', 'change', 'switch', 'different time', 'another day', 'new time'],
    cancel: ['cancel', 'cancellation', 'not needed', 'don\'t need', 'skip'],
    postpone: ['postpone', 'delay', 'push back', 'later date'],
    emergency: ['emergency', 'urgent', 'asap', 'right away', 'immediately'],
    timing: ['tomorrow', 'today', 'this week', 'next week', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
    family: ['sick', 'family emergency', 'funeral', 'hospital', 'doctor'],
    travel: ['traveling', 'out of town', 'vacation', 'trip'],
    work: ['work', 'meeting', 'business trip', 'conference']
  };

  // Find matching keywords
  const foundKeywords = [];
  let maxCategoryScore = 0;
  let primaryCategory = null;

  for (const [category, keywords] of Object.entries(scheduleKeywords)) {
    const matches = keywords.filter(keyword => text.includes(keyword));
    if (matches.length > 0) {
      foundKeywords.push(...matches);
      if (matches.length > maxCategoryScore) {
        maxCategoryScore = matches.length;
        primaryCategory = category;
      }
    }
  }

  // If no schedule keywords found, not a schedule request
  if (foundKeywords.length === 0) {
    return {
      isScheduleRequest: false,
      type: null,
      urgency: 'low',
      keywords: [],
      confidence: 0
    };
  }

  // Determine request type
  let requestType = 'reschedule'; // default
  if (primaryCategory === 'cancel') {
    requestType = 'cancellation';
  } else if (primaryCategory === 'postpone') {
    requestType = 'postpone';
  } else if (primaryCategory === 'reschedule') {
    requestType = 'reschedule';
  }

  // Determine urgency
  let urgency = 'medium'; // default for schedule requests
  
  // High urgency indicators
  const urgentIndicators = [
    ...scheduleKeywords.emergency,
    'today', 'tomorrow', 'this morning', 'this afternoon',
    'sick', 'family emergency', 'hospital'
  ];
  
  const hasUrgentKeywords = urgentIndicators.some(keyword => text.includes(keyword));
  
  // Check for same-day or next-day requests
  const timelyWords = ['today', 'tomorrow', 'this morning', 'this afternoon', 'tonight'];
  const isTimeSensitive = timelyWords.some(word => text.includes(word));
  
  if (hasUrgentKeywords || isTimeSensitive) {
    urgency = 'high';
  } else if (foundKeywords.length >= 3) {
    urgency = 'medium';
  } else {
    urgency = 'low';
  }

  // Calculate confidence score
  let confidence = Math.min(foundKeywords.length * 20, 100);
  
  // Boost confidence for clear schedule language
  const clearPhrases = [
    'reschedule my cleaning',
    'change my appointment',
    'move my cleaning',
    'cancel my appointment',
    'cancel the cleaning'
  ];
  
  if (clearPhrases.some(phrase => text.includes(phrase))) {
    confidence = Math.min(confidence + 30, 100);
  }

  return {
    isScheduleRequest: true,
    type: requestType,
    urgency: urgency,
    keywords: foundKeywords,
    confidence: confidence,
    primaryCategory: primaryCategory
  };
}

// Helper function for testing
function testScheduleDetection() {
  const testMessages = [
    "Hi! I need to reschedule tomorrow's cleaning to Friday if possible",
    "Emergency! Need to cancel today's 2pm cleaning - sick kid at home",
    "Can we move next week's appointment to a different day? I'll be traveling",
    "Hey this is Tom. Can we reschedule this Thursday to next Monday?",
    "Hi, need to postpone cleaning due to family emergency",
    "Hello, how are you today?", // Should not detect
    "Thanks for the great cleaning last week!", // Should not detect
    "Can you reschedule my cleaning appointment for this week?",
    "I need to cancel my appointment due to illness",
    "Is it possible to move my cleaning to another day?"
  ];

  console.log('🧪 Testing Schedule Detection');
  console.log('=' .repeat(50));

  testMessages.forEach((message, index) => {
    const result = detectScheduleRequest(message);
    console.log(`\nTest ${index + 1}: "${message}"`);
    console.log(`   Detected: ${result.isScheduleRequest ? '✅ YES' : '❌ NO'}`);
    if (result.isScheduleRequest) {
      console.log(`   Type: ${result.type}`);
      console.log(`   Urgency: ${result.urgency}`);
      console.log(`   Keywords: ${result.keywords.join(', ')}`);
      console.log(`   Confidence: ${result.confidence}%`);
    }
  });
}

module.exports = {
  detectScheduleRequest,
  testScheduleDetection
};
