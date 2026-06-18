#!/usr/bin/env bash
# Start the Heritage Auction Dashboard
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
  echo "Installing dependencies…"
  pip install -r auction_dashboard/requirements.txt
fi

echo "Starting Heritage Auction Dashboard on http://localhost:8000"
python -m uvicorn auction_dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload
