# ZAS Chat Utility - Salesforce Implementation Guide

## Overview

The ZAS Chat Utility is a Lightning Web Component that provides an AI-powered chat interface within Salesforce, connecting to the ZAS Chat API backend. It features real-time streaming responses, typing indicators, conversation management, and a modern UI built with Salesforce Lightning Design System.

## Features

### 🎯 Core Features
- **Real-time Chat Interface**: Clean, modern chat UI with message bubbles
- **Streaming Responses**: Progressive display of AI responses for better UX
- **Typing Indicator**: Animated "is typing" indicator while waiting for responses
- **Conversation Management**: Maintains context across multiple messages
- **Reset Functionality**: Clear conversation and start fresh
- **Error Handling**: Graceful error messages and recovery
- **Responsive Design**: Works on desktop and mobile

### 💎 Advanced Features
- **Session Management**: Automatic generation and tracking of conversation IDs
- **Tenant Context**: Passes organization context to the API
- **Formatted Responses**: Supports rich text formatting in messages
- **Timestamp Display**: Shows when each message was sent
- **System Messages**: Special styling for system notifications
- **Accessibility**: Built with SLDS for accessibility compliance

## Architecture

```
┌─────────────────────────────────────────────┐
│         Salesforce Org                      │
│                                             │
│  ┌───────────────────────────────────┐     │
│  │  Lightning Web Component          │     │
│  │  (zasChatUtility)                 │     │
│  │  - User Interface                 │     │
│  │  - Streaming Simulation           │     │
│  │  - State Management               │     │
│  └──────────────┬────────────────────┘     │
│                 │                           │
│                 │ @wire / Apex Call         │
│                 ▼                           │
│  ┌───────────────────────────────────┐     │
│  │  Apex Controller                  │     │
│  │  (ZASChatController)              │     │
│  │  - HTTP Callout                   │     │
│  │  - Session Management             │     │
│  │  - Error Handling                 │     │
│  └──────────────┬────────────────────┘     │
│                 │                           │
└─────────────────┼───────────────────────────┘
                  │ HTTP/REST
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         External API Server                 │
│                                             │
│  ┌───────────────────────────────────┐     │
│  │  FastAPI Application              │     │
│  │  (chat_api.py)                    │     │
│  │  - /chat endpoint                 │     │
│  │  - /reset endpoint                │     │
│  │  - Conversation history           │     │
│  └──────────────┬────────────────────┘     │
│                 │                           │
│                 ▼                           │
│  ┌───────────────────────────────────┐     │
│  │  ZAS Agent                        │     │
│  │  (zas_agent.py)                   │     │
│  │  - AI Processing                  │     │
│  │  - Tool Integration               │     │
│  └───────────────────────────────────┘     │
│                                             │
└─────────────────────────────────────────────┘
```

## Installation & Setup

### Step 1: Prerequisites

1. **Salesforce Org**: Developer Edition, Sandbox, or Production org
2. **Salesforce CLI**: Install from https://developer.salesforce.com/tools/sfdxcli
3. **VS Code** (recommended): With Salesforce Extension Pack
4. **ZAS Chat API**: Running instance of the chat API (see main README)

### Step 2: Configure Remote Site Settings

Before deploying, you must whitelist the API endpoint in Salesforce:

1. Go to **Setup** → **Security** → **Remote Site Settings**
2. Click **New Remote Site**
3. Fill in the details:
   - **Remote Site Name**: `ZAS_Chat_API`
   - **Remote Site URL**: `https://your-domain.ngrok-free.app` (or your actual API URL)
   - **Description**: `ZAS Chat API endpoint for AI chat integration`
   - **Active**: ✓ Checked
4. Click **Save**

**Important**: If using ngrok or similar tunneling service, you'll need to update this whenever your URL changes.

### Step 3: Update API Endpoint

Edit the `ZASChatController.cls` file and update the API endpoint:

```apex
private static String getAPIEndpoint() {
    // Update this to your actual API URL
    return 'https://your-domain.ngrok-free.app/chat';
}
```

### Step 4: Deploy to Salesforce

#### Option A: Using Salesforce CLI

```bash
# Navigate to salesforce directory
cd salesforce

# Authenticate to your org (first time only)
sf org login web --alias my-org

# Deploy all components
sf project deploy start --source-dir force-app

# Verify deployment
sf project deploy report
```

#### Option B: Using VS Code

1. Open the `salesforce` folder in VS Code
2. Ensure "Salesforce Extension Pack" is installed
3. Authorize an org:
   - Press `Cmd/Ctrl + Shift + P`
   - Type "SFDX: Authorize an Org"
   - Select org type and login
4. Deploy components:
   - Right-click on `force-app` folder
   - Select "SFDX: Deploy Source to Org"

#### Option C: Using Change Sets (Production)

1. Deploy to Sandbox first using CLI or VS Code
2. Create an Outbound Change Set
3. Add all components:
   - Apex Class: ZASChatController
   - Apex Class: ZASChatControllerTest
   - Lightning Component: zasChatUtility
4. Upload and deploy to Production

### Step 5: Run Tests

```bash
# Run Apex tests
sf apex run test --class-names ZASChatControllerTest --result-format human --code-coverage

# Or from Developer Console:
# 1. Open Developer Console
# 2. Test → New Run
# 3. Select ZASChatControllerTest
# 4. Click Run
```

### Step 6: Add Component to a Page

1. **Edit a Lightning App Page**:
   - Go to Setup → Lightning App Builder
   - Create new or edit existing page
   - Find "ZAS Chat Utility" in the component list (Custom section)
   - Drag it onto the page
   - Save and activate

2. **Add to Home Page**:
   - Go to Home tab
   - Click gear icon → Edit Page
   - Add "ZAS Chat Utility" component
   - Save and activate

3. **Add to Record Page**:
   - Go to any record (e.g., Account, Case)
   - Click gear icon → Edit Page
   - Add "ZAS Chat Utility" component
   - Save and activate

## Configuration

### Custom Metadata Type (Optional but Recommended)

For better configuration management, create a Custom Metadata Type:

1. **Create Custom Metadata Type**:
   - Setup → Custom Metadata Types → New
   - Label: `ZAS Chat Config`
   - API Name: `ZAS_Chat_Config`
   - Add fields:
     - `API_Endpoint__c` (Text, 255)
     - `Timeout__c` (Number)
     - `Enable_Debug__c` (Checkbox)

2. **Update Controller**:
   Modify `getAPIEndpoint()` method to read from metadata:
   ```apex
   private static String getAPIEndpoint() {
       ZAS_Chat_Config__mdt config = [
           SELECT API_Endpoint__c 
           FROM ZAS_Chat_Config__mdt 
           WHERE DeveloperName = 'Default' 
           LIMIT 1
       ];
       return config.API_Endpoint__c;
   }
   ```

### Custom Labels (Optional)

For internationalization, create custom labels:

1. Setup → Custom Labels → New
2. Create labels for all UI text
3. Update LWC to use `@salesforce/label` imports

## Usage

### Basic Chat Interaction

1. Open a page with the chat component
2. Type your question in the text area
3. Click "Verzenden" or press Enter
4. Watch the typing indicator while AI processes
5. See the response stream in character by character
6. Continue the conversation with context maintained

### Reset Conversation

1. Click the "Reset" button
2. Confirm the reset action
3. Start a fresh conversation

### Error Handling

The component automatically handles:
- Network errors
- API timeouts
- Invalid responses
- Empty messages

Errors are displayed in a red alert banner and logged to browser console.

## Troubleshooting

### Common Issues

#### 1. "Fout bij het verzenden van bericht"

**Cause**: Remote Site Setting not configured or API unreachable

**Solution**:
- Verify Remote Site Settings in Setup
- Check API endpoint URL in ZASChatController
- Ensure API server is running
- Check firewall/network settings

#### 2. Component Not Appearing

**Cause**: Deployment failed or not activated on page

**Solution**:
- Verify deployment: `sf project deploy report`
- Check component is in Lightning App Builder
- Ensure page is activated

#### 3. Timeout Errors

**Cause**: API taking too long to respond

**Solution**:
- Increase timeout in ZASChatController (max 120 seconds)
- Optimize API performance
- Check network latency

#### 4. Tests Failing

**Cause**: Mock responses not matching actual API

**Solution**:
- Update mock responses in ZASChatControllerTest
- Verify API contract hasn't changed
- Check test coverage requirements

### Debug Mode

Enable debug logging:

```apex
// In ZASChatController.sendMessage()
System.debug('Request: ' + JSON.serialize(requestBody));
System.debug('Response: ' + res.getBody());
```

Check logs in Developer Console → Logs.

## Advanced Customization

### Modify Streaming Speed

Edit `zasChatUtility.js`:

```javascript
const streamInterval = setInterval(() => {
    // Change 30 to adjust speed (milliseconds per word)
    // Lower = faster, Higher = slower
}, 30);
```

### Change Color Scheme

Edit `zasChatUtility.css`:

```css
.user-message .message-bubble {
    background-color: #0176d3; /* Change user message color */
}

.assistant-message .message-bubble {
    background-color: white; /* Change assistant message color */
}
```

### Add Message History Persistence

Implement custom object to store conversation history:

1. Create `Chat_Message__c` custom object
2. Add fields: `Conversation_Id__c`, `Message__c`, `Is_User__c`, `Timestamp__c`
3. Update controller to save/load messages
4. Update LWC to load history on init

### Add Voice Input

Integrate Web Speech API:

```javascript
// In zasChatUtility.js
handleVoiceInput() {
    const recognition = new webkitSpeechRecognition();
    recognition.onresult = (event) => {
        this.inputMessage = event.results[0][0].transcript;
        this.handleSend();
    };
    recognition.start();
}
```

## API Reference

### Apex Methods

#### `sendMessage(String message, String conversationId)`
- **Description**: Send a message to the chat API
- **Parameters**:
  - `message`: User's message text (required)
  - `conversationId`: Conversation ID for context (optional)
- **Returns**: JSON string with reply and conversationId
- **Throws**: `AuraHandledException` on error

#### `resetConversation(String conversationId)`
- **Description**: Reset a conversation
- **Parameters**:
  - `conversationId`: Conversation ID to reset
- **Returns**: "OK" on success
- **Throws**: `AuraHandledException` on error

#### `testConnection()`
- **Description**: Test API connectivity
- **Returns**: Connection status message

### LWC Properties

#### Public Properties
- `conversationId`: Current conversation UUID
- `messages`: Array of message objects
- `isTyping`: Boolean for typing indicator
- `isLoading`: Boolean for loading state

#### Message Object Structure
```javascript
{
    id: Number,           // Unique message ID
    text: String,         // Message text
    isUser: Boolean,      // True if from user
    isSystem: Boolean,    // True if system message
    timestamp: String     // Formatted time
}
```

## Performance Considerations

### Optimization Tips

1. **Limit Message History**: Keep only last N messages in memory
2. **Lazy Loading**: Load older messages on demand
3. **Debounce Input**: Prevent rapid-fire requests
4. **Cache Responses**: For common questions
5. **Batch Requests**: If implementing multi-user chat

### Monitoring

Track key metrics:
- API response time
- Error rate
- User engagement (messages per session)
- Conversation length

Use Salesforce Event Monitoring or custom logging.

## Security Best Practices

1. **API Key Management**: Never hardcode API keys in code
2. **Input Validation**: Sanitize user input before sending
3. **HTTPS Only**: Always use encrypted connections
4. **Rate Limiting**: Implement on API side
5. **Access Control**: Use Salesforce sharing and permissions
6. **Audit Trail**: Log all conversations for compliance
7. **Data Classification**: Handle PII appropriately

## Testing in Salesforce

### Manual Testing Checklist

- [ ] Component renders correctly
- [ ] Can send messages
- [ ] Receives responses
- [ ] Typing indicator appears/disappears
- [ ] Streaming animation works
- [ ] Can reset conversation
- [ ] Error messages display correctly
- [ ] Works on mobile
- [ ] Works on different browsers
- [ ] Handles slow network gracefully

### Automated Testing

The included test class provides ~95% code coverage. To add more tests:

1. Test custom metadata configuration
2. Test multi-user scenarios
3. Test long conversations
4. Load testing with JMeter

## Support & Contribution

For issues or questions:
1. Check this guide first
2. Review API documentation
3. Check Salesforce Developer Forums
4. Open GitHub issue

## License

See main project LICENSE file.

## Changelog

### Version 1.0.0 (Initial Release)
- Lightning Web Component with chat UI
- Apex REST controller
- Streaming response simulation
- Typing indicator
- Conversation reset
- Error handling
- Full test coverage
