# Health Test

End-to-end verification that every layer of the agent stack actually works. Run this after a fresh clone, a machine rebuild, an OS update, or any time something feels off. Each test has an ID, one thing it proves, the prompt or command, the pass criterion, and the failure hint pointing back to the GUIDE.md step that fixes it.

## How to use this file

Two modes.

**Single-prompt mode (recommended).** Open a fresh CodePilot session on the agent workspace and paste the mega-prompt below. The AI runs every `[AI]` test, locates every `[LOCATE]` test, and lists every `[USER]` test. You then run the `[USER]` tests yourself.

**Per-test mode.** Run individual tests by ID. Useful when only one layer is in question.

Tags:
- `[AI]` the AI runs this itself (tool call or shell command).
- `[LOCATE]` the AI verifies a file, config, or asks you to confirm a setting it cannot read.
- `[USER]` only you can run this (reboot, phone, hardware).

### The mega-prompt

```
Read healthtest.md from the workspace root. Run every test tagged [AI] or [LOCATE]. For each, report:
- test ID and name
- PASS or FAIL
- evidence (exact command output, tool result, or file content snippet, not a paraphrase)

For tests tagged [USER], list them with a one-line description so I can run them on my end.

End with a "## Summary" section: pass count out of total, the top 3 failures ranked by severity, and the single highest-leverage fix.

Do not skip tests. Do not summarize without evidence. If a tool errors, paste the error. If a file is missing, say so.
```

## Test inventory

| Layer | Tests | What it proves |
|---|---|---|
| Provider and model | T01 to T05 | GLM 5.2 reachable, config correct, long calls survive |
| MCP servers | T06 to T11 | Context7, Scrapling, SearXNG all wired and answering |
| Instruction files | T12 to T18 | claude.md, user.md, memory.md, .mcp.json all in place |
| Services and CLI | T19 to T23 | ripgrep, Docker, SearXNG container, Scrapling CLI all reachable |
| Remote access | T24 to T27 | Sunshine, Tailscale, config dirs, certs |
| Reboot persistence | T28 to T30 | autostart chain end-to-end |
| Ruleset behavior | T31 to T35 | claude.md actually governs voice and discipline |
| End-to-end | T36 | one real task that exercises everything |

Plus three user-only tests (U01 to U03) the AI cannot run.

---

## Layer 1 — Provider and model

### T01 — model identity `[AI]`
**Proves:** the model the harness thinks it is talking to is GLM 5.2.
**Prompt:** `What model are you, including version? One line.`
**Pass:** the answer names `GLM 5.2` or `glm-5.2`.
**Fail hint:** if it says Claude or Sonnet, the provider is not wired and the harness fell back to Anthropic.

### T02 — base URL is the bigmodel endpoint `[LOCATE]`
**Proves:** the provider is pointed at `open.bigmodel.cn/api/anthropic` (GUIDE.md step 2). The AI cannot read CodePilot's DB, but it can tell you what to confirm.
**Prompt:** `What base URL should I confirm in CodePilot Settings, Providers, for the z.ai entry? Tell me the exact URL and why it is the better default over the z.ai mirror.`
**Pass:** the answer includes `https://open.bigmodel.cn/api/anthropic` and cites the streaming argument from GUIDE.md step 0.
**Fail hint:** if it says `api.z.ai` is the primary, GUIDE.md step 0/14 is not loaded.

### T03 — API_TIMEOUT_MS `[LOCATE]`
**Proves:** the timeout env is set so long tool calls do not get cut off client-side.
**Prompt:** `What value should API_TIMEOUT_MS be set to in the provider's Extra Environment Variables, and where do I verify it?`
**Pass:** `3000000` or higher, in CodePilot, Settings, Providers, the z.ai entry, Extra Environment Variables.
**Fail hint:** if missing, long tool calls get cut off at the client, not at z.ai's edge (GUIDE.md step 14).

### T04 — thinking mode is MAX `[LOCATE]`
**Proves:** thinking is on MAX, the correct setting per GUIDE.md step 14.
**Prompt:** `What is the recommended thinking_mode setting for this stack, and what was the myth that made people turn it down?`
**Pass:** answer is MAX. The myth is "30s idle reset on z.ai" which was disproven by direct test on 2026-06-17 (235s silent generation on bigmodel, 190s on z.ai, both completed).
**Fail hint:** if the AI defends turning thinking down, claude.md or GUIDE.md step 14 is not loaded.

### T05 — long silent tool-call survival `[AI]`
**Proves:** a >30s silent tool-call generation actually completes, no client-side idle reset.
**Prompt:** `Search SearXNG for 5 distinct technical topics (your pick), fetch each result page with Scrapling, and summarize each in 2 sentences. Do not stream commentary, just call the tools in batch and report results when done.`
**Pass:** the AI completes the batch and returns 5 summaries with URLs.
**Fail hint:** if the stream cuts off mid-way with a "stream idle timeout" message, the client-side timeout layer is too low, see GUIDE.md step 14.

---

## Layer 2 — MCP servers

### T06 — Context7 `[AI]`
**Proves:** Context7 MCP is registered, can resolve libraries, can return docs.
**Prompt:** `Use Context7 to resolve the React library and pull the current docs for useEffect cleanup. Quote the exact code snippet from the docs and give the source URL.`
**Pass:** a real snippet about cleanup functions, a docs URL.
**Fail hint:** "no tool named resolve-library-id" means Context7 is not registered in CodePilot MCP page (GUIDE.md step 9, step 13).

### T07 — Scrapling fetch (the AP test) `[AI]`
**Proves:** Scrapling is installed with all five install lines done (`[fetchers]`, `scrapling install`, `[mcp]`, `markdownify`, Chromium browser), can fetch real-world pages via the default `get` tool, returns content not errors.
**Prompt:** `Fetch https://apnews.com/ using Scrapling's get tool. Pick any front-page article, follow the link, fetch the article with the get tool, and quote the first 3 sentences of the body verbatim. Give me the article URL so I can open it in a browser and verify your quote matches character-for-character. Do not use bulk_get as a workaround, the default get tool must work.`
**Pass:** a specific article URL, three sentences quoted exactly, the quote actually matches when you open the URL.
**Fail hints:**
- `ModuleNotFoundError: No module named 'mcp'`: run `pip install scrapling[mcp]`.
- `No module named 'markdownify'`: run `pip install markdownify`. The `bulk_get` tool works without it, which masks this bug, so the test explicitly forbids `bulk_get` as a workaround.
- `BrowserType.launch_persistent_context: Executable doesn't exist at ...ms-playwright/chromium-...`: run `playwright install chromium`. This is separate from `scrapling install` (which pulls Camoufox only, not Chromium).
- All three failure modes are covered in GUIDE.md step 10 (verified in the 2026-06-18 health test).

### T08 — SearXNG search `[AI]`
**Proves:** SearXNG is running, mcp-searxng is registered, the URL is the right port.
**Prompt:** `Use SearXNG to search for "Associated Press Israel Gaza October 2026". Return the top 5 results with title, URL, and snippet.`
**Pass:** 5 results with real URLs (apnews.com, reuters.com, bbc.com, etc).
**Fail hint:** `Invalid JSON format` means SEARXNG_URL points at the wrong port (GUIDE.md step 11, the 8080 gotcha).

### T09 — SearXNG instance info `[AI]`
**Proves:** same as T08 from a different angle, plus engine visibility.
**Prompt:** `Call searxng_instance_info and tell me which search categories are available, and which engines the general category uses.`
**Pass:** a list including general, images, news, it, etc.
**Fail hint:** same as T08.

### T10 — SearXNG web_url_read `[AI]`
**Proves:** the URL reader works even if search does not. It bypasses SearXNG, directly fetches.
**Prompt:** `Use web_url_read to fetch the full text of https://en.wikipedia.org/wiki/GLM_(language_model) and return the headings only.`
**Pass:** a list of section headings.
**Fail hints:**
- If this works but T08 fails, SearXNG itself is down (check `docker ps`), only the MCP's URL reader works.
- `MCP error -32603: Website Error (429): Rate limit exceeded` is transient, not a stack bug. Wikipedia and other big sources throttle aggressive fetchers. Retry with a less-busy URL (for example a MDN or IBM developer page), or wait a minute and try again. Do not "fix" this by changing SearXNG config.

### T11 — GitHub MCP (optional) `[AI]`
**Proves:** GitHub MCP is registered and the token works.
**Prompt:** `List my 3 most recently pushed repos.`
**Pass:** 3 real repo names you recognize.
**Fail hint:** if you skipped GitHub MCP (GUIDE.md step 12 marks it optional), skip this test.

---

## Layer 3 — Instruction files

For all tests in this layer, the AI should use the Read tool to open the file and report what it sees.

### T12 — claude.md `[LOCATE]`
**Proves:** the ruleset is at the workspace root and starts correctly.
**Prompt:** `Read E:/Logseq/claude.md (or your workspace root). Report: does it exist? What does the first line say? How many top-level sections does it have?`
**Pass:** exists. First line is `# Nonprofit Agent 操作准则`. 13 to 14 sections.
**Fail hint:** if missing, GUIDE.md step 4 was skipped.

### T13 — user.md filled `[LOCATE]`
**Proves:** user.md is not still the template.
**Prompt:** `Read E:/Logseq/user.md. Is it still the template, or is it filled in? Show me the "Who I am" section.`
**Pass:** real name, role, languages. Not the blank template.
**Fail hint:** if template, GUIDE.md step 5 was skipped.

### T14 — soul.md `[LOCATE]`
**Proves:** soul.md exists. Optional but should not be missing or bloated.
**Prompt:** `Read E:/Logseq/soul.md. Report the first line.`
**Pass:** exists. Content is one short paragraph or one line, not duplicating claude.md.
**Fail hint:** if it has a long persona block duplicating claude.md, it was not pruned in the 2026-06-18 rewrite.

### T15 — memory system (both of them) `[LOCATE]`
**Proves:** both memory systems are set up. This stack has two, they serve different purposes:
- **Manual Logseq memory** at `E:/Logseq/memory.md` + `E:/Logseq/memory/`: the cave-speak convention from `claude.md` section 11, you write it manually as a durable rule.
- **Harness auto-memory** at `C:/Users/<you>/.claude/projects/<workspace-slug>/memory/MEMORY.md` + `.../memory/`: the harness's own memory system, the AI writes via tools, the index is loaded into every session's context.

**Prompt:** `Check both memory systems. First: does E:/Logseq/memory.md exist and does E:/Logseq/memory/ have any files in it? Show the first 10 lines of memory.md. Second: does the harness auto-memory directory at C:/Users/Anira/.claude/projects/E--Logseq/memory/ exist? List its files and show the first 10 lines of MEMORY.md if present.`
**Pass:** both directories exist. At least one has actual entries (not just the template header).
**Fail hints:**
- Logseq `memory.md` is just the template header: GUIDE.md step 7 was set up but you have not written any entries yet. Not broken, just empty.
- Harness auto-memory directory missing: the harness has not been initialized on this workspace yet. Run the AI once and have it save a memory entry to create the directory.
- If the AI's T31 write test lands in the harness auto-memory path, that is correct, not a bug. The Logseq manual memory is for you, the harness auto-memory is for the AI.

### T16 — .mcp.json at workspace root `[LOCATE]`
**Proves:** the project-level MCP config is in place (best-effort fallback, GUIDE.md step 13).
**Prompt:** `Read E:/Logseq/.mcp.json. Show me its full content. Does it have context7, scrapling, and searxng servers?`
**Pass:** all three servers listed, searxng URL on port 8888.
**Fail hint:** if searxng is on 8080, the file drifted from GUIDE.md step 11 (the exact issue documented in the 2026-06-18 fix).

### T17 — HEARTBEAT.md `[LOCATE]`
**Proves:** the heartbeat file exists.
**Prompt:** `Read E:/Logseq/HEARTBEAT.md. Report the first line.`
**Pass:** exists.
**Fail hint:** CodePilot usually scaffolds this automatically. If missing, CodePilot was not launched on this workspace yet (GUIDE.md step 3).

### T18 — .claude/settings.json `[LOCATE]`
**Proves:** the optional hooks config exists.
**Prompt:** `Check if E:/Logseq/.claude/settings.json exists. If yes, show the hooks block.`
**Pass:** exists with the git push PreToolUse hook, or the AI reports it is not present (which is fine, it is optional per GUIDE.md step 19).
**Fail hint:** if you want hooks to gate pushes, it needs to exist.

---

## Layer 4 — Services and CLI

### T19 — ripgrep `[AI]`
**Proves:** rg is on PATH.
**Prompt:** `Run \`rg --version\` and report the version.`
**Pass:** a version string like `ripgrep 14.x.x`.
**Fail hint:** GUIDE.md step 8 was skipped.

### T20 — Docker engine `[AI]`
**Proves:** Docker is running.
**Prompt:** `Run \`docker ps\` and report the output.`
**Pass:** a table of containers (even empty is OK, as long as no error).
**Fail hint:** "Docker daemon not running" means Docker Desktop is not started.

### T21 — SearXNG container `[AI]`
**Proves:** the searxng container is up and on the right port.
**Prompt:** `Run \`docker ps --filter name=searxng --format "{{.Names}} {{.Status}} {{.Ports}}"\` and report.`
**Pass:** one line showing `searxng Up ...`, port mapping `0.0.0.0:8888->8080/tcp`.
**Fail hint:** GUIDE.md step 11 command was not run, or run on the wrong port.

### T22 — SearXNG returns JSON `[AI]`
**Proves:** the JSON API is enabled, not just HTML.
**Prompt:** `Run \`curl -s "http://127.0.0.1:8888/search?q=test&format=json" | head -c 200\` and report what you see.`
**Pass:** JSON starting with `{"query":`.
**Fail hint:** if HTML, the settings.yml on the container does not have `json` in formats, or the port is wrong (GUIDE.md step 11).

### T23 — Scrapling mcp loads `[AI]`
**Proves:** the `mcp` module is installed (the GUIDE.md step 10 gotcha).
**Prompt:** `Run \`scrapling mcp --help\` and report the first 5 lines.`
**Pass:** a usage line, no traceback.
**Fail hint:** if `ModuleNotFoundError: No module named 'mcp'`, run `pip install scrapling[mcp]`.

---

## Layer 5 — Remote access

### T24 — Sunshine service `[AI]`
**Proves:** Sunshine is installed as a Windows service and set to Automatic.
**Prompt:** `Run \`sc query SunshineService 2>&1 | head -10 ; sc qc SunshineService 2>&1 | grep -i start_type\` and report.`
**Pass:** service exists, state `RUNNING`, `START_TYPE : 2 AUTO_START`.
**Fail hint:** GUIDE.md step 17 was not completed, or service set to Manual.

### T25 — Tailscale up `[AI]`
**Proves:** Tailscale is running and the host is on the tailnet.
**Prompt:** `Run \`tailscale status 2>&1 | head -5 ; tailscale ip -4 2>&1\` and report.`
**Pass:** a list of peers and a `100.x.x.x` IP for this host.
**Fail hint:** tailscale service not started, or not signed in.

### T26 — Sunshine config dir `[LOCATE]`
**Proves:** Sunshine has been initialized (creates the config dir on first run).
**Prompt:** `Sunshine's config dir is install-location-dependent, not always C:/ProgramData/Sunshine. First find the service binary path with \`sc qc SunshineService 2>&1 | grep -i binary_path_name\`, then check the sibling config dir (typically <install-dir>/config/). Also check the default C:/ProgramData/Sunshine/ in case the installer used it. Report which path actually has the config and what files are in it.`
**Pass:** one of the candidate paths has `sunshine.conf`, `apps.json` (or an `apps/` folder), and a `credentials/` subfolder with `cacert.pem` + `cakey.pem`.
**Fail hint:** if neither candidate path has those files, Sunshine was installed but never launched to setup. Run the Sunshine UI once to trigger initial config generation, or check `sunshine.log` in the install dir for startup errors (GUIDE.md step 17).

### T27 — Tailscale IP known and stable `[AI]`
**Proves:** you have the IP to give Moonlight.
**Prompt:** `Run \`tailscale ip -4\` and tell me the IP.`
**Pass:** a `100.x.x.x` address.
**Fail hint:** see T25.

---

## Layer 6 — Reboot persistence

### T28 — Docker autostart `[AI]`
**Proves:** Docker engine comes back at login.
**Prompt:** `Run \`python -c "import json; print('AutoStart =', json.load(open(r'C:/Users/Anira/AppData/Roaming/Docker/settings-store.json'))['AutoStart'])"\` and report.`
**Pass:** `AutoStart = True`.
**Fail hint:** Docker Desktop, Settings, General, tick "Start Docker Desktop when you sign in to your computer" (GUIDE.md step 18).

### T29 — Docker UI does not pop at login `[LOCATE]`
**Proves:** "Use Docker Desktop in background by default" / "Open Docker Dashboard when Docker Desktop starts" is correctly configured so only the engine loads, not the window.
**Prompt:** `Ask the user to confirm: in Docker Desktop, Settings, General, is "Open Docker Dashboard when Docker Desktop starts" unchecked (or "Use Docker Desktop in background by default" ticked)? Report their answer.`
**Pass:** user confirms the dashboard does not pop on login.
**Fail hint:** uncheck the dashboard-at-start box manually in Docker Desktop, Settings, General, Apply and restart (GUIDE.md step 18).

### T30 — CodePilot autostart `[AI]`
**Proves:** CodePilot is in the user Run key so it launches at login.
**Prompt:** `Run this literal command and report its output: \`reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v CodePilot\`. Do NOT substitute PowerShell cmdlets like \`Get-ItemProperty\` or \`Get-Item\`, they return empty in some agent shell contexts and produce false negatives even when the registry entry exists. Use the cmd \`reg query\` form.`
**Pass:** output shows `<key path>` then a line with `CodePilot REG_SZ "C:\path\to\CodePilot.exe"`.
**Fail hint:** if `reg query` (the cmd form, not PowerShell) returns "not found", run the GUIDE.md step 18 `reg add` command.

---

## Layer 7 — Ruleset actually governs

### T31 — compressed Chinese memory `[AI]`
**Proves:** claude.md section 11 (memory in cave-speak) is loaded.
**Prompt:** `Save a test memory with content "test health check 2026-06-18: stack running" using cave-speak compression, append-only.`
**Pass:** memory entry appended to `memory.md` or a new file in `memory/`, in compressed Chinese.
**Fail hint:** if it writes a long English paragraph, claude.md section 11 is not being followed.

### T32 — no em dashes `[AI]`
**Proves:** claude.md section 1 (voice) is loaded.
**Prompt:** `Explain in 4 sentences why \`pip install scrapling[mcp]\` is needed.`
**Pass:** no em dashes anywhere in the answer.
**Fail hint:** if em dashes appear, claude.md is not being followed, or claude.md is missing.

### T33 — confirmed vs inferred labels `[AI]`
**Proves:** claude.md section 8 (verify before claim) is loaded.
**Prompt:** `Is the Sunshine service set to Automatic? Report with the confirmed/inferred label and evidence.`
**Pass:** the answer uses labels (or clearly separates confirmed vs inferred), cites the command it ran or the file it read.
**Fail hint:** if the AI just says "yes" without evidence or label, claude.md section 8 is not loaded.

### T34 — web-verify discipline `[AI]`
**Proves:** claude.md section 4 (web-verify) is loaded.
**Prompt:** `What is the latest Node.js LTS version as of today?`
**Pass:** the AI searches (SearXNG or Scrapling) rather than answering from memory, and cites a recent source with a URL.
**Fail hint:** if it answers from memory without a search, section 4 is not being followed.

### T35 — tool-call intent line `[USER]`
**Proves:** claude.md section 3 (tool-call hygiene) is loaded. The user watches the AI's behavior during the whole test.
**Pass:** before every batch of tool calls, the AI emits one sentence of intent.
**Fail hint:** if the AI goes silent for 30s+ then dumps a batch of tool calls, section 3 is not being followed.

---

## Layer 8 — End-to-end

### T36 — full research pipeline `[AI]`
**Proves:** the stack can do a real task end-to-end.
**Prompt:**
```
Find an Associated Press article from the last 7 days on any topic. Use SearXNG to find it, Scrapling to fetch the full text. Quote the lede paragraph verbatim. Save a cave-speak memory entry summarizing the article in one line with the URL. Give me the URL so I can verify the quote.
```
**Pass:**
- a real AP URL from the last 7 days
- a verbatim quote that matches when you open the URL
- a memory entry appended to `memory.md` or `memory/`
- the memory entry is compressed Chinese with the English URL preserved
**Fail hint:** isolate which step failed by re-running the matching single test (T07, T08, T10, T31).

---

## User-only tests

These cannot be run by the AI. Do them yourself after the AI-run tests pass.

### U01 — reboot persistence end-to-end
Reboot the host. Do not log in for a minute. Log in via Moonlight from your phone on cellular (or walk to the machine).
**Pass:** desktop comes up. CodePilot icon in tray. Docker engine running. SearXNG responds on `127.0.0.1:8888`.
**Fail hint:** whichever layer did not come back, check its autostart config (GUIDE.md step 18).

### U02 — remote access from phone
On your phone, disconnect from WiFi (use cellular). Open Moonlight. Tap the host.
**Pass:** full desktop appears. You can click around.
**Fail hint:** if the host does not show up, Tailscale is not running on the host or phone. If it shows up but pairing fails, follow GUIDE.md step 17 troubleshooting (delete `cacert.pem` and `cakey.pem` in `%ProgramData%\Sunshine`, restart the service, pair again).

### U03 — Telegram bridge (if enabled)
Message your bot. Approve an action from the phone.
**Pass:** the bot responds, the approval flow works.
**Fail hint:** GUIDE.md step 16 was skipped or the chat id allowlist is wrong.

---

## Final checklist

- [ ] T01 to T36 all pass.
- [ ] U01 to U03 all pass.

If anything fails, fix the highest-severity failure first, not the easiest one. Severity order:
1. Provider and model broken (T01 to T05) — nothing else works, fix this first.
2. Ruleset not loaded (T31 to T35) — the AI will drift without you noticing.
3. MCP broken (T06 to T11) — partial capability, research is degraded.
4. Services and persistence (T19 to T30) — works now, breaks on reboot.
5. Files (T12 to T18) — usually a one-copy fix.

When the whole checklist is green, the stack is verified end-to-end. Do not call it working until you have done U01 (the actual reboot).
