---
type: constraint           # product | architecture | constraint | decision | runbook | incident | glossary
source: canonical          # canonical (born here) | from-code (cache) | from-doc (mirror)
covers: []                 # globs of code this page claims about, e.g. [src/billing/**]; drives `kb status`
# from: []                 # synthesized only: upstream source (code paths or a doc path/URL)
verified_against:          # sha (or hash) at last confirmation == the newest Timeline entry
status: active             # active | superseded | archived
---

## Compiled Truth

<The current best understanding. Terse, claim-first. This is the cheap head that gets
injected at session start — keep it scannable, not an essay.>

## Timeline

- <YYYY-MM-DD> — <what happened / evidence / source, e.g. "captured from chat (session
  abc)"> — verified @<sha>
