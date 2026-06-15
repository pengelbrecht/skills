#!/usr/bin/env bash
# sessionend-hook.sh — SessionEnd hook: nudge to mine chat before the session is gone.
#
# Installed by `kb.py init` into .claude/settings.json under "SessionEnd":
#
#   "hooks": {
#     "SessionEnd": [
#       {
#         "matcher": "",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "python3 \"$CLAUDE_PROJECT_DIR/skills/repo-wiki/scripts/kb.py\" session-end 2>/dev/null || true"
#           }
#         ]
#       }
#     ]
#   }
#
# What it does:
#   - Nudges the agent to run `kb catchup` so this session's durable knowledge is
#     mined before the chat window is no longer accessible.
#   - Propose-only: knowledge goes into repo-wiki/, watermark advances after review.
#   - Best-effort: always exits 0 so it never blocks session teardown.

python3 "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}/skills/repo-wiki/scripts/kb.py" session-end 2>/dev/null || true
