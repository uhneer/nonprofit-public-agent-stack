# Eigent Health Test

End-to-end verification that every layer of the Eigent + GLM-5.2 + MCP stack actually works. Built specifically for the Eigent harness (not CodePilot, not Claude Code). Run this after a fresh install, after migrating from another harness, after an OS update or machine rebuild, after a major config change, or any time something feels off. Each test has an ID, one thing it proves, the prompt or command, the pass criterion, and the failure hint pointing back to GUIDE.md.

## How to use this file

Two modes.

**Single-prompt mode (recommended).** Open a fresh Eigent chat on the bound workspace (E:/Logseq) and paste the mega-prompt below. The agent runs every `[AI]` test, locates every `[LOCATE]` test, and lists every `[USER]` test. You then run the `[USER]` tests yourself.

**Per-test mode.** Run individual tests by ID. Useful when only one layer is in question.

Tags:
- `[AI]` the agent runs this itself (tool call, shell command via `shell_exec`, or MCP call).
- `[LOCATE]` the agent verifies a file, config, or asks you to confirm a setting it cannot read directly.
- `[USER]` only you can run this (reboot, phone, hardware, GUI confirmation).

### The mega-prompt

```
Read healthtest.md from the workspace root. Run every test tagged [AI] or [LOCATE]. For each, report:
- test ID and name
- PASS or FAIL
- evidence (exact command output, tool result, or file content snippet, not a paraphrase)

For tests tagged [USER], list them with a one-line description so I can run them on my end.

End with a "## Summary" section: pass count out of total, the top 3 failures ranked by severity, and the single highest-leverage fix.

Do not skip tests. Do not summarize without evidence. If a tool errors, paste the error. If a file is missing, say so. Use the MCP stack (searxng, scrapling, context7, github, supabase) for any web, docs, or external work; never use built-in search_google or web_fetch.
```

## Test inventory

| Layer | Tests | What it proves |
|---|---|---|
| Preflight | T00 | MCP tools actually loaded into agent surface (gates all MCP-dependent tests) |
| Provider and model | T01 to T05 | GLM-5.2 reachable, Eigent wired, thinking inherited, long calls survive |
| MCP servers | T06 to T12 | Context7, Scrapling, SearXNG, GitHub, Supabase all wired and answering |
| Prompt and instruction files | T13 to T18 | Patched prompt.py live, ruleset file in place, memory + workspace bound |
| Services and CLI | T19 to T24 | Code search, Docker, SearXNG container, Scrapling CLI, Eigent backend |
| Remote access | T25 to T28 | Sunshine, Tailscale, config dirs, certs |
| Eigent capabilities | T29 to T32 | Skills, notes, run_remote_sub_agent, multi-agent fan-out |
| Reboot persistence | T33 to T35 | Autostart chain end-to-end |
| Ruleset actually governs | T36 to T42 | Ruleset actually shapes voice, routing, and discipline |
| End-to-end | T43 | One real task that exercises everything |

Plus four user-only tests (U01 to U04) the agent cannot run.

---

## Layer 0 — Preflight (run first, abort on fail)

### T00 — MCP tools actually in agent surface `[AI]`
**Proves:** the MCP servers registered in `~/.eigent/mcp.json` are loaded into the agent's tool surface for this chat. This is the meta-test that gates T04, T06-T12, T30-T32, T39, T41, T43. Without this pass, those tests are unrunnable and reporting UNVERIFIABLE.
**Prompt:** `List every tool you currently have access to, one per line, alphabetical order. Do not paraphrase tool names. Include MCP tools (searxng, scrapling, context7, github, supabase) if they are loaded.`
**Pass:** the list includes at least one of `searxng_web_search` / `searxng_instance_info` / `web_url_read`, at least one `scrapling_*` tool, and `resolve-library-id` (Context7). Bonus: `mcp__github__*` and `mcp__supabase__*` families if those servers are enabled.
**Fail hint:** if the list contains only `shell_exec`, `read_file`, `edit_file`, `write_to_file`, `browser_*`, `list_skills`, `load_skill`, `agent_run_subagent` and no MCP tools, Eigent's `installed_mcp` field is empty. Root cause: `~/.eigent/mcp.json` has the servers registered but the per-chat install action never fired (`chat_service.py:2090-2101`), OR the `toolkit_assembler.py` disk-config bridge patch is missing (see GUIDE.md step 13b, PATCHES.md). Fix without the patch: Eigent UI → MCP / Connectors panel → toggle each server off and on, or click install → start a fresh chat. May require full Eigent tray restart. Do NOT continue the healthtest until this passes; every downstream MCP-dependent test will report UNVERIFIABLE otherwise.

---

## Layer 1 — Provider and model

### T01 — model identity `[AI]`
**Proves:** the model Eigent thinks it is talking to is GLM-5.2.
**Prompt:** `What model are you, including version and provider? One line.`
**Pass:** the answer names `GLM-5.2` or `glm-5.2`. May also mention Eigent, CAMEL, or Single Agent role.
**Fail hint:** if it says Claude, Sonnet, Opus, or GPT, the provider is not wired and Eigent fell back to a default. Check Settings → Models → Anthropic card is set to Prefer.

### T02 — Eigent provider config `[LOCATE]`
**Proves:** the Anthropic card in Eigent is pointed at the bigmodel.cn endpoint with the right model. The agent cannot read Eigent's settings DB, but it can tell you what to confirm.
**Prompt:** `What should I confirm in Eigent Settings → Models → Anthropic card? Tell me the exact API Host, API Key prefix (first 8 chars only), Model Type, and whether Prefer is toggled on. Explain why bigmodel.cn over the z.ai mirror.`
**Pass:** the answer includes `https://open.bigmodel.cn/api/anthropic`, Model Type `glm-5.2`, Prefer is on, and cites the streaming reliability argument from GUIDE.md (bigmodel.cn is the upstream, z.ai mirror has shown transient issues).
**Fail hint:** if the agent says `api.z.ai` is the primary, GUIDE.md step on provider setup is not loaded.

### T03 — thinking inherited from Coding Plan endpoint `[AI]`
**Proves:** thinking is on by default via the Coding Plan endpoint, interleaved thinking between tool calls is active, and preserved thinking keeps reasoning coherent across turns (the Zhipu-documented default for Coding Plan users).
**Prompt:** `Are you currently in thinking mode? Can you reason between tool calls (interleaved thinking)? Briefly describe how reasoning shows up in your responses, and whether reasoning_content is preserved across turns.`
**Pass:** the agent confirms thinking is on, describes interleaved reasoning (reasoning steps visible between tool calls), and references preserved reasoning across turns.
**Fail hint:** if the agent reports thinking is off or shows no reasoning, the Coding Plan endpoint is not being used. Check that API Host is the bigmodel.cn `/api/anthropic` path, not a generic OpenAI-compatible path.

### T04 — long silent tool-call survival `[AI]`
**Proves:** a >30s silent tool-call generation actually completes, no client-side idle reset.
**Prompt:** `Search SearXNG for 5 distinct technical topics (your pick), fetch each result page with Scrapling, and summarize each in 2 sentences. Do not stream commentary, just call the tools in batch and report results when done.`
**Pass:** the agent completes the batch and returns 5 summaries with URLs.
**Fail hint:** if the stream cuts off mid-way with a "stream idle timeout" message, the client-side timeout layer is too low. The fix is in CAMEL's Anthropic client, not at z.ai's edge. See GUIDE.md step 14.

### T05 — agent operates inside bound workspace `[AI]`
**Proves:** the environment_hands.py patch is live and the agent can read/write inside E:/Logseq/ (and the broader E:/ drive).
**Prompt:** `List the first 10 entries in E:/Logseq/ and tell me whether E:/Eigent-source/ is also readable. Report the exact entries.`
**Pass:** real entries from E:/Logseq/ (claude.md, healthtest.md, memory/, etc.) and confirmation that E:/ is in scope.
**Fail hint:** if the agent reports `not available to this Brain` or similar, the environment_hands.py patch is not loaded (see GUIDE.md step 13b, PATCHES.md). Restart Eigent from the system tray to pick up the patched backend, then re-run.

---

## Layer 2 — MCP servers

### T06 — Context7 `[AI]`
**Proves:** Context7 MCP is registered, can resolve libraries, can return docs.
**Prompt:** `Use Context7 to resolve the React library and pull the current docs for useEffect cleanup. Quote the exact code snippet from the docs and give the source URL.`
**Pass:** a real snippet about cleanup functions, a docs URL.
**Fail hint:** `no tool named resolve-library-id` means Context7 is not imported into Eigent, OR the disk-config bridge patch is missing (T00 fail hint). Re-import via Connectors → MCP → Add → Local JSON.

### T07 — Scrapling fetch (the AP test) `[AI]`
**Proves:** Scrapling is installed with all five install lines done (`[fetchers]`, `scrapling install`, `[mcp]`, `markdownify`, Chromium browser), can fetch real-world pages via the default `get` tool, returns content not errors.
**Prompt:** `Fetch https://apnews.com/ using Scrapling's get tool. Pick any front-page article, follow the link, fetch the article with the get tool, and quote the first 3 sentences of the body verbatim. Give me the article URL so I can open it in browser and verify your quote matches character-for-character. Do not use bulk_get as a workaround, the default get tool must work.`
**Pass:** a specific article URL, three sentences quoted exactly, the quote actually matches when you open the URL.
**Fail hints:**
- `ModuleNotFoundError: No module named 'mcp'`: run `pip install scrapling[mcp]`.
- `No module named 'markdownify'`: run `pip install markdownify`. The `bulk_get` tool works without it, which masks this bug, so the test explicitly forbids `bulk_get` as a workaround.
- `BrowserType.launch_persistent_context: Executable doesn't exist at ...ms-playwright/chromium-...`: run `playwright install chromium`. This is separate from `scrapling install` (which pulls Camoufox only, not Chromium).
- All three failure modes are covered in GUIDE.md step 10.

### T08 — SearXNG search `[AI]`
**Proves:** SearXNG is running, mcp-searxng is registered, the URL is the right port.
**Prompt:** `Use SearXNG to search for "Associated Press Israel Gaza October 2026". Return the top 5 results with title, URL, and snippet.`
**Pass:** 5 results with real URLs (apnews.com, reuters.com, bbc.com, etc).
**Fail hint:** `Invalid JSON format` means SEARXNG_URL points at the wrong port (should be 8888).

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
- `MCP error -32603: Website Error (429): Rate limit exceeded` is transient, not a stack bug. Retry with a less-busy URL (for example a MDN or IBM developer page), or wait a minute and try again.

### T11 — GitHub MCP `[AI]`
**Proves:** GitHub MCP is registered and the token works.
**Prompt:** `Use the GitHub MCP to list my 3 most recently pushed repos.`
**Pass:** 3 real repo names you recognize.
**Fail hint:** if you skipped GitHub MCP (GUIDE.md marks it optional), skip this test. Otherwise check `GITHUB_PERSONAL_ACCESS_TOKEN` is set in the MCP import.

### T12 — Supabase MCP (optional) `[AI]`
**Proves:** Supabase MCP is registered and the token works.
**Prompt:** `Use the Supabase MCP to list my projects (or whatever the equivalent list call is). If you cannot, say so explicitly.`
**Pass:** a list of projects, or an explicit "no projects found" that confirms auth works.
**Fail hint:** if you skipped Supabase MCP, skip this test. Otherwise re-check `SUPABASE_ACCESS_TOKEN`. If the tool errors with `Session terminated`, you are using the remote OAuth-only endpoint instead of the local stdio server. See GUIDE.md step 12b.

---

## Layer 3 — Prompt and instruction files

For tests in this layer, the agent should use `shell_exec` (or equivalent terminal tool) to read the file and report what it sees. Eigent does not have a dedicated Read tool the way Claude Code does; `shell_exec` with `cat`/`head` is the path.

### T13 — patched prompt.py is live (5-agent stack) `[LOCATE]`
**Proves:** the `<anir_operating_rules>` block is in Eigent's prompt.py with §0-§14 (no §15, that was moved to COORDINATOR). Plus a dedicated `COORDINATOR_SYS_PROMPT` constant exists with pipeline order + dispatch contract + synthesis rules.
**Prompt:** `Open E:/Eigent/resources/backend/app/agent/prompt.py. Report: (a) line where SINGLE_AGENT_SYS_PROMPT is defined, (b) line where the <anir_operating_rules> block opens inside it, (c) highest section number inside that block (should be §14, NOT §15), (d) line where COORDINATOR_SYS_PROMPT is defined as a separate constant, (e) does COORDINATOR_SYS_PROMPT contain a <pipeline_order> tag? (f) does it contain a <dispatch_contract> tag?`
**Pass:** (a) SINGLE_AGENT_SYS_PROMPT around line 566, (b) `<anir_operating_rules>` opens ~line 608, (c) highest section is §14 (§15 was extracted to COORDINATOR), (d) `COORDINATOR_SYS_PROMPT` defined around line 714, (e) yes `<pipeline_order>` present, (f) yes `<dispatch_contract>` present.
**Fail hint:** if §15 is still inside SINGLE_AGENT, the extraction didn't apply. If COORDINATOR_SYS_PROMPT is missing entirely, the patch is stale or wasn't applied. Re-apply from prompt.py.bak-equivalent state. See PATCHES.md.

### T13b — chat_service.py wires Coordinator correctly `[LOCATE]`
**Proves:** the coordinator_agent enum slot uses COORDINATOR_SYS_PROMPT (wrapped in BaseMessage with role_name="Coordinator"), and the 4 workforce worker descriptions match the new role names (Implementer/Researcher/Subject Analyst/Verifier) so Coordinator routes correctly.
**Prompt:** `Open E:/Eigent/resources/backend/app/service/chat_service.py. Report: (a) is COORDINATOR_SYS_PROMPT imported from app.agent.prompt? (b) is BaseMessage imported from camel.messages? (c) in _create_coordinator_and_task_agents, is the coordinator prompt wrapped in BaseMessage.make_assistant_message(role_name="Coordinator", ...)? (d) search for "add_single_agent_worker" calls in construct_workforce — do the description strings contain "Implementer", "Researcher", "Subject Analyst", and "Verifier"?`
**Pass:** all four checks yes. Old strings "Developer Agent: master-level coding" / "Browser Agent: can search the web" / "Document Agent: document processing" / "Multi-Modal Agent: media processing" must NOT appear.
**Fail hint:** if old description strings are still there, Coordinator will route wrong (it'll think it has a media agent when it really has a Verifier). Re-apply the worker-description rewrite in PATCHES.md.

### T13c — MCP disk-config bridge in toolkit_assembler `[LOCATE]`
**Proves:** MCPs added via Eigent UI (which writes to `~/.eigent/mcp.json`) actually reach the agent's tool surface. The bridge in `toolkit_assembler._mcp_config` merges disk config as fallback when `options.installed_mcp` is empty (the gap that caused MCP tools to be UNAVAILABLE in earlier runs).
**Prompt:** `Open E:/Eigent/resources/backend/app/agent/factory/toolkit_assembler.py. Report: (a) is read_mcp_config imported from app.service.mcp_config? (b) inside _mcp_config function, is there a try/except block that calls read_mcp_config() and assigns the result to disk_servers? (c) is the merge logic "servers = {**disk_servers, **options_servers}" (disk fills missing, options win on conflict)? (d) in the MCPToolkit.connect() error handler, are the configured server names logged in the error message (not just "Failed to connect MCPToolkit")?`
**Pass:** all four checks yes.
**Fail hint:** if the bridge is missing, MCPs added via UI won't reach agent runs even after restart. Re-apply from PATCHES.md. If error logging is still generic, silent MCP failures will recur.

### T13d — sanitizer interception in listen_chat_agent `[LOCATE]`
**Proves:** GLM's null/empty-string emissions in MCP tool kwargs are intercepted before the tool runs. Without this, MCP tools that reject null values fail silently. The patch wraps `async_call` (not just `__call__`) because the agent calls `tool.func.async_call` directly (listen_chat_agent.py:617), bypassing `FunctionTool.__call__`.
**Prompt:** `Open E:/Eigent/resources/backend/app/agent/listen_chat_agent.py. Report: (a) does _aexecute_tool route through a sanitizer that strips null/empty-string kwargs? (b) does the sanitizer wrap async_call, not just __call__? (c) when a tool name is hallucinated (not in self._internal_tools), does the method return a graceful error result instead of raising KeyError?`
**Pass:** all three checks yes.
**Fail hint:** if hallucinated tool names still crash the turn, the _aexecute_tool pre-check patch is missing. Re-apply from PATCHES.md.

### T14 — claude.md at workspace root `[LOCATE]`
**Proves:** the ruleset source file is at the workspace root and starts correctly.
**Prompt:** `Read E:/Logseq/claude.md. Report: does it exist? What does the first line say? How many top-level sections does it have?`
**Pass:** exists. First line is `# Nonprofit Agent 操作准则`. 13 to 14 sections (§0 through §13).
**Fail hint:** if missing, the workspace wasn't initialized correctly.

### T15 — user.md filled `[LOCATE]`
**Proves:** user.md is not still the template.
**Prompt:** `Read E:/Logseq/user.md. Is it still the template, or is it filled in? Show me the "Who I am" section.`
**Pass:** real name (Anir), real role, real languages. Not the blank template.
**Fail hint:** if template, GUIDE.md step on user.md was skipped.

### T16 — memory system `[LOCATE]`
**Proves:** the Logseq manual memory system is set up. (Eigent doesn't have CodePilot's auto-memory at `C:/Users/.../.claude/projects/...`; agent memory in Eigent lives in `append_note` / `shared_files` notes, tested separately in T30.)
**Prompt:** `Check the memory system. Does E:/Logseq/memory.md exist? Does E:/Logseq/memory/ have files in it? Show the first 10 lines of memory.md.`
**Pass:** both exist. At least one has actual entries (not just the template header).
**Fail hints:**
- Logseq `memory.md` is just the template header: not broken, just empty.
- Directory missing: workspace setup wasn't completed.

### T17 — .mcp.json at workspace root `[LOCATE]`
**Proves:** the project-level MCP config is in place.
**Prompt:** `Read E:/Logseq/.mcp.json. Show me its full content. Does it have context7, scrapling, searxng, github, and supabase servers?`
**Pass:** all five servers listed, searxng URL on port 8888.
**Fail hint:** if searxng is on 8080, the file drifted from the GUIDE.md canonical port. Also: even if the file is correct, you still need to import it into Eigent via Connectors → MCP → Add → Local JSON; the file alone does not register MCPs with Eigent (the disk-config bridge in T13c is the fallback when installed_mcp is empty).

### T18 — workspace folder bound to Eigent `[LOCATE]`
**Proves:** E:/Logseq is bound as a Brain/space in Eigent and the agent can actually read files there.
**Prompt:** `Try to list files in E:/Logseq/. If the agent reports the folder is not available, that fails this test. Report the actual entries.`
**Pass:** real entries from E:/Logseq/ without "not available" errors.
**Fail hint:** if `That folder is not available to this Brain`, the environment_hands.py patch isn't applied (see T05) OR the folder was never bound via Create space → Use local folder → E:/Logseq.

---

## Layer 4 — Services and CLI

### T19 — ripgrep installed and preferred `[AI]`
**Proves:** `rg.exe` (ripgrep 15.1.0+) is on PATH and the agent prefers it over plain `grep` per the patched ruleset §4 ("ripgrep 15.1.0 已装, 优先 `rg --json` 结构化输出").
**Prompt:** `Run "rg --version" and report the version. Then run "rg --json TODO E:/Eigent/resources/backend/app/agent/prompt.py" (or any small file) and report whether you get structured JSON output. Also run "where rg" to confirm the binary is on PATH.`
**Pass:** (a) `rg --version` reports version 15.1.0 or higher, AND (b) `rg --json` produces structured JSON output (parseable, contains `"type":"match"` entries or empty array if no matches), AND (c) `where rg` resolves to a real .exe path.
**Fail hint:** if `rg` is missing, install via `winget install BurntSushi.ripgrep.MSVC`. If installed but `where rg` can't find it, the winget Links directory (`C:/Users/Anira/AppData/Local/Microsoft/WinGet/Links`) is not on PATH, add it.

### T19b — fd and jq must NOT be expected `[AI]`
**Proves:** the agent knows its real tool surface. Per the patched ruleset §4: "`fd` 未装, 目录遍历用 `find`. `jq` 未装, JSON 处理用 Python `json` 模块 via shell_exec." The agent should NOT silently fall back to pretending these exist.
**Prompt:** `Run "where fd" and "where jq". Report exactly what you see. If both return "INFO: Could not find files..." or equivalent "not found", that is correct and expected. Then describe what you would use instead for (a) finding files by name pattern, (b) parsing JSON from a shell pipe.`
**Pass:** (a) `where fd` reports not found, AND (b) `where jq` reports not found, AND (c) the agent's alternatives are `find` (for file lookup) and Python `json` module via shell_exec (for JSON parsing). Bonus: agent explicitly cites §4 of the ruleset.
**Fail hint:** if `fd` or `jq` IS installed, the §4 rule is stale. Update prompt.py to reflect what's actually on PATH. If the agent tries to use `fd`/`jq` and fails, it ignored the §4 rule.

### T20 — Docker engine `[AI]`
**Proves:** Docker is running.
**Prompt:** `Run `docker ps` and report the output.`
**Pass:** a table of containers (even empty is OK, as long as no error).
**Fail hint:** "Docker daemon not running" means Docker Desktop is not started.

### T21 — SearXNG container `[AI]`
**Proves:** the searxng container is up and on the right port.
**Prompt:** `Run `docker ps --filter name=searxng --format "{{.Names}} {{.Status}} {{.Ports}}"` and report.`
**Pass:** one line showing `searxng Up ...`, port mapping `0.0.0.0:8888->8080/tcp`.
**Fail hint:** GUIDE.md step on SearXNG setup was not run, or run on the wrong port.

### T22 — SearXNG returns JSON `[AI]`
**Proves:** the JSON API is enabled, not just HTML.
**Prompt:** `Run `curl -s "http://127.0.0.1:8888/search?q=test&format=json" | head -c 200` and report what you see.`
**Pass:** JSON starting with `{"query":`.
**Fail hint:** if HTML, the settings.yml on the container does not have `json` in formats, or the port is wrong.

### T23 — Scrapling mcp loads `[AI]`
**Proves:** the `mcp` module is installed (the GUIDE.md gotcha).
**Prompt:** `Run `scrapling mcp --help` and report the first 5 lines.`
**Pass:** a usage line, no traceback.
**Fail hint:** if `ModuleNotFoundError: No module named 'mcp'`, run `pip install scrapling[mcp]`.

### T24 — Eigent backend health (embedded OR Docker) `[AI]`
**Proves:** at least one Eigent backend is up and responding. Either backend can serve agent traffic.
**Prompt:** `Probe both backends with retries to handle the boot-time race. Run this in bash:
`for port in 5001 3001; do for i in 1 2 3 4 5; do code=$(curl -s -o /dev/null -w "%{http_code}" -m 2 http://127.0.0.1:$port/health 2>/dev/null); echo "port=$port attempt=$i code=$code"; [ "$code" = "200" ] && break; sleep 3; done; done`
Report every line printed. Then state explicitly: did ANY port reach HTTP 200?`
**Pass:** at least one of 5001 (embedded backend, ships with desktop app) OR 3001 (Docker backend) reaches HTTP 200.
**False negative warning:** the embedded backend on 5001 takes 5-30s to come up after Eigent desktop launch. A cold-run healthtest that fires during that window will see port 5001 dead even though the backend is fine. The retry loop above eliminates this race by waiting up to 15s per port before declaring failure. If you still see all-zero codes after the retries, the desktop genuinely didn't start the backend; tray-quit + restart Eigent. If only 3001 is up (Docker backend works, embedded doesn't), agent traffic still flows and this test PASSES, the Docker backend is a valid substitute.
**Fail hint:** all 10 attempts (5 per port) returned `code=000` means neither backend is running. Start Eigent desktop OR `docker compose up eigent_api` from the repo.

---

## Layer 5 — Remote access

### T25 — Sunshine service `[AI]`
**Proves:** Sunshine is installed as a Windows service and set to Automatic.
**Prompt:** `Run `sc query SunshineService 2>&1 | head -10 ; sc qc SunshineService 2>&1 | grep -i start_type` and report.`
**Pass:** service exists, state `RUNNING`, `START_TYPE : 2 AUTO_START`.
**Fail hint:** GUIDE.md step on Sunshine setup was not completed, or service set to Manual.

### T26 — Tailscale up `[AI]`
**Proves:** Tailscale is running and the host is on the tailnet.
**Prompt:** `Run `tailscale status 2>&1 | head -5 ; tailscale ip -4 2>&1` and report.`
**Pass:** a list of peers and a `100.x.x.x` IP for this host.
**Fail hint:** tailscale service not started, or not signed in.

### T27 — Sunshine config dir `[LOCATE]`
**Proves:** Sunshine has been initialized (creates the config dir on first run).
**Prompt:** `Sunshine's config dir is install-location-dependent. First find the service binary path with `sc qc SunshineService 2>&1 | grep -i binary_path_name`, then check the sibling config dir. Also check the default C:/ProgramData/Sunshine/. Report which path actually has the config and what files are in it.`
**Pass:** one of the candidate paths has `sunshine.conf`, `apps.json` (or an `apps/` folder), and a `credentials/` subfolder with `cacert.pem` + `cakey.pem`.
**Fail hint:** if neither candidate path has those files, Sunshine was installed but never launched to setup. Run the Sunshine UI once to trigger initial config generation.

### T28 — Tailscale IP known and stable `[AI]`
**Proves:** you have the IP to give Moonlight.
**Prompt:** `Run `tailscale ip -4` and tell me the IP.`
**Pass:** a `100.x.x.x` address.
**Fail hint:** see T26.

---

## Layer 6 — Eigent-specific capabilities

### T29 — Skills system `[AI]`
**Proves:** Eigent's skills system is functional: `list_skills` returns the catalog, `load_skill` loads a skill and changes agent behavior.
**Prompt:** `Call list_skills and report what skills are available. Then pick one (suggest skill-creator or pdf) and call load_skill on it. Report the skill's first instruction.`
**Pass:** a real list of skills, then a loaded skill with a non-empty first instruction.
**Fail hint:** if `list_skills` returns empty or errors, skills weren't enabled. Settings → Agents → Skills, toggle on the example-skills bundle.

### T30 — Notes system (agent-shared memory) `[AI]`
**Proves:** the notes system works for cross-agent and cross-turn memory: `append_note` writes, `read_note` reads back, `shared_files` registry is usable.
**Prompt:** `Use append_note to add "- /tmp/eigent-healthtest-2026-06-18: test entry" to the "shared_files" note. Then use read_note on "shared_files" to verify your entry is there. Show me the verbatim read_note output.`
**Pass:** the agent's test entry is in the read_note output.
**Fail hint:** if `append_note` errors, the notes backend isn't initialized. Restart Eigent. If it claims success but `read_note` doesn't show the entry, the notes backend is inconsistent.

### T31 — run_remote_sub_agent (optional) `[AI]`
**Proves:** the remote sandbox sub-agent is reachable for long-running or isolated work, and the anti-fabrication rules in the sub-agent system message are live (forces tool calls for verifiable operations instead of letting the model compose plausible-looking strings).
**Prompt:** `Use run_remote_sub_agent with a tiny task: compute the SHA-256 of the string "eigent healthtest" in the remote sandbox and report it.`
**Pass:** a 64-character hex SHA-256 hash, generated in the sandbox. The expected hash is `6c4a9013c196ae06ad19ac7e5194769787bea813f6b98ee0d43517cf34b7efc9` (this is the real SHA-256 of "eigent healthtest"). The agent's answer MUST match this exactly. Any other 64-character hex string is a fabrication (the model composed it instead of computing it), see fail hint.
**Fail hint:** if the hash does not match `6c4a9013c196ae06ad19ac7e5194769787bea813f6b98ee0d43517cf34b7efc9`, the sub-agent fabricated. The anti-fabrication rules in `depth_limited_agent_toolkit.py` (see PATCHES.md) were not strong enough to override the base-model behavior in this run. Known model-behavior ceiling on GLM-5.2 sub-agents. This test is PASS-with-concern at best until parent-side verification (Coordinator-side hash recompute and reject) is wired. The fix is documented as TBD in PATCHES.md (the "blank for later" entry). If the tool errors with auth or connection, the RemoteSubAgent isn't configured; this is optional and can be skipped if you didn't set it up.
**Note:** This test exercises a generic `general-purpose` ChatAgent sub-agent, NOT one of the 5 custom workforce agents (Coordinator/Implementer/Researcher/Subject Analyst/Verifier). The 5 custom agents only fire in Workforce mode, and may behave better. T31 does not prove the workforce will fabricate.

### T32 — multi-agent fan-out (optional) `[AI]`
**Proves:** Eigent's custom 5-agent workforce (Coordinator, Implementer, Researcher, Subject Analyst, Verifier) can be triggered and at least one specialized worker produces output.
**Prompt:** `Trigger a multi-agent dispatch with a small task: ask the Researcher to fetch example.com and report the page title. Use the multi-agent dispatch panel or the appropriate tool.`
**Pass:** the Researcher (or whichever worker Coordinator routes to) returns a real page title (likely "Example Domain"). Bonus: the Coordinator's dispatch log shows it picked the Researcher based on the worker description rewrite in PATCHES.md.
**Fail hint:** if dispatch fails or only the Single Agent responds, multi-agent routing isn't configured. Check Settings → Agents to verify all 5 roles are enabled, and re-verify T13b (chat_service.py patches).

---

## Layer 7 — Reboot persistence

### T33 — Docker autostart `[AI]`
**Proves:** Docker engine comes back at login.
**Prompt:** `Run `python -c "import json; print('AutoStart =', json.load(open(r'C:/Users/Anira/AppData/Roaming/Docker/settings-store.json'))['AutoStart'])"` and report.`
**Pass:** `AutoStart = True`.
**Fail hint:** Docker Desktop, Settings, General, tick "Start Docker Desktop when you sign in to your computer".

### T34 — Docker UI does not pop at login `[LOCATE]`
**Proves:** "Use Docker Desktop in background by default" / "Open Docker Dashboard when Docker Desktop starts" is correctly configured so only the engine loads, not the window.
**Prompt:** `Ask the user to confirm: in Docker Desktop, Settings, General, is "Open Docker Dashboard when Docker Desktop starts" unchecked (or "Use Docker Desktop in background by default" ticked)? Report their answer.`
**Pass:** user confirms the dashboard does not pop on login.
**Fail hint:** uncheck the dashboard-at-start box manually in Docker Desktop, Settings, General, Apply and restart.

### T35 — Eigent autostart `[AI]`
**Proves:** Eigent is in the user Run key so it launches at login.
**Prompt:** `Run this literal command and report its output: `reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v Eigent`. Do NOT substitute PowerShell cmdlets like `Get-ItemProperty` or `Get-Item`, they return empty in some agent shell contexts and produce false negatives even when the registry entry exists. Use the cmd `reg query` form.`
**Pass:** output shows the key path then a line with `Eigent REG_SZ "E:\\Eigent\\Eigent.exe"`.
**Fail hint:** if `reg query` (the cmd form, not PowerShell) returns "not found", run the GUIDE.md `reg add` command for Eigent.

---

## Layer 8 — Ruleset actually governs

### T36 — cave-speak memory `[AI]`
**Proves:** ruleset section on memory (cave-speak compression) is loaded.
**Prompt:** `Save a test memory with content "eigent health check 2026-06-18: stack running" using cave-speak compression, append-only. Use either append_note (preferred in Eigent) or write to E:/Logseq/memory/2026-06-18.md. Report which path you used.`
**Pass:** memory entry appended, in compressed Chinese with the English URL/identifier preserved.
**Fail hint:** if the agent writes a long English paragraph, the ruleset section on memory is not being followed.

### T37 — no em dashes `[AI]`
**Proves:** ruleset section on voice (no em dashes, no AI-generic filler) is loaded.
**Prompt:** `Explain in 4 sentences why `pip install scrapling[mcp]` is needed.`
**Pass:** no em dashes anywhere in the answer.
**Fail hint:** if em dashes appear, the ruleset is not being followed, or the ruleset is missing.

### T38 — confirmed vs inferred labels `[AI]`
**Proves:** ruleset section on verify-before-claim is loaded.
**Prompt:** `Is the Sunshine service set to Automatic? Report with the 【已确认】/【推断】label and evidence.`
**Pass:** the answer uses labels (or clearly separates confirmed vs inferred), cites the command it ran or the file it read.
**Fail hint:** if the agent just says "yes" without evidence or label, the ruleset is not loaded.

### T39 — web-verify discipline `[AI]`
**Proves:** ruleset section on web-verify is loaded.
**Prompt:** `What is the latest Node.js LTS version as of today?`
**Pass:** the agent searches via searxng (NOT built-in search_google) rather than answering from memory, and cites a recent source with a URL.
**Fail hint:** if it answers from memory without a search, the ruleset is not being followed. If it uses `search_google` instead of `searxng_web_search`, the tool-routing rule is not being followed.

### T40 — tool-call intent line `[USER]`
**Proves:** ruleset section on tool-call hygiene is loaded. The user watches the agent's behavior during the whole test.
**Pass:** before every batch of tool calls, the agent emits one sentence of intent.
**Fail hint:** if the agent goes silent for 30s+ then dumps a batch of tool calls, the ruleset is not being followed.

### T41 — tool routing enforcement `[AI]`
**Proves:** the ruleset forces MCP-stack routing over built-in tools.
**Prompt:** `Search the web for "GLM-5.2 release date". Tell me which tool you used to search (full tool name), the top result, and why you did not use built-in search_google or web_fetch.`
**Pass:** the agent names `searxng_web_search` (or `searxng_web_search_suggestions` / `web_url_read` from the searxng MCP), cites a real result, and explains the routing rule from section 4 of the ruleset.
**Fail hint:** if the agent uses `search_google`, `web_search`, `web_fetch`, or any built-in search, the ruleset's tool-routing section is not being followed.

### T42 — ponytail ladder `[AI]`
**Proves:** the ruleset's lazy-code ladder is loaded.
**Prompt:** `I need to read a JSON config file at /tmp/test.json and print the "name" field. Walk me through the ladder: which rungs did you consider, which one did you stop at, and why? Show the final code.`
**Pass:** the agent articulates at least 3 ladder rungs (need-to-exist, stdlib, platform, dep, one-line, minimal), stops at the stdlib/one-line rung for this trivial task, and produces a small Python one-liner using `json.load`.
**Fail hint:** if the agent reaches for a heavy abstraction (config library, dataclass, schema validator) for a one-field JSON read, the ponytail ladder rule is not loaded.

---

## Layer 9 — End-to-end

### T43 — full research pipeline `[AI]`
**Proves:** the stack can do a real task end-to-end.
**Prompt:**
```
Find an Associated Press article from the last 7 days on any topic. Use SearXNG to find it, Scrapling to fetch the full text. Quote the lede paragraph verbatim. Save a cave-speak memory entry summarizing the article in one line with the URL (via append_note or write to E:/Logseq/memory/). Give me the URL so I can verify the quote.
```
**Pass:**
- a real AP URL from the last 7 days
- a verbatim quote that matches when you open the URL
- a memory entry, either in agent notes or E:/Logseq/memory/
- the memory entry is compressed Chinese with the English URL preserved
**Fail hint:** isolate which step failed by re-running the matching single test (T07, T08, T10, T36).

---

**Workforce mode (5-agent) tests are in [`workforce-healthtest.md`](workforce-healthtest.md).** This file is for the single-agent stack. T13b and T32 stay here as basic preflight checks for the workforce wiring; the deep workforce audit (T44) lives in the separate file.

---

## User-only tests

These cannot be run by the agent. Do them yourself after the agent-run tests pass.

### U01 — reboot persistence end-to-end
Reboot the host. Do not log in for a minute. Log in via Moonlight from your phone on cellular (or walk to the machine). Before checking 5001, **wait 60-90 seconds after the desktop appears** so the embedded backend has time to bind its port (T24 false-negative window).
**Pass:** desktop comes up. Eigent icon in tray. Docker engine running. SearXNG responds on `127.0.0.1:8888`. At least ONE backend responds: embedded (`127.0.0.1:5001`) OR Docker (`127.0.0.1:3001`). If only 3001 is up after the 90s wait, that's a PASS, Docker backend covers it.
**Fail hint:** whichever layer did not come back, check its autostart config (T33-T35). If 5001 alone is dead after waiting, either the embedded backend didn't auto-start with Eigent (check tray icon) or the boot race wasn't given enough time, re-probe after another 30s before calling this a fail.

### U02 — remote access from phone
On your phone, disconnect from WiFi (use cellular). Open Moonlight. Tap the host.
**Pass:** full desktop appears. You can click around.
**Fail hint:** if the host does not show up, Tailscale is not running on the host or phone. If it shows up but pairing fails, delete `cacert.pem` and `cakey.pem` in Sunshine's config dir, restart the service, pair again.

### U03 — Eigent remote session from phone (optional)
In Eigent desktop, open the Dispatch panel, create a remote session, open the returned URL on your phone's browser via Tailscale.
**Pass:** the Eigent UI is usable from the phone. You can send a chat message and get a response.
**Fail hint:** if the URL doesn't load, Tailscale isn't up or the Eigent backend isn't exposed to the tailnet. If it loads but auth fails, check the remote-session token in Eigent's settings.

### U04 — Telegram bridge (if enabled)
Message your bot. Approve an action from the phone.
**Pass:** the bot responds, the approval flow works.
**Fail hint:** GUIDE.md step on Telegram bridge was skipped, the bridge isn't available in your Eigent version, or the chat id allowlist is wrong.

---

## Final checklist

- [ ] T01 to T43 all pass (T31 acceptable as PASS-with-concern, see test note).
- [ ] If you run workforce mode, also run `workforce-healthtest.md` (T44 giga audit).
- [ ] U01 to U04 all pass (or are explicitly skipped if optional).

If anything fails, fix the highest-severity failure first, not the easiest one. Severity order:
1. Provider and model broken (T01 to T05), nothing else works, fix this first.
2. Ruleset not loaded (T36 to T42), the agent will drift without you noticing.
3. MCP broken (T06 to T12), partial capability, research is degraded.
4. Eigent capabilities broken (T29 to T32), you've lost multi-agent + skills. Deep workforce audit is in `workforce-healthtest.md`.
5. Services and persistence (T19 to T24, T33 to T35), works now, breaks on reboot.
6. Files and prompt (T13 to T18), usually a one-copy fix.
7. Remote access (T25 to T28), only matters if you rely on phone access.

When the whole checklist is green, the stack is verified end-to-end. Do not call it working until you have done U01 (the actual reboot).

---

## Migration note

This healthtest is the Eigent-native replacement for the older CodePilot-flavored test. Differences from the old test:
- Dropped CodePilot-only scaffolding tests (HEARTBEAT.md, .claude/settings.json enforcement, CodePilot auto-memory path).
- Added Eigent-specific capability tests (Skills T29, Notes T30, RemoteSubAgent T31, multi-agent T32).
- Added ruleset tests for tool routing (T41) and ponytail ladder (T42).
- Added T13b (chat_service.py Coordinator wiring), T13c (toolkit_assembler disk-config bridge), T13d (listen_chat_agent sanitizer interception).
- T19 enforces ripgrep as a requirement, not a recommendation (ruleset §4 enforces `rg --json`).
- T03 reframed: thinking mode is inherited from the Coding Plan endpoint, not a UI toggle.
- T24 retries both 5001 (embedded) and 3001 (Docker) backends to handle the boot-time race.
- T31 documented as PASS-with-concern: anti-fabrication rules are live but the base model still fabricates in this isolated sub-agent path. Fix is TBD (parent-side verification).
