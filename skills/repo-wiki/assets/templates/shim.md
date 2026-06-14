<!--
  This block replaces the *knowledge* that used to live in CLAUDE.md / AGENTS.md.
  Keep it ~12 lines. Knowledge belongs in repo-wiki/, not here. Only universal,
  always-relevant directives stay below.
-->

## Knowledge base

This repo's knowledge lives in `repo-wiki/`. **Read `repo-wiki/INDEX.md` first** — it's
the map + filing rules. Don't read the whole wiki; pull pages by relevance (`covers:`
frontmatter, `grep`, descriptive filenames, each page's Compiled-Truth first line).
Session start injects the pages relevant to your working set. When you settle a decision
or learn a constraint, file it per `repo-wiki/INDEX.md` (propose-only).
**If knowledge you need isn't in the wiki:** find it (read the code, ask me, or
web-search), use it, then **propose adding it to `repo-wiki/`** so the next agent doesn't
re-derive it — but only if it's durable and non-obvious. Full method: the `repo-wiki`
skill.
**Wiki comments are a feedback channel:** if the UserPromptSubmit hook injects a
`PENDING WIKI COMMENTS` block, act on each comment and resolve it. See
`repo-wiki/references/comments.md` for the full consumption protocol.

## Always-on directives

<!-- Only the few universal, safety-critical rules that must be in every context. -->
- <e.g. Use pnpm, never npm.>
- <e.g. Never commit secrets.>
- <e.g. Run `pnpm typecheck` before committing.>
