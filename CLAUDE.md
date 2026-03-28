# Skills Repository

This is a monorepo of Claude Code skills authored by Peter Engelbrecht.

> **Note:** "Skills" in this repo are distributable skill packages (installed via [skills.sh](https://skills.sh) / `npx skills add`) — they are NOT `.claude/` or `~/.claude/` local configuration files. Each skill lives in a subdirectory here for distribution to other Claude Code instances.

## Structure

```
skills/
  <skill-name>/
    SKILL.md          # Skill definition (required by skills.sh)
    pyproject.toml    # If the skill has a Python package
    src/              # Source code
    samples/          # Example inputs
    Makefile          # Dev commands
```

Each skill lives in `skills/<skill-name>/` with a `SKILL.md` at its root. This structure is compatible with `npx skills add pengelbrecht/skills`.

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`)
2. Add any supporting files (source code, references, samples) in the same directory
3. Update the table in `README.md`

## Current skills

- **agent-screencast** — Record narrated, captioned video demos of web apps using agent-browser + edge-tts + ffmpeg
