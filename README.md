# 🧠 Grime Guardians - AI-Powered Operations System

**Ava (COO) + CMO Suite - Complete Business Automation**

## 🎯 **System Overview**

Advanced dual-agent system for cleaning business automation:
- **Ava (COO)**: Pure operations - scheduling, logistics, client management
- **CMO Suite**: Sales & revenue - pricing, lead qualification, conversion

### **Current Capabilities:**
✅ **Context-Aware Messaging** - Maintains conversation threads per client  
✅ **Google Voice Integration** - Automated SMS response system  
✅ **GPT-4o-mini Classification** - 90-95% accuracy ops vs sales routing  
✅ **Discord Approval Workflow** - Reaction-based message oversight  
✅ **Natural Language Training** - Learn from corrections in real-time  
✅ **Multi-Channel Support** - Google Voice active, High Level ready  

## 🚀 **Quick Start**

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Configure: DISCORD_BOT_TOKEN, OPENAI_API_KEY, GMAIL_* variables

# Run the system
npm start

# Or with PM2 for production
pm2 start src/index.js --name grime-guardians
```

## 📋 **Key Features**

### **Intelligent Message Processing:**
- Detects new Google Voice messages via Gmail
- Classifies as operations vs sales with GPT-4o-mini
- Routes to appropriate agent (Ava or CMO)
- Maintains conversation context across message chains

### **Operations Automation:**
- Scheduling confirmations and changes
- Client support and communication
- Team coordination and logistics
- Add-on pricing for existing clients

### **Learning & Training:**
- Natural language feedback via Discord DMs
- Pattern recognition and communication style adaptation
- Continuous improvement from corrections
- Speech pattern mimicry with professional enhancement

## 🏗️ **Architecture**

```
Lead Inquiry → CMO (sales) → Booking → Ava (operations) → Client Success
```

### **Core Components:**
- `src/agents/ava.js` - COO operations agent
- `src/utils/emailCommunicationMonitor.js` - Message detection
- `src/utils/conversationManager.js` - Context threading
- `src/utils/messageClassifier.js` - GPT-4o-mini classification
- `src/utils/avaTrainingSystem.js` - Natural language learning

## 📊 **Documentation**

- [`SYSTEM_ARCHITECTURE_SUMMARY.md`](SYSTEM_ARCHITECTURE_SUMMARY.md) - Complete system overview
- [`LOGIC_OVERVIEW_UPDATED.md`](LOGIC_OVERVIEW_UPDATED.md) - Detailed workflow logic
- [`AI_MODEL_STRATEGY.md`](AI_MODEL_STRATEGY.md) - GPT model strategy and costs
- [`ENHANCED_AVA_DEPLOYMENT.md`](ENHANCED_AVA_DEPLOYMENT.md) - Deployment guide

## 🎓 **Training Ava**

Simply talk to Ava naturally via Discord DMs:

```
You: "This should be classified as a scheduling change, not new prospect"
Ava: "✅ Got it! I'll remember that pattern for next time"

You: "Route all pricing questions to CMO immediately"
Ava: "✅ Understood! All pricing inquiries → CMO handoff"
```
