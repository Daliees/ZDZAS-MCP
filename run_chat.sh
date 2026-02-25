#!/bin/bash
set -a
cd /home/meetmaxim/Code/DS/ZDZAS-MCP
source /home/meetmaxim/Code/DS/ZDZAS-MCP/.env
set +a
export VIRTUAL_ENV=/home/meetmaxim/Code/DS/ZDZAS-MCP/.venv
export PATH=$VIRTUAL_ENV/bin:$PATH
/home/meetmaxim/Code/DS/ZDZAS-MCP/.venv/bin/python -m uvicorn chat_api:app --host 0.0.0.0 --port 9000
