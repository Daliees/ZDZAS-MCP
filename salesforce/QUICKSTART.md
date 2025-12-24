# Quick Setup Guide - ZAS Chat Utility

## 🚀 Get Started in 10 Minutes

### Prerequisites Checklist
- [ ] Salesforce Developer Org or Sandbox
- [ ] ZAS Chat API running (default: http://localhost:9000)
- [ ] Salesforce CLI installed
- [ ] Internet connection

---

## Step 1: Start the API (5 min)

```bash
# In the main project directory
cd /path/to/ZDZAS-MCP

# Install dependencies (if not done)
pip install -r requirements.txt

# Start the MCP server (in one terminal)
python app.py

# Start the chat API (in another terminal)
python chat_api.py
```

API should now be running on `http://127.0.0.1:9000`

---

## Step 2: Expose API Publicly (2 min)

### Using ngrok (Recommended for testing)

```bash
# Install ngrok from https://ngrok.com/download
# Or: brew install ngrok (Mac)

# Start tunnel
ngrok http 9000

# Copy the HTTPS URL shown (e.g., https://abc123.ngrok-free.app)
```

**Save this URL - you'll need it in Step 3!**

---

## Step 3: Deploy to Salesforce (3 min)

```bash
# Navigate to salesforce directory
cd salesforce

# Login to your Salesforce org
sf org login web --alias my-dev-org

# Update API endpoint in ZASChatController.cls
# Replace: https://your-domain.ngrok-free.app
# With: Your actual ngrok URL

# Deploy
sf project deploy start --source-dir force-app

# Wait for success message ✓
```

---

## Step 4: Configure Salesforce (2 min)

1. **Add Remote Site Setting**:
   - Setup → Quick Find → "Remote Site"
   - New Remote Site:
     - Name: `ZAS_Chat_API`
     - URL: `https://your-ngrok-url.ngrok-free.app`
     - Active: ✓
   - Save

2. **Add Component to Page**:
   - Go to any Lightning page (Home, App, Record)
   - Click ⚙️ → Edit Page
   - Drag "ZAS Chat Utility" from Components panel
   - Save & Activate

---

## Step 5: Test! ✨

1. Open the page where you added the component
2. Type: "Hallo, kun je me helpen?"
3. Click Send or press Enter
4. Watch the typing indicator
5. See the AI response stream in!

---

## Troubleshooting Quick Fixes

### "Fout bij het verzenden"
- ✓ Check Remote Site Settings
- ✓ Verify ngrok is running
- ✓ Check API endpoint URL in controller

### Component Not Found
```bash
# Redeploy
sf project deploy start --source-dir force-app --ignore-conflicts
```

### API Not Responding
```bash
# Check if services are running
curl http://localhost:9000/chat -X POST -H "Content-Type: application/json" -d '{"message":"test"}'
```

---

## File to Edit for Your Setup

Only **ONE** file needs your URL:

```
salesforce/force-app/main/default/classes/ZASChatController.cls
```

Find this line (around line 24):
```apex
return 'https://your-domain.ngrok-free.app/chat';
```

Replace with your actual URL.

---

## Next Steps

✅ **Working?** Great! See full README.md for:
- Custom styling
- Advanced features
- Production deployment
- Security best practices

❌ **Issues?** See README.md Troubleshooting section or check:
- Browser console (F12)
- Salesforce Debug Logs
- API logs

---

## Production Deployment

When ready for production:

1. **Use permanent domain** (not ngrok)
2. **Configure Custom Metadata** for API URL
3. **Enable HTTPS** on API server
4. **Add authentication** to API
5. **Deploy via Change Sets** to production
6. **Set up monitoring** and logging

See README.md for detailed production guide.

---

## Commands Reference

```bash
# Deploy
sf project deploy start --source-dir force-app

# Run tests
sf apex run test --class-names ZASChatControllerTest

# Check deployment status
sf project deploy report

# View logs
sf org tail log

# Open org
sf org open

# Retrieve changes from org
sf project retrieve start --source-dir force-app
```

---

**Need help?** Check the full README.md in this directory!
