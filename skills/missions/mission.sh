#!/usr/bin/env bash
# mission.sh — Shell utilities for the Missions skill.
# Source this file before calling any mission_* function.
#
# Usage:
#   source /path/to/mission.sh
#   mission_init "add-auth"
#   mission_list
#   mission_status ./missions/001-add-auth

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MISSIONS_DIR="./missions"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_missions_dir() {
  echo "$MISSIONS_DIR"
}

_zero_pad() {
  printf "%03d" "$1"
}

_now() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

_today() {
  date -u +"%Y-%m-%d"
}

# ---------------------------------------------------------------------------
# mission_next_id — Get the next sequential mission number
# ---------------------------------------------------------------------------

mission_next_id() {
  local dir
  dir="$(_missions_dir)"
  if [[ ! -d "$dir" ]]; then
    echo 1
    return
  fi
  local max=0
  for entry in "$dir"/*/; do
    [[ -d "$entry" ]] || continue
    local base
    base="$(basename "$entry")"
    local num="${base%%-*}"
    num="${num#"${num%%[!0]*}"}"  # strip leading zeros
    if [[ "$num" =~ ^[0-9]+$ ]] && (( num > max )); then
      max=$num
    fi
  done
  echo $(( max + 1 ))
}

# ---------------------------------------------------------------------------
# mission_init <slug> — Create a new mission directory with scaffolding
# ---------------------------------------------------------------------------

mission_init() {
  local slug="${1:?Usage: mission_init <slug>}"
  local id
  id="$(mission_next_id)"
  local padded
  padded="$(_zero_pad "$id")"
  local name="${padded}-${slug}"
  local dir
  dir="$(_missions_dir)/${name}"

  mkdir -p "$dir/knowledge"

  # Scaffold plan.yaml
  cat > "$dir/plan.yaml" <<EOF
mission: "${slug}"
id: ${id}
created: "$(_today)"
base_branch: "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
status: planning
milestones: []
EOF

  # Scaffold status.yaml
  cat > "$dir/status.yaml" <<EOF
mission: "${name}"
started: "$(_now)"
status: planning
current_milestone: null
current_feature: null
milestones: {}
features: {}
validation_rounds: {}
EOF

  # Scaffold empty files
  touch "$dir/validation-contract.md"
  touch "$dir/features.json"
  echo "[]" > "$dir/features.json"
  touch "$dir/AGENTS.md"

  echo "$dir"
}

# ---------------------------------------------------------------------------
# mission_list — List all missions with status summary
# ---------------------------------------------------------------------------

mission_list() {
  local dir
  dir="$(_missions_dir)"
  if [[ ! -d "$dir" ]]; then
    echo "No missions directory found."
    return
  fi

  printf "%-25s %-15s %-12s %s\n" "MISSION" "STATUS" "CREATED" "PROGRESS"
  printf "%-25s %-15s %-12s %s\n" "-------" "------" "-------" "--------"

  for entry in "$dir"/*/; do
    [[ -d "$entry" ]] || continue
    local name
    name="$(basename "$entry")"
    local status="unknown"
    local created="?"
    local progress=""

    if [[ -f "$entry/status.yaml" ]]; then
      # Parse status without yq dependency — simple grep approach
      status=$(grep -m1 "^status:" "$entry/status.yaml" | sed 's/^status: *//' | tr -d '"' || echo "unknown")
      local total=0 done=0
      if [[ -f "$entry/features.json" ]]; then
        total=$(grep -c '"id"' "$entry/features.json" 2>/dev/null || echo 0)
        done=$(grep -c '"completed"' "$entry/status.yaml" 2>/dev/null || echo 0)
      fi
      progress="${done}/${total} features"
    fi

    if [[ -f "$entry/plan.yaml" ]]; then
      created=$(grep -m1 "^created:" "$entry/plan.yaml" | sed 's/^created: *//' | tr -d '"' || echo "?")
    fi

    local icon="◇"
    case "$status" in
      completed) icon="✓";;
      executing|validating) icon="◆";;
      planning) icon="○";;
      blocked) icon="✗";;
    esac

    printf "%-25s %s %-13s %-12s %s\n" "$name" "$icon" "$status" "$created" "$progress"
  done
}

# ---------------------------------------------------------------------------
# mission_status <mission-dir> — Show detailed progress for a mission
# ---------------------------------------------------------------------------

mission_status() {
  local dir="${1:?Usage: mission_status <mission-dir>}"

  if [[ ! -d "$dir" ]]; then
    echo "Mission directory not found: $dir" >&2
    return 1
  fi

  echo "=== Mission: $(basename "$dir") ==="
  echo ""

  if [[ -f "$dir/status.yaml" ]]; then
    cat "$dir/status.yaml"
  else
    echo "No status.yaml found."
  fi

  echo ""
  echo "=== Features ==="
  if [[ -f "$dir/features.json" ]]; then
    cat "$dir/features.json"
  else
    echo "No features.json found."
  fi

  echo ""
  echo "=== Knowledge Files ==="
  if [[ -d "$dir/knowledge" ]]; then
    ls -1 "$dir/knowledge/" 2>/dev/null || echo "(empty)"
  fi
}

# ---------------------------------------------------------------------------
# mission_feature_done <mission-dir> <feature-id>
# Mark a feature as completed in status.yaml
# ---------------------------------------------------------------------------

mission_feature_done() {
  local dir="${1:?Usage: mission_feature_done <mission-dir> <feature-id>}"
  local fid="${2:?Usage: mission_feature_done <mission-dir> <feature-id>}"
  local status_file="$dir/status.yaml"

  if [[ ! -f "$status_file" ]]; then
    echo "status.yaml not found in $dir" >&2
    return 1
  fi

  # Append or update feature status
  if grep -q "  ${fid}:" "$status_file" 2>/dev/null; then
    sed -i "s/  ${fid}: .*/  ${fid}: completed/" "$status_file"
  else
    # Add under features: section
    echo "  ${fid}: completed" >> "$status_file"
  fi

  echo "Feature $fid marked completed."
}

# ---------------------------------------------------------------------------
# mission_milestone_done <mission-dir> <milestone-id>
# Mark a milestone as completed in status.yaml
# ---------------------------------------------------------------------------

mission_milestone_done() {
  local dir="${1:?Usage: mission_milestone_done <mission-dir> <milestone-id>}"
  local mid="${2:?Usage: mission_milestone_done <mission-dir> <milestone-id>}"
  local status_file="$dir/status.yaml"

  if [[ ! -f "$status_file" ]]; then
    echo "status.yaml not found in $dir" >&2
    return 1
  fi

  if grep -q "  ${mid}:" "$status_file" 2>/dev/null; then
    sed -i "s/  ${mid}: .*/  ${mid}: completed/" "$status_file"
  else
    echo "  ${mid}: completed" >> "$status_file"
  fi

  echo "Milestone $mid marked completed."
}

# ---------------------------------------------------------------------------
# mission_merge <mission-dir> <branch-name>
# Merge a worker's feature branch back to the base branch
# ---------------------------------------------------------------------------

mission_merge() {
  local dir="${1:?Usage: mission_merge <mission-dir> <branch-name>}"
  local branch="${2:?Usage: mission_merge <mission-dir> <branch-name>}"

  # Determine base branch from plan.yaml
  local base_branch="main"
  if [[ -f "$dir/plan.yaml" ]]; then
    base_branch=$(grep -m1 "^base_branch:" "$dir/plan.yaml" | sed 's/^base_branch: *//' | tr -d '"' || echo "main")
  fi

  echo "Merging $branch into $base_branch..."

  local current_branch
  current_branch="$(git rev-parse --abbrev-ref HEAD)"

  # If not on base branch, switch to it
  if [[ "$current_branch" != "$base_branch" ]]; then
    git checkout "$base_branch"
  fi

  # Merge with a descriptive commit message
  if git merge "$branch" --no-ff -m "mission: merge $branch"; then
    echo "Successfully merged $branch into $base_branch."
    # Clean up the feature branch
    git branch -d "$branch" 2>/dev/null || true
  else
    echo "MERGE CONFLICT merging $branch. Manual resolution required." >&2
    git merge --abort 2>/dev/null || true
    # Switch back if we changed
    if [[ "$current_branch" != "$base_branch" ]]; then
      git checkout "$current_branch"
    fi
    return 1
  fi

  # Switch back if we changed
  if [[ "$(git rev-parse --abbrev-ref HEAD)" != "$current_branch" ]] && [[ "$current_branch" != "$base_branch" ]]; then
    git checkout "$current_branch"
  fi
}

# ---------------------------------------------------------------------------
# mission_update_status <mission-dir> <key> <value>
# Update a top-level key in status.yaml
# ---------------------------------------------------------------------------

mission_update_status() {
  local dir="${1:?Usage: mission_update_status <dir> <key> <value>}"
  local key="${2:?}"
  local value="${3:?}"
  local status_file="$dir/status.yaml"

  if grep -q "^${key}:" "$status_file" 2>/dev/null; then
    sed -i "s/^${key}: .*/${key}: ${value}/" "$status_file"
  else
    echo "${key}: ${value}" >> "$status_file"
  fi
}
