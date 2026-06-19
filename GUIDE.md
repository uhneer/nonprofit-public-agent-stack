# Build Guide (click-by-click edition)

Every step on earth, in order, so anyone can fully replicate the environment by following along. No assumed knowledge. No skipped clicks.

**How to use this doc.** Start at step 0. Do not skip. Each step has: what it is, where to click, what to type, what to expect, how to verify, and how to fix if it goes wrong. A step is not done until its Verify bullet passes. The whole build is done when the [health test](healthtest.md) passes (T01 through T43, U01 through U04).

**Conventions.**
- `code font` = type exactly what is shown (substitute your real value when you see `<angle brackets>`).
- `Start menu` = press the Windows key, type the search box, click the result.
- `Settings` inside an app = the app's own settings, not Windows Settings unless explicitly said "Windows Settings".
- "Verify" = the build is not done until this works. Re-read the step if your output does not match.
- Paths like `E:\Logseq` and `E:\Eigent` are the defaults used throughout this guide. If you install on a different drive or folder, substitute your paths wherever you see those literals; nothing in the code or rulesets is hardcoded to `E:\`.

**Name slots are blank by design.** Nothing in this repo will make the AI call you by a hardcoded name. The ruleset (`files/nonprofitclaude.md`) refers to "the operator" throughout. `files/user.md` ships with `_____` placeholders and blank fields. To fill them in, either edit `files/user.md` before copying it to your workspace, or just tell the agent your name in your first chat after install and the agent will write it to `user.md` itself.

**Time budget.** A clean install on a fresh Windows 11 machine takes 4 to 8 hours depending on download speeds and whether you hit the gotchas flagged inline. The big chunks are: Scrapling Camoufox binaries (~15 min), Docker images (~10 min), patch application (~30 min if you go carefully).

**Prerequisites.** Windows 11 (any edition), admin rights on the machine, a fast drive with at least 60 GB free for the workspace + Docker images + node_modules + Python venvs, and a working internet connection.

Secrets (API keys, tokens) stay on your machine and are never committed.

**Person-agnostic by design.** This repo ships nameless. The ruleset (`files/nonprofitclaude.md`) refers to "the operator" throughout. `files/user.md` ships with blank fields including Name. When the operator first tells the agent their name (or any other durable fact), the agent's job is to fill `E:\Logseq\user.md` with that information; it does not need to rewrite the ruleset. The ruleset is name-agnostic, user.md is where personalization lives.

---

## Repository file map (unpack order)

Every file in this repo has exactly one destination. An agent or human can unpack the stack by copying each file to its target path. Files are listed in install order, matches the step numbers below.

| Repo file | Destination | Step | Notes |
|---|---|---|---|
| `files/nonprofitclaude.md` | `E:\Logseq\claude.md` | 4 | Rename on copy. The brain. |
| `files/user.md` | `E:\Logseq\user.md` | 5 | Edit placeholders before saving. |
| `files/nonprofitmemory.md` | `E:\Logseq\memory.md` | 7 | Template. Real entries get appended over time. |
| `files/eigent-mcp.json` | import via Eigent UI (writes to `~/.eigent/mcp.json`) | 13 | Substitute `${...}` env vars first, or set them as user env vars. |
| `files/eigent-headless-chrome.bat` | `shell:startup` (i.e. `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`) | 18b | Portable, uses `%USERPROFILE%` and `%ProgramFiles%`. No edits needed. |
| `files/eigent-backend/*` (7 files) | `E:\Eigent\resources\backend\app\` matching subpaths | 13b | Drop-in replacement for stock backend files. Skip PATCHES.md apply step. |

Files that do NOT ship in this repo and how to get them:
- **Stock Eigent backend files** (`prompt.py`, `chat_service.py`, etc.) ship as patched drop-ins at `files/eigent-backend/`. If you prefer to patch stock files yourself, the originals are at `E:\Eigent\resources\backend\app\` after installing Eigent; back them up, then apply [PATCHES.md](PATCHES.md) in place. The drop-in and the patch paths produce equivalent results; pick one.
- **`claude.md` (the ruleset upstream)** — same content as `files/nonprofitclaude.md`, mirror of `https://github.com/uhneer/nonprofit-agent-rules`. Use either source.
- **Settings DB** — Eigent stores provider config, MCP imports, and UI state in its own settings DB (under `~/.eigent/`). Configured via the Settings UI, not by dropping files.

After every file is in place, run the [health test](healthtest.md). If anything fails, the troubleshooting table at the bottom of this guide maps symptoms to fixes.

---

## Step 0 — Buy the z.ai GLM Coding plan

The cheap frontier model the whole stack rides on. Buy this first, before anything else, so you have the key in hand when you reach step 2.

### 0.1 Sign up
1. Open a browser, go to `https://z.ai`.
2. Click **Sign up** (top right).
3. Use email or a Google / GitHub OAuth. Confirm the email if you used email.
4. Sign in.

### 0.2 Buy the plan
1. Once signed in, the dashboard loads.
2. Click **Coding plans** in the left sidebar (or go to `https://z.ai/billing` directly).
3. Pick **Coding Lite**. Click **Subscribe**.
4. Enter payment, confirm. The plan activates immediately.

### 0.3 Generate an API key
1. In the dashboard, click **API Keys** in the left sidebar (or `https://z.ai/apikeys`).
2. Click **Create new key**.
3. Name it something useful (for example `eigent-desktop-home`).
4. Copy the displayed key. **Store it in a password manager immediately.** You will not be able to see it again after you close the dialog.
5. Keep the key handy in your password manager. You will paste it into Eigent in step 2.

### 0.4 Note the endpoints
Your Coding plan key works on both Anthropic-format endpoints (verified):
- **Primary (this stack):** `https://open.bigmodel.cn/api/anthropic`. Streams the first byte in ~7s during long tool-call generation. Use this one.
- International mirror: `https://api.z.ai/api/anthropic`. Same protocol, same key, but buffers the whole tool-call response server-side (first byte only after the model finishes generating, 190s+ on a big call). Slower perceived latency, no other difference.
- OpenAI-format (do NOT use with this stack): `https://api.z.ai/api/paas/v4`. Coding plan keys are scoped to the coding endpoints and rejected here.

**Verify:** you have an API key string (52-64 chars, alphanumeric) and you know the primary base URL is `https://open.bigmodel.cn/api/anthropic`.

---

## Step 1 — Install Eigent

The desktop agent app. Electron UI plus Python backend, CAMEL-AI runtime, MCP support, multi-agent workforce, skills.

### 1.1 Download
1. Open a browser, go to `https://github.com/EigentAI/eigent/releases`.
2. Pick the latest release. Download the Windows installer (for example `Eigent-Setup-1.0.0.exe`).
3. Save it to `Downloads`.

### 1.2 Run the installer
1. Double-click `Eigent-Setup-1.0.0.exe` in `Downloads`.
2. If Windows SmartScreen pops "Windows protected your PC", click **More info**, then **Run anyway**. (Eigent's installer is not code-signed in every release.)
3. The installer extracts bundled Python, Node modules, and the Electron app into `C:\Users\<you>\AppData\Local\Programs\Eigent\` and `C:\Users\<you>\.eigent\`.
4. When the installer finishes, click **Finish**. Eigent does not auto-launch yet.

### 1.3 First launch
1. `Start menu`, type `Eigent`, Enter. The app opens.
2. The tray icon (bottom right of the taskbar, may need the `^` arrow to expand hidden icons) appears.
3. On first launch, Eigent creates:
   - `C:\Users\<you>\.eigent\` (config, MCP, venvs).
   - The bundled Python venv at `C:\Users\<you>\.eigent\venvs\backend-1.0.0\`.
4. The Settings window may pop automatically. Close it. We will configure it in step 2.

### 1.4 Backend ports
Eigent ships two backends:
- **Embedded** on port `5001`. Starts with the desktop app. Takes 5-30 seconds after the desktop appears before it accepts HTTP.
- **Docker** on port `3001`. Optional. Starts only if you run `docker compose up eigent_api` from the repo.

Either can serve agent traffic. You do not need both.

**Verify:**
1. Wait 30 seconds after the desktop appears.
2. Open a browser, go to `http://127.0.0.1:5001/health`. You should see `{"status":"ok"}` or HTTP 200 with a JSON body.
3. If you see "connection refused", wait another 30 seconds and retry. If still refused after 90 seconds total, the embedded backend did not start. Tray-quit Eigent (right-click the tray icon, Quit), relaunch from Start menu, retry.
4. Alternative: open Command Prompt, run `curl http://127.0.0.1:5001/health`. Same expected output.

---

## Step 2 — Connect the z.ai provider

Tell Eigent where to send model calls and which model to use.

### 2.1 Open Settings
1. Click the Eigent tray icon to bring the app window to front.
2. Click the gear icon (top right) or press `Ctrl+,`. Settings opens.

### 2.2 Add the Anthropic provider card
1. In Settings, click **Models** in the left sidebar.
2. Click **+ Add provider** (or **Add card** in some versions).
3. Fill in:
   - **Provider type:** `Anthropic` (or `Anthropic-compatible`).
   - **Display name:** `z.ai bigmodel` (any label, this is just for the UI).
   - **API Host:** `https://open.bigmodel.cn/api/anthropic`
   - **API Key:** paste the z.ai key from step 0.3.
   - **Model Type:** `glm-5.2` (lowercase, hyphen, no space).
4. Click **Save** (or **Test connection** first, then **Save**).

### 2.3 Set the card to Prefer
1. Back on the Models list, find the card you just created.
2. Toggle **Prefer** to on (or click **Set as default** depending on version).
3. The card should now show a "Default" or "Preferred" badge.

### 2.4 Verify the model answers
1. Close Settings.
2. Click **+ New chat** (or similar) in the app's main view.
3. Type: `What model are you, including version and provider? One line.`
4. Press Enter. Wait for the response.
5. The answer should name `GLM-5.2` or `glm-5.2`. May also mention Eigent, CAMEL, or Single Agent role.
6. If the answer says Claude, Sonnet, Opus, or GPT, the provider is not wired. Re-do 2.2 and 2.3.

### 2.5 Thinking mode
Thinking mode is inherited from the Coding Plan endpoint. No UI toggle to set. Zhipu's docs confirm interleaved thinking is the default for Coding Plan users on `/api/anthropic`, and reasoning_content is preserved across turns.

**Verify:** in the same test chat from 2.4, ask: `Are you currently in thinking mode? Can you reason between tool calls (interleaved thinking)?` The answer should confirm thinking is on.

---

## Step 3 — Install Logseq and bind the workspace

### 3.1 Install Logseq
1. Open a browser, go to `https://logseq.com/downloads`.
2. Download the Windows installer (64-bit).
3. Run it. Default install location is fine.
4. `Start menu`, type `Logseq`, Enter. The app opens.

### 3.2 Create the graph
1. Logseq first-launch dialog: click **Create a new graph**.
2. Click **Choose a folder** (or **Use local folder**).
3. Navigate to `E:\`. Click **New folder** (Windows Explorer button), name it `Logseq`. Press Enter.
4. Select `E:\Logseq`. Click **Select folder**.
5. Logseq creates the graph. The main window opens with a default page.

### 3.3 Bind to Eigent
1. Back in Eigent. Click the **Spaces** icon (left sidebar, may look like a folder).
2. Click **+ Create space** (or **Add space**).
3. Pick **Use local folder**.
4. Browse to `E:\Logseq`. Click **Select folder**.
5. Name the space (for example `Logseq`). Click **Create**.

### 3.4 Verify the workspace is bound
1. In Eigent, open a new chat in that space.
2. Ask: `List the first 10 entries in E:/Logseq/. Report the exact entries.`
3. The answer should list real entries (at minimum `pages/`, `logseq/`, maybe `assets/`).
4. If the answer says `not available to this Brain` or similar, the environment_hands.py patch from step 13b is not applied yet. That is OK at this stage, just note it. We will patch in 13b.

---

## Step 4 — Drop in the instruction ruleset (`claude.md`)

The brain: priorities, voice, long-run behavior, web-verify discipline, tool-call hygiene, verify-before-claim, few-shot examples.

### 4.1 Get the ruleset file
- Source: `https://github.com/uhneer/nonprofit-agent-rules` (raw file `claude.md`).
- Or, if you are using this repo, the file is at [files/nonprofitclaude.md](files/nonprofitclaude.md).

### 4.2 Copy to workspace root
1. Open Windows Explorer, navigate to `E:\Logseq\`.
2. Copy the ruleset file there.
3. Rename it to `claude.md` (exactly that, lowercase, no other extension).
4. The full path is `E:\Logseq\claude.md`.

### 4.3 Verify
1. Open Command Prompt.
2. Run: `type E:\Logseq\claude.md | more` (or just open the file in Notepad).
3. First line should be: `# Nonprofit Agent 操作准则`
4. There should be roughly 13 to 14 top-level sections (§0 through §13).
5. Keep one source of truth, the workspace copy is what loads, the repo is the mirror. Do not let them drift.

---

## Step 5 — Fill `user.md`

### 5.1 Copy the template
1. From this repo, copy [files/user.md](files/user.md) to `E:\Logseq\user.md`.
2. Open it in Notepad or your text editor.

### 5.2 Fill it in
Replace every template placeholder with real, durable facts about you:
- **Name.** Real first name.
- **Role.** What you do (for example "indie game developer", "data scientist", "student").
- **Languages.** Programming languages and frameworks you know well.
- **Active projects.** 1 to 3 projects you are actively working on. Include repo paths.
- **Standing preferences.** Things like "prefer short responses", "commit message style: conventional", "no emojis".

### 5.3 Verify
1. Save `user.md`.
2. In an Eigent chat, ask: `Read E:/Logseq/user.md and tell me who I am according to that file.`
3. The answer should reflect what you just wrote, not the template blanks.

---

## Step 7 — Memory store (cave-speak)

### 7.1 Copy the template
1. From this repo, copy [files/nonprofitmemory.md](files/nonprofitmemory.md) to `E:\Logseq\memory.md`.

### 7.2 Create the memory folder
1. Windows Explorer, navigate to `E:\Logseq\`.
2. Right-click empty space, **New** > **Folder**. Name it `memory`. Press Enter.
3. Full path: `E:\Logseq\memory\`.

### 7.3 Convention
Write memory in compressed Chinese plus English technical terms, append-only, no secrets. See the ruleset file section 11 for the rule. Example line:
```
修 audio desync：bakeAudio 用截断后时长。Mp4Bake.java:264。
```

### 7.4 Verify
1. Open Command Prompt, run: `dir E:\Logseq\memory*`
2. You should see both `memory.md` (file) and `memory` (directory).
3. Open `memory.md` in Notepad. It should start with the template header, no real entries yet (that is fine, the first real entry will be written by the agent during the health test T36).

### 7.5 Eigent agent notes (separate from Logseq memory)
Eigent has its own agent-shared memory layer: `append_note`, `read_note`, and a `shared_files` note. Use it for transient working state within a chat or across chats. Use `E:\Logseq\memory.md` for durable facts you want to survive an Eigent reinstall. Health test T30 exercises the notes path.

Eigent's auto-memory is limited to those in-chat notes. Durable cross-session memory in this stack is the Logseq manual store governed by `claude.md` §11 (cave-speak). No per-conversation memory toggle to worry about, the ruleset is the only memory rule that governs writes.

---

## Step 8 — ripgrep

Fast code search the agent prefers over plain grep. Required, not optional: the operating rules baked into `prompt.py` (operator_operating_rules §4) enforce `rg --json` structured output. The user-facing ruleset (`claude.md`) does not reference ripgrep by name; enforcement comes from the baked-in system prompt.

### 8.1 Install
1. `Start menu`, type `cmd`, Enter to open Command Prompt.
2. Run: `winget install BurntSushi.ripgrep.MSVC`
3. Accept the source agreement if prompted.
4. Wait for the install to finish.

### 8.2 Verify on PATH
1. Close the Command Prompt, open a new one (to refresh PATH).
2. Run: `where rg`
3. Expected: a real path like `C:\Users\<you>\AppData\Local\Microsoft\WinGet\Links\rg.exe`.
4. Run: `rg --version`
5. Expected: `ripgrep 15.1.0` or higher.

### 8.3 Troubleshooting
If `where rg` returns "INFO: Could not find files" but the install succeeded:
- The winget Links directory is not on PATH.
- Fix: open Windows Settings (Win+I), System, About, Advanced system settings, Environment Variables.
- Under "User variables", find `Path`, click Edit.
- Click New, paste: `C:\Users\<you>\AppData\Local\Microsoft\WinGet\Links` (substitute your username).
- Click OK three times. Close all Command Prompts. Open a new one. Retry `where rg`.

---

## Step 9 — Context7 MCP (live docs)

Feeds the agent current library docs, kills confidently-wrong API calls.

### 9.1 Verify npx is available
1. Command Prompt: `npx --version`
2. Expected: a version number (10.x or higher). If you get "command not found", install Node.js LTS from `https://nodejs.org` first.

### 9.2 Test Context7 starts
1. Command Prompt: `npx -y @upstash/context7-mcp`
2. First run downloads the package (a few seconds). Then it waits silently on stdio. This is correct, it is an MCP server waiting for input.
3. Press `Ctrl+C` to exit.

### 9.3 No permanent install needed
The Eigent UI will invoke `npx -y @upstash/context7-mcp` for you each time the MCP server is needed. You do not need to keep the server running manually.

**Verify:** step 9.2 completed without errors.

---

## Step 10 — Scrapling MCP (stealth fetch)

The agent's human-looking page reader. Three tiers: fast HTTP impersonation, Chromium, and Camoufox stealth.

### 10.1 Find Eigent's bundled Python
The patches later in this guide run inside Eigent's Python venv. Find it:
1. Windows Explorer, navigate to `C:\Users\<you>\.eigent\venvs\`.
2. Note the version folder, for example `backend-1.0.0`.
3. Full venv path: `C:\Users\<you>\.eigent\venvs\backend-1.0.0\`.

### 10.2 Install Scrapling and dependencies
Open Command Prompt and run all five lines, one at a time, waiting for each to finish:
```
C:\Users\<you>\.eigent\venvs\backend-1.0.0\Scripts\pip.exe install "scrapling[fetchers]"
C:\Users\<you>\.eigent\venvs\backend-1.0.0\Scripts\python.exe -m scrapling install
C:\Users\<you>\.eigent\venvs\backend-1.0.0\Scripts\pip.exe install scrapling[mcp]
C:\Users\<you>\.eigent\venvs\backend-1.0.0\Scripts\pip.exe install markdownify
C:\Users\<you>\.eigent\venvs\backend-1.0.0\Scripts\playwright.exe install chromium
```

Substitute `<you>` for your actual Windows username.

Each line plugs a specific failure mode (all verified on Scrapling v0.4.9, 2026-06-18):
- `scrapling[fetchers]` is the main package with HTTP impersonation.
- `scrapling install` pulls Camoufox browser binaries (a few hundred MB). It does NOT install Chromium for the Playwright fetcher path.
- `scrapling[mcp]` installs the `mcp` module the MCP entry point imports. Without it `scrapling mcp` crashes with `ModuleNotFoundError: No module named 'mcp'` even though `scrapling --version` works fine.
- `markdownify` is what the `get` tool's HTML-to-Markdown converter imports. Without it, `mcp__scrapling__get` raises `No module named 'markdownify'` on every call. The `bulk_get` path works without it, which masks the bug.
- `playwright install chromium` installs the Chromium binary the `fetch` tool launches. Without it, `mcp__scrapling__fetch` raises `BrowserType.launch_persistent_context: Executable doesn't exist`. `scrapling install` does not pull this, it pulls Camoufox only.

### 10.3 Verify
1. Run: `C:\Users\<you>\.eigent\venvs\backend-1.0.0\Scripts\scrapling.exe --version`
   Expected: a version string, no traceback.
2. Run: `C:\Users\<you>\.eigent\venvs\backend-1.0.0\Scripts\scrapling.exe mcp --help`
   Expected: a usage line. If you see `ModuleNotFoundError: No module named 'mcp'`, the third install line failed. Re-run it.

---

## Step 11 — SearXNG + mcp-searxng (private search)

The agent's own anonymous search, self-hosted, never routes through an AI vendor. SearXNG finds, Scrapling reads.

### 11.1 Make sure Docker is installed and running
1. Command Prompt: `docker --version`
2. If you get a version, skip to 11.2.
3. If you get "command not found", install Docker Desktop from `https://www.docker.com/products/docker-desktop`. Run the installer. Launch Docker Desktop from Start menu. Wait for the engine to start (whale icon in tray, steady state).

### 11.2 Create the SearXNG config directory
1. Windows Explorer, pick a stable location, for example `C:\Users\<you>\docker\searxng\`.
2. Create that folder path.
3. Inside it, create a text file named `settings.yml` (note the `.yml` extension, not `.yaml`).

### 11.3 Write the settings.yml
Open `settings.yml` in Notepad, paste exactly:
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
Replace `<random-hex>` with 32+ random hex characters. You can generate one at `https://www.random.org/strings/?num=32&digits=on&loweralpha=on&unique=off&format=html&rnd=new` or by running `python -c "import secrets; print(secrets.token_hex(32))"` in Command Prompt.

### 11.4 Run the container
Command Prompt (substitute `<you>` for your username):
```
docker run -d --name searxng --restart unless-stopped -p 8888:8080 -v "C:/Users/<you>/docker/searxng:/etc/searxng" docker.io/searxng/searxng:latest
```

**Why port 8888 and not 8080?** 8080 is the default for Open WebUI, Jenkins, Tomcat, and a pile of other dev tools. SearXNG silently returns HTML with no error when something else is on the port, and the MCP then fails with `Invalid JSON format`. Use 8888 unless you know 8080 is free.

### 11.5 Verify the JSON API
1. Open a browser, go to: `http://127.0.0.1:8888/search?q=test&format=json`
2. Expected: JSON starting with `{"query":`.
3. If you see HTML (a web page), the port is occupied by something else and SearXNG never started. Run `docker ps -a | findstr searxng` to check. If it shows "Exited", run `docker logs searxng` to see why. Usually the cause is a port conflict, fix by stopping the conflicting service or using a different host port.

### 11.6 mcp-searxng (no permanent install needed)
The Eigent UI invokes `npx -y mcp-searxng` for you. The env var `SEARXNG_URL=http://127.0.0.1:8888` will be set in step 13.

**Verify:** step 11.5 returned JSON.

---

## Step 12 — GitHub MCP (optional)

Your repos: browse, issues, PRs.

### 12.1 Generate a fine-grained PAT
1. Browser, go to `https://github.com/settings/tokens?type=beta` (fine-grained PATs).
2. Click **Generate new token**.
3. Name it `eigent-github-mcp`.
4. Expiration: pick what you are comfortable with (90 days is fine).
5. Repository access: **All repositories** or pick specific repos.
6. Permissions: under Repository permissions, set **Contents** = Read, **Issues** = Read, **Pull requests** = Read, **Metadata** = Read. Under Account permissions, set **Plan** = Read.
7. Click **Generate token**. Copy the token. Store in password manager. You will not see it again.

### 12.2 Note the env var name
The env var the MCP reads is `GITHUB_PERSONAL_ACCESS_TOKEN`. You will set this in step 13.

### 12.3 Streamable HTTP transport
GitHub MCP uses streamable_http transport (not stdio). The URL is `https://api.githubcopilot.com/mcp/`. The header is `Authorization: Bearer <your-token>`. Eigent handles this when you import the config in step 13.

**Verify:** the token string is in your password manager. No command-line verification needed yet.

---

## Step 12b — Supabase MCP (optional, local stdio)

Your Supabase projects: query, manage, inspect.

### 12b.1 Generate a Supabase PAT
1. Browser, go to `https://supabase.com/dashboard/account/tokens`.
2. Click **Generate new token**.
3. Name it `eigent-supabase-mcp`.
4. Copy the token. Store in password manager.

### 12b.2 Important: use the local stdio server
Do NOT use the remote endpoint `https://api.supabase.com/mcp/v1`. That endpoint is OAuth-only and rejects personal access tokens with a silent `Session terminated` error in the MCP connect log. Use the local stdio server instead.

### 12b.3 Note the env var name
The env var the MCP reads is `SUPABASE_ACCESS_TOKEN`. You will set this in step 13.

**Verify:** the token string is in your password manager.

---

## Step 13 — Register the MCP servers in Eigent

### 13.1 Get the config file
1. From this repo, open [files/eigent-mcp.json](files/eigent-mcp.json).
2. Edit it: replace `${GITHUB_PERSONAL_ACCESS_TOKEN}` and `${SUPABASE_ACCESS_TOKEN}` with your actual tokens, OR set those as Windows environment variables (recommended, so the file has no real tokens).

### 13.2 Set env vars (recommended over inline tokens)
1. Windows Settings (Win+I), System, About, Advanced system settings, Environment Variables.
2. Under "User variables", click New.
3. Variable name: `GITHUB_PERSONAL_ACCESS_TOKEN`. Value: paste token. OK.
4. Click New again. Variable name: `SUPABASE_ACCESS_TOKEN`. Value: paste token. OK.
5. Close all Command Prompts and Eigent. Reopen them so they pick up the new env vars.

### 13.3 Import the config into Eigent
1. Open Eigent. Settings.
2. Click **Connectors** (or **MCP**) in the left sidebar.
3. Click **+ Add** > **Local JSON** (or **Import**).
4. Browse to your edited `eigent-mcp.json`, OR paste the `mcpServers` block into the dialog.
5. Click **Save** (or **Import**).
6. Eigent writes the imported config to `C:\Users\<you>\.eigent\mcp.json`.

### 13.4 Verify each server connects
1. In the Connectors list, each server should show a green dot or "Connected" status.
2. If any shows red, click it for the error. Common errors:
   - Context7 red: npx failed. Check Node.js is installed (step 9.1).
   - Scrapling red: `scrapling` not on PATH in Eigent's venv. Re-do step 10.2.
   - SearXNG red: SEARXNG_URL wrong or the container is down. Re-do step 11.
   - GitHub red: token not set or expired.
   - Supabase red: if it says `Session terminated`, you are using the remote endpoint. Switch to local stdio per step 12b.2.

### 13.5 The MCP loading gap (important)
There is a silent MCP loading gap in stock Eigent. The per-chat `installed_mcp` field can stay empty even when the disk config is correct. The fix is a patch in `toolkit_assembler.py` (see [PATCHES.md](PATCHES.md) P3) that bridges disk config into agent runs as a fallback when `installed_mcp` is empty.

Without the patch: after every import, start a fresh chat, and verify in chat that the agent can list MCP tools (run health test T00). Toggling a server off and on in the Connectors panel is the manual kick if a server is stuck on "not installed."

With the patch (applied in step 13b): everything just works after import.

**Verify:** in a fresh chat in the bound workspace, ask: `List every tool you currently have access to, one per line, alphabetical order.` The list should include `searxng_web_search`, `scrapling_*` tools, and `resolve-library-id` (Context7). If MCP tools are missing, apply the patch in step 13b before continuing.

---

## Step 13b — Drop in the patched backend files

This is the part that turns a stock Eigent install into the 5-agent workforce with the ruleset-aware prompt. The repo ships the full patched versions of all 7 backend files. Copy them in; skip manual patching.

### 13b.1 Find the backend source
Windows Explorer, navigate to `E:\Eigent\resources\backend\app\`. This is the target directory.

### 13b.2 Back up the stock files first
Open Command Prompt:
```
cd E:\Eigent\resources\backend\app
copy agent\prompt.py agent\prompt.py.bak
copy service\chat_service.py service\chat_service.py.bak
copy agent\factory\toolkit_assembler.py agent\factory\toolkit_assembler.py.bak
copy agent\factory\browser.py agent\factory\browser.py.bak
copy hands\environment_hands.py hands\environment_hands.py.bak
copy agent\listen_chat_agent.py agent\listen_chat_agent.py.bak
copy agent\toolkit\depth_limited_agent_toolkit.py agent\toolkit\depth_limited_agent_toolkit.py.bak
```
Keep the `.bak` files; they are the restore path.

### 13b.3 Copy the drop-in files
The repo ships 7 patched backend files at [files/eigent-backend/](files/eigent-backend/), mirroring the backend tree:
- `agent/prompt.py`
- `agent/listen_chat_agent.py`
- `agent/factory/browser.py`
- `agent/factory/toolkit_assembler.py`
- `agent/toolkit/depth_limited_agent_toolkit.py`
- `hands/environment_hands.py`
- `service/chat_service.py`

Copy each file to its matching subpath under `E:\Eigent\resources\backend\app\`. Example using Command Prompt:
```
xcopy /Y "E:\Games\nonprofit-agent-stack\files\eigent-backend\*.*" "E:\Eigent\resources\backend\app\" /E
```
This preserves the subdirectory structure (`agent/`, `agent/factory/`, `agent/toolkit/`, `hands/`, `service/`).

### 13b.4 What each file does (overview)
For the why behind each patch, see [PATCHES.md](PATCHES.md). The short version:
- **environment_hands.py** (P4) — adds `E:\` as an allowed filesystem root so the agent can read `E:\Logseq\` without moving it under your home dir.
- **prompt.py** (P1) — bakes the operating ruleset (`operator_operating_rules` §0-§14) into every agent. Includes Coordinator dispatch protocol, anti-fabrication rules, URL verification.
- **chat_service.py** (P2) — wires the Coordinator role + asyncio.gather bugfix for browser_agent.
- **toolkit_assembler.py** (P3) — disk-config bridge for MCP loading, sanitizer empty-string coercion, env var handling.
- **listen_chat_agent.py** (P5) — sanitizer interception fix (wraps async_call too), handles hallucinated tool names gracefully.
- **depth_limited_agent_toolkit.py** (P6) — anti-fabrication enforcement.
- **browser.py** (P7) — headless CDP browser toolkit integration.

### 13b.5 Optional: mirror to the source copy
If you keep a second Eigent source tree at `E:\Eigent-source\backend\` for reading and diffing, repeat the same xcopy against that target.

### 13b.6 Restart Eigent
1. Right-click the tray icon, **Quit**.
2. Wait 5 seconds.
3. `Start menu`, type `Eigent`, Enter.

### 13b.7 Verify each patch is live
Run health tests T13, T13b, T13c, T13d in a fresh chat. Each test prompts the agent to open a patched file and report what it sees. All four should PASS before you continue.

### 13b.8 Patch-apply alternative (skip unless you have a heavily-modified backend)
If your backend is already customized and you cannot drop in the full files, fall back to applying individual diffs from [PATCHES.md](PATCHES.md). Read PATCHES.md P1-P9 in numerical order, apply each diff manually. P10 (T31 sub-agent fabrication) has no fix yet, parent-side verification only.

---

## Step 14 — Config tweaks and the timeout fix

### 14.1 Base URL
In Eigent Settings > Models > Anthropic card, API Host must be `https://open.bigmodel.cn/api/anthropic` (set in step 2.2). It is not a "fallback", it is the better default. bigmodel streams the first byte in ~7s on a long tool call, api.z.ai buffers the whole call and only then sends anything.

### 14.2 Thinking mode
Inherited from the Coding Plan endpoint, no UI toggle. The "30s idle reset" is not real on the Anthropic-format endpoints. Direct test on 2026-06-17: a 235s silent tool-call generation on `open.bigmodel.cn/api/anthropic` and a 190s one on `api.z.ai/api/anthropic` both completed without any reset. Extended thinking streams as `thinking` deltas immediately on bigmodel, so it never sits silent in the first place.

### 14.3 If you ever see "stream idle timeout"
The actual timeout layer is client-side, in Eigent or CAMEL, not at z.ai's edge. Fix it there: raise the stream-idle limit in CAMEL's Anthropic client. Do not add a proxy and do not disable thinking.

### 14.4 Do not bother with `tool_stream=true` or a local proxy
It is a paas/v4 (OpenAI-format) flag only. On `/api/anthropic` it is silently ignored, verified by direct test (233s silent generation with the flag set, no incremental streaming).

### 14.5 Permissions
Eigent does not have a "skip all permission prompts" toggle. The equivalent is per-tool gating: either via the agent's own system prompt (the ruleset) or via a pre-tool hook you build into the backend (see step 19). For unattended runs, make sure your hooks allow the tools you expect to use, and keep at least one gate (the Telegram bridge allowlist in step 16, a git-push pre-hook per step 19.2, or equivalent).

A reasonable allowlist surface for this stack: `Read`, `Edit`, `Write`, `Bash(git*)`, `Bash(rg*)`. Everything else, gate manually.

### 14.6 Security note
Unattended, plus a remote bridge, plus stealth web, all at once, means anyone who reaches the bridge drives a fully ungated agent on your machine. Keep at least one gate.

**Verify:** Settings > Models shows the Anthropic card with bigmodel.cn as the API Host, Prefer toggled on.

---

## Step 15 — Project formatter

### 15.1 Pick the formatter for your active project
- JavaScript/TypeScript: Prettier (`npm install --save-dev prettier`).
- Python: Black (`pip install black`).
- Go: `gofmt` (built-in).
- Java: your build's formatter (for example Gradle's `spotlessApply`).
- Rust: `rustfmt` (built-in).

### 15.2 Why
Lets the agent self-format instead of hand-fixing style. Less token waste, fewer cycles spent on cosmetic diffs.

**Verify:** running the formatter from your project root succeeds with no errors.

---

## Step 16 — Telegram bridge (approve from phone)

> **Status note.** Eigent's Telegram bridge is community-contributed and may lag behind the core. Check the current state in the Eigent repo before relying on it. If the bridge is unavailable in your version, the Sunshine + Moonlight remote-desktop layer in step 17 covers the same "approve from phone" use case with a real desktop.

### 16.1 Create the bot
1. Open Telegram (phone or desktop). Search for `@BotFather`.
2. Start a chat. Send `/newbot`.
3. Follow the prompts: name, then username (must end in `bot`).
4. BotFather replies with a token like `1234567890:ABCdefGhi...`. Copy it.

### 16.2 Wire it into Eigent (if available in your version)
1. Eigent, Settings, **Telegram** (or **Integrations** > **Telegram**).
2. Toggle **Enable**.
3. Paste the bot token.
4. Save.

### 16.3 Get your chat ID and allowlist it
1. Message your new bot in Telegram with any text.
2. In a browser, go to `https://api.telegram.org/bot<TOKEN>/getUpdates` (substitute your token).
3. Find `"chat":{"id": <number>` in the JSON. That number is your chat ID.
4. In Eigent Settings > Telegram, paste your chat ID into the **Allowlist** field. Save.

### 16.4 Verify
1. From your phone, message the bot.
2. It should respond.
3. Trigger an action in Eigent that requires approval. The approval prompt should appear in Telegram.
4. Approve from your phone. The action should proceed.

**Why allowlist is mandatory:** without it, anyone who finds your bot can drive your agent.

---

## Step 17 — Full remote desktop (Sunshine + Moonlight + Tailscale)

Low-latency, always-on, across-the-world access from your laptop or phone. No accept prompt, no third-party relay, no open inbound port. This replaces RustDesk/AnyDesk entirely.

### 17.1 Install Tailscale on the host
1. Browser, go to `https://tailscale.com/download`.
2. Download Windows installer. Run it.
3. `Start menu`, type `Tailscale`, Enter. The Tailscale icon appears in the tray.
4. Click the tray icon, **Log in**.
5. Browser opens to Tailscale's auth page. Sign up / sign in (Google, GitHub, Microsoft, or email).
6. Authorize this device in the Tailscale admin console (`https://login.tailscale.com/admin/machines`).
7. Note the host's Tailscale IP. It is a stable `100.x.x.x` address. Find it in the admin console or by running `tailscale ip -4` in Command Prompt.

### 17.2 Install Tailscale on every client
1. Laptop: same installer.
2. Phone: Tailscale app from App Store / Play Store.
3. Sign in on the same account on each device. Authorize each in the admin console.

### 17.3 Install Sunshine on the host
1. Browser, go to `https://github.com/LizardByte/Sunshine/releases/latest`.
2. Download the Windows installer (for example `sunshine-windows-installer.exe`).
3. Run the installer. When prompted, allow the Windows Firewall exception.
4. `services.msc` (Win+R, type `services.msc`, Enter). Find `SunshineService`.
5. Right-click, **Properties**. Set **Startup type** to **Automatic**. Click **Apply**, **OK**.
6. The Sunshine web UI is at `https://localhost:47990`. Open it in a browser.
7. First launch: create a username and password. Save them in your password manager.

### 17.4 Set the host's Sleep to Never
1. Win+R, type `control`, Enter.
2. Power Options.
3. **Change when the computer sleeps** (left sidebar).
4. Set **Put the computer to sleep** to **Never**.
5. Save changes.

Sleep breaks the Tailscale connection and the stream. Never is mandatory for unattended remote access.

### 17.5 Install Moonlight on the client
1. Desktop (laptop): browser to `https://moonlight-stream.org`, download, install.
2. Phone: Moonlight app from App Store / Play Store.

### 17.6 Pair
1. Open Moonlight on the client. Settings (gear icon). Add a host manually.
2. Host IP: the host's **Tailscale IP** (`100.x.x.x`), not its LAN IP.
3. Moonlight shows a 4-digit PIN.
4. On any device that can reach the host, open `https://<tailscale-ip>:47990`.
5. Sign in with the Sunshine credentials.
6. Go to the **PIN** page. Paste the 4-digit PIN. Authorize.
7. Moonlight remembers the host.

### 17.7 Stream shortcuts (Moonlight)
- `Ctrl+Alt+Shift+X` toggle fullscreen.
- `Ctrl+Alt+Shift+Z` toggle mouse capture.
- `Ctrl+Alt+Shift+Q` disconnect.

### 17.8 Verify
With the host idle at the login screen, open Moonlight on your phone over cellular:
1. Disable WiFi on your phone. Use cellular only.
2. Open Moonlight. Tap the host.
3. The full desktop should appear. Click around. If it works, the stack is correct end-to-end.

### 17.9 Troubleshooting
- **Pairing `Error [-20]` or "Error 2"** (certificate mismatch after a reinstall or hardware change): stop the Sunshine service (`services.msc` > SunshineService > Stop), delete `cacert.pem` and `cakey.pem` in `%ProgramData%\Sunshine\`, start the service, pair again.
- **Moonlight cannot see the host**: ping the Tailscale IP first. Tailscale is the connectivity layer, Sunshine is the stream layer.

---

## Step 18 — Reboot persistence (zero-touch startup)

Goal: reboot the machine, walk away, come back to a fully working agent stack with no windows opened and no prompts accepted. Set each layer once.

### 18.1 Docker Desktop engine autostart
1. Open Docker Desktop.
2. Settings (gear icon).
3. **General**.
4. Tick **Start Docker Desktop when you sign in to your computer**.
5. Tick **Use Docker Desktop in background by default**.
6. Untick **Open Docker Dashboard when Docker Desktop starts**.
7. Apply & Restart.

The SearXNG container from step 11 has `--restart unless-stopped`, so it comes back with the engine. The optional Eigent Docker backend (3001) follows the same rule if you enable it.

### 18.2 Eigent autostart
1. Command Prompt (admin not needed for HKCU):
```
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Eigent /t REG_SZ /d "\"E:\Eigent\Eigent.exe\"" /f
```
2. Verify:
```
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Eigent
```
Expected: a line with `Eigent REG_SZ "E:\Eigent\Eigent.exe"`.

Eigent's embedded backend on port 5001 takes 5-30s to come up after the desktop appears. The Docker backend on 3001 is the fallback. Either backend serving agent traffic is a PASS.

### 18.3 Sunshine service
Already set to Automatic in step 17.3. Verify in `services.msc`, `SunshineService`, Startup type: Automatic.

### 18.4 Tailscale service
The installer sets `Tailscale` to Automatic by default. Verify in `services.msc`.

### 18.5 Host power
Already set Sleep to Never in step 17.4. Also set "Turn off the display" to Never if you want Sunshine to stream the actual desktop rather than wake from sleep.

### 18.6 Hide tray icons (optional)
1. Windows Settings (Win+I), Personalization, Taskbar.
2. **Other system tray icons** (or "Taskbar corner overflow").
3. Flip Docker / Eigent / Tailscale / Sunshine to Off. They still run, they just stop cluttering the tray.

### 18.7 Verify
1. Reboot the host.
2. Do not log in for a minute.
3. Log in via Moonlight from your phone over Tailscale (or just walk to the machine).
4. The desktop should be up.
5. Eigent icon in tray.
6. Docker engine running (whale icon steady).
7. SearXNG responding on `http://127.0.0.1:8888/search?q=test&format=json`.
8. At least one Eigent backend responding (`http://127.0.0.1:5001/health` or `http://127.0.0.1:3001/health`).
9. No clicks given.

---

## Step 18b — Headless CDP Chrome autostart

Eigent's renderer auto-launches a **visible** Chrome (no `--headless` flag in `electron/main/index.ts:865`) whenever the CDP browser pool is empty. Pre-launch a dedicated **headless** Chrome at login to keep the pool non-empty and suppress the visible-Chrome spawn.

### 18b.1 Create the profile directory
1. Windows Explorer, navigate to `C:\Users\<you>\.eigent\`.
2. Create folder path `browser_profiles\headless_startup`.
3. Full path: `C:\Users\<you>\.eigent\browser_profiles\headless_startup`.

### 18b.2 Open the Startup folder
1. Win+R, type `shell:startup`, Enter.
2. Windows Explorer opens at `C:\Users\<you>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`.

### 18b.3 Drop in the .bat file
1. From this repo, copy [files/eigent-headless-chrome.bat](files/eigent-headless-chrome.bat) into the Startup folder you just opened.
2. No edits needed. The .bat uses `%USERPROFILE%` and `%ProgramFiles%`, so it is portable across Windows usernames.
3. The shipped .bat also auto-creates the profile directory if missing, and includes a kill-switch env var (`EigHeadlessChrome=0`).

If you would rather write the .bat yourself, see the file in the repo for the exact contents. The previous paste-in version has been retired in favor of the shipped file.

### 18b.4 Add the external CDP browser to Eigent
1. Open Eigent. Settings.
2. Find the **Browser** or **CDP** page (sometimes under Connectors or Advanced).
3. Click **Add external CDP browser**.
4. URL: `http://127.0.0.1:9224`.
5. Save. This entry persists across reboots in Eigent's settings (`cdp_browser_pool`).

### 18b.5 First-time launch
Either log out and log back in (so the .bat runs), or double-click the .bat manually once now to start Chrome headless.

### 18b.6 Verify
1. Command Prompt: `curl http://127.0.0.1:9224/json/version`
2. Expected: JSON with Chrome version info.
3. In Eigent, send any chat that triggers a browser tool. No visible Chrome window should pop.

### 18b.7 To disable
Delete the `.bat`, or set user env var `EigHeadlessChrome=0` (Windows Settings > System > About > Advanced system settings > Environment Variables > New user variable).

### 18b.8 Permanent fix (not in this guide)
Patch `electron/main/index.ts:867` to add `'--headless=new'` to the spawn args and rebuild Eigent from source. That removes the need for this entire step. Tracked as a future patch.

---

## Step 19 — Optional hooks

Eigent does not honor a `.claude/settings.json` natively. If you want pre-tool or post-tool hooks, you build them in Eigent's own backend (or wait for a future Eigent release that exposes a hook config).

### 19.1 If you want to build a hook in Eigent
1. Find the tool dispatch path in `listen_chat_agent.py` (around `_aexecute_tool`).
2. Wrap the tool call with your pre and post logic.
3. Mirror to `E:\Eigent-source\backend\` if you keep a source mirror.
4. Restart Eigent from the tray.

### 19.2 Example hook: gate `git push`
Pseudocode:
```python
async def _aexecute_tool(self, request):
    if request.tool_name == "shell_exec" and "git push" in request.args.get("command", ""):
        if not self._user_approved_push(request):
            return self._record_tool_calling(..., result="denied by pre-hook", ...)
    return await super()._aexecute_tool(request)
```

**Verify:** trigger the hooked tool in chat. The hook should fire.

---

## Step 20 — Final checklist

Tick each box. The build is not done until all are checked.

- [ ] z.ai Coding Lite plan, API key in hand (step 0).
- [ ] Eigent installed (step 1), z.ai Anthropic card added with bigmodel.cn base URL, model `glm-5.2`, Prefer on (step 2).
- [ ] Logseq graph at `E:\Logseq`, workspace bound via Create space > Use local folder > `E:\Logseq` (step 3).
- [ ] `claude.md` at workspace root, first line is `# Nonprofit Agent 操作准则` (step 4).
- [ ] `user.md` filled with real details (step 5).
- [ ] `memory.md` and `memory/` folder created (step 7).
- [ ] ripgrep on PATH, `where rg` resolves, version 15.1.0+ (step 8).
- [ ] Context7 MCP verified startable via `npx -y @upstash/context7-mcp` (step 9).
- [ ] Scrapling installed with all 5 install lines (`[fetchers]`, `scrapling install`, `[mcp]`, `markdownify`, `playwright install chromium`) in Eigent's bundled venv (step 10).
- [ ] SearXNG container up, JSON verified on port 8888 (step 11).
- [ ] GitHub MCP token generated, env var `GITHUB_PERSONAL_ACCESS_TOKEN` set (step 12).
- [ ] Supabase MCP token generated, env var `SUPABASE_ACCESS_TOKEN` set, using local stdio server not the remote endpoint (step 12b).
- [ ] All MCP servers registered and green in Eigent Connectors (step 13).
- [ ] Eigent backend patches applied (P1 to P9 from PATCHES.md), T13/T13b/T13c/T13d all PASS (step 13b).
- [ ] Base URL on `open.bigmodel.cn/api/anthropic`, thinking inherited from Coding Plan endpoint (step 14).
- [ ] Project formatter present (step 15).
- [ ] Telegram bridge enabled and allowlisted (if available in your Eigent version) (step 16).
- [ ] Tailscale on host + all clients. Sunshine service Automatic on host. Sleep Never. Moonlight paired over the Tailscale IP. Remote desktop verified from phone over cellular (step 17).
- [ ] Reboot persistence configured: Docker autostart + tray, Eigent autostart via HKCU Run key, services Automatic, Sleep Never, headless CDP Chrome .bat in `shell:startup` (step 18, 18b).
- [ ] Permissions decision made with at least one gate kept (step 14.5, 16, 19).
- [ ] **Run [healthtest.md](healthtest.md) in a fresh Eigent session. Every AI/LOCATE test passes (T31 acceptable as PASS-with-concern). Then do the user-only reboot test (U01).**

Done. A lean, autonomous, remotely-drivable 5-agent workforce for the price of a coding plan.

---

## Troubleshooting quick-reference

If something breaks, find the symptom and follow the link.

| Symptom | Likely cause | Fix |
|---|---|---|
| "An asyncio.Future, a coroutine or an awaitable is required" in workforce | `browser_agent` (sync) called inside `asyncio.gather` without `asyncio.to_thread` wrapper | Re-apply P2 in PATCHES.md |
| "MCP connection failed for URL: https://api.supabase.com/mcp/v1. Error: Session terminated" | Remote Supabase endpoint rejects PATs | Switch to local stdio per step 12b |
| "Tool execution failed: Error executing tool 'list_repositories': tool 'list_repositories' is not in this agent's surface" | Model hallucinated a non-existent tool name | P5 already handles this gracefully. The error message tells the model what tools ARE available. |
| Agent reports "not available to this Brain" for `E:\Logseq\` | environment_hands.py patch (P4) missing | Re-apply P4, restart Eigent tray |
| No MCP tools in agent surface (T00 fails) | toolkit_assembler.py disk-config bridge (P3) missing | Re-apply P3, restart Eigent tray |
| Chrome window pops on every chat after reboot | Step 18b .bat not in `shell:startup` or not run yet | Re-do step 18b |
| "stream idle timeout" on long tool calls | CAMEL client-side timeout too low | Raise in CAMEL's Anthropic client. Do NOT disable thinking or add a proxy. |
| T31 sub-agent fabricates the SHA-256 hash | GLM-5.2 base-model behavior ceiling | PASS-with-concern. P10 (parent-side verification) TBD. |
| `ModuleNotFoundError: No module named 'mcp'` from Scrapling | Step 10.2 third line skipped | Run `pip install scrapling[mcp]` in Eigent's venv |
| `No module named 'markdownify'` from Scrapling get tool | Step 10.2 fourth line skipped | Run `pip install markdownify` in Eigent's venv |
| SearXNG returns HTML not JSON | Port 8080 conflict | Stop conflicting service, redo step 11 on port 8888 |
| Moonlight pairing Error [-20] | Sunshine cert mismatch after reinstall | Delete `cacert.pem` and `cakey.pem` in `%ProgramData%\Sunshine\`, restart service, re-pair |
| Eigent 5001 false-negative right after reboot | Boot race, embedded backend not up yet | Wait 60-90s, retry. T24 has the retry loop. |
