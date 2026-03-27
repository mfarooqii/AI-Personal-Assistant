#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════
# Aria — Start Script
# Launches backend + frontend in one command
# ══════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BOLD='\033[1m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}Starting Aria...${NC}\n"

# Ensure Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "  Starting Ollama..."
    ollama serve &> /dev/null &
    sleep 2
fi

# Start backend
echo -e "  ${GREEN}▸${NC} Starting backend on :8000"
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo -e "  ${GREEN}▸${NC} Starting frontend on :3000"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n${GREEN}${BOLD}Aria is running!${NC}"
echo -e "  Open ${BOLD}http://localhost:3000${NC}"
echo -e "  Press Ctrl+C to stop\n"

# Cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Stopping Aria...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

# Wait for either to exit
wait
