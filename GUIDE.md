# Build Guide

Lock in every layer, in order. One step per component. Each step says what it is, the exact codebase, the commands, where the file goes, and how to verify. Secrets (API keys, tokens) stay on your machine and are never committed. Commands assume Windows; adjust paths for your OS.

---

## Step 0 — Buy the z.ai GLM Coding plan

The cheap frontier model the whole stack rides on. Buy this first.

- Site: [z.ai](https://z.ai) · API docs: [docs.z.ai](https://docs.z.ai)
1. Sign up at [z.ai](https://z.ai).
2. Open the coding plans page, pick **Coding Lite** (the subsidized entry tier built for agent use).
3. Dashboard, create an **API key**. Copy it, keep it private, never commit it.
4. Note the endpoints:
   - Anthropic-compatible (this stack): `https://api.z.ai/api/anthropic`
   - OpenAI-compatible: `https://api.z.ai/api/paas/v4`
   - Mainland fallback to test later: `https://open.bigmodel.cn`
- **Verify:** you have an API key string and the base URL.

## Step 1 — Install CodePilot

The desktop agent app. Multi-model, Claude Agent SDK runtime, MCP support, remote bridge.

- Codebase: [github.com/op7418/CodePilot](https://github.com/op7418/CodePilot) · docs: [codepilot.sh](https://www.codepilot.sh/docs/providers)
1. Download a release from the repo, or build from source.
2. Launch it once so it creates `~/.codepilot/codepilot.db`.
- **Verify:** the app opens and shows Settings.

## Step 2 — Connect the z.ai provider

- In CodePilot: Settings, Providers, Add provider.
  - Type: **Anthropic-compatible**
  - Base URL: `https://api.z.ai/api/anthropic`
  - API key: your z.ai key (step 0)
  - Model name: `glm-5.2`
- Advanced Options, Extra Environment Variables, paste:
  ```json
  { "API_TIMEOUT_MS": "3000000" }
  ```
- Set default model to `glm-5.2`. If the provider catalog exposes role models, set `sonnet -> GLM-5-Turbo`, `opus -> GLM-5.1`, `haiku -> GLM-4.5-Air`.
- **Verify:** send a one-line prompt, get a GLM reply.

## Step 3 — Install Logseq and make the workspace

- Site: [logseq.com](https://logseq.com)
1. Install Logseq, create a new graph, for example a folder `E:\Logseq` on a fast drive.
2. In CodePilot, set the assistant workspace path and default work dir to that folder.
3. CodePilot scaffolds `README.ai.md`, `PATH.ai.md`, `HEARTBEAT.md`. Leave them.
- **Verify:** CodePilot's file tree shows the Logseq folder.

## Step 4 — Drop in the instruction ruleset (`claude.md`)

The brain: priorities, voice, long-run behavior, web-verify discipline, tool-call hygiene, verify-before-claim, few-shot examples.

- Source: [github.com/uhneer/nonprofit-agent-rules](https://github.com/uhneer/nonprofit-agent-rules) · this repo: [files/nonprofitclaude.md](files/nonprofitclaude.md)
1. Copy `files/nonprofitclaude.md` into the workspace root as **`E:\Logseq\claude.md`**.
2. Keep one source of truth, the workspace copy is what loads, the repo is the mirror. Do not let them drift.
- **Verify:** `E:\Logseq\claude.md` exists and starts with `# Nonprofit Agent 操作准则`.

## Step 5 — Fill `user.md`

- Template: [files/user.md](files/user.md)
1. Copy it to `E:\Logseq\user.md`.
2. Fill it with real, durable facts: who you are, your stacks, standing preferences, active projects.
- **Verify:** the file has your actual details, not the template blanks.

## Step 6 — `soul.md` (optional persona)

- Template: [files/soul.md](files/soul.md)
1. Copy to `E:\Logseq\soul.md`, keep it to a line or two, or skip. `claude.md` section 1 already owns voice.

## Step 7 — Memory store (cave-speak)

- Template: [files/nonprofitmemory.md](files/nonprofitmemory.md)
1. Copy to `E:\Logseq\memory.md`, create folder `E:\Logseq\memory\`.
2. Write memory in compressed Chinese plus English technical terms, append-only, no secrets. See the file for the rule.
- **Verify:** `memory.md` exists and the `memory/` folder is present.

## Step 8 — ripgrep

Fast code search the SDK prefers over shell grep.

- Codebase: [github.com/BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep)
- Install: `winget install BurntSushi.ripgrep.MSVC` (or `scoop install ripgrep`, `choco install ripgrep`).
- **Verify:** `rg --version` prints a version.

## Step 9 — Context7 MCP (live docs)

Feeds the agent current library docs, kills confidently-wrong API calls.

- Codebase: [github.com/upstash/context7](https://github.com/upstash/context7)
- Command (npx fetches it, no pre-install): `npx -y @upstash/context7-mcp`
- **Verify:** `npx -y @upstash/context7-mcp` starts and waits on stdio (Ctrl-C to exit).

## Step 10 — Scrapling MCP (stealth fetch)

The agent's human-looking page reader. Three tiers: fast HTTP impersonation, Chromium, and Camoufox stealth.

- Codebase: [github.com/D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)
- Install:
  ```
  pip install "scrapling[fetchers]"
  scrapling install
  ```
  (`scrapling install` pulls the browser binaries, a few hundred MB.)
- MCP command: `scrapling mcp`
- **Verify:** `scrapling --version` prints, and `scrapling mcp` starts.

## Step 11 — SearXNG + mcp-searxng (private search)

The agent's own anonymous search, self-hosted, never routes through an AI vendor. SearXNG finds, Scrapling reads.

- Codebases: [github.com/searxng/searxng](https://github.com/searxng/searxng) · MCP: [github.com/ihor-sokoliuk/mcp-searxng](https://github.com/ihor-sokoliuk/mcp-searxng)
1. Write a config that enables the JSON API (the MCP needs it). Save as `<config>\settings.yml`:
   ```yaml
   use_default_settings: true
   server:
     secret_key: "<random-hex>"
     limiter: false
   search:
     formats:
       - html
       - json
   ```
2. Run the container (needs Docker Desktop running):
   ```
   docker run -d --name searxng --restart unless-stopped -p 8080:8080 \
     -v "C:/path/to/config:/etc/searxng" docker.io/searxng/searxng:latest
   ```
3. MCP command: `npx -y mcp-searxng`, env `SEARXNG_URL=http://127.0.0.1:8080`.
- **Verify:** `curl "http://127.0.0.1:8080/search?q=test&format=json"` returns JSON.

## Step 12 — GitHub MCP (optional)

Your repos: browse, issues, PRs.

- Codebase: [github.com/github/github-mcp-server](https://github.com/github/github-mcp-server)
- Command: `npx -y @modelcontextprotocol/server-github`, env `GITHUB_PERSONAL_ACCESS_TOKEN` (a fine-grained token, you add it, never commit it).

## Step 13 — Register the MCP servers in CodePilot

- Config: [files/codepilot-mcp.json](files/codepilot-mcp.json)
1. CodePilot, MCP page in the sidebar, add each server (stdio) with the command, args, and env from the JSON.
2. CodePilot stores MCP config in its own database, so the MCP page is the verified path. A project-level `.mcp.json` in the work dir is a best-effort fallback if your build of CodePilot honors the SDK's project config, verify before relying on it.
- **Verify:** the MCP page shows each server with a green/running status, and the agent can list their tools.

## Step 14 — Config tweaks and the timeout fix

In CodePilot settings:
- **1M context:** on.
- **thinking mode:** the one to tune. Extended thinking is a long silent generation burst, the main thing that trips z.ai's idle reset (it drops after about 30s of silence). If you get "stream idle timeout" stalls, turn thinking down or off for long binges. Highest-probability fix.
- **Endpoint fallback:** if stalls persist with thinking low, switch the base URL to `https://open.bigmodel.cn` and test.
- **dangerously skip permissions:** on for uninterrupted binges, off to gate each action. Security note below.

Security note: skip-permissions removes the gate. Unattended, plus a remote bridge, plus stealth web, all at once, means anyone who reaches the bridge drives a fully ungated agent on your machine. Keep at least one gate (the bridge allowlist in step 16, or a hook in [files/claude-settings.json](files/claude-settings.json)).

## Step 15 — Project formatter

- Add a formatter to your active project (Prettier, Black, gofmt, or your build's, for example Gradle's `spotlessApply`). Lets the agent self-format instead of hand-fixing style.

## Step 16 — Telegram bridge (approve from phone)

Drive the agent and approve its actions from your phone, no physical clicking.

1. Talk to **@BotFather** in Telegram, `/newbot`, copy the token.
2. CodePilot, enable the Telegram bridge, paste the token.
3. **Allowlist your own chat id.** Mandatory if skip-permissions is on, it is the only thing stopping a stranger from driving your agent.
- **Verify:** message the bot, it responds, and you can approve an action from the phone.

## Step 17 — Full remote desktop

See the whole screen and click anything, including any prompt.
- **RustDesk** (open-source, self-hostable, free, iOS and Android apps): [github.com/rustdesk/rustdesk](https://github.com/rustdesk/rustdesk) · [rustdesk.com](https://rustdesk.com). Recommended for privacy, run your own relay.
- **AnyDesk** (commercial, simplest): [anydesk.com](https://anydesk.com).
- Use the Telegram bridge for normal approve-from-phone, RustDesk/AnyDesk as the backup for full control.

## Step 18 — Optional hooks

- Config: [files/claude-settings.json](files/claude-settings.json) at `E:\Logseq\.claude\settings.json`.
- Hooks run regardless of skip-permissions, so a `PreToolUse` hook gating `git push` is your real guard. Verify CodePilot honors project `.claude` config before relying on it.

## Step 19 — Final checklist

- [ ] z.ai Coding Lite plan, API key in hand (0)
- [ ] CodePilot installed (1), z.ai provider added with `API_TIMEOUT_MS`, model glm-5.2 (2)
- [ ] Logseq graph, workspace path set (3)
- [ ] `claude.md` (4), `user.md` filled (5), `soul.md` (6), `memory.md` + `memory/` (7)
- [ ] ripgrep on PATH (8)
- [ ] Context7 (9), Scrapling installed (10), SearXNG container up + JSON verified (11), GitHub MCP optional (12)
- [ ] all MCP servers registered and green in CodePilot (13)
- [ ] 1M context on, thinking tuned, endpoint fallback noted (14)
- [ ] project formatter present (15)
- [ ] Telegram bridge enabled and allowlisted (16)
- [ ] RustDesk or AnyDesk installed (17)
- [ ] skip-permissions decision made with at least one gate kept (14, 16, 18)

Done. A lean, autonomous, remotely-drivable agent for the price of a coding plan.
