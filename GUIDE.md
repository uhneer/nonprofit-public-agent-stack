# Build Guide

Lock in every layer, in order. One step per component. Each step says what it is, the exact codebase, the commands, where the file goes, and how to verify. Secrets (API keys, tokens) stay on your machine and are never committed. Commands assume Windows; adjust paths for your OS.

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

## Step 1 — Install CodePilot

The desktop agent app. Multi-model, Claude Agent SDK runtime, MCP support, remote bridge.

- Codebase: [github.com/op7418/CodePilot](https://github.com/op7418/CodePilot) · docs: [codepilot.sh](https://www.codepilot.sh/docs/providers)
1. Download a release from the repo, or build from source.
2. Launch it once so it creates `~/.codepilot/codepilot.db`.
- **Verify:** the app opens and shows Settings.

## Step 2 — Connect the z.ai provider

- In CodePilot: Settings, Providers, Add provider.
  - Type: **Anthropic-compatible**
  - Base URL: `https://open.bigmodel.cn/api/anthropic`
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
  pip install scrapling[mcp]
  pip install markdownify
  playwright install chromium
  ```
  Five lines, each plugs a specific failure mode (all verified on v0.4.9, 2026-06-18 health test):
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
- Command: `npx -y @modelcontextprotocol/server-github`, env `GITHUB_PERSONAL_ACCESS_TOKEN` (a fine-grained token, you add it, never commit it).

## Step 13 — Register the MCP servers in CodePilot

- Config: [files/codepilot-mcp.json](files/codepilot-mcp.json)
1. CodePilot, MCP page in the sidebar, add each server (stdio) with the command, args, and env from the JSON.
2. CodePilot stores MCP config in its own database, so the MCP page is the verified path. A project-level `.mcp.json` in the work dir is a best-effort fallback if your build of CodePilot honors the SDK's project config, verify before relying on it.
- **Verify:** the MCP page shows each server with a green/running status, and the agent can list their tools.

## Step 14 — Config tweaks and the timeout fix

In CodePilot settings:
- **1M context:** on.
- **thinking mode:** MAX, no caveats. The "30s idle reset" is not real on the Anthropic-format endpoints (direct test, 2026-06-17: a 235s silent tool-call generation on `open.bigmodel.cn/api/anthropic` and a 190s one on `api.z.ai/api/anthropic` both completed without any reset). Extended thinking streams as `thinking` deltas immediately on bigmodel, so it never sits silent in the first place. Keep it on MAX.
- **Base URL:** use `https://open.bigmodel.cn/api/anthropic` (step 2). It is not a "fallback," it is the better default. bigmodel streams the first byte in ~7s on a long tool call, api.z.ai buffers the whole call and only then sends anything.
- **The actual timeout layer (if you ever see "stream idle timeout"):** it is client-side, in CodePilot or the SDK, not at z.ai's edge. Fix it there, raise the stream-idle limit. Do not touch thinking mode and do not add a proxy.
- **Do not bother with `tool_stream=true` or a local proxy.** It is a paas/v4 (OpenAI-format) flag only. On `/api/anthropic` it is silently ignored, verified by direct test (233s silent generation with the flag set, no incremental streaming).
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

1. **Docker Desktop engine autostart.** Open Docker Desktop, Settings, General, tick "Start Docker Desktop when you sign in to your computer" and "Use Docker Desktop in background by default." The SearXNG container from step 11 has `--restart unless-stopped`, so it comes back with the engine.
2. **CodePilot autostart.** Add `CodePilot.exe` to the user Run key:
   ```
   reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v CodePilot /t REG_SZ /d "\"C:\path\to\CodePilot.exe\"" /f
   ```
   In CodePilot's own settings, toggle any "start minimized to tray" or "minimize on close" option so it does not pop a window at login. Closing the main window should send it to the tray, not exit the process. MCP servers spawn on-demand from CodePilot, so once CodePilot is up, the entire MCP layer is up.
3. **Sunshine service.** Step 17 already set the Sunshine service to Automatic. Verify in `services.msc`, `SunshineService`, Startup type: Automatic.
4. **Tailscale service.** The installer sets `Tailscale` to Automatic by default. Verify in `services.msc`.
5. **Host power.** Step 17 set Sleep to Never. Also set "Turn off the display" to Never if you want Sunshine to stream the actual desktop rather than wake from sleep.
6. **Hide tray icons (optional).** Windows, Settings, Personalization, Taskbar, "Other system tray icons," flip Docker / CodePilot / Tailscale / Sunshine to Off. They still run, they just stop cluttering the tray.
- **Verify:** reboot, do not log in for a minute, log in from your phone via Moonlight over Tailscale (or just walk to the machine). The desktop should be up, CodePilot in the tray, Docker engine running, SearXNG responding on `127.0.0.1:8888`. No clicks given.

## Step 19 — Optional hooks

- Config: [files/claude-settings.json](files/claude-settings.json) at `E:\Logseq\.claude\settings.json`.
- Hooks run regardless of skip-permissions, so a `PreToolUse` hook gating `git push` is your real guard. Verify CodePilot honors project `.claude` config before relying on it.

## Step 20 — Final checklist

- [ ] z.ai Coding Lite plan, API key in hand (0)
- [ ] CodePilot installed (1), z.ai provider added with `API_TIMEOUT_MS`, model glm-5.2 (2)
- [ ] Logseq graph, workspace path set (3)
- [ ] `claude.md` (4), `user.md` filled (5), `soul.md` (6), `memory.md` + `memory/` (7)
- [ ] ripgrep on PATH (8)
- [ ] Context7 (9), Scrapling installed with `scrapling[mcp]` (10), SearXNG container up + JSON verified on a non-8080 port (11), GitHub MCP optional (12)
- [ ] all MCP servers registered and green in CodePilot (13)
- [ ] 1M context on, thinking MAX, base URL on `open.bigmodel.cn/api/anthropic` (14)
- [ ] project formatter present (15)
- [ ] Telegram bridge enabled and allowlisted (16)
- [ ] Tailscale on host + clients, Sunshine service Automatic on host, Sleep Never, Moonlight paired over the Tailscale IP (17)
- [ ] reboot persistence configured: Docker autostart + tray, CodePilot autostart + tray, services Automatic, Sleep Never (18)
- [ ] skip-permissions decision made with at least one gate kept (14, 16, 19)
- [ ] **run [healthtest.md](healthtest.md) in a fresh CodePilot session, every AI-run test passes, then do the user-only reboot test (U01)**

Done. A lean, autonomous, remotely-drivable agent for the price of a coding plan.
