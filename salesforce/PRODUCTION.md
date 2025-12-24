# Production Deployment Guide

## 📋 Pre-Deployment Checklist

### Code Quality
- [ ] All Apex tests pass with >75% coverage
- [ ] No hardcoded credentials or API keys
- [ ] Error handling implemented everywhere
- [ ] Logging configured appropriately
- [ ] Code follows Salesforce best practices

### Security
- [ ] Input validation in place
- [ ] XSS prevention implemented
- [ ] HTTPS enforced for all API calls
- [ ] No sensitive data in client code
- [ ] API authentication configured
- [ ] Rate limiting implemented
- [ ] Security review completed

### Configuration
- [ ] API endpoint is production URL (not ngrok/localhost)
- [ ] Remote Site Settings documented
- [ ] Custom Metadata or Custom Settings for config
- [ ] Timeout values appropriate for production
- [ ] Error messages user-friendly (no stack traces)

### Testing
- [ ] All tests pass in sandbox
- [ ] UAT completed successfully
- [ ] Performance testing done
- [ ] Load testing completed
- [ ] Security testing passed
- [ ] Mobile testing done

### Documentation
- [ ] README.md complete
- [ ] Setup instructions clear
- [ ] Troubleshooting guide available
- [ ] API documentation updated
- [ ] User guide created
- [ ] Admin guide created

### Infrastructure
- [ ] Production API server running
- [ ] Load balancer configured
- [ ] SSL certificates valid
- [ ] DNS configured correctly
- [ ] Monitoring set up
- [ ] Alerting configured
- [ ] Backup plan in place

### Rollback Plan
- [ ] Rollback procedure documented
- [ ] Previous version backed up
- [ ] Rollback tested in sandbox
- [ ] Team trained on rollback

---

## 🚀 Deployment Steps

### Step 1: Final Sandbox Validation (30 min)

```bash
# Deploy to sandbox one final time
sf org login web --alias prod-sandbox --instance-url https://test.salesforce.com

cd salesforce

# Deploy everything
sf project deploy start --source-dir force-app --target-org prod-sandbox

# Run all tests
sf apex run test --class-names ZASChatControllerTest \
  --target-org prod-sandbox \
  --code-coverage \
  --result-format human

# Verify coverage
sf apex get test --code-coverage --target-org prod-sandbox
```

**Expected Results:**
- ✓ Deployment successful
- ✓ All tests pass
- ✓ Coverage > 75%

### Step 2: Update API Endpoint (10 min)

**Option A: Custom Metadata (Recommended)**

1. Create Custom Metadata Type in Production:
   - Setup → Custom Metadata Types → New
   - Label: `ZAS Chat Config`
   - API Name: `ZAS_Chat_Config`
   - Fields:
     - `API_Endpoint__c` (Text, 255)
     - `Timeout__c` (Number)

2. Create Record:
   - Label: `Default`
   - API Endpoint: `https://your-production-api.com/chat`
   - Timeout: `60000`

3. Update Controller:
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

**Option B: Custom Setting**

1. Create Hierarchy Custom Setting
2. Add fields for API configuration
3. Update controller to read from setting

**Option C: Hardcode (Not Recommended)**

Only if you have a static, never-changing URL:
```apex
private static String getAPIEndpoint() {
    return 'https://zas-api.yourdomain.com/chat';
}
```

### Step 3: Create Change Set (20 min)

In your **Sandbox**:

1. **Create Outbound Change Set**
   - Setup → Outbound Change Sets
   - New Change Set
   - Name: `ZAS_Chat_Utility_v1_0`
   - Description: `Initial deployment of ZAS Chat Utility Lightning Web Component`

2. **Add Components**
   - Click "Add" → "Apex Class"
     - ☑ ZASChatController
     - ☑ ZASChatControllerTest
   - Click "Add" → "Lightning Component Bundle"
     - ☑ zasChatUtility
   - If using Custom Metadata:
     - Add Custom Metadata Type
     - Add Custom Metadata Record

3. **Upload**
   - Click "Upload"
   - Select target: Production
   - Wait for upload to complete

### Step 4: Configure Production (15 min)

In **Production**:

1. **Remote Site Settings**
   - Setup → Remote Site Settings → New Remote Site
   - Remote Site Name: `ZAS_Chat_API`
   - Remote Site URL: `https://your-production-api.com`
   - Description: `ZAS Chat API for AI assistant integration`
   - Active: ✓
   - Save

2. **CORS Configuration (if needed)**
   - Setup → CORS
   - Add your API domain to whitelist

### Step 5: Validate Change Set (20 min)

In **Production**:

1. **Open Inbound Change Set**
   - Setup → Inbound Change Sets
   - Find: `ZAS_Chat_Utility_v1_0`
   - Click "Validate"

2. **Run Tests**
   - Automatically runs during validation
   - Must pass with >75% coverage

3. **Review Results**
   - Check for any conflicts
   - Review test results
   - Fix any issues in sandbox if validation fails

### Step 6: Deploy to Production (15 min)

**Only proceed if validation passed!**

1. **Deploy Change Set**
   - Click "Deploy" on validated change set
   - Monitor deployment progress
   - Wait for completion

2. **Verify Deployment**
   ```bash
   # Or via CLI
   sf org login web --alias production
   
   # Check deployment status
   sf project deploy report --target-org production
   ```

### Step 7: Configure Pages (10 min)

1. **Add to Lightning Page**
   - Setup → Lightning App Builder
   - Edit target page (Home, App, or Record page)
   - Add "ZAS Chat Utility" component
   - Configure height if needed
   - Save and Activate

2. **Set Page Visibility**
   - Assign to appropriate profiles/permissions
   - Configure org-wide default or page assignment

### Step 8: Smoke Test (10 min)

Immediately test in production:

1. **Access Component**
   - Navigate to page with component
   - Verify component renders

2. **Send Test Message**
   - Type: "Hello, this is a test"
   - Click Send
   - Verify response received

3. **Check Console**
   - Open browser DevTools (F12)
   - Verify no JavaScript errors
   - Check network tab for successful API calls

4. **Test Error Handling**
   - Temporarily enter wrong endpoint in config
   - Verify error message displays correctly
   - Restore correct endpoint

5. **Test Reset**
   - Click Reset button
   - Verify conversation clears

### Step 9: Monitor (Ongoing)

1. **Check Debug Logs**
   - Setup → Debug Logs
   - Monitor for errors

2. **Monitor API**
   - Check API logs for requests
   - Monitor error rates
   - Watch response times

3. **User Feedback**
   - Create feedback channel
   - Monitor support tickets
   - Track user satisfaction

---

## 🔧 Post-Deployment Configuration

### 1. Set Up Monitoring

**Salesforce Event Monitoring**
```
Setup → Event Monitoring
- Enable Lightning Usage
- Enable API Usage
- Configure storage
```

**Custom Logging (Optional)**
```apex
// Create Custom Object: Chat_Log__c
// Fields:
// - User__c (Lookup to User)
// - Message__c (Long Text)
// - Response__c (Long Text)
// - Duration__c (Number)
// - Error__c (Checkbox)
// - Error_Message__c (Long Text)
```

### 2. Create Custom Labels

For internationalization:

```
Setup → Custom Labels → New

- Label: Chat_Window_Title
  Value: ZAS Chat Assistant

- Label: Chat_Placeholder
  Value: Typ uw vraag hier...

- Label: Send_Button
  Value: Verzenden

- Label: Reset_Button
  Value: Reset

- Label: Error_Sending
  Value: Er is een fout opgetreden bij het verzenden
```

Update LWC to use labels:
```javascript
import CHAT_TITLE from '@salesforce/label/c.Chat_Window_Title';
```

### 3. Configure Profiles & Permissions

```
Setup → Profiles
- Select profile
- Apex Class Access:
  ☑ ZASChatController (enabled)
- Lightning Component Visibility:
  ☑ zasChatUtility (enabled)
```

### 4. Set Up Page Layouts

Add to multiple page types:
- Home Page
- Account Record Page
- Case Record Page
- Custom App Page

### 5. Create Help Documentation

Document for users:
- How to access chat
- What questions to ask
- How to reset conversation
- Who to contact for issues

---

## 📊 Success Metrics

Track these KPIs post-deployment:

### Usage Metrics
- Daily active users
- Messages per day
- Average conversation length
- Peak usage hours

### Performance Metrics
- Average response time
- API timeout rate
- Error rate
- User satisfaction score

### Business Metrics
- Time saved per support ticket
- Questions answered by AI
- Escalation rate
- User adoption rate

---

## 🚨 Rollback Procedure

If critical issues occur:

### Immediate Actions (5 min)

1. **Remove Component from Pages**
   ```
   Lightning App Builder → Edit Page → Remove Component → Save
   ```

2. **Disable Remote Site**
   ```
   Setup → Remote Site Settings → Deactivate ZAS_Chat_API
   ```

### Full Rollback (20 min)

1. **Create Destructive Change Set**
   ```
   Setup → Outbound Change Sets → New
   Add components to delete
   Upload to production
   ```

2. **Or Delete Manually**
   ```
   Setup → Apex Classes → Delete ZASChatController
   Setup → Apex Classes → Delete ZASChatControllerTest
   Setup → Lightning Components → Delete zasChatUtility
   ```

3. **Clean Up**
   - Remove Remote Site Setting
   - Remove Custom Metadata (if used)
   - Clear cache

### Communication

- Notify users immediately
- Update status page
- Send internal announcement
- Schedule post-mortem

---

## 📝 Deployment Checklist Summary

**Pre-Deploy**
- [ ] All tests pass
- [ ] Security review done
- [ ] Documentation complete
- [ ] API endpoint configured

**Deploy**
- [ ] Sandbox validated
- [ ] Change set created
- [ ] Production configured
- [ ] Change set validated
- [ ] Change set deployed

**Post-Deploy**
- [ ] Smoke test passed
- [ ] Monitoring configured
- [ ] Users notified
- [ ] Documentation published

**Verify**
- [ ] Component accessible
- [ ] Messages send/receive
- [ ] No console errors
- [ ] Performance acceptable

---

## 🎯 Go-Live Announcement

### Internal Email Template

```
Subject: New Feature: ZAS Chat Assistant Now Available

Hi Team,

We're excited to announce the launch of the ZAS Chat Assistant in Salesforce!

What is it?
An AI-powered chat assistant that helps you quickly find information,
analyze tickets, and get answers to common questions - all within Salesforce.

Where to find it?
[Home Page / Account Pages / Case Pages - specify locations]

How to use it?
1. Open the page with the chat component
2. Type your question
3. Get instant AI-powered responses

Features:
- Real-time responses with typing indicators
- Maintains conversation context
- Connects to Zendesk, Jira, and Confluence data
- Easy-to-use interface

Need help?
- Documentation: [Link to docs]
- Support: [Contact information]
- Training: [Training session details]

Please try it out and send us your feedback!

Best regards,
[Your Team]
```

### User Training

Provide:
1. 10-minute overview video
2. Quick start guide (1 page)
3. FAQ document
4. Office hours for questions

---

## 🔐 Security Considerations

### Production Security

1. **API Security**
   - Use API Gateway with rate limiting
   - Implement authentication (OAuth 2.0)
   - Use API keys with rotation policy
   - Monitor for suspicious activity

2. **Data Security**
   - Encrypt data in transit (TLS 1.2+)
   - Mask PII in logs
   - Implement data retention policy
   - Regular security audits

3. **Access Control**
   - Minimum necessary permissions
   - Regular permission reviews
   - Audit trail enabled
   - IP restrictions if needed

### Compliance

- [ ] GDPR compliance verified
- [ ] Data processing agreement signed
- [ ] Privacy policy updated
- [ ] Terms of service reviewed
- [ ] Audit logs configured

---

## 📞 Support Plan

### Level 1: User Issues
- Can't access component
- Component not loading
- Error messages
**Response:** Help desk, documentation

### Level 2: Integration Issues
- API connectivity problems
- Timeout errors
- Performance issues
**Response:** Admin team, check API status

### Level 3: Critical Issues
- Complete service outage
- Security breach
- Data loss
**Response:** Development team, execute rollback

### Support Contacts
- Help Desk: [Email/Phone]
- Admin Team: [Email/Phone]
- Dev Team: [Email/Phone]
- On-Call: [Phone/Pager]

---

## ✅ Launch Complete!

Congratulations on successfully deploying the ZAS Chat Utility to production!

**Next Steps:**
1. Monitor usage and performance
2. Collect user feedback
3. Plan iterative improvements
4. Schedule regular maintenance

**Remember:**
- Respond quickly to issues
- Communicate proactively
- Iterate based on feedback
- Celebrate the win! 🎉
