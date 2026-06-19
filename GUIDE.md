# Build Guide

Lock in every layer, in order. One step per component. Each step says what it is, the exact codebase, the commands, where the file goes, and how to verify. Secrets (API keys, tokens) stay on your machine and are never committed. Commands assume Windows; adjust paths for your OS.

This is the **Eigent** build. If you are migrating from CodePilot, every step below is the new path; the only old-config artifact worth keeping is your z.ai API key.

---

## Step 0 — Buy the z.ai GLM Coding plan

The cheap frontier model the whole stack rides on. Buy this first.

- Site: [z.ai](https://z.ai) · API docs: [docs.z.ai](https://docs.z.ai)
1. Sign up at [z.ai](https://z.ai).
2. Open the coding plans page, pick **Coding Lite** (the subsidized entry tier built for agent use).
3. Dashboard, create an **API key**. Copy it, keep it private, never commit it.
4. Note the endpoints (your Coding plan key works on both Anthropic-format endpoints, tested):
   - **Primary (this stack):** `https://open.bigmodel.cn/api/anthropic` — streams the first byte in ~7s during long tool-call generation. Use this one.
   - International mirror: `https://api.z.ai/api/anthropic` — same protocol, same key, but buffers the whole tool-call response server-side (first byte only after the model finishes generating, 190s+ on a big call). Slower perceived latency, no other difference.
   - OpenAI-format (do not use with this stack): `https://api.z.ai/api/paas/v4` — Coding plan keys are scoped to the coding endpoints and rejected here.
- **Verify:** you have an API key string and the base URL.

## Step 1 — Install Eigent

The desktop agent app. Electron UI plus Python backend, CAMEL-AI runtime, MCP support, multi-agent workforce, skills.

- Codebase: [github.com/EigentAI/eigent](https://github.com/EigentAI/eigent)
1. Download a release installer from the repo, or clone and build from source.
2. Launch it once. On first launch it creates `~/.eigent/` (config, MCP, venvs) and binds a workspace folder.
3. Eigent ships two backends: an **embedded** backend on port 5001 (starts with the desktop app) and a **Docker** backend on port 3001 (optional, `docker compose up eigent_api` from the repo). Either can serve agent traffic.
- **Verify:** the app opens, the tray icon shows, and after 30-60s `curl http://127.0.0.1:5001/health` returns 200 (or 3001 if you started the Docker backend).

## Step 2 — Connect the z.ai provider

- In Eigent: Settings, Models, Anthropic card.
  - API Host: `https://open.bigmodel.cn/api/anthropic`
  - API Key: your z.ai key (step 0)
  - Model Type: `glm-5.2`
  - Prefer: **on** (this card should win over any other provider card)
- Thinking mode is inherited from the Coding Plan endpoint. No UI toggle to set. Zhipu's docs confirm interleaved thinking is the default for Coding Plan users on `/api/anthropic`.
- **Verify:** send a one-line prompt in any chat, get a GLM reply. Ask "what model are you" and the answer should name GLM-5.2.

## Step 3 — Install Logseq and make the workspace

- Site: [logseq.com](https://logseq.com)
1. Install Logseq, create a new graph, for example a folder `E:\Logseq` on a fast drive.
2. In Eigent: Create space, **Use local folder**, pick `E:\Logseq`. This binds the folder as the agent's workspace and unlocks file read/write inside it (and inside `E:\` generally, after the environment_hands.py patch in step 13b).
- **Verify:** Eigent's file browser shows the Logseq folder contents (claude.md will appear after step 4).

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

> **Eigent agent notes (separate from Logseq memory)**
> Eigent has its own agent-shared memory layer: `append_note`, `read_note`, and a `shared_files` note. Use it for transient working state within a chat or across chats (for example `- /tmp/eigent-healthtest-2026-06-18: test entry`). Use `E:\Logseq\memory.md` for durable facts you want to survive an Eigent reinstall. Health test T30 exercises the notes path.
>
> Eigent does not have CodePilot's auto-memory layer keyed by workspace path. There is no per-conversation memory toggle to worry about, the ruleset section 11 (cave-speak) is the only memory rule that governs writes.

## Step 8 — ripgrep

Fast code search the agent prefers over plain grep. Required, not optional, the ruleset §4 enforces `rg --json` structured output.

- Codebase: [github.com/BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep)
- Install: `winget install BurntSushi.ripgrep.MSVC` (or `scoop install ripgrep`, `choco install ripgrep`).
- If `rg --version` works but `where rg` cannot find it, the winget Links directory (`C:\Users\<you>\AppData\Local\Microsoft\WinGet\Links`) is not on PATH. Add it.
- **Verify:** `rg --version` prints a version, `where rg` resolves to a real `.exe` path.

## Step 9 — Context7 MCP (live docs)

Feeds the agent current library docs, kills confidently-wrong API calls.

- Codebase: [github.com/upstash/context7](https://github.com/upstash/context7)
- Command (npx fetches it, no pre-install): `npx -y @upstash/context7-mcp`
- **Verify:** `npx -y @upstash/context7-mcp` starts and waits on stdio (Ctrl-C to exit).

## Step 10 — Scrapling MCP (stealth fetch)

The agent's human-looking page reader. Three tiers: fast HTTP impersonation, Chromium, and Camoufox stealth.

- Codebase: [github.com/D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)
- Install (five lines, each plugs a specific failure mode, all verified on v0.4.9):
  ```
  pip install "scrapling[fetchers]"
  scrapling install
  pip install scrapling[mcp]
  pip install markdownify
  playwright install chromium
  ```
  - `scrapling[fetchers]` is the main package with HTTP impersonation.
  - `scrapling install` pulls Camoufox browser binaries (a few hundred MB). It does **not** install Chromium for the Playwright fetcher path.
  - `scrapling[mcp]` installs the `mcp` module the MCP entry point imports. Without it `scrapling mcp` crashes with `ModuleNotFoundError: No module named 'mcp'` even though `scrapling --version` works fine.
  - `markdownify` is what the `get` tool's HTML-to-Markdown converter imports. Without it, `mcp__scrapling__get` raises `No module named 'markdownify'` on every call (the `bulk_get` path works without it, which masks the bug).
  - `playwright install chromium` installs the Chromium binary the `fetch` tool launches. Without it, `mcp__scrapling__fetch` raises `BrowserType.launch_persistent_context: Executable doesn't exist at ...ms-playwright/chromium-.../chrome.exe`. `scrapling install` does not pull this, it pulls Camoufox only.
- MCP command: `scrapling mcp`
- **Verify:** run `scrapling mcp` and confirm it starts an MCP server (waits on stdio). Then run a real `mcp__scrapling__get` call against any page and confirm it returns markdown, not a `markdownify` import error. `scrapling --version` alone is not enough, it does not load any of the `mcp`, `markdownify`, or Chromium dependencies.

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
2. Run the container. **Pick a port that is not 8080.** 8080 is the default for Open WebUI, Jenkins, Tomcat, and a pile of other dev tools, and SearXNG silently returns HTML with no error when something else is on the port (the MCP then fails with `Invalid JSON format`). Use 8888 unless you know 8080 is free:
   ```
   docker run -d --name searxng --restart unless-stopped -p 8888:8080 \
     -v "C:/path/to/config:/etc/searxng" docker.io/searxng/searxng:latest
   ```
3. MCP command: `npx -y mcp-searxng`, env `SEARXNG_URL=http://127.0.0.1:8888` (or whatever host port you mapped in the previous step).
- **Verify:** `curl "http://127.0.0.1:8888/search?q=test&format=json"` returns JSON, not HTML. If you get HTML, the port is occupied by something else and SearXNG never started, repeat step 2 on a different port.

## Step 12 — GitHub MCP (optional)

Your repos: browse, issues, PRs.

- Codebase: [github.com/github/github-mcp-server](https://github.com/github/github-mcp-server)
- Transport: streamable_http. URL `https://api.githubcopilot.com/mcp/`. Header `Authorization: Bearer <your-fine-grained-PAT>`. Never commit the token.

## Step 12b — Supabase MCP (optional, local stdio)

Your Supabase projects: query, manage, inspect.

- Codebase: [github.com/supabase/mcp-server-supabase](https://github.com/supabase/mcp-server-supabase)
- **Important:** do NOT use the remote endpoint `https://api.supabase.com/mcp/v1`. That endpoint is OAuth-only and rejects personal access tokens with a silent `Session terminated` error. Use the local stdio server.
- Command: `npx -y @supabase/mcp-server-supabase@latest`, env `SUPABASE_ACCESS_TOKEN=<your-PAT>`.
- **Verify:** list your projects via the MCP. A successful "no projects found" response also confirms auth works.

## Step 13 — Register the MCP servers in Eigent

- Config: [files/eigent-mcp.json](files/eigent-mcp.json)
1. Eigent, Connectors / MCP page in the sidebar, **Add → Local JSON**, paste the `mcpServers` block from `files/eigent-mcp.json`. Or add each server individually (stdio) with command, args, env.
2. Eigent writes the imported config to `~/.eigent/mcp.json`. The file is the on-disk source of truth.
3. **Gotcha:** there is a silent MCP loading gap. Eigent's per-chat `installed_mcp` field can stay empty after import, and the agent runs without any MCP tools. The fix is a patch in `toolkit_assembler.py` (see PATCHES.md) that bridges disk config into agent runs as a fallback when `installed_mcp` is empty. Without the patch, MCP tools will not reach the agent even when `mcp.json` looks correct. The health test T00 detects this directly.
4. Without the patch: after every import, start a fresh chat, and verify the MCP page shows each server with a green/running status AND the agent can list MCP tools in the chat. Toggling a server off and on in the Connectors panel is the manual kick if a server is stuck on "not installed."
- **Verify:** the Connectors page shows each server green, AND in a fresh chat the agent can list its MCP tools (run health test T00).

## Step 13b — Apply the Eigent backend patches

This is the part that turns a stock Eigent install into the 5-agent workforce with the ruleset-aware prompt. Every patch is documented in [PATCHES.md](PATCHES.md) with file path, line numbers, and verification. Read it before applying anything, and read it again before debugging weird agent behavior.

The short version of what each patch does:
- `prompt.py`: adds the `<anir_operating_rules>` block (§0-§14) to SINGLE_AGENT_SYS_PROMPT, plus a dedicated `COORDINATOR_SYS_PROMPT` constant with pipeline_order + dispatch_contract.
- `chat_service.py`: wires Coordinator with `role_name="Coordinator"`, renames the 4 workers to Implementer/Researcher/Subject Analyst/Verifier in `add_single_agent_worker` descriptions so Coordinator routes correctly.
- `toolkit_assembler.py`: bridges disk MCP config into agent runs as fallback when `installed_mcp` is empty. Also schema-aware sanitizer for GLM null/empty-string emissions in MCP kwargs. Also env var expansion for `${SUPABASE_ACCESS_TOKEN}` and friends.
- `environment_hands.py`: adds `E:\` to the agent's allowed-path list (stock only allows user dirs).
- `listen_chat_agent.py`: filters `message_*` kwargs that GLM hallucinates into tool calls, and gracefully handles hallucinated tool names (returns "tool not in surface" error instead of crashing the whole turn).
- `depth_limited_agent_toolkit.py`: adds 4 anti-fabrication rules to the sub-agent system message (forces tool calls for verifiable operations instead of letting the model compose plausible-looking strings).
- `browser.py`: restores after the `_cdp_pool_manager` import break (stock bug).

Apply order matters. Re-apply from the patched `.bak` files if the stock version is in place, or restore from `.bak` if you need to start over.

- **Verify:** run the Layer 3 tests in [healthtest.md](healthtest.md) (T13, T13b, T13c) to confirm each patch is live.

## Step 14 — Config tweaks and the timeout fix

In Eigent settings:
- **Base URL:** use `https://open.bigmodel.cn/api/anthropic` (step 2). It is not a "fallback," it is the better default. bigmodel streams the first byte in ~7s on a long tool call, api.z.ai buffers the whole call and only then sends anything.
- **Thinking mode:** inherited from the Coding Plan endpoint, no UI toggle. The "30s idle reset" is not real on the Anthropic-format endpoints (direct test, 2026-06-17: a 235s silent tool-call generation on `open.bigmodel.cn/api/anthropic` and a 190s one on `api.z.ai/api/anthropic` both completed without any reset). Extended thinking streams as `thinking` deltas immediately on bigmodel, so it never sits silent in the first place.
- **The actual timeout layer (if you ever see "stream idle timeout"):** it is client-side, in Eigent or CAMEL, not at z.ai's edge. Fix it there, raise the stream-idle limit in CAMEL's Anthropic client. Do not add a proxy and do not disable thinking.
- **Do not bother with `tool_stream=true` or a local proxy.** It is a paas/v4 (OpenAI-format) flag only. On `/api/anthropic` it is silently ignored, verified by direct test (233s silent generation with the flag set, no incremental streaming).
- **Permissions:** Eigent has no CodePilot-style skip-permissions toggle. The equivalent is per-tool gating via the agent's own system prompt and via hooks if you build them. If you want unattended binges, make sure your hooks (if any) allow the tools you expect to use, and keep at least one gate (the Telegram bridge allowlist in step 16, or a per-tool hook).

Security note: unattended, plus a remote bridge, plus stealth web, all at once, means anyone who reaches the bridge drives a fully ungated agent on your machine. Keep at least one gate.

## Step 15 — Project formatter

- Add a formatter to your active project (Prettier, Black, gofmt, or your build's, for example Gradle's `spotlessApply`). Lets the agent self-format instead of hand-fixing style.

## Step 16 — Telegram bridge (approve from phone)

Drive the agent and approve its actions from your phone, no physical clicking.

> **Status note.** Eigent's Telegram bridge is not as polished as CodePilot's. Check the current state in the Eigent repo before relying on it. If the bridge is unavailable in your version, the Sunshine + Moonlight remote-desktop layer in step 17 covers the same "approve from phone" use case with a real desktop.

1. Talk to **@BotFather** in Telegram, `/newbot`, copy the token.
2. Eigent, enable the Telegram bridge (if available in your version), paste the token.
3. **Allowlist your own chat id.** Mandatory, it is the only thing stopping a stranger from driving your agent.
- **Verify:** message the bot, it responds, and you can approve an action from the phone.

## Step 17 — Full remote desktop (Sunshine + Moonlight + Tailscale)

Low-latency, always-on, across-the-world access from your laptop or phone. No accept prompt, no third-party relay, no open inbound port. This replaces RustDesk/AnyDesk entirely.

- Sunshine (host): [github.com/LizardByte/Sunshine](https://github.com/LizardByte/Sunshine) · [sunshine.com](https://sunshine.com)
- Moonlight (client): [github.com/moonlight-stream/moonlight-qt](https://github.com/moonlight-stream/moonlight-qt) · [moonlight-stream.org](https://moonlight-stream.org) (iOS and Android apps in their respective stores)
- Tailscale (mesh VPN): [github.com/tailscale/tailscale](https://github.com/tailscale/tailscale) · [tailscale.com](https://tailscale.com)
1. **Install Tailscale on both the host and every client** (laptop, phone). Sign in on the same account, authorize each device in the admin console. Note the host's Tailscale IP, it is a stable `100.x.x.x` address.
2. **Install Sunshine on the host.** Windows installer from the releases page. During install, set the Windows Firewall exception (the installer prompts). The Sunshine web UI lives at `https://localhost:47990`, set a username and password on first launch.
3. **Set Sunshine service to Automatic.** `services.msc`, find `SunshineService`, Startup type: Automatic. This keeps the host reachable after reboot with no one logged in to click anything.
4. **Set the host's Sleep to Never.** Control Panel, Power Options, "Change when the computer sleeps", Put the computer to sleep: Never. Sleep breaks the Tailscale connection and the stream.
5. **Install Moonlight on the client.** Desktop (laptop) from the moonlight-stream repo releases, phone from the App Store / Play Store.
6. **Pair.** In Moonlight, add a new host, use the host's **Tailscale IP** (`100.x.x.x`), not its LAN IP. Moonlight shows a 4-digit PIN. Open `https://<tailscale-ip>:47990` on the client (or the host's `https://localhost:47990`), Sunshine Web UI, PIN page, paste the PIN. Authorize once, Moonlight remembers it.
7. **Connect.** Tap the host in Moonlight, you are on the desktop. Use the Telegram bridge (step 16) for quick approve-from-phone without opening the stream, Sunshine + Moonlight for full visual control.
- **Stream shortcuts (Moonlight):** `Ctrl+Alt+Shift+X` toggle fullscreen · `Ctrl+Alt+Shift+Z` toggle mouse capture · `Ctrl+Alt+Shift+Q` disconnect.
- **Verify:** with the host idle at the login screen, open Moonlight on your phone over cellular, get the full desktop, click around. If that works, the stack is correct end-to-end.
- **Troubleshooting:** pairing `Error [-20]` or "Error 2" (certificate mismatch after a reinstall or hardware change), stop the Sunshine service, delete `cacert.pem` and `cakey.pem` in `%ProgramData%\Sunshine`, start the service, pair again. If Moonlight cannot see the host, ping the Tailscale IP first, Tailscale is the connectivity layer, Sunshine is the stream layer.

## Step 18 — Reboot persistence (zero-touch startup)

Goal: reboot the machine, walk away, come back to a fully working agent stack with no windows opened and no prompts accepted. Set each layer once.

1. **Docker Desktop engine autostart.** Open Docker Desktop, Settings, General, tick "Start Docker Desktop when you sign in to your computer" and "Use Docker Desktop in background by default." The SearXNG container from step 11 has `--restart unless-stopped`, so it comes back with the engine. The optional Eigent Docker backend (3001) follows the same rule if you enable it.
2. **Eigent autostart.** Add `Eigent.exe` to the user Run key:
   ```
   reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Eigent /t REG_SZ /d "\"E:\Eigent\Eigent.exe\"" /f
   ```
   Eigent's embedded backend on port 5001 takes 5-30s to come up after the desktop appears. The Docker backend on 3001 is the fallback. Either backend serving agent traffic is a PASS. The health test T24 and the user-only reboot test U01 both account for this race.
3. **Sunshine service.** Step 17 already set the Sunshine service to Automatic. Verify in `services.msc`, `SunshineService`, Startup type: Automatic.
4. **Tailscale service.** The installer sets `Tailscale` to Automatic by default. Verify in `services.msc`.
5. **Host power.** Step 17 set Sleep to Never. Also set "Turn off the display" to Never if you want Sunshine to stream the actual desktop rather than wake from sleep.
6. **Hide tray icons (optional).** Windows, Settings, Personalization, Taskbar, "Other system tray icons," flip Docker / Eigent / Tailscale / Sunshine to Off. They still run, they just stop cluttering the tray.
- **Verify:** reboot, do not log in for a minute, log in from your phone via Moonlight over Tailscale (or just walk to the machine). The desktop should be up, Eigent in the tray, Docker engine running, SearXNG responding on `127.0.0.1:8888`, and at least one backend responding (5001 or 3001). No clicks given.

## Step 18b — Headless CDP Chrome autostart

Eigent's renderer auto-launches a **visible** Chrome (no `--headless` flag in `electron/main/index.ts:865`) whenever the CDP browser pool is empty. Pre-launch a dedicated **headless** Chrome at login to keep the pool non-empty and suppress the visible-Chrome spawn.

1. Create a dedicated profile dir so this Chrome does not share state with your daily browser:
   ```
   C:\Users\<you>\.eigent\browser_profiles\headless_startup
   ```
2. Drop a `.bat` in `shell:startup` (Win+R, `shell:startup`, Enter). Call it `eigent-headless-chrome.bat`. Contents:
   ```bat
   @echo off
   rem Eigent headless CDP Chrome — keep pool non-empty so chatStore auto-launch never fires.
   if /i "%EigHeadlessChrome%"=="0" exit 0
   powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://127.0.0.1:9224/json/version' -UseBasicParsing -TimeoutSec 1).StatusCode | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
   if %ERRORLEVEL%==0 exit 0
   start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
     --headless=new ^
     --remote-debugging-port=9224 ^
     --user-data-dir="C:\Users\<you>\.eigent\browser_profiles\headless_startup" ^
     --no-first-run ^
     --no-default-browser-check ^
     --disable-blink-features=AutomationControlled ^
     about:blank
   exit 0
   ```
3. In Eigent UI, open the Browser / CDP page, **Add external CDP browser** with URL `http://127.0.0.1:9224`. This entry persists across reboots in Eigent's settings (`cdp_browser_pool`), no need to re-add.
4. Log out, log back in. The `.bat` runs at login, Chrome comes up headless on 9224, Eigent starts from its own Run key, sees the pool is non-empty, never triggers the visible-Chrome spawn.
- **Verify:** after a reboot, send any chat in Eigent that triggers a browser tool. No visible Chrome window appears. `curl http://127.0.0.1:9224/json/version` returns JSON.
- **To disable:** delete the `.bat`, or set user env var `EigHeadlessChrome=0`.
- **Permanent fix (not in this guide):** patch `electron/main/index.ts:867` to add `'--headless=new'` to the spawn args and rebuild Eigent from source. That removes the need for this entire step.

## Step 19 — Optional hooks

Eigent does not honor `.claude/settings.json` hooks natively. If you want pre-tool or post-tool hooks, you have to build them in Eigent's own backend (or wait for a future Eigent release that exposes a hook config). The file [files/claude-settings.json](files/claude-settings.json) is kept as reference for what a typical hook setup looks like in the CodePilot world, treat it as a blueprint only.

## Step 20 — Final checklist

- [ ] z.ai Coding Lite plan, API key in hand (0)
- [ ] Eigent installed (1), z.ai Anthropic card added with bigmodel.cn base URL, model glm-5.2, Prefer on (2)
- [ ] Logseq graph, workspace bound via Create space → Use local folder → `E:\Logseq` (3)
- [ ] `claude.md` (4), `user.md` filled (5), `soul.md` (6), `memory.md` + `memory/` (7)
- [ ] ripgrep on PATH, `where rg` resolves (8)
- [ ] Context7 (9), Scrapling installed with `scrapling[mcp]` + `markdownify` + `playwright install chromium` (10), SearXNG container up + JSON verified on a non-8080 port (11), GitHub MCP optional (12), Supabase MCP via local stdio (12b)
- [ ] all MCP servers registered and green in Eigent Connectors, agent lists MCP tools in a fresh chat (13, T00)
- [ ] Eigent backend patches applied: prompt.py, chat_service.py, toolkit_assembler.py, environment_hands.py, listen_chat_agent.py, depth_limited_agent_toolkit.py, browser.py (13b, T13/T13b/T13c)
- [ ] base URL on `open.bigmodel.cn/api/anthropic` (14)
- [ ] project formatter present (15)
- [ ] Telegram bridge enabled and allowlisted, if available in your Eigent version (16)
- [ ] Tailscale on host + clients, Sunshine service Automatic on host, Sleep Never, Moonlight paired over the Tailscale IP (17)
- [ ] reboot persistence configured: Docker autostart + tray, Eigent autostart, services Automatic, Sleep Never, headless CDP Chrome .bat in shell:startup (18, 18b)
- [ ] skip-permissions decision made with at least one gate kept (14, 16, 19)
- [ ] **run [healthtest.md](healthtest.md) in a fresh Eigent session, every AI-run test passes, then do the user-only reboot test (U01)**

Done. A lean, autonomous, remotely-drivable 5-agent workforce for the price of a coding plan.
