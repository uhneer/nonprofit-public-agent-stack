# Eigent Backend Patches (PATCHES.md)

This is the giga changelog of every patch shipped to the Eigent backend to make the nonprofit-agent-stack work the way the ruleset expects. Stock Eigent ships with a generic 4-agent workforce (Developer/Browser/Document/Multi-Modal) and a generic system prompt. The patches here turn it into a 5-agent workforce (Coordinator/Implementer/Researcher/Subject Analyst/Verifier) with the nonprofit ruleset baked into the system prompt and the Coordinator dispatch contract.

Read this before debugging weird agent behavior. The cause is usually in here.

## Table of contents
1. [patch_log.md format](#patch-logmd-format)
2. [P1 — prompt.py rewrite (5-agent stack)](#p1--promptpy-rewrite-5-agent-stack)
3. [P2 — chat_service.py Coordinator wiring](#p2--chat_servicepy-coordinator-wiring)
4. [P3 — toolkit_assembler.py MCP disk-config bridge + sanitizer + env var expansion](#p3--toolkit_assemblerpy-mcp-disk-config-bridge--sanitizer--env-var-expansion)
5. [P4 — environment_hands.py E:\ allowlist](#p4--environment_handspy-e-allowlist)
6. [P5 — listen_chat_agent.py message_* filtering + hallucinated tool name handling](#p5--listen_chat_agentpy-message_-filtering--hallucinated-tool-name-handling)
7. [P6 — depth_limited_agent_toolkit.py anti-fabrication rules](#p6--depth_limited_agent_toolkitpy-anti-fabrication-rules)
8. [P7 — browser.py restore after _cdp_pool_manager import break](#p7--browserpy-restore-after-_cdp_pool_manager-import-break)
9. [P8 — Headless CDP Chrome autostart .bat](#p8--headless-cdp-chrome-autostart-bat)
10. [P9 — Supabase MCP stdio switch](#p9--supabase-mcp-stdio-switch)
11. [P10 — T31 sub-agent fabrication (TBD, blank for later)](#p10--t31-sub-agent-fabrication-tbd-blank-for-later)

---

## patch_log.md format

Each entry below has:
- **File**: the patched backend file path (both `E:\Eigent\resources\backend\` and `E:\Eigent-source\backend\` mirrored).
- **Stock behavior**: what the unpatched code does.
- **Patched behavior**: what the new code does.
- **Why**: the failure mode the patch fixes.
- **Verification**: how to confirm the patch is live (usually a health test reference).
- **Code**: the actual diff or new code block, in order.

Back up the original before patching: `cp <file> <file>.bak`. Keep the `.bak` files; they are the restore path. Patches are applied in numbered order. If the stock version is in place, re-apply from the patch code. If a patch is broken, restore from `.bak` and re-apply from there.

---

## P1 — prompt.py rewrite (5-agent stack)

**File:** `E:\Eigent\resources\backend\app\agent\prompt.py` (mirrored to `E:\Eigent-source\backend\app\agent\prompt.py`)

**Stock behavior:** Single `SINGLE_AGENT_SYS_PROMPT` constant with the factory system prompt. No Coordinator prompt, no operator_operating_rules block, no tool-routing enforcement.

**Patched behavior:** Three changes:
1. The `<operator_operating_rules>` block (§0-§14) is appended to `SINGLE_AGENT_SYS_PROMPT`. This is the nonprofit ruleset: priorities, voice, long-run behavior, web-verify discipline, tool-call hygiene, verify-before-claim, few-shot examples. §15 (Coordinator dispatch protocol) was extracted to a dedicated constant.
2. A new `COORDINATOR_SYS_PROMPT` constant is defined separately. It contains `<pipeline_order>`, `<dispatch_contract>`, and `<synthesis_rules>` tags. This prompt is what the Coordinator workforce role actually loads.
3. Worker descriptions in `construct_workforce` calls are rewritten so Coordinator routes to the right worker (see P2).

**Why:** Stock Eigent prompt is too generic. The ruleset needs to be in the system prompt directly, not just in a workspace file the agent might not load. Extracting §15 to COORDINATOR_SYS_PROMPT (instead of piggybacking on SINGLE_AGENT) keeps the Single Agent path clean and gives Coordinator its own routing logic.

**Verification:** health test T13.
- SINGLE_AGENT_SYS_PROMPT around line 566.
- `<operator_operating_rules>` opens ~line 608.
- Highest section inside is §14 (NOT §15).
- COORDINATOR_SYS_PROMPT defined ~line 714.
- `<pipeline_order>` tag present in COORDINATOR_SYS_PROMPT.
- `<dispatch_contract>` tag present in COORDINATOR_SYS_PROMPT.

**Code (outline, see the actual prompt.py for the full text):**
```python
SINGLE_AGENT_SYS_PROMPT = (
    "<stock factory prompt>"
    + "\n\n<operator_operating_rules>"
    + "\n## 0. 优先级（平局以此为准）"
    + "\n- the operator 的意图和体验第一..."
    + "\n## 1. 文风（本文件也遵守）"
    # ... sections 2 through 14 ...
    + "\n## 14. 发送前，重读一遍"
    + "\n</operator_operating_rules>"
)

COORDINATOR_SYS_PROMPT = (
    "<stock coordinator preamble>"
    + "\n<pipeline_order>"
    + "\n1. Subject Analyst (problem decomposition, domain reasoning)"
    + "\n2. Researcher (web search, docs, fetch)"
    + "\n3. Implementer (code, file edits, scripts)"
    + "\n4. Verifier (run tests, verify claims)"
    + "\n</pipeline_order>"
    + "\n<dispatch_contract>"
    + "\n- One task per worker, one worker per task."
    + "\n- Pass the full context the worker needs, do not paraphrase."
    + "\n- Wait for worker response before dispatching the next step."
    + "\n- If a worker reports NO_TOOL_AVAILABLE, do not retry with the same worker."
    + "\n</dispatch_contract>"
    + "\n<synthesis_rules>"
    + "\n- Cite worker outputs verbatim when they contain verifiable facts."
    + "\n- Apply the operator_operating_rules from SINGLE_AGENT_SYS_PROMPT to your own output."
    + "\n- If any worker fabricates (T31 pattern), discard its output and flag the failure."
    + "\n</synthesis_rules>"
)
```

**To restore:** `cp prompt.py.bak prompt.py` (or prompt.py.bak2 for the pre-5-agent-extraction state).

---

## P2 — chat_service.py Coordinator wiring

**File:** `E:\Eigent\resources\backend\app\service\chat_service.py` (mirrored)

**Stock behavior:** The workforce coordinator uses a generic system prompt, and the 4 workers have descriptions like "Developer Agent: master-level coding," "Browser Agent: can search the web," "Document Agent: document processing," "Multi-Modal Agent: media processing."

**Patched behavior:**
1. Import `COORDINATOR_SYS_PROMPT` from `app.agent.prompt`.
2. Import `BaseMessage` from `camel.messages`.
3. In `_create_coordinator_and_task_agents`, wrap the Coordinator prompt in `BaseMessage.make_assistant_message(role_name="Coordinator", content=COORDINATOR_SYS_PROMPT)`.
4. In `construct_workforce` (the `add_single_agent_worker` calls), rewrite the worker descriptions to:
   - "Implementer Agent: master-level coding, file edits, script execution"
   - "Researcher Agent: web search, page fetch, library docs lookup"
   - "Subject Analyst Agent: domain reasoning, problem decomposition, requirement clarification"
   - "Verifier Agent: run tests, verify claims, catch fabricated output"

**Why:** Without the `role_name="Coordinator"`, CAMEL does not pick up the COORDINATOR_SYS_PROMPT and Coordinator falls back to the factory default. Without the worker description rewrite, Coordinator routes wrong (it'll think it has a media agent when it really has a Verifier, etc).

**Verification:** health test T13b.
- `COORDINATOR_SYS_PROMPT` imported from `app.agent.prompt`: yes.
- `BaseMessage` imported from `camel.messages`: yes.
- Coordinator prompt wrapped in `BaseMessage.make_assistant_message(role_name="Coordinator", ...)`: yes.
- `add_single_agent_worker` description strings contain "Implementer", "Researcher", "Subject Analyst", "Verifier": yes.
- Old strings "Developer Agent: master-level coding", "Browser Agent: can search the web", "Document Agent: document processing", "Multi-Modal Agent: media processing": NOT present.

**Regression note (2026-06-19):** The 5-agent wiring introduced an asyncio bug in the same file. The stock `asyncio.gather(...)` block that builds all 7 worker agents called `browser_agent(...)` and `developer_agent(...)` as bare callables, but `browser_agent` is defined as a *sync* function (`def browser_agent(` at `app/agent/factory/browser.py:176`), so its direct return value is a `ChatAgent`, not a coroutine. `asyncio.gather` runs every arg through `ensure_future`, which rejects non-awaitables with `an asyncio.Future, a coroutine or an awaitable is required`. `developer_agent` and `document_agent` happen to be async so they survived; `browser_agent` and `multi_modal_agent` (also sync) must be wrapped in `asyncio.to_thread(partial(...))`.

**Regression fix:** Always wrap the two sync factories. Sketch:
```python
from functools import partial

results = await asyncio.gather(
    asyncio.to_thread(_create_coordinator_and_task_agents),
    asyncio.to_thread(_create_new_worker_agent),
    asyncio.to_thread(partial(browser_agent, options, hands=hands)),      # sync, MUST wrap
    developer_agent(options, hands=hands),                                 # async, no wrap
    document_agent(options, hands=hands),                                  # async, no wrap
    asyncio.to_thread(partial(multi_modal_agent, options, hands=hands)),  # sync, MUST wrap
    mcp_agent(options),
)
```
The 7-element order is preserved so the downstream `results[0]..results[6]` tuple unpackling does not shift. Verified against `.bak3` backup which already had the correct wrap; the regression was introduced when the wrap was lost during a later edit.

**Code (sketch):**
```python
from app.agent.prompt import COORDINATOR_SYS_PROMPT
from camel.messages import BaseMessage

def _create_coordinator_and_task_agents(...):
    coordinator_msg = BaseMessage.make_assistant_message(
        role_name="Coordinator",
        content=COORDINATOR_SYS_PROMPT,
    )
    # ...

def construct_workforce(...):
    workforce.add_single_agent_worker(
        "Implementer Agent: master-level coding, file edits, script execution",
        implementer_agent,
    )
    workforce.add_single_agent_worker(
        "Researcher Agent: web search, page fetch, library docs lookup",
        researcher_agent,
    )
    workforce.add_single_agent_worker(
        "Subject Analyst Agent: domain reasoning, problem decomposition, requirement clarification",
        subject_analyst_agent,
    )
    workforce.add_single_agent_worker(
        "Verifier Agent: run tests, verify claims, catch fabricated output",
        verifier_agent,
    )
```

---

## P3 — toolkit_assembler.py MCP disk-config bridge + sanitizer + env var expansion

**File:** `E:\Eigent\resources\backend\app\agent\factory\toolkit_assembler.py` (mirrored)

**Stock behavior:** Three bugs that combine to make MCP tools silently unavailable:
1. The `_mcp_config` function reads only from `options.installed_mcp`. If that field is empty (which it often is after fresh install), no MCP servers get registered, even when `~/.eigent/mcp.json` has them all configured.
2. The MCPToolkit.connect() error handler logs a generic "Failed to connect MCPToolkit" message with no server names, so silent MCP failures are impossible to diagnose.
3. Env vars in the form `${SUPABASE_ACCESS_TOKEN}` are not expanded in stdio `env` blocks, so Supabase MCP launches with the literal string `${SUPABASE_ACCESS_TOKEN}` and fails auth.
4. GLM emits `null` and empty strings in MCP tool kwargs. MCP tools with required non-null fields reject these silently.

**Patched behavior:** Four fixes in one file:
1. **Disk-config bridge:** `_mcp_config` calls `read_mcp_config()` from `app.service.mcp_config` and merges disk config as fallback when `options.installed_mcp` is empty. Merge is `{**disk_servers, **options_servers}` so options win on conflict, disk fills missing.
2. **Error logging:** MCPToolkit.connect() error handler includes the configured server names in the error message, not just the generic failure.
3. **Env var expansion:** `os.path.expandvars` runs on env values before spawning the stdio child process. `${SUPABASE_ACCESS_TOKEN}` resolves from the user environment.
4. **Schema-aware sanitizer:** Wraps `tool.func` in `_aexecute_tool` so null/empty kwargs are stripped before the tool runs. The sanitizer inspects the tool's openapi_schema to know which fields are required vs optional.

**Why:** Each bug here cost a full afternoon to diagnose. The disk-config bridge is the highest-impact: without it, MCP tools silently fail to load after fresh install and there is no way to tell from the UI.

**Verification:** health tests T13c (disk-config bridge) and T13d (sanitizer interception).

**Code (sketch of the bridge):**
```python
from app.service.mcp_config import read_mcp_config

def _mcp_config(options):
    # Start with options (per-chat)
    options_servers = dict(options.installed_mcp or {})
    # Fall back to disk config
    disk_servers = {}
    try:
        disk = read_mcp_config()
        disk_servers = disk.get("mcpServers", {})
    except Exception as e:
        logger.warning("Failed to read disk MCP config: %s", e)
    # Merge: options win on conflict, disk fills missing
    servers = {**disk_servers, **options_servers}
    # Expand env vars in env blocks
    for name, cfg in servers.items():
        if "env" in cfg:
            cfg["env"] = {k: os.path.expandvars(v) for k, v in cfg["env"].items()}
    return servers
```

**Code (sketch of the sanitizer):**
```python
def _sanitize_kwargs(tool, kwargs):
    schema = tool.openapi_schema or {}
    required = set(schema.get("required", []))
    cleaned = {}
    for k, v in kwargs.items():
        if v is None or v == "":
            if k in required:
                # leave it, let the tool raise a clear error
                cleaned[k] = v
            else:
                continue  # strip
        else:
            cleaned[k] = v
    return cleaned

# In _aexecute_tool:
tool: FunctionTool = self._internal_tools[func_name]
args = _sanitize_kwargs(tool, args)
```

---

## P4 — environment_hands.py E:\ allowlist

**File:** `E:\Eigent\resources\backend\app\hands\environment_hands.py` (mirrored)

**Stock behavior:** The agent's file access is allowlisted to user-profile directories (`C:\Users\<you>\`). Any path outside that is "not available to this Brain."

**Patched behavior:** `E:\` is added to the allowlist.

**Why:** The workspace is at `E:\Logseq`. Without this patch, the agent cannot read its own workspace, nor any of the files on `E:\` (the Logseq graph, the Eigent source mirror, the patches themselves, etc).

**Verification:** health tests T05 (agent operates inside bound workspace) and T18 (workspace folder bound to Eigent).

**Code:** roughly a one-liner. Find the allowed-paths list (a Python list of path strings) and add `"E:\\"` (or `Path("E:/")`) to it.

---

## P5 — listen_chat_agent.py message_* filtering + hallucinated tool name handling

**File:** `E:\Eigent\resources\backend\app\agent\listen_chat_agent.py` (mirrored)

**Stock behavior:** Two bugs:
1. GLM sometimes emits `message_title`, `message_description`, `message_attachment` kwargs into tool calls (looks like it's confusing tool calls with message creation). These kwargs cause the tool to reject the call with "unexpected kwarg."
2. When GLM hallucinates a tool name (calls a tool that does not exist on the agent's surface), CAMEL's `self._internal_tools[func_name]` raises a `KeyError`. The KeyError propagates up and kills the whole turn, even if 22 previous tool calls in the same turn succeeded.

**Patched behavior:** Two fixes at the start of `_aexecute_tool`:
1. Strip `message_*` kwargs from the args dict before dispatching.
2. Pre-check `if func_name not in self._internal_tools`. If hallucinated, return a graceful error result that the model can react to, instead of raising.

**Why:** The KeyError crash was responsible for at least one major healthtest run failing mid-turn with 22 successful tool calls lost. The `message_*` kwarg bug silently broke ~5% of tool calls.

**Verification:** health test T13d.

**Code (the hallucinated-name pre-check):**
```python
async def _aexecute_tool(self, tool_call_request: ToolCallRequest) -> ToolCallingRecord:
    func_name = tool_call_request.tool_name
    tool_call_id = tool_call_request.tool_call_id
    args = {
        k: v
        for k, v in tool_call_request.args.items()
        if k not in ("message_title", "message_description", "message_attachment")
    }

    if func_name not in self._internal_tools:
        available = sorted(self._internal_tools.keys())
        preview = available[:40]
        suffix = "..." if len(available) > 40 else ""
        result = (
            f"Tool execution failed: Error executing tool '{func_name}': "
            f"tool '{func_name}' is not in this agent's surface "
            f"(hallucinated name). Available tools: {preview}{suffix}"
        )
        logger.warning(
            "_aexecute_tool: hallucinated tool %r rejected. "
            "%d tools available.",
            func_name,
            len(available),
        )
        return self._record_tool_calling(
            func_name, args, result, tool_call_id,
            mask_output=False,
            extra_content=tool_call_request.extra_content,
        )
    tool: FunctionTool = self._internal_tools[func_name]
    # ... rest of the method unchanged
```

---

## P6 — depth_limited_agent_toolkit.py anti-fabrication rules

**File:** `E:\Eigent\resources\backend\app\agent\toolkit\depth_limited_agent_toolkit.py` (mirrored)

**Stock behavior:** The sub-agent system message is built from the factory base + a one-liner about not delegating further.

**Patched behavior:** `_build_system_message` appends four anti-fabrication rules:
1. For any verifiable operation (hashing, math, file reads, command output, API responses, dates, code execution), you MUST invoke the corresponding tool and use the tool's actual output.
2. If no tool on your surface can compute the answer, return `NO_TOOL_AVAILABLE: <what you needed>` instead of guessing.
3. Every numeric, hex, base64, UUID, or hash-shaped string in your final answer must be copied verbatim from a tool result.
4. Parent agent will verify your output against ground truth. Fabricated outputs fail the task; honest "I could not compute" answers are recoverable.

**Why:** T31 health test caught a sub-agent returning a fake SHA-256 hash (`f3d2c5b1a8e9...`) instead of computing the real one (`6c4a9013c196...`). Probe verified the sub-agent received the 1118-char message with all 4 rules verbatim. The model reads them and fabricates anyway. This patch is necessary but not sufficient. See P10.

**Verification:** health test T31. Probe script:
```python
from app.agent.toolkit.depth_limited_agent_toolkit import DepthLimitedAgentToolkit
# construct an instance, then call _build_system_message("general-purpose", "test")
# assert "ANTI-FABRICATION RULES" in the returned string
# assert len(returned) >= 1000
```

**Code:**
```python
def _build_system_message(self, subagent_type: str, description: str) -> str:
    base = super()._build_system_message(subagent_type, description)
    return (
        base
        + "\nYou are a child sub-agent. Complete the assigned task "
        "directly and do not create or delegate to any further sub-agents."
        + "\n\nANTI-FABRICATION RULES (hard requirements, not suggestions):"
        + "\n1. For any verifiable operation (hashing, math, file reads, "
        "command output, API responses, dates, code execution), you MUST "
        "invoke the corresponding tool and use the tool's actual output. "
        "Pattern-likely strings you compose in your head are forbidden."
        + "\n2. If no tool on your surface can compute the answer, return "
        "'NO_TOOL_AVAILABLE: <what you needed>' instead of guessing."
        + "\n3. Every numeric, hex, base64, UUID, or hash-shaped string "
        "in your final answer must be copied verbatim from a tool result. "
        "If you cannot point to the tool call that produced it, omit it."
        + "\n4. Parent agent will verify your output against ground truth. "
        "Fabricated outputs fail the task; honest 'I could not compute' "
        "answers are recoverable."
    )
```

---

## P7 — browser.py restore after _cdp_pool_manager import break

**File:** `E:\Eigent\resources\backend\app\agent\factory\browser.py` (mirrored)

**Stock behavior (in some Eigent builds):** An upstream refactor moved `_cdp_pool_manager` to a different module but did not update `browser.py`'s import. Result: `ImportError` on agent startup, the entire browser tool path is dead, and the CDP auto-launch workaround (P8) is also dead.

**Patched behavior:** Import `_cdp_pool_manager` from its new location, or define a local shim if the symbol was removed entirely.

**Why:** Discovered during the 2026-06-18 health test run. Browser-dependent tasks (Scrapling via the Chromium tier, the headless CDP Chrome workaround) all silently failed until this was fixed.

**Verification:** start Eigent from the tray and run a task that uses the browser tool. No ImportError. The headless Chrome on port 9224 should be connectable.

**Code:** restore from `browser.py.bak`. The exact fix depends on which version of Eigent you have; check the import in the `.bak` file before re-applying.

---

## P8 — Headless CDP Chrome autostart .bat

**File:** `C:\Users\<you>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\eigent-headless-chrome.bat`

**Stock behavior:** Eigent's renderer auto-fires an IPC `launch-cdp-browser` whenever the CDP browser pool is empty on chat send. The Electron main-process handler spawns Playwright's Chromium with `--remote-debugging-port`, `--user-data-dir`, `--no-first-run`, `--no-default-browser-check`, `--disable-blink-features=AutomationControlled`, `about:blank`, and **no `--headless` flag**. Result: every fresh chat after a reboot pops a visible Chrome window the user has to close by hand. Setting `headless=True` on the Python `HybridBrowserToolkit` does nothing, because Electron already spawned a non-headless Chrome and Python just connects over CDP.

**Patched behavior:** Pre-launch a dedicated headless Chrome at login so the CDP pool is never empty and `chatStore.ts` skips auto-launch entirely. See GUIDE.md step 18b for the full `.bat` contents.

**Why:** Without this, every reboot means a visible Chrome window pops on first chat. Annoying for interactive use, fatal for unattended remote access.

**Verification:** reboot, wait 60-90s, send any chat that triggers a browser tool. No visible Chrome window. `curl http://127.0.0.1:9224/json/version` returns JSON.

**To disable:** delete the `.bat`, or set user env var `EigHeadlessChrome=0`.

**Permanent fix (not shipped here):** patch `electron/main/index.ts:867` to add `'--headless=new'` to the spawn args and rebuild Eigent from source. That removes the need for this entire step. Tracked as a future patch.

---

## P9 — Supabase MCP stdio switch

**File:** `~/.eigent/mcp.json`, `E:\Logseq\.mcp.json`, and `files/eigent-mcp.json` (this repo).

**Stock behavior (the bug):** The Supabase MCP entry pointed at the remote endpoint `https://api.supabase.com/mcp/v1`. That endpoint is OAuth-only and rejects personal access tokens with a silent `Session terminated` error in the MCP connect log.

**Patched behavior:** Switch to the local stdio server:
```json
"supabase": {
  "command": "npx",
  "args": ["-y", "@supabase/mcp-server-supabase@latest"],
  "env": { "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}" }
}
```

**Why:** Spent an hour diagnosing "MCP connection failed for URL: https://api.supabase.com/mcp/v1. Error: Session terminated." Direct curl test confirmed the PAT works against the REST API (`/v1/projects` returned HTTP 200 with real projects), so the token was fine. The remote MCP endpoint just doesn't accept PATs.

**Verification:** health test T12. List projects via the MCP. A successful "no projects found" response also confirms auth works. With the P3 env-var expansion patch, `${SUPABASE_ACCESS_TOKEN}` is resolved from the user environment at spawn time.

---

## P10 — T31 sub-agent fabrication (TBD, blank for later)

**This is the open item.** The T31 health test still fails because GLM-5.2 sub-agents fabricate verifiable output (fake hashes, fake command output, fake file contents) despite the P6 anti-fabrication rules being live in their system message. Probe verified the rules are received (1118-char message), the model just ignores them.

**Why this is hard:** This is a base-model behavior ceiling, not a wiring bug. Options considered:
- **(A) Stronger prompt patch.** Eliminated. The probe proved the model reads the rules and fabricates anyway. More words won't help.
- **(B) Switch sub-agent to a different model.** Possible but expensive. GLM-5-Turbo or GLM-4.5-Air may behave differently. Untested.
- **(C) Parent-side verification.** The recommended fix. Coordinator (or a dedicated Verifier role) recomputes any verifiable output from a sub-agent and rejects mismatches. Requires:
  1. A new "verifiable claim" envelope in sub-agent output (the sub-agent says "computed hash: X via tool Y").
  2. A parent-side recompute path that runs the same tool and compares.
  3. A reject-and-retry loop when mismatch is detected.
- **(D) Disable run_remote_sub_agent entirely.** Treat as optional. The 5 custom workforce agents may behave better in actual Workforce mode (they have their own specialized prompts and the Coordinator dispatch contract). T31 only exercises a generic `general-purpose` ChatAgent sub-agent, not the workforce.

**Current status:** T31 marked PASS-with-concern in the health test. The fix (option C or D) is deferred. The T31 note in healthtest.md calls this out explicitly so the next person reading the test result knows the failure is a known ceiling, not a regression.

**Slot for the fix when it ships:** (leave blank, fill in when option C or D is implemented. Include the file path, the diff, and the verification probe.)

---

## P11 — Verifier URL-redirect rule baked into sys_prompt

**File:** `E:\Eigent\resources\backend\app\agent\prompt.py` (mirrored at `E:\Eigent-source\backend\app\agent\prompt.py`).

**Stock behavior:** `MULTI_MODAL_SYS_PROMPT` (the Verifier prompt, lines 208-297) had no explicit URL-reachability rule. The 308-to-200 false-fail on openhands.dev/docs.openhands.dev in the 2026-06-19 workforce validation run happened because the Verifier invented a strict "HTTP 200 only" rule from training data and applied it without instruction.

**Patched behavior:** Added a new `<url_verification>` block immediately after `<collaboration>` (around line 273-283). The block explicitly says:
- HTTP 200/201/204 = PASS.
- HTTP 301/302/307/308 followed by 2xx = PASS (normal redirects, fetch with redirects enabled, report final code).
- HTTP 4xx/5xx = FAIL.
- Connection error/DNS failure/timeout = FAIL.

**Why:** The W2 giga audit prompt already included the rule as user-prompt text, but if the operator (or any future test prompt) omits it from the user message, the Verifier will fall back to its training-data default and re-introduce the false-fail. Baking the rule into sys_prompt is belt-and-suspenders: applies regardless of user-prompt content.

**Verification:** health test workforce-healthtest.md W2 criterion 8. If the Verifier marks any 308-to-200 as FAIL after this patch, either the patch was reverted or the model is overriding an explicit rule (deeper GLM-5.2 behavior ceiling, similar to T31).

**Code (sketch):**
```python
MULTI_MODAL_SYS_PROMPT = """\
<role>
You are the Verifier, ...
</role>
...
<collaboration>
...
</collaboration>

<url_verification>
When checking URL reachability, apply this rule strictly:
- HTTP 200, 201, 204 = PASS.
- HTTP 301, 302, 307, 308 that resolves to a 2xx final response = PASS. These
  are normal permanent/temporary redirects (e.g., openhands.dev 308 →
  www.openhands.dev 200). Do NOT mark them FAIL. Fetch with redirects enabled
  and report the FINAL code, not the intermediate.
- HTTP 4xx, 5xx = FAIL.
- Connection error, DNS failure, timeout = FAIL.
Report each URL with: original URL | final URL (if redirected) | final HTTP | verdict.
</url_verification>

<tool_routing>
...
"""
```

---

## P12 — Backend asyncio event loop hang (KNOWN ISSUE, no fix yet)

**File:** `E:\Eigent\resources\backend\app\service\chat_service.py` (the suspect). Possibly also `app/agent/factory/browser.py` or `app/agent/factory/multi_modal.py`.

**Symptom (observed 2026-06-19 14:05):** Eigent backend (uvicorn on port 5001) served `GET /` once with HTTP 200 + JSON body, then the asyncio event loop hung. Every subsequent probe (`/health`, `/docs`, `/api/v1/*`) timed out with HTTP 000 at 8-40s. Process alive, socket accepts, no HTTP response.

**Suspects:**
1. The `asyncio.to_thread(partial(browser_agent, ...))` and `asyncio.to_thread(partial(multi_modal_agent, ...))` wrappers (P2 regression fix). If `browser_agent()` or `multi_modal_agent()` internally call `asyncio.run()` or `loop.run_until_complete()` on the same running loop, the thread pool task will deadlock against the main loop.
2. A prior in-UI chat dispatch that triggered a workforce run may have deadlocked and never released.
3. A camel model call (GLM API) blocked indefinitely without timeout.

**Diagnosis gap:** Eigent.exe does not surface uvicorn stderr to a file. Without per-request logging in the FastAPI app, we cannot tell which dispatch is stuck. Adding structured logging to `chat_service.py:construct_workforce` and `listen_chat_agent._aexecute_tool` would help, but is out of scope for this entry.

**Recovery (user action):** close and restart Eigent.exe, OR `taskkill /PID <uvicorn-pid> /F` then relaunch. Restart loses in-UI session state. No in-app recovery path exists.

**Verification:** health test T24 (`healthtest.md`) probes both 5001 (embedded) and 3001 (Docker). If T24 returns HTTP 000 for 5001 after a 90s post-login wait AND 3001 also fails, this issue is likely the cause.

**Fix slot (TBD):** Options considered:
- **(A) Add asyncio timeouts to every `await` in the workforce dispatch path.** Prevents indefinite hangs but adds complexity.
- **(B) Refactor `browser_agent` and `multi_modal_agent` to be truly async-native** (no internal `asyncio.run` calls). Cleanest but largest scope.
- **(C) Add a watchdog task** that kills stuck dispatches after N seconds. Brute force.
- **(D) Surface uvicorn stderr to a log file** so the next hang can be diagnosed. Diagnostic only, not a fix.

Recommend (D) first to pin the root cause, then decide between (A)/(B)/(C) based on what the log shows.

---

## P13 — prompt.py workspace filing convention (run-folder structure)

**File:** `E:\Eigent\resources\backend\app\agent\prompt.py` (mirrored to `E:\Eigent-source\backend\app\agent\prompt.py`)

**Stock behavior:** All seven file-writing agent prompts (SOCIAL_MEDIA, MULTI_MODAL, DOCUMENT, DEVELOPER, SINGLE_AGENT, COORDINATOR, BROWSER) tell the agent "all local file operations occur in `{working_directory}`" but never specify a layout. Every run dumps its outputs flat into the working-directory root, so the workspace becomes an undifferentiated pile of `.md`, `.html`, `.json`, `.csv`, and one-shot scripts from many unrelated runs.

**Patched behavior:** A module-level `WORKSPACE_FILING_CONVENTION` constant (a `<workspace_filing>` block) is defined near the end of `prompt.py` and appended to each of the seven file-writing prompts via a loop. It instructs every agent to file outputs under:

    <Month YYYY>/<Month Dayth>/<Run Topic>/<Primary | Secondary | Search-Scrape Runs>/

- **Primary/** — only the crux deliverable(s) the run exists to produce (the final .docx, the finished script, the headline report).
- **Secondary/** — written supplementary context (.md notes, extracted findings, per-subtask analysis).
- **Search-Scrape Runs/** — raw/intermediate dumps (searxng/scrapling results, fetched .html/.json, RAG dumps, .csv exports, one-shot parse/extract scripts, probes).

The Coordinator owns the run folder: it names `<Run Topic>`, creates the three subfolders, and tells each worker the exact subfolder to write into. The block is brace-free (survives the existing `.format()` calls) and name-neutral (identical text across the live mirrors and the public/private repo copies).

**Why:** Stops the working-directory-root flood. Each run becomes self-contained: deliverable in Primary, supporting writeups in Secondary, throwaway/search dumps quarantined in Search-Scrape Runs. Mirrors how the operator already files runs by hand (Month > Day > Run Topic).

**Verification:**
- After import, each of the 7 file-writing prompts contains exactly one `<workspace_filing>`.
- `python -m py_compile prompt.py` passes on all 4 copies.
- `DEVELOPER_SYS_PROMPT.format(...)` output contains `Primary/` and `Search-Scrape Runs/` (filing text survives formatting).
- The utility prompts (TASK_SUMMARY / QUESTION_CONFIRM / MCP / DEFAULT_SUMMARY) do NOT contain `<workspace_filing>`.

**Code (outline, see prompt.py for full text):**
```python
WORKSPACE_FILING_CONVENTION = """
<workspace_filing>
  <Month YYYY>/<Month Dayth>/<Run Topic>/<Primary | Secondary | Search-Scrape Runs>/
  ... (Primary = crux deliverable, Secondary = supporting .md, Search-Scrape Runs = raw dumps) ...
</workspace_filing>"""

for _filing_prompt in (
    "SOCIAL_MEDIA_SYS_PROMPT", "MULTI_MODAL_SYS_PROMPT", "DOCUMENT_SYS_PROMPT",
    "DEVELOPER_SYS_PROMPT", "SINGLE_AGENT_SYS_PROMPT", "COORDINATOR_SYS_PROMPT",
    "BROWSER_SYS_PROMPT",
):
    globals()[_filing_prompt] = globals()[_filing_prompt] + WORKSPACE_FILING_CONVENTION
```

**To restore:** delete the `WORKSPACE_FILING_CONVENTION` block and the append loop at the end of `prompt.py`, or restore `prompt.py.bak.prefiling` on the live mirrors.

---

## Apply order

For a fresh install (stock Eigent), apply patches in this order:
1. P4 (environment_hands.py) — unlocks the workspace.
2. P1 (prompt.py) — bakes the ruleset in (note: P11 is a sub-patch to the Verifier prompt section of prompt.py, apply together).
3. P2 (chat_service.py) — wires Coordinator.
4. P3 (toolkit_assembler.py) — fixes MCP loading, sanitizer, env vars.
5. P5 (listen_chat_agent.py) — fixes hallucinated tool names and message_* kwargs.
6. P6 (depth_limited_agent_toolkit.py) — anti-fabrication rules.
7. P7 (browser.py) — restore (only if your build has the import break).
8. P9 (Supabase MCP stdio switch) — config fix, not a code patch.
9. P8 (headless CDP Chrome .bat) — runtime workaround, not a code patch.
10. P10 — TBD.
11. P12 — KNOWN ISSUE (backend hang), no fix yet. Diagnostic work recommended before any code change.
12. P13 — prompt.py workspace filing convention (run-folder structure), apply with P1.

After applying, run the health test from a fresh Eigent chat. Every AI/LOCATE test except T31 (PASS-with-concern) should pass. U01 (actual reboot) is the last gate. If the backend hangs after workforce use, see P12.

## Mirror note

The patches above are applied to BOTH `E:\Eigent\resources\backend\` (the live app, what you run) and `E:\Eigent-source\backend\` (the source mirror, what you read and diff). Keep both in sync. The health test T05 references `E:\Eigent-source\` intentionally to confirm the agent can read across drives after the P4 patch.
