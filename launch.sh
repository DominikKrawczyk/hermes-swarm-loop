#!/bin/bash
# ==============================================================
# HERMES SWARM LOOP — 3×3×3×N
# ==============================================================
# Launches the full 3-loop cycle via Hermes Agent CLI.
# 
# Usage:
#   ./launch.sh --name "MyProject" --desc "Build a PoS blockchain" [options]
#
# Options:
#   --name        Project name (required)
#   --desc        Project description (required)
#   --agents      Max agents (default: 33)
#   --yolo        YOLO mode (default: on)
#   --push        Push to GitHub when done
# ==============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   HERMES SWARM LOOP — 3×3×3×N                          ║"
echo "║   Build anything with autonomous agent iteration       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─── Parse Args ──────────────────────────────────────────────

PROJECT_NAME=""
PROJECT_DESC=""
MAX_AGENTS=33
YOLO=true
PUSH_GITHUB=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name) PROJECT_NAME="$2"; shift 2 ;;
        --desc) PROJECT_DESC="$2"; shift 2 ;;
        --agents) MAX_AGENTS="$2"; shift 2 ;;
        --yolo) YOLO="$2"; shift 2 ;;
        --push) PUSH_GITHUB=true; shift ;;
        -h|--help)
            echo "Usage: $0 --name <name> --desc <desc> [options]"
            echo ""
            echo "Required:"
            echo "  --name   Project name"
            echo "  --desc   Project description"
            echo ""
            echo "Options:"
            echo "  --agents  Max agents (default: 33)"
            echo "  --yolo    YOLO mode on/off (default: on)"
            echo "  --push    Push to GitHub when done"
            exit 0
            ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [[ -z "$PROJECT_NAME" || -z "$PROJECT_DESC" ]]; then
    echo "❌ --name and --desc are required"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  LAUNCH PARAMETERS                                      ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Project:    $PROJECT_NAME"
echo "║  Description: ${PROJECT_DESC:0:60}..."
echo "║  Max Agents: $MAX_AGENTS"
echo "║  YOLO:       $YOLO"
echo "║  Push:       $PUSH_GITHUB"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

YOLO_ARG=""
if [[ "$YOLO" == true ]]; then
    YOLO_ARG=", yolo"
fi

PUSH_ARG=""
if [[ "$PUSH_GITHUB" == true ]]; then
    PUSH_ARG=", auto-github-push"
fi

echo "🚀 To run this via Hermes Agent, use:"
echo "================================================================"
echo "hermes chat -q \"Load hermes-swarm-loop skill and run a 3-loop cycle"
echo "  on $(pwd) — N=$MAX_AGENTS$YOLO_ARG$PUSH_ARG\""
echo "================================================================"
echo ""
echo "Or for dogfood (run on the framework itself):"
echo "hermes chat -q \"Load hermes-swarm-loop and run 3-loop cycle"
echo "  on $SCRIPT_DIR — N=$MAX_AGENTS$YOLO_ARG$PUSH_ARG\""
echo ""

if [[ "$PUSH_GITHUB" == true ]]; then
    echo "📦 Setting up GitHub..."
    if command -v gh &> /dev/null; then
        SAFE_NAME=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
        gh repo view "DominikKrawczyk/hermes-swarm-loop" &>/dev/null || \
            echo "Repo DominikKrawczyk/hermes-swarm-loop should exist already"
        echo "✅ Will push to github.com/DominikKrawczyk/hermes-swarm-loop"
    fi
fi

echo ""
echo "🐝 Get shit done. Iterate until masterpiece."
