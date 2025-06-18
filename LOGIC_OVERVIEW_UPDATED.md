# Grime Guardians Agentic Ops Logic Overview

_Last updated: 2025-06-17_

## System Purpose
A dual-agent system for comprehensive business automation: Ava (COO) handles pure operations while CMO Suite manages sales/revenue. Context-aware conversation threading ensures seamless client experience across all channels.

## 🎯 **Core Architecture: Operations + Sales Separation**

### **Ava (COO) - Operations Focus**
- **Scope**: Scheduling, logistics, client management, operational support
- **Channels**: Google Voice, High Level, Discord (internal)
- **Autonomy**: 80% confidence auto-responses for routine operations
- **Learning**: Natural language training via Discord DMs

### **CMO Suite - Sales Focus** 
- **Scope**: Pricing, lead qualification, prospect conversion, market analysis
- **Handoff Point**: After booking → transfers to Ava for operations
- **Tools**: Advanced GPT-4o with web search capabilities

## 🧠 **Context-Aware Conversation Management**

### **ConversationManager System:**
- **Message Threading**: Maintains conversation state per phone number/contact
- **Context Memory**: Remembers questions asked and responses expected  
- **Pipeline Awareness**: Tracks ops vs sales conversation position
- **Multi-Channel**: Unified context across Google Voice and High Level

### **Classification Logic:**
```javascript
// Operations (Ava handles)
- scheduling_inquiry: "What time is my cleaning?"
- reschedule_request: "Can we move Thursday to Friday?"
- add_on_request: "Can you add fridge cleaning?" (+$120)

// Sales (CMO handles)  
- pricing_inquiry: "How much for deep cleaning?"
- new_prospect: "I need a quote for my house"
- service_inquiry: "What services do you offer?"
```

## 🔄 **Workflow Integration**

### **Message Processing Flow:**
1. **Message Received** → ConversationManager loads context
2. **Classification** → GPT-4o-mini determines ops vs sales
3. **Routing Decision**:
   - **Operations** → Ava processes with full context
   - **Sales** → CMO handoff with warm transition
4. **Response Generation** → Context-aware, conversation-threaded
5. **Approval Workflow** → Discord reactions for oversight
6. **Context Update** → ConversationManager stores state

### **Learning & Training:**
- **Natural Language Feedback**: "Ava, this should be routed to CMO"
- **Pattern Recognition**: Learns from corrections and communication style
- **Conversation Monitoring**: Observes High Level interactions for training
- **Continuous Improvement**: Adapts speech patterns and decision-making

## 🚀 **Current Capabilities**

### **Working Systems:**
- ✅ Google Voice conversation threading
- ✅ Context-aware message processing  
- ✅ Operations vs sales classification
- ✅ Natural language training system
- ✅ Discord reaction approval workflow
- ✅ Multi-account Gmail integration

### **Next Phase:**
- 🔄 High Level real-time conversation monitoring
- 🔄 CMO Suite implementation
- 🔄 Advanced autonomy with confidence thresholds
- 🔄 Speech pattern learning and mimicry

## 🏗️ **Technical Architecture**

### **Core Agents & Roles**
- **Ava (COO):** Context-aware operations management, client communication, scheduling
- **Keith (Check-in Monitor):** Attendance tracking, punctuality escalation, team coordination
- **ConversationManager:** Message threading, context persistence, pipeline tracking
- **MessageClassifier:** GPT-4o-mini powered ops vs sales routing

### **Attendance & Escalation (Unchanged)**
- Punctuality tracking with 30-day rolling strikes
- Discord-based escalation system
- Quality complaint detection and flagging
- Real-time alerts and notifications

### **Data Flow & Storage**
- **Notion**: System of record for all operational data
- **Discord**: Real-time communication and approval workflows  
- **JSON Memory**: Conversation context and training corrections
- **Gmail Integration**: Multi-account Google Voice message processing

## 🎓 **Training & Learning System**

### **Natural Language Training:**
```
You: "Ava, this is actually a scheduling change, not a new prospect"
Ava: "✅ Got it! I'll remember that 'reschedule my appointment' = scheduling_inquiry"
```

### **Pattern Recognition:**
- Speech pattern analysis and mimicry
- Conversation style adaptation
- Punctuation and tone matching
- Confidence threshold adjustment based on feedback

---

_This file is the single source of truth for agentic logic. Updated to reflect operations-focused Ava with CMO sales handoff and context-aware conversation management._
