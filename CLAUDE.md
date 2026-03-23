# Skills Repository

This is a monorepo of Claude Code skills authored by Peter Engelbrecht.

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
