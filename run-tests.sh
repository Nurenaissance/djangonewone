#!/usr/bin/env bash
# ============================================================================
# Pre-commit test suite — runs all 4 service test suites sequentially.
# Exits on first failure. Run from whatsapp_latest_final-mainjunk/ root.
# ============================================================================

set -e  # Exit on first failure

ROOT="$(cd "$(dirname "$0")" && pwd)"
PASS=0

echo ""
echo "============================================================"
echo "  WhatsApp CRM Platform — Pre-Commit Test Suite"
echo "============================================================"
echo ""

# ── 1. Django Tests ──
echo "[1/4] Running Django tests..."
echo "------------------------------------------------------------"
cd "$ROOT/whatsapp_latest_final_withclaude"
python -m pytest tests/ -v --tb=short -q
PASS=$((PASS + 1))
echo "PASS: Django tests passed."
echo ""

# ── 2. Node.js Tests ──
echo "[2/4] Running Node.js tests..."
echo "------------------------------------------------------------"
cd "$ROOT/whatsapp_bot_server_withclaude"
node --experimental-vm-modules node_modules/jest/bin/jest.js --forceExit --detectOpenHandles
PASS=$((PASS + 1))
echo "PASS: Node.js tests passed."
echo ""

# ── 3. FastAPI Tests ──
echo "[3/4] Running FastAPI tests..."
echo "------------------------------------------------------------"
cd "$ROOT/fastAPIWhatsapp_withclaude"
python -m pytest tests/ -v --tb=short -q
PASS=$((PASS + 1))
echo "PASS: FastAPI tests passed."
echo ""

# ── 4. Frontend Tests ──
echo "[4/4] Running Frontend tests..."
echo "------------------------------------------------------------"
cd "$ROOT/whatsappBusinessAutomation_withclaude"
npx vitest run
PASS=$((PASS + 1))
echo "PASS: Frontend tests passed."
echo ""

echo "============================================================"
echo "  ALL ${PASS}/4 SUITES PASSED — safe to push!"
echo "============================================================"
