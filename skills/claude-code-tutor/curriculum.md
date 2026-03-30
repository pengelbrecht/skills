# Claude Code Tutor — Curriculum

> Power-user patterns for Claude Code, distilled from 800+ real sessions.
> Everything here teaches general principles — adapt the examples to your
> own projects and workflows.

## Philosophy

The most effective Claude Code users treat it as an **autonomous collaborator**,
not a code autocomplete. They use it across the full spectrum — writing
migrations, creating slide decks, analyzing business data, debugging with
a browser, deploying to production. The key insight: Claude Code is most
powerful when you stop thinking of it as a coding tool and start thinking
of it as a capable colleague who happens to live in your terminal.

---

## Module Map

### Track A: Foundations

| # | Module | Description |
|---|--------|-------------|
| A1 | The Mental Model | How to think about Claude Code — it's a colleague, not a tool |
| A2 | Context Is Everything | Project vs user context, CLAUDE.md, how Claude "sees" your project |
| A3 | Prompting Like a Tech Lead | Short, directive prompts. Say what you want, not how to do it |
| A4 | The Skill Ecosystem | What skills are, how to find and install them, key skills to know |
| A5 | External Systems | CLIs, MCP servers, and how Claude reaches beyond your codebase |

### Track B: Coding Workflows

| # | Module | Description |
|---|--------|-------------|
| B1 | Project Bootstrap | From idea to repo: specs, project setup, git + GitHub |
| B2 | Feature Development | Worktrees, branches, the build-test-review loop |
| B3 | Browser-Driven Development | Using the browser for testing, debugging, and visual verification |
| B4 | Code Quality | /simplify, /review, the "fix then verify" pattern |
| B5 | Data & Pipelines | SQL, migrations, ETL, data analysis from the terminal |
| B6 | Deployment | Shipping from the terminal — CI, cloud providers, wrangler, vercel |

### Track C: Non-Coding Power Moves

| # | Module | Description |
|---|--------|-------------|
| C1 | Research & Recall | Searching past sessions as institutional memory |
| C2 | Presentations | Creating slide decks without leaving the terminal |
| C3 | Business Analysis | Sales metrics, data storytelling, ad-hoc analysis |
| C4 | Browser Automation Beyond Code | Chrome MCP and agent-browser for non-dev web tasks |
| C5 | Content Creation | Screencasts, demos, website cloning, video as documentation |

### Track D: Advanced Patterns

| # | Module | Description |
|---|--------|-------------|
| D1 | Multi-Agent Orchestration | Subagents, parallel work, worktree isolation |
| D2 | Building Your Own Skills | SKILL.md anatomy, skill-creator, distributing skills |
| D3 | Hooks & Automation | settings.json hooks, automated behaviors on events |
| D4 | Browser Sessions & Auth | Session persistence, cookie reuse, authenticated workflows |
| D5 | The Meta Game | Using Claude to improve how you use Claude |

---

## A1: The Mental Model

### Key Concept

Claude Code is not an IDE plugin that completes your lines. It's an autonomous
agent that can read files, run commands, search the web, control browsers,
create presentations, analyze data, and deploy code. Power users treat it like
a capable junior developer / chief of staff hybrid — they give it high-level
objectives and let it figure out the details.

### The Three Principles

**1. Delegate entire workflows, not individual steps.**
Instead of telling Claude each step, describe the outcome you want.

```
# Instead of this:
"Open the file src/auth/middleware.js, find the error handler,
 add a try-catch block around the token validation..."

# Do this:
"the login page shows a 500 error on bad passwords, debug it"
```

**2. Trust but verify.**
Let Claude work autonomously, then check the output. Use screenshots,
code review skills, and screencasts as verification — not line-by-line
supervision during execution.

**3. Context over instructions.**
A well-written CLAUDE.md file and SPEC.md are worth more than detailed
step-by-step prompts in every conversation. Invest in your project's
context documents and Claude will make better decisions automatically.

### What Good Prompts Look Like

These are real prompts from power-user sessions:

```
"use /clone-website to clone example.com, front page only"
"do a review of how well current implementation reflects the spec"
"use /agent-screencast to record a demo for my review before we merge"
"please init a git repo and create a private gh repo"
```

Notice: short, directive, outcome-focused. They say *what* they want, not
*how* to do it.

### Exercise

Think of a task you'd normally do manually in 10+ steps — maybe setting up
a new project, debugging a UI issue, or refactoring a module. Write a single
sentence describing the desired outcome. Then actually give that prompt to
Claude Code and see what happens. Don't intervene unless it goes off track.

### Quiz

1. What's the difference between "write a React component that displays a
   list of users with sorting and pagination" and "the users page needs
   sorting and pagination"? Why does the second one tend to produce better
   results?
2. When should you give Claude detailed step-by-step instructions instead
   of a high-level goal?

---

## A2: Context Is Everything

### Key Concept

Claude Code has two layers of persistent context that shape every interaction:

1. **Project context** — `CLAUDE.md` files in your repo (checked into git,
   shared with your team)
2. **User context** — `~/.claude/` settings, installed skills, memory files
   (personal, follows you across all projects)

Understanding this hierarchy is how you go from "Claude keeps making wrong
assumptions" to "Claude just knows how my project works."

### Project Context (CLAUDE.md)

Every project should have a `CLAUDE.md` at its root. Think of it as Claude's
onboarding doc — it reads this before doing anything. A good one includes:

- What the project is and its tech stack
- Repository structure (where things live)
- How to build, test, and deploy
- Key conventions and patterns
- What NOT to do (common pitfalls)

### User Context (~/.claude/)

Your personal Claude directory contains:

- **skills/** — Installed skill packages (your personal toolkit)
- **settings.json** — Hooks, permissions, MCP server configs
- **memory/** — Persistent memories Claude saves across conversations

### How They Layer

When you open Claude Code in a project, it reads all context in order:
1. `~/.claude/` — your personal setup (skills, settings, memory)
2. `CLAUDE.md` in the project root — project-wide instructions
3. `.claude/` directory in the project — project-specific config and skills
4. Everything combines into its working context

### Power-User Patterns

- **CLAUDE.md for every project** — even a 5-line one dramatically improves
  Claude's first guesses about your project
- **SPEC.md for product requirements** — Claude reads this to understand
  *why* you're building something, not just *what*
- **Phase documents** (e.g., `docs/phases/01-mvp.md`) — break big projects
  into chunks Claude can implement one at a time

### Exercise

Open a project you're working on. Check if it has a CLAUDE.md:

```bash
cat CLAUDE.md 2>/dev/null || echo "No CLAUDE.md found"
```

If it doesn't have one, create one now. Start with three things: what the
project is, what the tech stack is, and how to run it locally. Then start a
new conversation in that project and notice how Claude's first responses
are better-informed.

### Quiz

1. Where does Claude look for project-specific instructions?
2. What's the difference between `~/.claude/` and `.claude/` inside a project?
3. If CLAUDE.md says "use pnpm" but you tell Claude "use npm" in chat,
   which wins? Why?

---

## A3: Prompting Like a Tech Lead

### Key Concept

The best Claude Code prompts read like Slack messages from a senior engineer
to a capable team member: brief, assume shared context, focus on outcomes.
No pleasantries, no over-explanation, no step-by-step handholding.

### Five Patterns

**1. Outcome-first, one sentence**
```
"the dashboard doesn't load when there's no data, debug it"
"forgot to run /simplify on the PR. can we do that retroactively?"
"find the performance analysis we did last week (use /recall)"
```

**2. Chain skills with plain English**
```
"implement the feature, run /simplify, then use /agent-screencast to record a demo"
```
One sentence triggers three distinct tools. Claude figures out the sequencing.

**3. Ask "why" questions, not just "what"**
```
"the hero section analysis missed the background video. can you root-cause why?"
```
Don't just say "fix it." Ask Claude to explain *why* it got something wrong —
this leads to better fixes and permanent improvements.

**4. Correct immediately, then generalize**
```
"wrong directory. move it to ~/projects/skills/"
"the close icon is visible when the menu is closed"
"why are you not using agent-browser for screenshots?"
```
Direct corrections, no softening. Then ask for the improvement to be documented
so the same mistake doesn't happen again.

**5. Delegate thinking, not just doing**
```
"we need to think about how multi-tenant provisioning should work.
How would you architect the database layer? Think about this."
```
Use Claude for strategy, architecture, and product design — not just code output.

### Anti-Patterns to Avoid

- Writing paragraphs when a sentence will do
- Explaining how tools work — just tell Claude to use them
- Saying "can you...?" or "could you please...?" — just state what you want
- Repeating context that's already in CLAUDE.md
- Dictating implementation details when the outcome is what matters

### Exercise

Look at your last 5 Claude Code prompts (scroll up, or check your session
history). For each one, try to rewrite it shorter — ideally one sentence.
Then use one of your rewritten prompts in a real task right now and compare
the results.

### Quiz

1. Rewrite this prompt in one sentence: "I have a bug where the login page
   shows a 500 error when the user enters an incorrect password. Can you
   please look at the error handling in the auth middleware and figure out
   what's going wrong? The relevant files are in src/auth/."
2. When is it actually appropriate to write a longer, more detailed prompt?

---

## A4: The Skill Ecosystem

### Key Concept

Skills are Claude Code's plugin system. They're markdown files (SKILL.md) that
teach Claude how to do specific things — like recipes it can follow. Power
users have 10-20+ skills installed and create their own for repeated workflows.

### Finding Skills

```
# Use the find-skills skill to discover what's available
/find-skills browser automation
/find-skills presentation creation
/find-skills code review
```

### Installing Skills

```bash
# From any GitHub repo that hosts skills
npx skills add username/repo

# Install a specific skill
npx skills add username/repo/skill-name
```

### Recommended Starting Skills

The skill ecosystem is large and growing — use `/find-skills` to discover
what's available for your workflows. That said, these four are strong
starting recommendations:

| Skill | Install | What It Does |
|-------|---------|-------------|
| find-skills | `npx skills add anthropic/skills` | Discover and install new skills — your gateway to everything else |
| agent-browser | `npx skills add anthropic/skills` | Headless browser automation for testing, screenshots, scraping |
| recall | `npx skills add arjunkmrm/recall` | Search your past Claude Code sessions as institutional memory |
| modern-python | `npx skills add pengelbrecht/skills` | Modern Python project setup with uv, ruff, and ty |

Beyond these, build your toolkit based on what you actually do. A frontend
developer might install `frontend-design` and `tdd`. Someone doing data
work might want presentation and analysis skills. Use `/find-skills` to
explore — that's what it's there for.

### Invoking Skills

Prefix with `/`:
```
/find-skills browser automation
/recall that authentication discussion from last week
/agent-browser screenshot localhost:3000
```

### Exercise

1. Check what skills you currently have installed:
   ```bash
   ls ~/.claude/skills/
   ```
2. Try discovering a new skill: use `/find-skills` with a capability you
   wish you had (e.g., "database migration helper" or "API documentation")
3. If you find one you like, install it.

### Quiz

1. What file must every skill have at its root?
2. What's the difference between a skill and a CLAUDE.md instruction?
3. How do you invoke a skill during a conversation?

---

## A5: External Systems — CLIs and MCPs

### Key Concept

Claude Code can interact with the outside world through two mechanisms:

1. **CLI tools** — Command-line programs Claude runs via bash (gh, wrangler,
   supabase, dbt, agent-browser, etc.)
2. **MCP servers** — Model Context Protocol servers that give Claude
   structured access to external services (your Chrome browser, meeting
   transcripts, design tools, etc.)

Both extend Claude's reach beyond your local codebase.

### Common CLIs

| CLI | Purpose |
|-----|---------|
| `agent-browser` | Headless browser automation (scraping, testing, screenshots) |
| `gh` | GitHub operations (PRs, issues, repos, actions) |
| `wrangler` | Cloudflare Workers deployment and management |
| `supabase` | Database migrations, local dev environment |
| `dbt` | Data transformations and modeling |
| `uv` | Modern Python package management |
| `npx skills` | Skill installation and management |

### MCP Servers

MCPs are richer than CLIs — they provide Claude with structured tools that
have typed inputs and outputs. Examples:

- **claude-in-chrome** — Control your actual Chrome browser (navigate, click,
  fill forms, extract data from pages you're logged into)
- **fireflies** — Access meeting transcripts, search past conversations
- **stitch** — Design system and screen generation

### CLI vs MCP: When to Use Which

- **CLI**: Claude runs a shell command, gets text back. Best for tools with
  good command-line interfaces and well-defined inputs/outputs.
- **MCP**: Claude gets structured tools with schemas and context. Best for
  complex, stateful interactions (browser sessions, threaded conversations).

### A Real-World Example: Two Browser Tools

Many power users have *both* agent-browser (CLI) and Chrome MCP installed:

- **agent-browser**: Headless, fresh session every time. Great for scraping,
  automated testing, screenshots where you don't need to be logged in.
- **Chrome MCP**: Controls your actual browser with your cookies and sessions.
  Great for admin dashboards, authenticated apps, anything where you're
  already logged in.

```
# Headless, fresh session — good for public pages
"use agent-browser to screenshot the landing page"

# Your actual browser, your auth — good for dashboards
"use chrome to check the deploy status on the hosting dashboard"
```

### Exercise

1. Check what MCP servers you have configured:
   ```bash
   cat ~/.claude/settings.json | head -50
   ```
2. Try using a CLI tool through Claude. For example:
   "use gh to list my open PRs" or "what agent-browser commands are available?"

### Quiz

1. When would you use agent-browser (headless) vs Chrome MCP (your browser)?
2. What's an MCP server and how does it differ from a CLI tool?
3. Name two external systems you could connect to Claude Code that would be
   useful in your work.

---

## B1: Project Bootstrap

### Key Concept

Power users have a consistent pattern for starting new projects. They go
from idea to running code faster than most people create their first file,
because they let Claude handle the scaffolding while they focus on decisions.

### The Pattern

1. **Describe the product** — Tell Claude what you're building and why
2. **Create a spec** — Claude writes the product spec (SPEC.md), you refine together
3. **Init the repo** — `git init`, GitHub repo, initial commit
4. **Write CLAUDE.md** — Project conventions, tech stack, local dev setup
5. **Phase the work** — Break the spec into implementation phases
6. **Start building** — Pick Phase 1, tell Claude to implement it

### Example Flow

```
# Step 1: Start with the idea
"please init a git repo and create a private gh repo for a new project"

# Step 2: Think about the product
"we need to think about how the multi-tenant architecture should work.
How would you handle per-customer databases?"

# Step 3: Start building
"implement Phase 1 from the spec"
```

The second prompt — asking Claude to *think* about architecture — often
produces surprisingly thorough analysis. Don't jump straight to code.
Use Claude's reasoning to make better design decisions first.

### The Power of Phased Implementation

Big projects fail when you try to implement everything at once. Break your
spec into phases, put each in its own doc (e.g., `docs/phases/01-mvp.md`),
and implement one at a time. Claude can hold a single phase in context
much better than an entire product spec.

### Exercise

Think of a project idea — can be a toy project. Give Claude a one-paragraph
description and ask it to create a SPEC.md. Then ask it to break the spec
into 3 implementation phases. Notice how much structure you get from two
short prompts.

### Quiz

1. Why write a SPEC.md before coding, even for personal projects?
2. What goes in a CLAUDE.md that doesn't go in a SPEC.md?

---

## B2: Feature Development

### Key Concept

Effective feature development in Claude Code follows a disciplined cycle:
isolate, implement, test visually, review, then merge. The key tools are
worktrees (for isolation) and skills like /simplify and /review (for quality).

### The Workflow

1. **Isolate** — Claude creates a git worktree for the feature (separate
   directory, own branch, no interference with your main work)
2. **Implement** — Claude builds the feature
3. **Test** — Visual verification with agent-browser, plus automated tests
4. **Review** — `/simplify` for code quality, `/review` for correctness
5. **Demo** — `/agent-screencast` to record a video showing it works
6. **Merge** — Create PR with the video as evidence, merge

### Worktrees

Worktrees let you work on multiple features simultaneously. Each gets its
own copy of the repo in a separate directory, with its own branch:

```
# Claude handles worktree creation automatically
# You can also ask explicitly:
"start this feature in a worktree"
```

This means you can have Claude working on Feature A in one terminal while
you review Feature B in another.

### The Review Loop

Don't skip review. Power users treat `/simplify` and `/review` as mandatory:

```
"forgot to run /simplify and /review on the PR. do it retroactively"
```

These skills catch duplication, complexity, and bugs that are easy to miss
when you're focused on making something work.

### Exercise

If you have an active project, try this:
1. Ask Claude to implement a small feature (or a refactor) in a worktree
2. After it's done, run `/simplify`
3. Note what it catches — unused imports, duplicated logic, simpler patterns

If you don't have a project handy, create a toy one and try the worktree flow.

### Quiz

1. What's the benefit of using a worktree instead of just a new branch?
2. What's the difference between /simplify and /review?

---

## B3: Browser-Driven Development

### Key Concept

The browser is a first-class development tool, not just something you open
manually to "check if it works." Claude can drive the browser to verify its
own work, debug visual issues, and catch problems that unit tests miss.

### Patterns

**1. Debug with the browser, not just logs**
```
"I see 'Failed to fetch' on the dashboard page. Use agent-browser to
check what's happening"
```
Claude opens the page, checks the console, inspects network requests,
and often finds the problem faster than reading server logs.

**2. Visual verification after changes**
```
agent-browser open http://localhost:3000
agent-browser screenshot --full ./after-changes.png
```
The `--full` flag captures the entire page in one shot — much better than
scrolling and screenshotting multiple times.

**3. Before/after comparison**
Take a screenshot before making changes, make the changes, take another.
Compare visually. This catches CSS regressions, layout shifts, and missing
elements that tests won't find.

**4. Choosing the right browser tool**
- **agent-browser** (headless CLI): Fresh session, no auth state. Best for
  public pages, testing login flows, automated verification.
- **Chrome MCP** (your browser): Your cookies, your logged-in sessions.
  Best for admin panels, authenticated dashboards, any page where you'd
  normally need to log in first.

### Exercise

Start a dev server for any web project (or use any public website):
1. Take a full-page screenshot with agent-browser:
   ```
   "use agent-browser to take a full-page screenshot of localhost:3000"
   ```
2. If you have a project, make a small CSS change, then take another
   screenshot and compare.

### Quiz

1. Why use `--full` instead of scrolling and taking multiple screenshots?
2. When would you use Chrome MCP instead of agent-browser?

---

## B4: Code Quality

### Key Concept

Quality isn't something you add at the end — it's a loop. Power users run
quality checks after every significant change, catching issues while
context is fresh. The two key skills are `/simplify` (is the code as clean
as it could be?) and `/review` (is the code correct?).

### The Pattern

```
# After implementing a feature:
/simplify    # Looks for: duplication, unnecessary complexity,
             # dead code, simpler patterns for the same logic

/review      # Looks for: bugs, edge cases, security issues,
             # deviations from the spec or conventions
```

These are separate skills because they ask different questions.
`/simplify` is about *elegance* — could this be shorter, clearer, more
maintainable? `/review` is about *correctness* — does this actually work
in all cases?

### When to Run Them

- After implementing any feature or fix
- Before creating a PR
- Retroactively on PRs you already created (yes, this works)
- After a large refactor to make sure you didn't miss anything

### The "Fix Then Verify" Pattern

When Claude finds an issue during review:
1. Claude fixes it
2. Claude verifies the fix (runs tests, takes screenshots)
3. You review the fix

Don't just trust that the fix is right — have Claude prove it.

### Exercise

Find a piece of code you've written recently (in any project). Run
`/simplify` on it. Were you surprised by anything it found?

### Quiz

1. What's the difference between `/simplify` and `/review`?
2. Why run quality checks after every change rather than batching them
   before a release?

---

## B5: Data & Pipelines

### Key Concept

Claude Code is surprisingly effective for data work — writing SQL,
building ETL pipelines, running ad-hoc analysis, and managing database
migrations. You don't need a separate data tool for many common tasks.

### Patterns

**1. SQL and migrations**
```
"write a migration to add a user_preferences table with jsonb column"
"what's in the orders table? show me the schema and a few sample rows"
```
Claude can write migrations for Supabase, Prisma, Drizzle, raw SQL —
whatever your project uses. It reads your existing migrations to match
conventions.

**2. Ad-hoc data analysis**
```
"analyze the CSV in data/sales.csv — what are the top 10 products by
revenue, and is there a seasonal pattern?"
```
Claude can use Python (with uv for dependency management), DuckDB for
SQL-on-files, or whatever tool fits. It often writes a quick script,
runs it, and presents the results.

**3. ETL and transformations**
```
"we need to pull data from the API, transform it, and load into our
analytics database. write the pipeline"
```
For dbt users, Claude understands models, sources, and the DAG. For
custom ETL, it writes clean Python scripts with proper error handling.

### Exercise

If you have a CSV file handy (any data will do), try:
```
"analyze this CSV and tell me what's interesting about it"
```
Watch how Claude picks the right tool (Python, DuckDB, etc.) and
explores the data without you specifying how.

### Quiz

1. When would you use DuckDB vs. a database migration for data work?
2. How does Claude decide which tool to use for data analysis?

---

## B6: Deployment

### Key Concept

Claude can deploy your code, not just write it. From configuring CI to
pushing to cloud providers, the deployment step is just another task you
can delegate — as long as you verify before it touches production.

### Common Patterns

**1. Cloud provider CLIs**
```
"deploy this to Cloudflare Workers using wrangler"
"set up the Vercel project config for this Next.js app"
"create a Dockerfile for this service"
```

**2. CI/CD configuration**
```
"add a GitHub Actions workflow for test + deploy on push to main"
```

**3. Infrastructure setup**
```
"configure the wrangler.toml for staging and production environments"
```

### The Safety Pattern

Deployment is one area where you should verify before Claude acts,
especially for production:

- **Staging**: Let Claude deploy freely. That's what staging is for.
- **Production**: Review the deploy command before confirming. Claude will
  ask for confirmation on risky actions by default.
- **Destructive operations**: Database drops, force pushes, DNS changes —
  always review these manually.

### Exercise

If you have a project that deploys somewhere, ask Claude:
```
"how is this project currently deployed? what would you change to
make the deploy process better?"
```
Even if you don't deploy, Claude's analysis of the current setup is useful.

### Quiz

1. Why should Claude deploy freely to staging but require confirmation
   for production?
2. What's one deployment task you'd delegate to Claude? One you wouldn't?

---

## C1: Research & Recall

> **Prerequisite:** `/recall` is a third-party skill, not built into Claude
> Code. Install it with `npx skills add arjunkmrm/recall` before starting
> this module.

### Key Concept

`/recall` turns your entire Claude Code history into searchable institutional
memory. Every past session — the code you wrote, the decisions you made,
the analysis you ran — becomes findable. This is powerful because the best
context for current work is often in a past conversation.

### Patterns

**Find previous analysis**
```
"find that performance analysis we did last week (use /recall)"
```

**Resume previous work**
```
"we built something similar before — /recall it"
```

**Find past decisions**
```
"/recall the discussion where we decided on the auth approach"
```

**Find conversations about features**
```
"/recall that conversation about the notification system from last month"
```

### Query Syntax

```bash
# Simple keyword search
/recall authentication

# Exact phrase
/recall "error handling middleware"

# Boolean
/recall "react AND testing"

# Prefix matching
/recall deploy*

# Filter by recency
/recall "database schema" --days 7
```

### When to Use It

- **Before starting work** that might duplicate past effort
- **When you remember doing something** but can't find the file/conversation
- **When onboarding someone** to a project ("here's why we chose this approach")
- **When past context is relevant** to current work

### Exercise

Try searching your own session history right now:
```
/recall <keyword from a recent project>
```
Can you find a conversation from the past week? Try different keywords
if the first one doesn't hit.

### Quiz

1. Why is /recall better than just searching your files for past decisions?
2. Name three situations where you'd reach for /recall.

---

## C2: Presentations

### Key Concept

You can create professional presentations entirely from the terminal — no
PowerPoint, no Google Slides UI. Claude generates the content, applies
themes, handles layout, and exports. This is especially powerful for
data-driven decks where the content comes from analysis Claude just did.

### Tools

- **lucida** — YAML-to-HTML/PDF slide engine. Define content in YAML,
  get polished decks with themes.
- **gws-slides** — Google Slides via CLI. Creates slides programmatically
  through the Google Workspace API.
- **agentpreso** — Another presentation tool with chart and diagram support.

### The Pattern

```
"create a 10-slide presentation about our Q1 metrics.
Include charts for revenue trend, churn rate, and customer growth."

"make a pitch deck for [product concept]. Keep it to 12 slides."
```

Claude handles: slide structure, content writing, visual theming, chart
generation, and export.

### Why This Is Powerful

The killer use case isn't "I'm too lazy to open PowerPoint." It's that
Claude can go from *analysis* to *presentation* in one conversation.
Analyze your data, then immediately turn the findings into a deck — without
context-switching to another tool or copy-pasting numbers.

### Exercise

Create a simple 5-slide presentation about any topic you're knowledgeable
about. Try:
```
"create a 5-slide presentation about [your topic]"
```
Use /lucida or /agentpreso if you have them installed.

### Quiz

1. What's the advantage of creating presentations in Claude Code vs.
   a traditional tool?
2. When would you still use Google Slides or PowerPoint directly?

---

## C3: Business Analysis

### Key Concept

Claude Code isn't just for developers. It's remarkably effective at
business analysis — pulling data from various sources, doing calculations,
creating visualizations, and summarizing findings. You can go from raw
data to actionable insights in a single conversation.

### Patterns

**Ad-hoc metrics analysis**
```
"analyze our sales data in data/sales.csv — show me weekly trends,
top performers, and conversion rates"
```

**Connecting data sources**
```
"pull the latest data from the API, join it with the local CSV,
and show me which segments are growing"
```

**Creating dashboards**
```
"build a simple HTML dashboard showing our key metrics from this data"
```

### The Power Move: Analysis to Presentation

The strongest pattern is chaining analysis into output:

1. Ask Claude to analyze your data
2. Discuss the findings
3. Ask Claude to turn it into a presentation or report

```
"analyze this data... now turn those findings into a 5-slide deck
for the team meeting"
```

### Exercise

If you have any business data (CSV, JSON, database), try:
```
"analyze this data and tell me the three most important things I should know"
```
If you don't have data handy, try it with any public dataset.

### Quiz

1. How is doing analysis in Claude Code different from using a spreadsheet?
2. What makes the "analysis to presentation" chain powerful?

---

## C4: Browser Automation Beyond Code

### Key Concept

Browser automation isn't just for testing your code. Claude can use the
browser for all kinds of tasks — filling forms, extracting data from
websites, interacting with admin dashboards, checking deploy status, and
managing cloud services.

### Patterns

**Admin tasks via your browser**
```
"use chrome to check the deploy status on our hosting dashboard"
"go to the cloud console and check our current resource usage"
```
When you use Chrome MCP, Claude operates your actual browser with your
existing login sessions. No need to provide credentials.

**Data extraction**
```
"use agent-browser to scrape the pricing table from competitor.com"
"extract all the product names and prices from this catalog page"
```

**Form filling**
```
"fill out the configuration form on the settings page with these values: ..."
```

### The Key Insight

Any task you do in a browser, Claude can potentially do too. The question
is whether it's faster to describe the task or just do it yourself. For
repetitive tasks, one-time scraping jobs, or tasks requiring data from
multiple pages — Claude wins.

### Exercise

Think of a browser task you do regularly (checking a dashboard, filling
a form, extracting data from a page). Try describing it to Claude and
let it do it via agent-browser or Chrome MCP.

### Quiz

1. What kinds of browser tasks are good candidates for automation?
2. What's the difference between using Chrome MCP vs agent-browser for
   non-coding browser tasks?

---

## C5: Content Creation — Screencasts & Demos

### Key Concept

`/agent-screencast` creates narrated, captioned video recordings of web
applications. Power users use this not just for marketing — but as
**evidence** that features work before merging, as onboarding material,
and as async communication with stakeholders.

### The Pipeline

1. **Research pass** — visit pages, understand what's on screen
2. **Dry-run** — replay the script without recording to verify everything works
3. **Record** — generate narration audio, record browser synced to audio timing, assemble MP4

### Use Cases

- **PR evidence**: "record a demo of this feature so I can review before merge"
- **Stakeholder updates**: "record a walkthrough of the new dashboard"
- **Documentation**: screencasts as living docs that show how features work
- **Bug reports**: "record what happens when I click the submit button"

### Website Cloning

Another content-creation pattern: `/clone-website` scrapes an existing site
and rebuilds it as clean, modern code (typically Astro + Tailwind). Useful
for redesigns, learning from other sites' patterns, or rapid prototyping.

### Exercise

If you have a web project running locally, try:
```
/agent-screencast record a 30-second demo of [feature]
```
If not, try cloning a simple public website:
```
/clone-website example.com
```

### Quiz

1. Why use screencasts as part of the development workflow, not just marketing?
2. What are the three passes in the screencast pipeline?

---

## D1: Multi-Agent Orchestration

### Key Concept

Claude Code can spawn subagents — separate Claude instances that work in
parallel on different parts of a problem. This is how large tasks get done
efficiently: Claude breaks the work into independent pieces and farms them
out simultaneously.

### Three Patterns

**1. Parallel research**
Claude spawns multiple Explore agents to investigate different parts of
the codebase simultaneously. Instead of searching sequentially, it gets
answers from 3-4 areas at once.

**2. Parallel implementation**
Using worktree isolation, multiple agents can work on different files or
services without conflicting. Each agent gets its own copy of the repo.

**3. Context offloading**
When the main conversation's context gets large, Claude spawns a subagent
with just the relevant subset — keeping the main thread clean and focused.

### When Multi-Agent Triggers

You don't usually ask for it explicitly. Claude decides to use subagents when:
- A task spans multiple packages or services
- Research requires checking many files independently
- Implementation can be parallelized across files
- Context is getting too large for a single thread

You *can* ask for it:
```
"research these two things in parallel"
"implement these changes in separate worktrees"
```

### Exercise

Ask Claude to research two unrelated things about a codebase you're
working in. For example:
```
"in parallel: how does auth work in this project, and what's the test coverage like?"
```
Watch it spawn agents.

### Quiz

1. What are three scenarios where subagents help?
2. Why would Claude use worktree isolation for parallel implementation?

---

## D2: Building Your Own Skills

### Key Concept

If you do something more than twice with Claude Code, make it a skill.
Skills capture workflows as reusable instructions, saving you from
re-explaining the same process every time.

### Skill Anatomy

```
my-skill/
  SKILL.md          # The skill definition (required)
  references/       # Supporting docs, templates, guides
  scripts/          # Executable code for deterministic tasks
  samples/          # Example inputs
```

### SKILL.md Structure

```yaml
---
name: my-skill
description: >
  What the skill does and when to trigger it.
  Include specific phrases that should activate it.
---

# My Skill

Step-by-step instructions Claude follows when this skill triggers.
Include examples, templates, and edge cases.
```

The `description` field is crucial — it determines when Claude uses the skill.
Make it "pushy" — include many trigger phrases and contexts.

### The Skill Development Loop

1. Do something manually with Claude
2. Notice you're repeating the pattern across sessions
3. Use `/skill-creator` to create a skill from the pattern
4. Test the skill on real tasks
5. Iterate: when the skill gets something wrong, improve it rather than
   just fixing the output

### The Key Insight

Step 5 is what separates power users: when a skill fails, they don't just
fix the immediate problem. They figure out *why* it failed and update the
skill so it never fails that way again. This compounds over time — each
failure makes the skill better.

### Exercise

Think of a workflow you repeat often in Claude Code. Write down the steps
in plain English (3-5 steps). Could this be a skill? If yes:
```
/skill-creator create a skill for [your workflow]
```

### Quiz

1. What file must every skill have? What goes in the frontmatter?
2. Why is step 5 (iterating on failures) the most important step?

---

## D3: Hooks & Automation

### Key Concept

Hooks are shell commands that Claude Code runs automatically in response to
events — like "before every commit" or "when a session starts." They live
in `settings.json` and let you automate behaviors without remembering to
ask for them every time.

### How Hooks Work

Hooks are configured in `~/.claude/settings.json` (user-level) or
`.claude/settings.json` (project-level). They fire on specific events:

- **PreToolUse** — before Claude runs a tool
- **PostToolUse** — after Claude runs a tool
- **Stop** — when Claude finishes a response

### Example: Auto-lint on Commit

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "git commit",
        "command": "npm run lint"
      }
    ]
  }
}
```

### When to Use Hooks

- Enforcing project conventions automatically
- Running checks before risky operations
- Triggering external systems when Claude completes tasks
- Gathering context before Claude starts work

### Exercise

Look at your current settings:
```bash
cat ~/.claude/settings.json
```
Do you have any hooks? If not, think about one automated behavior that
would save you time — even something simple like "run the linter after
every file edit."

### Quiz

1. Where are hooks configured?
2. What's the difference between a PreToolUse and PostToolUse hook?

---

## D4: Browser Sessions & Auth

### Key Concept

When automating browser tasks that require authentication, you need to
think about session management. Fresh headless browsers have no cookies —
they're logged out of everything. There are several strategies for handling
this, and the right one depends on the situation.

### Three Strategies

**1. Use your own browser (Chrome MCP)**
The simplest approach: Claude controls your actual browser via Chrome
DevTools Protocol. You're already logged in, so Claude inherits your session.

```
"use chrome to check the admin dashboard — I'm already logged in"
```

Best for: one-off tasks, admin dashboards, anything where you'd normally
just click around yourself.

**2. Headless with fresh auth**
Use agent-browser and have Claude log in as part of the workflow:

```
"use agent-browser to log into staging and take a screenshot of the
dashboard. Credentials are in .env"
```

Best for: automated testing where you want to verify the login flow itself.

**3. Cookie/session reuse**
For repeated headless tasks, you can persist sessions:

```bash
# agent-browser supports saving and loading browser state
agent-browser --save-storage ./auth-state.json
agent-browser --load-storage ./auth-state.json
```

Best for: recurring automated tasks (screencasts, monitoring, scraping
behind login walls).

### Exercise

Try both approaches on any authenticated web app you use:
1. Chrome MCP: "use chrome to check [some dashboard you're logged into]"
2. agent-browser: "use agent-browser to visit [a public site] and take a screenshot"

Notice the difference: Chrome MCP sees your logged-in state, agent-browser
gets a fresh session.

### Quiz

1. Why does agent-browser start with no cookies while Chrome MCP has yours?
2. When would you choose cookie persistence over using Chrome MCP directly?

---

## D5: The Meta Game — Using Claude to Improve How You Use Claude

### Key Concept

The most advanced pattern: using Claude Code to analyze and improve your
own Claude Code usage. Study your sessions, identify patterns, build
skills from them, and create a flywheel where every session makes future
sessions more effective.

### The Flywheel

```
Better skills → faster work → more sessions → more patterns to extract → better skills
```

### Patterns

**1. Session analysis with /recall**
Search your past sessions to find workflows you repeat. These are skill
candidates:
```
/recall "I keep doing this..."
```

**2. Skill improvement, not just bug fixing**
When a skill produces wrong output, don't just fix the output. Ask
*why* the skill failed and update the instructions:
```
"the analysis missed the background video. root-cause why, and write
a suggestion for the skill developer"
```

**3. Turn expertise into teachable skills**
If you've developed a good workflow for anything — debugging, deploying,
analyzing data — it can become a skill that others install and benefit from.

**4. The feedback loop**
Claude's memory system learns your preferences over time. Correct it
when it's wrong, confirm when it's right, and it builds an increasingly
accurate model of how you work.

### Exercise

1. Run `/recall` and look at your last 10 sessions
2. What workflows appear more than once?
3. Pick one and ask yourself: could this be a skill?

If yes, try `/skill-creator` to build it. If not yet, save the idea for later.

### Quiz

1. What's the "flywheel" and why does it accelerate over time?
2. Why is "improve the skill" better than "fix the output" when something
   goes wrong?
