# Testing Guide - ZAS Chat Utility

## Overview

This guide covers all testing approaches for the ZAS Chat Utility, from local HTML testing to Salesforce deployment validation.

---

## 🧪 Testing Hierarchy

```
1. Local HTML Test Harness (Fastest)
   ↓
2. Salesforce Sandbox Deployment
   ↓
3. Apex Unit Tests
   ↓
4. User Acceptance Testing
   ↓
5. Production Deployment
```

---

## 1. Local HTML Test Harness

### Purpose
Test the API endpoints before deploying to Salesforce.

### Steps

1. **Start API Services**
   ```bash
   # Terminal 1: Start MCP Server
   cd /path/to/ZDZAS-MCP
   python app.py
   
   # Terminal 2: Start Chat API
   python chat_api.py
   ```

2. **Open Test Harness**
   ```bash
   # Option 1: Direct file open
   open salesforce/test-harness.html  # Mac
   xdg-open salesforce/test-harness.html  # Linux
   start salesforce/test-harness.html  # Windows
   
   # Option 2: With a simple HTTP server (if CORS issues)
   cd salesforce
   python -m http.server 8080
   # Then open http://localhost:8080/test-harness.html
   ```

3. **Configure Endpoint**
   - Click "⚙️ Configuratie" button
   - Verify endpoint is `http://localhost:9000/chat`
   - Note the auto-generated Conversation ID

4. **Test Scenarios**

   **Basic Chat:**
   ```
   Input: "Hallo, kun je me helpen?"
   Expected: Response from ZAS agent with greeting
   ```

   **Tool Usage:**
   ```
   Input: "Zoek tickets over login problemen"
   Expected: Agent uses tickets_search tool and returns results
   ```

   **Conversation Context:**
   ```
   Input 1: "Wat zijn de meest voorkomende problemen?"
   Input 2: "Vertel me meer over het eerste probleem"
   Expected: Agent remembers context from first question
   ```

   **Error Handling:**
   ```
   Test: Stop API service
   Input: "Test"
   Expected: Error message shown in red banner
   ```

   **Reset:**
   ```
   Action: Click "Reset" button
   Expected: Conversation cleared, new ID generated
   ```

### What to Verify

- ✓ Messages appear in correct order
- ✓ Typing indicator shows while processing
- ✓ Streaming effect displays smoothly
- ✓ Timestamps are accurate
- ✓ Errors are handled gracefully
- ✓ Reset clears conversation
- ✓ Conversation ID changes after reset
- ✓ Console shows no JavaScript errors (F12)

### Common Issues

**Issue:** "Failed to fetch"
- **Cause:** API not running or wrong endpoint
- **Fix:** Check API is running on port 9000

**Issue:** CORS errors in console
- **Cause:** Browser security for local files
- **Fix:** Use Python HTTP server method

---

## 2. API Testing with cURL

### Basic Chat Request

```bash
curl -X POST http://localhost:9000/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: test-session-123" \
  -d '{
    "message": "Hallo, test bericht",
    "conversationId": "test-session-123"
  }'
```

### Expected Response
```json
{
  "reply": "Response from ZAS agent...",
  "conversationId": "test-session-123"
}
```

### Reset Request

```bash
curl -X POST http://localhost:9000/reset \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: test-session-123" \
  -d '{
    "conversationId": "test-session-123"
  }'
```

### Load Testing (Optional)

```bash
# Install Apache Bench
# Mac: brew install httpd
# Ubuntu: apt-get install apache2-utils

# Run 100 requests with 10 concurrent
ab -n 100 -c 10 -p request.json -T application/json \
  http://localhost:9000/chat
```

---

## 3. Salesforce Sandbox Testing

### Prerequisites

1. Salesforce Sandbox or Developer Org
2. Salesforce CLI installed
3. API running (local or ngrok tunnel)

### Deployment

```bash
# Navigate to salesforce directory
cd salesforce

# Login to sandbox
sf org login web --alias my-sandbox --instance-url https://test.salesforce.com

# Deploy
sf project deploy start --source-dir force-app --target-org my-sandbox

# Verify deployment
sf project deploy report --target-org my-sandbox
```

### Configuration

1. **Remote Site Settings**
   - Setup → Remote Site Settings → New
   - Name: `ZAS_Chat_API`
   - URL: Your API endpoint (ngrok or production URL)
   - Active: ✓

2. **Add to Page**
   - Lightning App Builder
   - Edit or create a page
   - Add "ZAS Chat Utility" component
   - Save and activate

### Manual Testing Checklist

Go to the page with the component and test:

#### Visual Testing
- [ ] Component renders without errors
- [ ] Header displays correctly
- [ ] Message area is scrollable
- [ ] Input field is visible and editable
- [ ] Buttons are styled correctly
- [ ] Colors match Salesforce theme

#### Functional Testing
- [ ] Can type in message field
- [ ] Send button is enabled when text entered
- [ ] Send button is disabled when empty
- [ ] Enter key sends message
- [ ] User messages appear on right
- [ ] AI messages appear on left
- [ ] Typing indicator shows
- [ ] Messages stream progressively
- [ ] Timestamps display correctly
- [ ] Reset button works
- [ ] Confirmation dialog appears on reset

#### Integration Testing
- [ ] API calls complete successfully
- [ ] Error messages display for failures
- [ ] Conversation context is maintained
- [ ] Session ID is preserved
- [ ] Multiple messages work in sequence

#### Performance Testing
- [ ] First message loads in < 5 seconds
- [ ] Subsequent messages load quickly
- [ ] UI remains responsive during processing
- [ ] Long messages display correctly
- [ ] Many messages don't slow down UI

#### Mobile Testing (if applicable)
- [ ] Component renders on mobile
- [ ] Touch interactions work
- [ ] Keyboard doesn't cover input
- [ ] Messages are readable
- [ ] Buttons are touchable

---

## 4. Apex Unit Testing

### Run All Tests

```bash
# Via CLI
sf apex run test --class-names ZASChatControllerTest --target-org my-sandbox --code-coverage --result-format human

# Via Developer Console
# 1. Open Developer Console
# 2. Test → New Run
# 3. Select ZASChatControllerTest
# 4. Click Run
```

### Expected Results

```
Test Results:
- Classes: 1
- Methods: 7
- Passed: 7
- Failed: 0
- Code Coverage: 95%+
```

### Test Coverage Requirements

- **Sandbox:** 75% minimum
- **Production:** 75% minimum (enforced)
- **Best Practice:** 90%+

### View Coverage

```bash
sf apex get test --test-run-id <id> --code-coverage --target-org my-sandbox
```

Or in Developer Console:
1. Test → View Code Coverage
2. Select ZASChatController
3. Review uncovered lines

---

## 5. Integration Testing

### Test with Actual API

1. **Setup ngrok tunnel**
   ```bash
   ngrok http 9000
   # Copy HTTPS URL
   ```

2. **Update Remote Site**
   - Setup → Remote Site Settings
   - Edit ZAS_Chat_API
   - Update URL to ngrok URL

3. **Update Controller**
   - Edit ZASChatController.cls
   - Update getAPIEndpoint() return value
   - Deploy changes

4. **Test End-to-End**
   - Send message from Salesforce
   - Verify API receives request (check logs)
   - Verify response returns to Salesforce
   - Check conversation history maintained

### Debug Logs

**Enable Debug Logs:**
1. Setup → Debug Logs
2. New → Select your user
3. Set log level to FINEST for Apex Code
4. Reproduce issue
5. View log for details

**Check for:**
- Request payload sent
- Response received
- HTTP status codes
- Error messages
- Timeout issues

---

## 6. User Acceptance Testing (UAT)

### Test Users
Create test users with different profiles:
- Standard User
- System Administrator
- Custom profiles with restricted access

### UAT Scenarios

1. **First Time User**
   - User sees component for first time
   - Expects clear interface
   - Should understand how to use it

2. **Power User**
   - Sends multiple messages
   - Uses reset feature
   - Expects fast responses

3. **Error Recovery**
   - Network fails mid-conversation
   - User sees error
   - Can recover and continue

4. **Long Session**
   - User has extended conversation
   - Context maintained throughout
   - No performance degradation

### UAT Checklist

- [ ] UI is intuitive
- [ ] Response time acceptable
- [ ] Errors are user-friendly
- [ ] Features work as expected
- [ ] Documentation is clear
- [ ] Users can accomplish tasks

---

## 7. Performance Testing

### Metrics to Track

1. **API Response Time**
   - Target: < 3 seconds
   - Measure: Time from send to first response

2. **Streaming Speed**
   - Target: 30ms per word
   - Adjust in zasChatUtility.js

3. **Memory Usage**
   - Monitor browser memory
   - Check for memory leaks
   - Test with 100+ messages

4. **Concurrent Users**
   - Test multiple users simultaneously
   - Verify API can handle load
   - Check Salesforce governor limits

### Load Testing

```bash
# Use JMeter or similar
# Test scenarios:
# - 10 users, 5 minutes
# - 50 users, 10 minutes
# - 100 users, 5 minutes

# Check for:
# - Response time degradation
# - Error rate
# - API timeout rate
```

---

## 8. Security Testing

### Security Checklist

- [ ] API endpoint uses HTTPS
- [ ] No API keys in client code
- [ ] Input sanitization works
- [ ] XSS prevention in place
- [ ] CSRF tokens if needed
- [ ] Rate limiting configured
- [ ] Authentication enforced
- [ ] Authorization checked
- [ ] Audit trail enabled
- [ ] PII handling compliant

### Test Inputs

**XSS Attempts:**
```
<script>alert('xss')</script>
<img src=x onerror=alert('xss')>
```

**SQL Injection Attempts:**
```
' OR '1'='1
'; DROP TABLE users; --
```

**Large Payloads:**
```
# 10,000 character message
# Should be rejected or truncated
```

---

## 9. Production Deployment Testing

### Pre-Deployment Checklist

- [ ] All tests pass in sandbox
- [ ] Code coverage > 75%
- [ ] UAT completed and signed off
- [ ] Security review completed
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Rollback plan prepared
- [ ] Change set validated

### Deployment Process

1. **Create Change Set**
   - In Sandbox: Setup → Outbound Change Sets
   - New Change Set: "ZAS Chat Utility v1.0"
   - Add components:
     - Apex Class: ZASChatController
     - Apex Class: ZASChatControllerTest
     - Lightning Component: zasChatUtility
   - Upload to Production

2. **Validate in Production**
   - In Production: Setup → Inbound Change Sets
   - Validate change set
   - Run all tests
   - Check for conflicts

3. **Deploy**
   - Deploy validated change set
   - Monitor deployment
   - Verify success

4. **Post-Deployment**
   - Configure Remote Site Settings
   - Update API endpoint if needed
   - Add component to pages
   - Test with real users

### Smoke Testing

After deployment, immediately test:

1. Component loads
2. Can send one message
3. Can receive one response
4. No console errors
5. API connectivity works

If any fail, execute rollback plan immediately.

---

## 10. Continuous Monitoring

### Metrics to Monitor

1. **Usage Metrics**
   - Messages per day
   - Users per day
   - Average conversation length
   - Peak usage times

2. **Performance Metrics**
   - Average response time
   - API timeout rate
   - Error rate
   - Concurrent users

3. **Quality Metrics**
   - User satisfaction
   - Task completion rate
   - Support tickets about component

### Monitoring Tools

- **Salesforce Event Monitoring**
- **Custom Logging**
- **API Gateway Logs**
- **Application Performance Monitoring (APM)**

### Alerts

Set up alerts for:
- Error rate > 5%
- Response time > 5 seconds
- API downtime
- High load

---

## 11. Troubleshooting Guide

### Common Issues

**1. "Fout bij het verzenden van bericht"**
```
Symptom: Error banner in UI
Check:
- Is API running?
- Remote Site Settings configured?
- Correct endpoint URL?
- Network connectivity?
Debug: Check browser console and Apex debug logs
```

**2. No Response Received**
```
Symptom: Typing indicator stays forever
Check:
- API timeout (increase if needed)
- API processing time
- Network issues
Debug: Check API logs for request
```

**3. Conversation Context Lost**
```
Symptom: Agent doesn't remember previous messages
Check:
- Conversation ID being passed?
- API maintaining history?
- Not exceeding history limit?
Debug: Check conversationId in requests
```

**4. Component Not Found**
```
Symptom: Can't find component in App Builder
Check:
- Deployment successful?
- Component targets correct?
- Cache clear needed?
Debug: Redeploy component
```

---

## Conclusion

This comprehensive testing approach ensures the ZAS Chat Utility works reliably in all scenarios before reaching end users. Start with local testing, progress through Salesforce sandbox, and only deploy to production after all tests pass.

Remember: **Test early, test often, test thoroughly!**
