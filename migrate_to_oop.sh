#!/bin/bash
# Migration script from old to new OOP architecture

set -e

echo "=========================================="
echo "ZAS Migration to OOP Architecture"
echo "=========================================="
echo ""

# Step 1: Backup old files
echo "Step 1: Backing up old files..."
mkdir -p backup_old
cp app.py core.py chat_api.py mcp_proxy.py server_wrapper.py zas_agent.py backup_old/ 2>/dev/null || true
cp tools_*.py backup_old/ 2>/dev/null || true
echo "✓ Old files backed up to backup_old/"
echo ""

# Step 2: Install dependencies
echo "Step 2: Installing dependencies..."
if [ -f "requirements_new.txt" ]; then
    pip install -r requirements_new.txt
    echo "✓ Dependencies installed"
else
    echo "⚠ requirements_new.txt not found, using requirements.txt"
    pip install -r requirements.txt
fi
echo ""

# Step 3: Verify structure
echo "Step 3: Verifying new structure..."
python3 verify_new_architecture.py
echo ""

# Step 4: Instructions for switchover
echo "=========================================="
echo "Migration Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test the new MCP server:"
echo "   python3 app_new.py"
echo ""
echo "2. Test the new Chat API:"
echo "   python3 chat_api_new.py"
echo ""
echo "3. Test the new MCP Proxy:"
echo "   python3 mcp_proxy_new.py"
echo ""
echo "4. Once verified, replace old files:"
echo "   mv app_new.py app.py"
echo "   mv chat_api_new.py chat_api.py"
echo "   mv mcp_proxy_new.py mcp_proxy.py"
echo "   mv server_wrapper_new.py server_wrapper.py"
echo ""
echo "5. Update your deployment scripts to use new files"
echo ""
echo "Old files are backed up in: backup_old/"
echo ""
