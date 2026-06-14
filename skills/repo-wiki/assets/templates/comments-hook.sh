#!/usr/bin/env bash
# comments-hook.sh — UserPromptSubmit hook: inject pending wiki comments as context.
#
# Wire this into .claude/settings.json under "UserPromptSubmit":
#
#   "hooks": {
#     "UserPromptSubmit": [
#       {
#         "matcher": "",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/comments-hook.sh\" 2>/dev/null || true"
#           }
#         ]
#       }
#     ]
#   }
#
# What it does:
#   - Runs `kb.py comments list` (open comments only, human-readable format).
#   - If there are open comments, prints them wrapped in a clearly-labelled context
#     block so Claude sees them at the top of the next turn.
#   - Prints nothing when the comments file is absent or all comments are resolved.
#   - Best-effort: always exits 0 so it never blocks a prompt.
#
# Install (done by `kb.py init` in a later tick — for now, copy manually):
#   mkdir -p .claude/hooks
#   cp skills/repo-wiki/assets/templates/comments-hook.sh .claude/hooks/comments-hook.sh
#   chmod +x .claude/hooks/comments-hook.sh
#   # then merge the JSON snippet above into .claude/settings.json

KB="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}/skills/repo-wiki/scripts/kb.py"

# Collect open comments (human-readable); suppress all errors.
PENDING="$(python3 "$KB" comments list 2>/dev/null)" || true

# Nothing to show — exit silently.
if [ -z "$PENDING" ] || [ "$PENDING" = "No open comments." ]; then
    exit 0
fi

printf '=== PENDING WIKI COMMENTS (feedback from the viewer — please act on these) ===\n'
printf '%s\n' "$PENDING"
printf '=== end wiki comments — resolve each with: kb.py comments resolve <id> --note "<what you did>" ===\n'
