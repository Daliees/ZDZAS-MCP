#!/bin/zsh
cd ~/zendesk-mcp-server || exit 1

# Virtuele omgeving activeren of aanmaken
if [ ! -d ".venv" ]; then
  echo "Virtuele omgeving niet gevonden, maak aan..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# Vereiste packages installeren
pip install --upgrade pip uv flask > /dev/null

# Start Flask-wrapper in achtergrond
echo "Start Flask-wrapper op poort 5001..."
nohup python3 server_wrapper.py > wrapper.log 2>&1 &

# Wacht even zodat Flask opstart
sleep 2

# Start ngrok-tunnel
echo "Start ngrok..."
nohup ngrok start --all --config=ngrok.yml > ngrok.log 2>&1 &

# Toon ngrok-URL
sleep 3
curl --silent http://127.0.0.1:4040/api/tunnels | grep -Eo "https://[a-zA-Z0-9.-]+\.ngrok.io"
echo "\n✅ Zendesk MCP-server + ngrok zijn gestart!"
