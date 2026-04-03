#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════
# Aria — One-Click Setup Script
# Works on Linux, macOS, and WSL
# ══════════════════════════════════════════════════════════
set -e

BOLD='\033[1m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║     🌟 Aria — Setup Assistant         ║"
echo "  ║     Your Personal AI Assistant        ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ── Helper functions ─────────────────────────────────────

check_command() {
    command -v "$1" &> /dev/null
}

log_step() {
    echo -e "\n${BLUE}▸${NC} ${BOLD}$1${NC}"
}

log_ok() {
    echo -e "  ${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
}

log_fail() {
    echo -e "  ${RED}✗${NC} $1"
}

# ── Step 1: Check Python ────────────────────────────────

log_step "Checking Python..."
if check_command python3; then
    PY=$(python3 --version)
    log_ok "Found $PY"
else
    log_fail "Python 3.10+ is required. Install from https://python.org"
    exit 1
fi

# ── Step 2: Check Node.js ───────────────────────────────

log_step "Checking Node.js..."
if check_command node; then
    NV=$(node --version)
    log_ok "Found Node.js $NV"
else
    log_warn "Node.js not found. Installing via nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm install --lts
    log_ok "Node.js installed"
fi

# ── Step 3: Install Ollama ──────────────────────────────

log_step "Checking Ollama (local AI model server)..."
if check_command ollama; then
    log_ok "Ollama is installed"
else
    log_warn "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    log_ok "Ollama installed"
fi

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    log_warn "Starting Ollama..."
    ollama serve &> /dev/null &
    sleep 3
fi

# ── Step 4: Pull AI models ──────────────────────────────

log_step "Setting up AI models..."

# Detect available RAM to recommend model sizes
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")
TOTAL_RAM_GB=$(( TOTAL_RAM_KB / 1024 / 1024 ))

if [ "$TOTAL_RAM_GB" -ge 16 ]; then
    echo -e "  Detected ${GREEN}${TOTAL_RAM_GB}GB RAM${NC} — using full-size models"
    MODELS=("llama3.2" "phi4-mini" "nomic-embed-text")
elif [ "$TOTAL_RAM_GB" -ge 8 ]; then
    echo -e "  Detected ${YELLOW}${TOTAL_RAM_GB}GB RAM${NC} — using smaller models"
    MODELS=("phi4-mini" "nomic-embed-text")
else
    echo -e "  Detected ${RED}${TOTAL_RAM_GB}GB RAM${NC} — using minimal models"
    MODELS=("phi4-mini" "nomic-embed-text")
fi

for model in "${MODELS[@]}"; do
    echo -e "  Pulling ${BOLD}$model${NC}..."
    ollama pull "$model" 2>&1 | tail -1
    log_ok "$model ready"
done

# ── Step 5: Python backend setup ────────────────────────

log_step "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
log_ok "Backend dependencies installed"
cd ..

# ── Step 6: Install browser automation (patchright) ────

log_step "Installing stealth browser (patchright)..."
cd backend
source venv/bin/activate
# patchright is a stealth-patched Playwright fork — bypasses bot detection
python -m patchright install chromium 2>&1 | tail -3 || log_warn "patchright chromium install failed — browser agent may be detected as bot"
log_ok "Stealth browser ready"
deactivate
cd ..

# ── Step 7: Frontend setup ──────────────────────────────

log_step "Setting up frontend..."
cd frontend
npm install --silent 2>&1 | tail -3
log_ok "Frontend dependencies installed"
cd ..

# ── Step 8: Electron desktop app dependencies ──────────

log_step "Setting up Electron desktop app..."
npm install --silent 2>&1 | tail -3
log_ok "Electron dependencies installed"

# ── Step 9: Create .env if needed ───────────────────────

if [ ! -f .env ]; then
    cp .env.example .env
    # Auto-adjust for low RAM
    if [ "$TOTAL_RAM_GB" -lt 16 ]; then
        sed -i 's/MODEL_CHAT=llama3.2/MODEL_CHAT=phi4-mini/' .env 2>/dev/null || true
        sed -i 's/MODEL_REASONING=deepseek-r1/MODEL_REASONING=phi4-mini/' .env 2>/dev/null || true
    fi
    log_ok "Created .env with auto-detected settings"
fi

# ── Done ─────────────────────────────────────────────────

echo -e "\n${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅ Aria is ready!${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}To start Aria (desktop app):${NC}"
echo -e "    ${BLUE}npm run electron:dev${NC}"
echo ""
echo -e "  ${BOLD}To start Aria (web app):${NC}"
echo -e "    ${BLUE}./start.sh${NC}"
echo ""
echo -e "  ${BOLD}Or start manually:${NC}"
echo -e "    Backend:  ${BLUE}cd backend && source venv/bin/activate && uvicorn app.main:app --reload${NC}"
echo -e "    Frontend: ${BLUE}cd frontend && npm run dev${NC}"
echo ""
echo -e "  Then open ${BOLD}http://localhost:3000${NC} in your browser."
echo ""
