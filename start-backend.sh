#!/bin/bash
cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment with Python 3.11..."
  python3.11 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt -q
uvicorn main:app --reload --port 8000
