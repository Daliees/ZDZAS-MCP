# Salesforce DX Project Configuration
# ====================================

# This file defines the structure of your Salesforce DX project
# and contains configuration options for the Salesforce CLI

## Project Details
- **API Version**: 59.0 (Winter '24)
- **Package Directory**: force-app/main/default

## Components Included
- Lightning Web Component: zasChatUtility
- Apex Controller: ZASChatController
- Apex Test Class: ZASChatControllerTest

## Local Development Prerequisites

### 1. Install Salesforce CLI
```bash
# Mac/Linux
npm install -g @salesforce/cli

# Or download from: https://developer.salesforce.com/tools/sfdxcli
```

### 2. Verify Installation
```bash
sf --version
```

### 3. Authenticate to Your Org
```bash
# For production/developer org
sf org login web --alias my-org

# For sandbox
sf org login web --alias my-sandbox --instance-url https://test.salesforce.com
```

### 4. Deploy Components
```bash
# Deploy to default org
sf project deploy start --source-dir force-app

# Deploy to specific org
sf project deploy start --source-dir force-app --target-org my-org
```

## Testing Locally

### Prerequisites
1. Have the ZAS Chat API running (see main README.md)
2. Configure Remote Site Settings in Salesforce
3. Update API endpoint in ZASChatController.cls

### Using VS Code
1. Install "Salesforce Extension Pack" from VS Code marketplace
2. Open the salesforce folder in VS Code
3. Authorize an org: Cmd/Ctrl + Shift + P → "SFDX: Authorize an Org"
4. Right-click on files to deploy to org

## Project Structure
```
salesforce/
├── force-app/
│   └── main/
│       └── default/
│           ├── lwc/
│           │   └── zasChatUtility/
│           │       ├── zasChatUtility.html
│           │       ├── zasChatUtility.js
│           │       ├── zasChatUtility.css
│           │       └── zasChatUtility.js-meta.xml
│           └── classes/
│               ├── ZASChatController.cls
│               ├── ZASChatController.cls-meta.xml
│               ├── ZASChatControllerTest.cls
│               └── ZASChatControllerTest.cls-meta.xml
├── sfdx-project.json
└── .gitignore
```
