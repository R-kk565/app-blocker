#!/bin/bash
# App Blocker - Start the web UI
# Usage: ./run.sh

cd "$(dirname "$0")"

# Install dependencies if needed
pip3 install -r requirements.txt -q 2>/dev/null || \
  pip3 install -r requirements.txt -q --break-system-packages 2>/dev/null

python3 app.py
