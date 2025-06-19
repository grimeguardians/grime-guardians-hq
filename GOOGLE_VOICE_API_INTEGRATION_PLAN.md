# Google Voice API Integration Plan

## 🎯 **Objective**
Remove Google Voice email monitoring from Gmail and implement direct Google Voice API integration for cleaner architecture.

## 📋 **Current State**
- Ava monitors Gmail for Google Voice SMS notifications (`txt.voice.google.com`)
- Replies via email which triggers SMS through Google Voice
- Mixed communication channels create complexity

## 🚀 **New Architecture**

### **Email Communication Monitor**
- **Focus**: Direct business emails only
- **Excludes**: Google Voice notifications
- **Monitors**: 
  - `grimeguardianscleaning@gmail.com`
  - `brandonr@grimeguardians.com`
  - `broberts111592@gmail.com`

### **Google Voice API Monitor** (New)
- **Purpose**: Direct SMS monitoring and sending
- **File**: `/src/utils/googleVoiceMonitor.js` (updated)
- **Integration**: Connects to conversation manager for Ava/Dean processing

## 🔧 **Implementation Options**

### **Option 1: Google Workspace Voice API** (Recommended)
- **Requirements**: Google Workspace account with Voice add-on
- **Benefits**: Official API, reliable, full feature support
- **Cost**: ~$20/month per user

### **Option 2: Twilio Integration**
- **Requirements**: Port Google Voice number to Twilio
- **Benefits**: Robust API, extensive features
- **Process**: Number porting (1-2 weeks)

### **Option 3: Web Automation** (Fallback)
- **Requirements**: Puppeteer/Playwright
- **Benefits**: Uses existing Google Voice
- **Drawbacks**: Less reliable, may break with UI changes

## 📱 **Integration Points**

### **Conversation Manager**
- Same processing logic for SMS and email
- Ava handles operational messages
- Dean (future) handles sales messages

### **Discord Integration**
- Same approval workflow
- DM notifications for response approval
- Consistent user experience

## 🎯 **Next Steps**

1. **Choose API Option**: Recommend Google Workspace Voice API
2. **API Setup**: Configure credentials and permissions
3. **Integration**: Connect to existing conversation flow
4. **Testing**: Verify SMS monitoring and sending
5. **Cleanup**: Remove Google Voice email monitoring code

## 💡 **Benefits**

- **Cleaner Architecture**: Separate channels for different purposes
- **Better Reliability**: Direct API vs email forwarding
- **Faster Response**: Real-time SMS vs email polling
- **Easier Maintenance**: No email parsing complexity
- **Future-Ready**: Scalable for multiple phone numbers

## 🔄 **Migration Plan**

1. **Phase 1**: Set up Google Voice API monitoring (parallel to email)
2. **Phase 2**: Test and verify API functionality
3. **Phase 3**: Disable email-based Google Voice monitoring
4. **Phase 4**: Clean up legacy email parsing code

---

**Status**: Architecture planned, implementation pending API choice and setup.
