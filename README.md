# Nonprofit's Agent Stack

A complete, opinionated build for a long-running, low-cost, autonomous coding and research agent. A cheap frontier model (GLM 5.2 via z.ai) plus a desktop harness (CodePilot, on the Claude Agent SDK), a Logseq workspace, a lean MCP tool set, a firm instruction ruleset, and remote access. The target is Fable-5-class behavior without the bloat or the price.

Two documents:
- **This README** is the architecture map: what every layer is and why (sections 1 to 8).
- **[GUIDE.md](GUIDE.md)** is the lock-in: a granular, numbered step for every single component, in order, starting from buying the plan. Each step names the exact codebase, command, and how to verify it.

---

## 1. Foundation (the spine)
- **Model:** GLM 5.2, the z.ai **Coding Lite** plan (subsidized, far cheaper than tokens). Endpoint `https://api.z.ai/api/anthropic` (Anthropic-compatible). Fallback to test if idle resets persist: `https://open.bigmodel.cn`.
- **Harness:** [CodePilot](https://github.com/op7418/CodePilot) (Electron desktop), runtime `claude-code-sdk` (the Claude Agent SDK under the hood).
- **Workspace:** a [Logseq](https://logseq.com) graph at `E:\Logseq`. The agent's work dir, notes, and memory home in one place.
- **Remote:** Telegram bridge for clawbot-style remote control and approve-from-phone, plus RustDesk or AnyDesk for full remote desktop.

## 2. Provider and runtime config (CodePilot Settings, stored in `codepilot.db`)
- `extra_env`: `API_TIMEOUT_MS=3000000`. Role models map `sonnet -> GLM-5-Turbo`, `opus -> GLM-5.1`, `haiku -> GLM-4.5-Air`. Note: fan-out subagents run on GLM-5-Turbo, not 5.2.
- `context_1m`: on.
- `thinking_mode`: on. It is the main source of the >30s silent generation that trips z.ai's idle reset, so turn it down or off for long binges if you hit stalls. Highest-probability timeout fix.
- `dangerously_skip_permissions`: on enables uninterrupted binges. Security caveat in step 14.
- Timeout switches, in order: thinking down, then the bigmodel endpoint. `API_TIMEOUT_MS` is already maxed and governs total time, not idle gaps.

## 3. Instruction documents (custom, in `E:\Logseq`, loaded by the SDK)
- `claude.md` = the [nonprofit ruleset](https://github.com/uhneer/nonprofit-agent-rules): firm GLM imperatives, compressed, with examples and tool-call hygiene. The brain.
- `user.md` = facts about you. Fill it, cheapest capability gain there is.
- `soul.md` = persona. One or two lines or skip it, `claude.md` owns voice.
- `memory.md` + `memory/` = the cave-speak memory store (section 5).
- `HEARTBEAT.md` = the heartbeat checklist (functional, for scheduled tasks and the bridge).
- `README.ai.md` / `PATH.ai.md` = CodePilot auto-generated index. Stock noise, ignore.

## 4. MCP servers (lean, add via CodePilot's MCP page)
Keep it to these. Past about five servers, tool-selection accuracy drops. The search half (SearXNG) finds pages, the fetch half (Scrapling) reads them, together a private human-looking web stack that never routes through an AI vendor.
- **Context7** ([upstash/context7](https://github.com/upstash/context7)): live library docs, kills confidently-wrong API calls. Highest value.
- **Scrapling** ([D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)): stealth fetch, the agent's human-looking reader.
- **SearXNG** ([searxng/searxng](https://github.com/searxng/searxng)) + **[mcp-searxng](https://github.com/ihor-sokoliuk/mcp-searxng)**: private, anonymous search.
- **GitHub** ([github/github-mcp-server](https://github.com/github/github-mcp-server)): optional, your repos.

Full config block: [files/codepilot-mcp.json](files/codepilot-mcp.json).

## 5. Memory system (cave-speak)
`E:\Logseq\memory.md` is the index, `memory/` holds topic files. Written in compressed Chinese plus English technical terms, append-only, no secrets. It is a writing convention (a rule in `claude.md` section 11), not a server. Example line: `修 audio desync：bakeAudio 用截断后时长。Mp4Bake.java:264。`

## 6. JSON rules and settings
- The MCP block (section 4) is the main one: [files/codepilot-mcp.json](files/codepilot-mcp.json).
- Optional `E:\Logseq\.claude\settings.json` for permissions and hooks: [files/claude-settings.json](files/claude-settings.json). Hooks run regardless of skip-permissions, so they are where real gating lives. Verify CodePilot reads project `.claude` config before relying on it.

## 7. Other tools (low stress, high value)
- **ripgrep** ([BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep)): fast code search the SDK uses, far cheaper than shell grep.
- A **formatter** on your active project (Prettier, Black, gofmt, your build's formatter).
- **Scheduled tasks / cron** for the heartbeat once the bridge is live.
- That is it. No sequential-thinking server, no kitchen sink. Overload is real.

## 8. Stock vs custom (so you know what is yours)
- **Stock:** the CodePilot app and runtime, the soul/user/memory/HEARTBEAT/README/PATH templates, the z.ai provider entry.
- **Custom (you added):** the `claude.md` ruleset, the MCP set, the cave-speak memory convention, the config tweaks (1M context, role models, timeout, skip-permissions), and the Telegram bridge.

---

## Files
- [GUIDE.md](GUIDE.md) — the granular, step-per-component build.
- [files/nonprofitclaude.md](files/nonprofitclaude.md) — the ruleset (rename to `claude.md`).
- [files/nonprofitmemory.md](files/nonprofitmemory.md) — memory template and cave-speak rule.
- [files/user.md](files/user.md), [files/soul.md](files/soul.md) — identity templates.
- [files/codepilot-mcp.json](files/codepilot-mcp.json) — MCP config (placeholders, no secrets).
- [files/claude-settings.json](files/claude-settings.json) — optional permissions and hooks.

## Warning
This stack can run unattended with permissions skipped, stealth web access, and remote control, all at once. That is a real trust surface. Read steps 14 and 16 before you combine them.
