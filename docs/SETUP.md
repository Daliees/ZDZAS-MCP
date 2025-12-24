# Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Access to Zendesk, Jira, and Confluence instances

## Installation

1. Clone the repository:
```bash
# Replace USERNAME with the actual repository owner
git clone https://github.com/USERNAME/ZDZAS-MCP.git
cd ZDZAS-MCP
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     - `ZENDESK_SUBDOMAIN`: Your Zendesk subdomain
     - `ZENDESK_EMAIL`: Your Zendesk email
     - `ZENDESK_API_TOKEN`: Your Zendesk API token
     - `JIRA_BASE_URL`: Your Jira base URL
     - `JIRA_EMAIL`: Your Jira email
     - `JIRA_API_TOKEN`: Your Jira API token
     - `CONFLUENCE_BASE_URL`: Your Confluence base URL
     - `CONFLUENCE_EMAIL`: Your Confluence email
     - `CONFLUENCE_API_TOKEN`: Your Confluence API token

## Running the Server

Start the MCP server:
```bash
./start_mcp.sh
```

Or run directly with Python:
```bash
python app.py
```

## Verification

Test if the server is running:
```bash
curl http://localhost:8000/health
```

## Troubleshooting

- **Port already in use**: Check if another process is using port 8000
- **Authentication errors**: Verify your API credentials in `.env`
- **Module not found**: Ensure all dependencies are installed with `pip install -r requirements.txt`
