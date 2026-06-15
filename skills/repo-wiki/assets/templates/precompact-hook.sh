#!/usr/bin/env bash
# precompact-hook.sh — PreCompact hook: inject extract-before-compaction directive.
#
# Installed by `kb.py init` into .claude/settings.json under "PreCompact":
#
#   "hooks": {
#     "PreCompact": [
#       {
#         "matcher": "",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "python3 \"$CLAUDE_PROJECT_DIR/skills/repo-wiki/scripts/kb.py\" precompact 2>/dev/null || true"
#           }
#         ]
#       }
#     ]
#   }
#
# What it does:
#   - Tells Claude to run the chat-extraction prompt (references/extraction.md, Prompt 1)
#     over the conversation window SINCE the last extraction watermark.
#   - Instructs Claude to propose durable knowledge (propose-only, never auto-apply).
#   - Instructs Claude to advance the watermark after extraction.
#   - References the watermark to avoid re-mining already-ingested turns on repeated
#     compactions within the same session.
#   - Best-effort: always exits 0 so it never blocks the compaction.

python3 "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}/skills/repo-wiki/scripts/kb.py" precompact 2>/dev/null || true
