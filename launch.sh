#!/bin/bash
# ==============================================================
# HERMES SWARM LOOP — Get Shit Done
# ==============================================================
# Launches the full 3×3 Ralph Loop with 400-agent swarm.
# 
# Usage:
#   ./launch.sh --name "My Blockchain" --desc "Build a PoS blockchain" --model deepseek-v4-flash
#
# Options:
#   --name       Project name (required)
#   --desc       Project description (required)
#   --goal       Specific goal (optional, defaults to description)
#   --model      Model to use (default: deepseek-v4-flash)
#   --agents     Max agents (default: 400)
#   --max-cycles Max iteration cycles (default: 100)
#   --yolo       YOLO mode on/off (default: on)
#   --state      Resume from saved state file
#   --push       Push to GitHub when done
#   --github     GitHub repo name (default: hermes-swarm-loop-<project>)
# ==============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   HERMES SWARM LOOP — Get Shit Done                    ║"
echo "║   The 3×3 Ralph Loop for Hermes + DeepSeek             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─── Parse Args ──────────────────────────────────────────────

PROJECT_NAME=""
PROJECT_DESC=""
PROJECT_GOAL=""
MODEL="deepseek-v4-flash"
MAX_AGENTS=400
MAX_CYCLES=100
YOLO=true
STATE_FILE=""
PUSH_GITHUB=false
GITHUB_REPO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name) PROJECT_NAME="$2"; shift 2 ;;
        --desc) PROJECT_DESC="$2"; shift 2 ;;
        --goal) PROJECT_GOAL="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        --agents) MAX_AGENTS="$2"; shift 2 ;;
        --max-cycles) MAX_CYCLES="$2"; shift 2 ;;
        --yolo) YOLO="$2"; shift 2 ;;
        --state) STATE_FILE="$2"; shift 2 ;;
        --push) PUSH_GITHUB=true; shift ;;
        --github) GITHUB_REPO="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 --name <name> --desc <desc> [options]"
            echo ""
            echo "Required:"
            echo "  --name   Project name"
            echo "  --desc   Project description"
            echo ""
            echo "Options:"
            echo "  --goal         Specific goal (default: description)"
            echo "  --model        Model (default: deepseek-v4-flash)"
            echo "  --agents       Max agents (default: 400)"
            echo "  --max-cycles   Max iterations (default: 100)"
            echo "  --yolo         YOLO mode on/off (default: on)"
            echo "  --state        Resume from state file"
            echo "  --push         Push to GitHub when done"
            echo "  --github       GitHub repo name"
            exit 0
            ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [[ -z "$PROJECT_NAME" || -z "$PROJECT_DESC" ]]; then
    echo "❌ --name and --desc are required"
    exit 1
fi

# ─── Setup GitHub if pushing ──────────────────────────────────

if [[ "$PUSH_GITHUB" == true ]]; then
    if [[ -z "$GITHUB_REPO" ]]; then
        SAFE_NAME=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
        GITHUB_REPO="hermes-swarm-loop-${SAFE_NAME}"
    fi
    
    echo "📦 GitHub repo: $GITHUB_REPO"
    
    # Check if gh CLI is available
    if command -v gh &> /dev/null; then
        # Create repo if it doesn't exist
        gh repo view "$GITHUB_REPO" &>/dev/null || \
            gh repo create "$GITHUB_REPO" --public --description "Hermes Swarm Loop: $PROJECT_DESC" --push
        echo "✅ GitHub repo ready"
    else
        echo "⚠️ gh CLI not found — install with: gh auth login"
    fi
fi

# ─── Validate ─────────────────────────────────────────────────

if [[ ! -f "$REPO_DIR/loop.py" ]]; then
    echo "❌ loop.py not found in $REPO_DIR"
    exit 1
fi

# ─── Launch ───────────────────────────────────────────────────

GOAL_FLAG=""
if [[ -n "$PROJECT_GOAL" ]]; then
    GOAL_FLAG="--goal \"$PROJECT_GOAL\""
fi

STATE_FLAG=""
if [[ -n "$STATE_FILE" ]]; then
    STATE_FLAG="--state \"$STATE_FILE\""
fi

YOLO_FLAG=""
if [[ "$YOLO" == true ]]; then
    YOLO_FLAG="--yolo"
fi

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  LAUNCH PARAMETERS                                      ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Project:    $PROJECT_NAME"
echo "║  Description: ${PROJECT_DESC:0:60}..."
echo "║  Model:      $MODEL"
echo "║  Max Agents: $MAX_AGENTS"
echo "║  Max Cycles: $MAX_CYCLES"
echo "║  YOLO:       $YOLO"
echo "║  Push:       $PUSH_GITHUB"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Launching Ralph Loop..."
echo ""

cd "$REPO_DIR"

# Phase 1: 400-Agent Swarm
echo "═══════════════════════════════════════════════════════════"
echo "🐝 PHASE 1: 400-AGENT SWARM"
echo "═══════════════════════════════════════════════════════════"

python launchers/swarm_400.py \
    --name "$PROJECT_NAME" \
    --desc "$PROJECT_DESC" \
    $GOAL_FLAG \
    --model "$MODEL" \
    --agents $MAX_AGENTS \
    $YOLO_FLAG

echo ""
echo "✅ Phase 1 complete — 400 agents finished"
echo ""

# Phase 2: Ralph Loop Iterations
echo "═══════════════════════════════════════════════════════════"
echo "🌀 PHASE 2: RALPH LOOP — 3×3 ITERATIONS"
echo "═══════════════════════════════════════════════════════════"

python loop.py \
    --name "$PROJECT_NAME" \
    --desc "$PROJECT_DESC" \
    $GOAL_FLAG \
    --model "$MODEL" \
    --max-agents $MAX_AGENTS \
    --max-cycles $MAX_CYCLES \
    $YOLO_FLAG \
    $STATE_FLAG

echo ""
echo "✅ Ralph Loop complete"
echo ""

# Phase 3: Bug + Security + Architecture Hunt
echo "═══════════════════════════════════════════════════════════"
echo "🔍 PHASE 3: BUG & SECURITY HUNT (3×3 deep hunt)"
echo "═══════════════════════════════════════════════════════════"

python hunting/bounty_hunter.py \
    --path "$REPO_DIR" \
    --depth 3 \
    --model "$MODEL" \
    $YOLO_FLAG

echo ""
echo "✅ All phases complete"
echo ""

# ─── Push to GitHub ────────────────────────────────────────────

if [[ "$PUSH_GITHUB" == true ]]; then
    echo "═══════════════════════════════════════════════════════════"
    echo "📤 PUSHING TO GITHUB"
    echo "═══════════════════════════════════════════════════════════"
    
    cd "$REPO_DIR"
    git add -A
    git commit -m "Hermes Swarm Loop: $PROJECT_NAME — $(date '+%Y-%m-%d %H:%M')" || true
    git remote add origin "https://github.com/$GITHUB_REPO.git" 2>/dev/null || true
    git push -u origin main || git push -u origin master
    
    echo ""
    echo "✅ Pushed to https://github.com/$GITHUB_REPO"
fi

# ─── Final Report ──────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅  HERMES SWARM LOOP — COMPLETE                       ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Project: $PROJECT_NAME"
echo "║  Status: Masterpiece check complete"
echo "║  Log: $REPO_DIR/swarm_state.json"
echo "║  GitHub: https://github.com/$GITHUB_REPO"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "🐝 Get shit done. Iterate until masterpiece."
