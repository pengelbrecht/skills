# Skills

A collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills by [@pengelbrecht](https://github.com/pengelbrecht).

## Available Skills

| Skill | Description |
|-------|-------------|
| [agent-screencast](skills/agent-screencast) | Record narrated, captioned screen recordings of web applications |
| [be-ambitious](skills/be-ambitious) | Rewrite a task into a deeper (not bigger) version, as a top professional would ask it — vendored from [DannyMac180/skills](https://github.com/DannyMac180/skills) (MIT) |
| [bro](skills/bro) | Restate the last message in plain human language, with no jargon |
| [clone-website](skills/clone-website) | Clone/replicate websites into production-ready Astro 6 code using agent-browser |
| [gws-slides](skills/gws-slides) | Create polished, professional Google Slides presentations using the gws CLI |
| [missions](skills/missions) | Break large engineering tasks into planned, validated missions executed by specialized agents |
| [repo-wiki](skills/repo-wiki) | Build and maintain a living, agent-first knowledge base for a git repo — staleness detected by git, tacit knowledge captured from chats |
| [telegram-cli](skills/telegram-cli) | Read, search, and send Telegram messages as your own account (MTProto userbot CLI) — with verbatim send-approval built in |
| [ui-polish-loop](skills/ui-polish-loop) | Iteratively improve a web app's UI with blinded judge sub-agents scoring agent-browser screenshots, in benchmark or solo mode |

## Installation

Install any skill using [skills.sh](https://skills.sh):

```bash
npx skills add pengelbrecht/skills
```

Or install a specific skill:

```bash
npx skills add pengelbrecht/skills --skill agent-screencast
```

## License

MIT
