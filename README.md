# Nonprofit's Agent Stack

A complete, opinionated setup for a long-running, low-cost, autonomous coding and research agent. It pairs a cheap frontier model (GLM 5.2 via z.ai) with a desktop agent harness (CodePilot, on the Claude Agent SDK), a Logseq workspace, a tight set of MCP tools, and a firm instruction ruleset. The goal is a Fable-5-class agent without the bloat or the price.

This repo is the buildbook. Follow [GUIDE.md](GUIDE.md) top to bottom, starting from buying the plan.

## The stack at a glance

- **Model:** GLM 5.2, z.ai Coding plan (subsidized), Anthropic-compatible endpoint.
- **Harness:** [CodePilot](https://github.com/op7418/CodePilot) (Electron, Claude Agent SDK runtime).
- **Workspace:** [Logseq](https://logseq.com) graph, used as work dir, notes, and memory.
- **Instruction ruleset:** [nonprofit-agent-rules](https://github.com/uhneer/nonprofit-agent-rules) (`files/nonprofitclaude.md`), GLM-firm, compressed, with examples.
- **MCP tools (lean):** Context7 (live docs), Scrapling (stealth fetch), SearXNG (private search), GitHub.
- **Extra tools:** ripgrep, a project formatter.
- **Memory:** cave-speak compressed Chinese plus English terms, in the Logseq graph.
- **Remote:** Telegram bridge for approve-from-phone, RustDesk or AnyDesk for full remote desktop.

## Files in this repo

- [GUIDE.md](GUIDE.md) — the full sequential setup, step 0 to step 8.
- [files/nonprofitclaude.md](files/nonprofitclaude.md) — the instruction ruleset (rename to `claude.md` in your workspace).
- [files/nonprofitmemory.md](files/nonprofitmemory.md) — the memory file template and cave-speak rules.
- [files/user.md](files/user.md), [files/soul.md](files/soul.md) — identity templates.
- [files/codepilot-mcp.json](files/codepilot-mcp.json) — the MCP server config (placeholders, no secrets).
- [files/claude-settings.json](files/claude-settings.json) — optional permissions and hooks.

## A warning before you start

This stack can run unattended with permissions skipped, stealth web access, and remote control. That is powerful and it is a real trust surface. Read the security notes in step 6 and step 7 before you turn on skip-permissions plus a remote bridge plus stealth fetching all at once.
