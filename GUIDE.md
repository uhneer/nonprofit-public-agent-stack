# Build Guide

Follow in order. Each step is self-contained. Where a value is secret (API key, token), it stays on your machine and is never committed.

---

## Step 0 — Buy the z.ai GLM Coding plan (do this first)

GLM 5.2 is the cheap frontier model this stack runs on. The subsidized "Coding" plans are far cheaper than buying tokens.

1. Go to [z.ai](https://z.ai) and sign up.
2. Open the coding plan page and pick the **Coding Lite** plan (the entry tier). It is the subsidized option meant for agent/coding use.
3. Create an API key in the dashboard. Keep it private.
4. Note the two endpoints z.ai exposes:
   - Anthropic-compatible: `https://api.z.ai/api/anthropic` (this stack uses this one)
   - OpenAI-compatible: `https://api.z.ai/api/paas/v4`
5. Optional mainland fallback endpoint: `https://open.bigmodel.cn` (try this if you hit idle-connection resets later, see step 6).

You now have: an API key and a base URL. That is everything the harness needs.

---

## Step 1 — Install CodePilot and connect z.ai

CodePilot is a desktop agent app built on the Claude Agent SDK. It drives any Anthropic- or OpenAI-compatible model and supports MCP servers and a remote bridge.

1. Install from [github.com/op7418/CodePilot](https://github.com/op7418/CodePilot) (releases, or build from source).
2. Open Settings, Providers, Add provider:
   - Type: **Anthropic-compatible**
   - Base URL: `https://api.z.ai/api/anthropic`
   - API key: your z.ai key
   - Model name: `glm-5.2`
3. Under the provider's Advanced Options, Extra Environment Variables, add:
   ```json
   { "API_TIMEOUT_MS": "3000000" }
   ```
   (50 minutes, so long turns are not cut off.)
4. Set the default model to `glm-5.2`.

---

## Step 2 — Set up the Logseq workspace

Logseq is the agent's home: work dir, notes, and memory all live in one graph.

1. Install [Logseq](https://logseq.com) and create a new graph, for example `Logseq` on a fast drive.
2. In CodePilot, set the assistant workspace path and default work dir to that graph folder.
3. CodePilot will scaffold helper files (`README.ai.md`, `PATH.ai.md`, `HEARTBEAT.md`). Leave them, they are auto-managed.

---

## Step 3 — Drop in the instruction and identity files

These live in the workspace root and load every session.

1. Copy [files/nonprofitclaude.md](files/nonprofitclaude.md) into the workspace as **`claude.md`**. This is the brain: priorities, voice, long-run behavior, web-verify discipline, tool-call hygiene, the verify-before-claim core, and few-shot examples. The canonical source is [nonprofit-agent-rules](https://github.com/uhneer/nonprofit-agent-rules).
2. Copy [files/user.md](files/user.md) and fill it with real facts about you. This is the cheapest capability gain, the agent gets your context every session.
3. Copy [files/soul.md](files/soul.md). Keep it tiny or skip it, `claude.md` already governs voice.
4. Copy [files/nonprofitmemory.md](files/nonprofitmemory.md) into the workspace as **`memory.md`**, and create a `memory/` folder. Memory is written in compressed Chinese plus English technical terms, see the file for the rule.

Keep these three in sync if you edit them: the workspace copy is what loads, the repo is the mirror. Pick one source of truth so they do not drift.

---

## Step 4 — Add the MCP servers (lean set)

Keep it to a handful. Past about five servers, tool-selection accuracy drops. Add these via CodePilot's MCP page. Config: [files/codepilot-mcp.json](files/codepilot-mcp.json).

1. **Context7** (live library docs, the highest-value coding tool):
   `npx -y @upstash/context7-mcp`
2. **Scrapling** (stealth page fetch, the agent's human-looking reader). Install first:
   ```
   pip install "scrapling[fetchers]"
   scrapling install
   ```
   Then MCP command: `scrapling mcp`. Repo: [github.com/D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling).
3. **SearXNG + mcp-searxng** (the agent's own private, anonymous search). Self-host SearXNG (one Docker container), then add the MCP. Repo: [github.com/ihor-sokoliuk/mcp-searxng](https://github.com/ihor-sokoliuk/mcp-searxng).
   ```
   docker run -d --name searxng -p 8080:8080 searxng/searxng
   ```
   MCP: `npx -y mcp-searxng`, env `SEARXNG_URL=http://127.0.0.1:8080`.
4. **GitHub** (optional, your repos): `npx -y @modelcontextprotocol/server-github`, env `GITHUB_PERSONAL_ACCESS_TOKEN` (a fine-grained token, you add it, never commit it).

Verify each package name and flag against its current README before pasting, those drift.

The split that matters: SearXNG **finds** pages (search), Scrapling **reads** them (fetch). Together they are a private, human-looking web stack that does not route through any AI vendor and is not fingerprinted as the AI.

---

## Step 5 — Extra tools (low stress, high value)

1. **ripgrep** on PATH (`rg`). The SDK uses it for fast code search, far cheaper than shell grep. Install from [github.com/BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep).
2. **A formatter for your active project** (Prettier, Black, gofmt, or your build's formatter). Lets the agent self-format instead of hand-fixing style.

That is the whole tool set. Resist adding more, overload is real and you do not need it.

---

## Step 6 — Config tweaks and the timeout fix

In CodePilot settings:

- **1M context**: on. Lets long binges stay coherent.
- **thinking mode**: this is the one to tune. Extended thinking is a long silent generation burst, which is the main thing that trips z.ai's idle reset (it drops the connection after about 30s of silence). **If you get "stream idle timeout" stalls, turn thinking down or off for long binges.** That is the highest-probability fix.
- **API_TIMEOUT_MS**: already set to 3000000 in step 1. This governs total time, not idle gaps, so it does not by itself stop the idle drop.
- **Endpoint fallback**: if stalls persist with thinking low, switch the base URL to `https://open.bigmodel.cn` and test, it may stream more steadily than `api.z.ai`.
- **dangerously skip permissions**: optional. On, the agent never pauses for approval, which is what makes long binges work. Off, it asks before each gated action. See the security note below before turning it on.

Security note: skip-permissions removes the gate entirely. If you run the agent unattended, with a remote bridge, and stealth web access, all at once, anyone who can reach the bridge can drive a fully ungated agent on your machine. Keep at least one gate (the bridge allowlist in step 7, or a hook in `files/claude-settings.json`).

---

## Step 7 — Remote access and approve-from-phone

Two different needs, two tools.

**Approve and drive from your phone (purpose-built): the CodePilot Telegram bridge.**
1. Create a Telegram bot with @BotFather, get the token.
2. In CodePilot, enable the Telegram bridge and paste the token.
3. **Lock it to your own chat id** (allowlist), so only you can drive it. This is mandatory if skip-permissions is on.
4. Now you can send the agent tasks and approve its actions from your phone, no physical clicking.

**Full remote desktop (see the screen, click anything, including any prompt):**
- **RustDesk** (open-source, self-hostable, free, iOS and Android apps): [rustdesk.com](https://rustdesk.com). Recommended for privacy, you can run your own relay. From the phone app you can view your desktop and click Accept on any prompt.
- **AnyDesk** (commercial, simplest): [anydesk.com](https://anydesk.com). Same capability, less setup.

Use the Telegram bridge for normal approve-from-phone, and RustDesk/AnyDesk as the backup for when you need to see the whole screen.

---

## Step 8 — Implementation checklist

Run in this order. Check off as you go.

- [ ] z.ai Coding Lite plan bought, API key in hand (step 0)
- [ ] CodePilot installed, z.ai provider added, `API_TIMEOUT_MS` set, model = glm-5.2 (step 1)
- [ ] Logseq graph created, workspace path set (step 2)
- [ ] `claude.md`, `user.md` (filled), `memory.md` in the workspace (step 3)
- [ ] Context7 added (step 4)
- [ ] Scrapling installed + MCP added (step 4)
- [ ] SearXNG container up + mcp-searxng added (step 4)
- [ ] GitHub MCP added with a token (optional, step 4)
- [ ] ripgrep on PATH, project formatter present (step 5)
- [ ] 1M context on, thinking tuned, endpoint fallback noted (step 6)
- [ ] Telegram bridge enabled and allowlisted to your chat id (step 7)
- [ ] RustDesk or AnyDesk installed for full remote (step 7)
- [ ] Skip-permissions decision made, with at least one gate kept (step 6 and 7)

Done. You have a lean, autonomous, remotely-drivable agent for the price of a coding plan.
