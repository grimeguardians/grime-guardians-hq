// Enhanced Discord DM Schema Demo
// This demonstrates the improved formatting and features

const exampleDiscordMessage = `🚨 **NEW SMS VIA GOOGLE VOICE (612-584-9396)**
═════════════════════════════════════════════

📞 **From:** 6518297734
👤 **Name:** Sarah Johnson
💬 **Message:** Hi! What time are you coming tomorrow? Also, can you add dishes to the cleaning?
⏰ **Time:** 1/15/2025, 2:30:45 PM

────────────────────────────── **ANALYSIS** ──────────────────────────────
🧠 **AI Assessment:**
⚡ **Type:** Customer Service Question
⚡ **Urgency:** medium
🎯 **Confidence:** 92%
💡 **Reasoning:** Client asking about appointment time and requesting additional service

─────────────────────────── **SUGGESTED REPLY** ───────────────────────────
💬 **Recommended Response:**
"Hi Sarah! Let me check your appointment details right away! I'll text you back within 15 minutes with your exact scheduled time and our team member's name. Absolutely! We can add dishes and any other kitchen tasks to your service. I'll note this in your appointment details and inform the team. Anything else you'd like us to include?"

🔄 **React with ✅ to send this reply via Google Voice**

═════════════════════════════════════════════
⚠️ **ACTION REQUIRED:** Review and respond as needed
═════════════════════════════════════════════`;

console.log("Enhanced Discord DM Schema:");
console.log(exampleDiscordMessage);

// Key improvements:
console.log("\n🔧 KEY ENHANCEMENTS:");
console.log("✅ Full 10-digit phone number display");
console.log("✅ Dynamic, context-aware suggested replies");
console.log("✅ Visual separation with Unicode characters");
console.log("✅ Clear action items and approval workflow");
console.log("✅ Only adds ✅ reaction when confidence > 80%");

// Suggested reply examples by message type:
const replyExamples = {
  "quote request": `Hi Sarah! Thank you for your interest! Based on what you've shared, I can provide a personalized quote. Could you confirm the number of bedrooms/bathrooms and your preferred frequency? We start at $80 for smaller homes with competitive rates for all sizes.`,
  
  "urgent booking": `Hi John! We can definitely help with short notice! Let me check our availability for tomorrow and get back to you within 30 minutes. What time would work best?`,
  
  "complaint": `Hi Mary! I sincerely apologize - this is absolutely not the standard we maintain at Grime Guardians. I want to make this right immediately. Can we schedule a time today for me to call you to discuss how we can resolve this?`,
  
  "time inquiry": `Hi Tom! Let me check your appointment details right away! I'll text you back within 15 minutes with your exact scheduled time and our team member's name.`,
  
  "adding services": `Hi Lisa! Absolutely! We can add dishes and any other kitchen tasks to your service. I'll note this in your appointment details and inform the team. Anything else you'd like us to include?`
};

console.log("\n💬 DYNAMIC REPLY EXAMPLES:");
Object.entries(replyExamples).forEach(([type, reply]) => {
  console.log(`\n${type.toUpperCase()}:`);
  console.log(`"${reply}"`);
});
