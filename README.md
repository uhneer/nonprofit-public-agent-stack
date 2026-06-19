# Nonprofit's Agent Stack

A fully self-hosted, Fable-5-class autonomous agent that runs all day, every day, for the price of a streaming subscription. Frontier reasoning (GLM 5.2, 1M context, MIT-licensed open weights), a desktop harness built on the same CAMEL-AI runtime Claude Code uses under the hood, a custom 5-agent workforce that actually fans out work in parallel, a private stealth-search stack, and a Logseq workspace as the agent's home base. The whole thing self-installs from this repo in an afternoon.

The honest pitch in one sentence: a frontier open-weights model plus a patched CAMEL-AI harness plus a dense ruleset plus a 5-agent workforce plus a private web stack, all on your hardware, all from this repo. No vendor in the path. No data retention. No model downgrade on flagged queries. No ceiling on how long it runs.

Real numbers, not vibes. GLM-5.2 trades blows with Opus 4.8 and GPT-5.5 on every major long-horizon coding benchmark, and beats both on several. The z.ai **Coding Lite** plan is $18/month flat for roughly 225M tokens of real API value, about 95% subsidized. Claude Code Pro extracts maybe $200 of API value for $20. ChatGPT Plus caps you around $100 for $20. This stack pulls ~2x what Claude Code Pro does, at lower monthly cost, with MIT-licensed weights you can self-host if z.ai ever pulls them.

The reason a cheap model feels like an expensive one here is the scaffolding around it. The dense ruleset forces verify-before-claim discipline. The cave-speak memory format (compressed Chinese + load-bearing English technical terms) crams 3x the context into the same 1M window. The 5-agent workforce (Coordinator, Implementer, Researcher, Subject Analyst, Verifier) runs real parallel dispatch with non-leaking parallel stages, instead of Claude Code's single-agent loop. The MCP stack (Context7, Scrapling, SearXNG, GitHub, Supabase) is a private web surface that never routes through an AI vendor. The whole thing boots itself at login and is reachable from your phone over a Tailscale-tunneled Moonlight stream.

You give up a few things. Setup is an afternoon, not one command. Plugin ecosystem is thinner than Claude Code's. Peak subtle-reasoning intelligence, Opus 4.8 still edges GLM-5.2 by a few points. None of that is a dealbreaker; all of it is named in the comparison below.

**Name slots are blank by design.** Every place that would normally carry an operator name ships with `_____` placeholders or the generic phrase "the operator". Nothing here will make the AI call you by someone else's name. Two ways to fill them in:
- **Human path:** open `files/user.md` in a text editor before you copy it to your workspace, replace `_____` and the blank fields with your own details, save.
- **Agent path:** when you first talk to the agent after install, just tell it your name (and any other durable facts). The agent writes what you said into `user.md` itself. You do not need to edit the ruleset.

**Path convention.** Examples assume the workspace lives at `E:\Logseq` and the harness at `E:\Eigent` (the defaults from [GUIDE.md](GUIDE.md)). If you install elsewhere, substitute your paths wherever you see those literals; nothing in the code or rulesets is hardcoded to `E:\`.

**Self-installable by design.** An agent reading this repo can self-install the entire stack by following [GUIDE.md](GUIDE.md) step by step, copying the drop-in files at `files/eigent-backend/` into the backend, and prompting the operator for the handful of one-time manual steps (buying the z.ai plan, generating tokens, UI clicks).

Three documents:
- **This README** is the architecture map: what every layer is and why (sections 1 to 10).
- **[GUIDE.md](GUIDE.md)** is the lock-in: a granular, numbered step for every single component, in order, starting from buying the plan. Each step names the exact codebase, command, and how to verify it.
- **[PATCHES.md](PATCHES.md)** is the giga changelog: every patch shipped to the Eigent backend to make this stack work the way the ruleset expects. Read it before debugging "weird" agent behavior, the cause is usually in there.

---

## Why this instead of Claude Code or OpenAI Codex

A feature-by-feature comparison. ✓ is yes, ✗ is no, no half-marks. Ordered by appeal to AI fanatics first, boring compliance last.

| Capability | This stack | Claude Code | ChatGPT Codex |
|---|---|---|---|
| $18/mo flat for ~80 prompts per 5h window, 10x to 25x cheaper than metered | ✓ | ✗ | ✗ |
| Real-world API value extractable per month on the entry plan | ~$393 on $18 (225M tokens, 95% subsidized) | ~$200 on $20 Pro (prompt-capped) | ~$100 on $20 Plus (severely capped) |
| Run all day every day without going broke | ✓ | ✗ | ✗ |
| 1M context window, whole project in one shot | ✓ | ✓ | ✓ |
| Custom 5-agent workforce (Coordinator + Implementer + Researcher + Subject Analyst + Verifier) with real parallel dispatch and non-leaking stages | ✓ | ✗ | ✗ |
| Adversarial subagent fan-out codified in the ruleset (verify-before-claim, anti-fabrication, parent-side check) | ✓ | ✗ | ✗ |
| Desktop GUI with live widgets, dashboard, charts, mockups, diagrams in chat | ✓ | ✗ | ✗ |
| Gemini image generation inline in chat, with persistent media library | ✓ | ✗ | ✗ |
| Skills system, extensible and promptable | ✓ | ✓ | ✗ |
| Multi-modal: native browser, document, image agents, all wired to the workforce | ✓ | partial | ✗ |
| Headless CDP Chrome for Browser Agent (no popup windows during search) | ✓ | ✗ | ✗ |
| Register any CLI binary as an agent tool | ✓ | ✗ | ✗ |
| Native notifications and scheduled cron tasks | ✓ | ✗ | ✗ |
| Telegram bridge for phone approval, no vendor in the path | ✓ | ✗ | ✗ |
| Skip-permissions mode for uninterrupted binges | ✓ | ✓ | ✓ |
| Thinking mode MAX, inherited from the Coding Plan endpoint, no UI toggle needed | ✓ | ✗ | ✗ |
| Stream-first endpoint, first byte in ~7s on long tool calls | ✓ | ✗ | ✗ |
| MIT-licensed open-weights model, self-hostable, no vendor lock-in | ✓ | ✗ | ✗ |
| Resistant to US export controls (frontier models have been pulled from all users overnight) | ✓ | ✗ | ✗ |
| No safeguard fallback to a weaker model on flagged queries | ✓ | ✗ | ✗ |
| Structured ruleset: verify-before-claim labels, tool-call hygiene, explicit scope-and-stop, no em dashes | ✓ | ✗ | ✗ |
| Super-compressed Chinese "cave-speak" memory, fits 3x more inside the 1M window | ✓ | ✗ | ✗ |
| Durable cross-session memory via Logseq workspace (not just in-chat notes) | ✓ | ✗ | ✗ |
| MCP-first architecture, lean 5-server tool surface (Context7, Scrapling, SearXNG, GitHub, Supabase) | ✓ | partial | ✗ |
| Stealth search any site on earth without being detected as AI | ✓ | ✗ | ✗ |
| Stealth-fetch any page with real browser fingerprints (Camoufox, Chromium, HTTP impersonation) | ✓ | ✗ | ✗ |
| Private self-hosted search, zero AI-vendor telemetry on your queries | ✓ | ✗ | ✗ |
| Live library docs lookup (Context7), kills confidently-wrong API calls | ✓ | ✗ | ✗ |
| Multi-provider harness, swap brains (z.ai, bigmodel.cn, Anthropic, OpenAI) without changing tools | ✓ | ✗ | ✗ |
| Full low-latency remote desktop from phone (Sunshine + Moonlight + Tailscale), no inbound port | ✓ | ✗ | ✗ |
| Reboot persistence, zero-touch autostart at login | ✓ | ✗ | ✗ |
| End-to-end health verification, 43 AI/LOCATE tests + 4 user tests, single-agent + workforce audits | ✓ | ✗ | ✗ |
| No 30-day vendor data retention policy | ✓ | ✗ | ✗ |
| ToS-compliant by design: uses the permitted `/api/anthropic` endpoint, respects Coding plan scope | ✓ | ✓ | ✓ |
| **Tally: rows won outright** | **31** | **0** | **0** |
| **Tally: rows at parity** | **5** | **5** | **3** |

**Where Claude Code or Codex still win (honest tradeoffs, none of these are gamebreakers):**

- **Peak subtle-reasoning intelligence, by a hair.** On the Artificial Analysis Intelligence Index v4.1 (June 2026), GLM-5.2, Opus 4.8, and GPT-5.5 cluster within a few points at the top. GLM-5.2 actually beats both on several long-horizon coding evals. Any edge the closed models hold on subtle reasoning is a percentage-point gap, not a chasm. The ruleset narrows even that by forcing verify-before-claim discipline and tool-call hygiene.
- **Setup effort.** Claude Code is a one-line install. Codex is a sign-up. This stack is an afternoon of click-by-click work following [GUIDE.md](GUIDE.md). The tradeoff: every patch and config choice is yours to inspect, modify, and learn from.
- **Ecosystem size.** Claude Code has more plugins, skills, and community extensions. Codex has OpenAI's broader toolchain. You are trading ecosystem size for stack control.
- **Direct vendor support.** Break Claude Code, Anthropic has support. Break Codex, OpenAI has support. Break this stack, you read [PATCHES.md](PATCHES.md) and fix it yourself. The flip side: when you fix it, you actually understand what changed.
- **First-party cloud runners.** Codex Cloud runs agents in OpenAI's infrastructure. This stack runs on your machine, which is the point, but worth naming.
- **TUI polish.** Claude Code's terminal UI is more refined than Eigent's Electron desktop. Eigent's desktop is functional and feature-rich (live widgets, dashboard, multi-modal viewers), not minimalist.

**The cost math.** Three points, in order of weight.

1. **Real-world extraction: roughly $393/month of raw API value on an $18 plan (about 95% subsidized).** A heavy user on the Lite plan tracked 35M tokens at 62% of the weekly quota before reset, with a 33% output split and roughly 85% prompt cache hits (typical for coding-agent loops). Extrapolated to 100%, that is 56.4M tokens and about $98 of raw GLM-5.2 API value per week, or 225M tokens and roughly $393 per month against the flat $18 subscription. z.ai does not enforce a separate monthly cap on top of the rolling weekly one, so this scales linearly. The reason the math works is prompt caching: cached input is $0.26 per M tokens vs $1.40 fresh, so a coding agent that re-reads your codebase every turn pays almost nothing for input. The Pro plan at $50.40/month gives 5x the Lite quota and is where the stack becomes a workhorse for full-time use.
2. **Token list prices as a sanity check.** GLM-5.2 is $1.40 input ($0.26 cached) and $4.40 output per million tokens. Opus 4.8 is $5 and $25 (3.6x and 5.7x more). GPT-5.5 is $5 and $30. A heavy day of long-context agent work, say 1M fresh input plus 500K output, costs $3.60 on GLM-5.2 tokens, $17.50 on Opus 4.8.
3. **What you give up for that price.** GLM-5.2 is not free of tradeoffs. It can hallucinate on computational sub-tasks (T31 in the health test documents a known ceiling on SHA-256 regurgitation by sub-agents). The ruleset mitigates this with parent-side verification, but the ceiling exists. You are paying for frontier-class long-horizon reasoning at 1/6th the cost, not for the absolute peak of subtle reasoning.

---

## 1. Foundation (the spine)
- **Model:** GLM 5.2, the z.ai **Coding Lite** plan (subsidized, far cheaper than tokens). Primary endpoint `https://open.bigmodel.cn/api/anthropic` (Anthropic-compatible, streams the first byte in ~7s on long tool calls). The z.ai mirror at `https://api.z.ai/api/anthropic` is the same protocol and key but buffers the whole tool-call response, so it is the slower perceived-latency fallback, not the default. Thinking mode is inherited from the Coding Plan endpoint, no UI toggle needed.
- **Harness:** [Eigent](https://github.com/EigentAI/eigent) (Electron desktop), runtime [CAMEL-AI](https://github.com/camel-ai/camel) (ChatAgent, AgentToolkit, MCPToolkit, FunctionTool). Ships with a 4-agent workforce (Developer/Browser/Document/Multi-Modal); this stack replaces it with a custom 5-agent workforce (Coordinator, Implementer, Researcher, Subject Analyst, Verifier), see section 8.
- **Workspace:** a [Logseq](https://logseq.com) graph at `E:\Logseq`. The agent's work dir, notes, and memory home in one place.
- **Remote:** Sunshine + Moonlight + Tailscale for full low-latency remote desktop. Replaces RustDesk/AnyDesk entirely, no third-party relay, no inbound port, no accept prompt.

## 2. Provider and runtime config (Eigent Settings, stored in Eigent's settings DB)
- Provider card type: **Anthropic-compatible**. Base URL `https://open.bigmodel.cn/api/anthropic`. Model `glm-5.2`. Toggle Prefer on.
- Thinking mode is inherited from the Coding Plan endpoint. Zhipu's docs confirm interleaved thinking is the default for Coding Plan users on `/api/anthropic`, and reasoning_content is preserved across turns. No UI toggle required (Eigent has no thinking-mode switch, and none is needed).
- The "z.ai 30s idle reset" is a myth, disproved by direct test on 2026-06-17 (235s silent generation on bigmodel, 190s on the z.ai mirror, both completed without reset). If you ever see a real "stream idle timeout" error, it is client-side in Eigent or CAMEL, not at z.ai's edge, fix it there.
- Boot-time race: Eigent's embedded backend on port 5001 takes 5-30s to come up after the desktop appears. The Docker backend on 3001 is the fallback. Health test T24 retries both for 15s each before declaring failure.

## 3. Instruction documents (custom, in `E:\Logseq`, loaded via Eigent workspace binding)
- `claude.md` = the [nonprofit ruleset](https://github.com/uhneer/nonprofit-agent-rules): firm GLM imperatives, compressed, with examples and tool-call hygiene. The brain.
- `user.md` = facts about you. Fill it, cheapest capability gain there is.
- `memory.md` + `memory/` = the cave-speak memory store (section 5).
- Eigent's auto-memory is limited to in-chat agent notes (`append_note` / `shared_files`). Durable cross-session memory in this stack is the Logseq manual store governed by `claude.md` §11.

## 4. MCP servers (lean, add via Eigent's Connectors page)
Keep it to five. Past about five servers, tool-selection accuracy drops. The search half (SearXNG) finds pages, the fetch half (Scrapling) reads them, together a private human-looking web stack that never routes through an AI vendor.
- **Context7** ([upstash/context7](https://github.com/upstash/context7)): live library docs, kills confidently-wrong API calls. Highest value.
- **Scrapling** ([D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)): stealth fetch, the agent's human-looking reader.
- **SearXNG** ([searxng/searxng](https://github.com/searxng/searxng)) + **[mcp-searxng](https://github.com/ihor-sokoliuk/mcp-searxng)**: private, anonymous search.
- **GitHub** ([github/github-mcp-server](https://github.com/github/github-mcp-server)): optional, your repos. Streamable HTTP transport.
- **Supabase** ([supabase/mcp-server-supabase](https://github.com/supabase/mcp-server-supabase)): optional, your projects. Use the local stdio variant with `${SUPABASE_ACCESS_TOKEN}` env var. The remote OAuth endpoint at `https://api.supabase.com/mcp/v1` rejects personal access tokens.

Gotcha: Eigent has a silent MCP loading gap. The disk config at `~/.eigent/mcp.json` lists servers, but the per-chat `installed_mcp` field can stay empty after a fresh install. The patch in `toolkit_assembler.py` (see PATCHES.md) bridges disk config into agent runs as a fallback. Without the patch, MCP tools will not reach the agent even when `mcp.json` looks correct.

Full config block: [files/eigent-mcp.json](files/eigent-mcp.json).

## 5. Memory system (cave-speak)
`E:\Logseq\memory.md` is the index, `memory/` holds topic files. Written in compressed Chinese plus English technical terms, append-only, no secrets. It is a writing convention (a rule in `claude.md` section 11), not a server. Example line: `修 audio desync：bakeAudio 用截断后时长。Mp4Bake.java:264。`

Eigent also has an agent-shared notes layer (`append_note` / `read_note` / `shared_files`) for cross-turn and cross-agent memory. Use it for transient working state, use the Logseq store for durable facts.

## 6. JSON rules and settings
- The MCP block (section 4) is the main one: [files/eigent-mcp.json](files/eigent-mcp.json).
- The `.mcp.json` at the workspace root (`E:\Logseq\.mcp.json`) is a project-level fallback if your Eigent build honors it. The disk config at `~/.eigent/mcp.json` is what Eigent writes when you import via the Connectors UI. Both should stay in sync.

## 7. Tooling inventory (this setup utilizes)

**Search and code navigation.**
- **ripgrep** ([BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep)) — fast structured code search. Install via `winget install BurntSushi.ripgrep.MSVC`. Required: the agent defaults to `rg` over plain grep for any codebase search. `fd` and `jq` are deliberately NOT installed; the agent uses `find` and Python `json` instead. The choice is enforced by the operating rules baked into `prompt.py` (`operator_operating_rules` §3). Do not install them without updating that ruleset.

**Formatting.**
- A **project formatter** on whatever you are actively shipping: Prettier (JS/TS), Black (Python), `gofmt` (Go), Spotless (Java/Gradle), `rustfmt` (Rust). Lets the agent self-format instead of hand-fixing style.

**Containerized services.**
- **Docker Desktop** — host for the SearXNG search container (section 4). Set to autostart at login, dashboard suppressed. See GUIDE step 11 + 18.1.

**Browser.**
- **Chrome** (stable, system install at `%ProgramFiles%\Google\Chrome\Application\chrome.exe`) — driven headless over CDP on port 9224 by the autostart `.bat` in `files/`. The Browser Agent connects to this headless instance via CDP, no visible window. See GUIDE step 18b.

**Shell.**
- **cmd.exe / PowerShell** — Windows shell. The agent dispatches terminal commands through Eigent's terminal toolkit, which uses the system-wide PATH (cmd shell). `winget` is the package manager for installing the above.

No sequential-thinking server, no kitchen sink. Tool overload is real, the list above is the full surface.

## 8. Custom 5-agent workforce (replaces factory Developer/Browser/Document/Multi-Modal)
Eigent ships with a generic 4-agent workforce. This stack replaces it with a 5-role pipeline:
- **Coordinator**: parses the task, dispatches to workers in pipeline order, synthesizes the final answer. Has its own system prompt (COORDINATOR_SYS_PROMPT, not piggybacked on the Single Agent prompt).
- **Implementer**: coding, file edits, script execution.
- **Researcher**: web search, fetch, doc lookup (SearXNG + Scrapling + Context7).
- **Subject Analyst**: domain reasoning, problem decomposition, "what does the task actually ask."
- **Verifier**: runs tests, checks claims, catches fabricated output (T31 leverages this role once parent-side verification is wired).

Patches live in `prompt.py` (COORDINATOR_SYS_PROMPT + operator_operating_rules §0-§14) and `chat_service.py` (role_name="Coordinator" + worker descriptions). Full details in PATCHES.md. Fan-out sub-agents currently run on the same model the parent uses (GLM-5.2), not a smaller role model.

## 9. Stock vs custom (so you know what is yours)
- **Stock:** the Eigent app and CAMEL-AI runtime, the user/memory templates, the z.ai provider entry, the factory 4-agent workforce (replaced, not deleted).
- **Custom (you added):** the `claude.md` ruleset, the MCP set, the cave-speak memory convention, the 5-agent workforce (Coordinator + 4 workers), the prompt.py + chat_service.py + toolkit_assembler.py + environment_hands.py + listen_chat_agent.py + depth_limited_agent_toolkit.py patches (full list in PATCHES.md), the headless CDP Chrome autostart workaround, and the Sunshine + Moonlight + Tailscale remote layer.

## 10. ToS compliance
- The **z.ai Coding Lite** plan permits use from third-party harnesses. The plan is scoped to the `/api/anthropic` and `/api/paas/v4` coding endpoints. This stack only uses `/api/anthropic`. Do not use `/api/paas/v4` (OpenAI-format) with the Coding plan key, it is rejected.
- **bigmodel.cn** (the upstream of z.ai) is more permissive. The Coding plan works there with the same key. We use bigmodel.cn as the primary because it streams the first byte faster.
- **Eigent** is Apache-2.0 (see [LICENSE in their repo](https://github.com/EigentAI/eigent)). Modifying `prompt.py`, `chat_service.py`, and the other patched files is permitted by the license. Keep the original copyright headers (the patches shipped here already preserve them).
- **Supabase MCP** remote endpoint uses OAuth only and rejects personal access tokens. Use the local stdio server (`@supabase/mcp-server-supabase@latest`) with your PAT via `SUPABASE_ACCESS_TOKEN`. This is the documented path for non-OAuth clients.
- **GitHub MCP** uses your personal access token via the `Authorization: Bearer` header. Fine-grained tokens with `repo` and `read:org` scopes cover everything the agent needs.
- **SearXNG** is self-hosted on your own machine, no third-party search API is called. The agent's web access looks like a normal browser to upstream sites because Scrapling impersonates real Chrome fingerprints.
- **Sunshine + Moonlight + Tailscale**: all three are open source, run on your own hardware, and do not route through any third-party relay. Tailscale's coordination server is the only external dependency, and it can be replaced with Headscale if you want full self-hosting.

---

## Files
- [GUIDE.md](GUIDE.md) — the granular, step-per-component build. Includes a repository file map at the top so an agent can self-unpack the stack.
- [PATCHES.md](PATCHES.md) — every Eigent backend patch shipped, with code diffs and verification steps.
- [healthtest.md](healthtest.md) — end-to-end health check, run it after the build is done. Eigent-native, 43 AI/LOCATE tests + 4 user-only tests.
- [files/nonprofitclaude.md](files/nonprofitclaude.md) — the ruleset (rename to `claude.md`).
- [files/nonprofitmemory.md](files/nonprofitmemory.md) — memory template and cave-speak rule.
- [files/user.md](files/user.md) — identity template (name, role, preferences).
- [files/eigent-mcp.json](files/eigent-mcp.json) — MCP config (placeholders, no secrets).
- [files/eigent-headless-chrome.bat](files/eigent-headless-chrome.bat) — headless CDP Chrome autostart. Portable, drop into `shell:startup`. Suppresses Eigent's visible-Chrome auto-launch.

## Warning
This stack can run unattended with a 5-agent workforce, stealth web access, and remote control, all at once. That is a real trust surface. Read steps 14 and 16 of GUIDE.md before you combine them, and read PATCHES.md before you debug weird agent behavior.
