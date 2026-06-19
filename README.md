# Nonprofit's Agent Stack

A complete, opinionated build for a long-running, low-cost, autonomous coding and research agent. A cheap frontier model (GLM 5.2 via z.ai) plus a desktop harness (Eigent, on CAMEL-AI), a Logseq workspace, a lean MCP tool set, a firm instruction ruleset, a custom 5-agent workforce, and remote access. The target is Fable-5-class behavior without the bloat or the price.

Three documents:
- **This README** is the architecture map: what every layer is and why (sections 1 to 9).
- **[GUIDE.md](GUIDE.md)** is the lock-in: a granular, numbered step for every single component, in order, starting from buying the plan. Each step names the exact codebase, command, and how to verify it.
- **[PATCHES.md](PATCHES.md)** is the giga changelog: every patch shipped to the Eigent backend to make this stack work the way the ruleset expects. Read it before debugging "weird" agent behavior, the cause is usually in there.

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
- `soul.md` = persona. One or two lines or skip it, `claude.md` owns voice.
- `memory.md` + `memory/` = the cave-speak memory store (section 5).
- Eigent does not have CodePilot's auto-memory layer keyed by workspace path. Memory in this stack is the Logseq manual store plus Eigent's agent notes (`append_note` / `shared_files`).

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

## 7. Other tools (low stress, high value)
- **ripgrep** ([BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep)): fast code search the agent prefers. Required (ruleset §4 enforces `rg --json`).
- A **formatter** on your active project (Prettier, Black, gofmt, your build's formatter).
- That is it. No sequential-thinking server, no kitchen sink. Overload is real.
- The ruleset declares `fd` and `jq` NOT installed. The agent uses `find` and Python `json` instead. Do not install them without updating the ruleset, or §4 will be stale.

## 8. Custom 5-agent workforce (replaces factory Developer/Browser/Document/Multi-Modal)
Eigent ships with a generic 4-agent workforce. This stack replaces it with a 5-role pipeline:
- **Coordinator**: parses the task, dispatches to workers in pipeline order, synthesizes the final answer. Has its own system prompt (COORDINATOR_SYS_PROMPT, not piggybacked on the Single Agent prompt).
- **Implementer**: coding, file edits, script execution.
- **Researcher**: web search, fetch, doc lookup (SearXNG + Scrapling + Context7).
- **Subject Analyst**: domain reasoning, problem decomposition, "what does the task actually ask."
- **Verifier**: runs tests, checks claims, catches fabricated output (T31 leverages this role once parent-side verification is wired).

Patches live in `prompt.py` (COORDINATOR_SYS_PROMPT + anir_operating_rules §0-§14) and `chat_service.py` (role_name="Coordinator" + worker descriptions). Full details in PATCHES.md. Fan-out sub-agents currently run on the same model the parent uses (GLM-5.2), not a smaller role model.

## 9. Stock vs custom (so you know what is yours)
- **Stock:** the Eigent app and CAMEL-AI runtime, the soul/user/memory templates, the z.ai provider entry, the factory 4-agent workforce (replaced, not deleted).
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
- [GUIDE.md](GUIDE.md) — the granular, step-per-component build.
- [PATCHES.md](PATCHES.md) — every Eigent backend patch shipped, with code diffs and verification steps.
- [healthtest.md](healthtest.md) — end-to-end health check, run it after the build is done. Eigent-native, 43 AI/LOCATE tests + 4 user-only tests.
- [files/nonprofitclaude.md](files/nonprofitclaude.md) — the ruleset (rename to `claude.md`).
- [files/nonprofitmemory.md](files/nonprofitmemory.md) — memory template and cave-speak rule.
- [files/user.md](files/user.md), [files/soul.md](files/soul.md) — identity templates.
- [files/eigent-mcp.json](files/eigent-mcp.json) — MCP config (placeholders, no secrets).
- [files/claude-settings.json](files/claude-settings.json) — optional permissions and hooks (left over from the CodePilot version; Eigent does not honor `.claude/settings.json` natively, treat as reference only).

## Warning
This stack can run unattended with a 5-agent workforce, stealth web access, and remote control, all at once. That is a real trust surface. Read steps 14 and 16 of GUIDE.md before you combine them, and read PATCHES.md before you debug weird agent behavior.
