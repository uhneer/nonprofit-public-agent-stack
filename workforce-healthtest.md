# Eigent Workforce Healthtest (5-agent mode)

This file is the deep audit for Eigent's **workforce mode** (Coordinator + Implementer + Researcher + Subject Analyst + Verifier). The single-agent stack has its own file at [`healthtest.md`](healthtest.md); run that first, then run this file when you want to validate multi-agent dispatch.

**What this proves that `healthtest.md` does not:**
- All 5 roles actually fire (not silently degraded).
- Each worker exhibits behavior UNIQUE to its sys_prompt role, not generic helpful-assistant output.
- Parallel-stage workers do NOT see each other's first-pass output (dependency routing is not leaking).
- Coordinator has zero tools and never produces tool output itself.
- Verifier runs last with explicit dependency on Implementer's output.
- URL verification uses sensible redirect rules (HTTP 301/302/307/308 followed by 2xx = PASS).
- Every claim traces to a tool call or verifiable artifact (anti-fabrication in workforce context).

**Preflight (run these from `healthtest.md` first):**
- T13 patched prompt.py is live (5-agent stack)
- T13b chat_service.py wires Coordinator correctly
- T13c MCP disk-config bridge in toolkit_assembler
- T13d sanitizer interception in listen_chat_agent
- T17 .mcp.json at workspace root
- T23 Scrapling mcp loads

If any preflight fails, fix that first. The audit below will not pass meaningfully if the wiring is broken.

---

## W1 — Workforce smoke test `[AI]`

**Proves:** Eigent's custom 5-agent workforce can be triggered at all and at least one specialized worker produces output.

**Prompt:**
```
Trigger a multi-agent dispatch with a small task: ask the Researcher to fetch example.com and report the page title. Use the multi-agent dispatch panel or the appropriate tool.
```

**Pass:**
- The Researcher (or whichever worker Coordinator routes to) returns the real page title (likely "Example Domain").
- Bonus: the Coordinator's dispatch log shows it picked the Researcher based on the worker description rewrite in PATCHES.md.

**Fail hint:** if dispatch fails or only the Single Agent responds, multi-agent routing isn't configured. Check Settings → Agents to verify all 5 roles are enabled, and re-verify `healthtest.md` T13b (chat_service.py patches).

**Note on UI count:** Eigent UI shows "4 agents running" during workforce dispatch. This is correct, not a bug. It counts dispatched workers (`workforce._children`). Coordinator is the orchestrator, passed separately to the `Workforce(...)` constructor, and is not counted as a child. 4 workers + 1 Coordinator = 5 total.

---

## W2 — Workforce architecture audit (giga) `[AI]`

**Proves:** the 5-agent workforce is firing exactly as architected. Specifically:
- 4 dispatched workers + 1 Coordinator orchestrator run.
- Each worker exhibits behavior UNIQUE to its sys_prompt role.
- Workers run in parallel when Coordinator declares no dependency; sequential when it does.
- Parallel-stage workers do NOT see each other's first-pass output.
- Coordinator has zero tools and never produces tool output itself (chat_service.py:2540-2548 empty-tool patch).
- Verifier runs last with explicit dependency on Implementer's output.
- URL verification uses sensible redirect rules (HTTP 301/302/307/308 followed by 2xx = PASS, not FAIL).
- Every claim in the final doc traces to a tool call or verifiable artifact (anti-fabrication).

**Setup:** Before dispatching, create the workspace dir. The agent will write the final report there.

**Prompt (paste into Eigent multi-agent dispatch — replace `<TS>` with a timestamp like `2026-06-19T12-00`):**

```
You are running a Workforce Architecture Audit. Final deliverable: a structured results sheet at E:/tmp/wf-audit-<TS>/audit-report.md written by the Implementer, verified by the Verifier, with parallel contributions from the Researcher and Subject Analyst. The doc's primary purpose is to PROVE the 5-agent architecture is firing. Every claim must trace back to a tool call or a verifiable artifact on disk.

# Subject of the doc

Build a 600-900 word technical doc titled "How Eigent's 5-Agent Workforce Routes a Task: From Coordinator Dispatch to Verifier Sign-Off" that cites real files from E:/Eigent/resources/backend/app/. The doc must include five sections:

1. Architecture overview — name all 5 roles (Coordinator, Implementer, Researcher, Subject Analyst, Verifier) and cite the file:line where each is constructed.
2. Pipeline stages — explain how Coordinator declares dependencies between stages, quote the pipeline_order or dispatch_contract from COORDINATOR_SYS_PROMPT.
3. Tool surfaces — list the MCP tools each worker has access to (context7, scrapling, searxng, github, supabase, plus file tools).
4. Anti-fabrication rules — cite the rule text from SINGLE_AGENT_SYS_PROMPT or the depth-limited toolkit that prevents fabricated tool output.
5. Real example trace — walk through probes P1-P5 below, showing which agent did what.

# Audit probes (each role MUST contribute)

## P1 — Researcher probe (web/scrapling/context7)
Pick ONE tool and use it for real:
  (a) Fetch https://example.com via Scrapling fetch, return the <title> tag verbatim.
  (b) Query Context7 for camel-ai, return the doc URL.
  (c) SearXNG search for "Eigent CAMEL workforce", return the top result URL.
Record in the report: the exact tool name, the verbatim tool output, and the timestamp.

## P2 — Subject Analyst probe (parallel to P1, MUST NOT see P1's output)
Without reading any external URL, decompose this question: "What are the 3 most important files in Eigent's workforce pipeline? Rank by importance."
  - Identify at least 3 files from E:/Eigent/resources/backend/app/ (use Read or Glob, NOT web).
  - Do NOT reference any URL or external fact (those belong to Researcher).
  - Explain the reasoning behind the ranking.
  - End your section with exactly one of these two sentences:
      "PARALLEL_DISPATCH_CONFIRMED: I did not have access to the Researcher's output during this analysis."
      "SEQUENTIAL_DISPATCH_LEAKED: I was given the Researcher's output as a dependency."
    (If you genuinely don't know which, write SEQUENTIAL_DISPATCH_LEAKED — Coordinator should have given you the dependency or not, and you can tell by checking your input.)

## P3 — Implementer probe (depends on P1 + P2)
Write the final doc to E:/tmp/wf-audit-<TS>/audit-report.md.
  - Cite the dependency task IDs from P1 and P2 (Coordinator provides these in the dispatch payload).
  - Use the Write tool to create the file.
  - After writing, run a Read on the file to confirm it exists and report its size in bytes.

## P4 — Verifier probe (depends on P3, runs LAST)
Open E:/tmp/wf-audit-<TS>/audit-report.md and verify:
  - File exists and word count is between 600 and 900.
  - All file:line citations in section 1 actually point to real lines. For each citation, Read the cited file:line and confirm the line content matches the claim.
  - All URLs in the doc are reachable. URL rule (READ CAREFULLY):
      HTTP 200, 201, 204 = PASS.
      HTTP 301, 302, 307, 308 followed by a 2xx final response = PASS. These are normal redirects. Do NOT mark them FAIL.
      HTTP 4xx, 5xx = FAIL.
      Connection error, timeout, DNS failure = FAIL.
  - P1's verbatim output actually appears in the report verbatim.
Build a 5-column table in the report:
  | Claim or URL | Verification method | Result | HTTP code | Verdict |

## P5 — Coordinator self-report
The Coordinator's wrap-up must include:
  - The dispatch order: which worker fired in which pipeline stage.
  - The dependency declarations: which task IDs depended on which.
  - Confirmation: "Coordinator made 0 tool calls during this audit." If this is false, explain.
  - The list of task IDs created and which worker each went to.
  - One sentence: "Audit verdict: PASS" or "Audit verdict: FAIL (reason)".

# Output structure of E:/tmp/wf-audit-<TS>/audit-report.md

# How Eigent's 5-Agent Workforce Routes a Task

## 1. Architecture overview
[citations from E:/Eigent/ with file:line]

## 2. Pipeline stages
[Coordinator's pipeline explanation + quoted dispatch_contract]

## 3. Tool surfaces
[MCP tools per worker]

## 4. Anti-fabrication rules
[verbatim rule text from prompt.py or depth_limited_agent_toolkit]

## 5. Real example trace
[walk through probes P1-P5 showing which agent did what]

## 6. Audit results sheet

### P1 Researcher probe
- Tool used: <name>
- Verbatim output: <text>
- Timestamp: <ISO>

### P2 Subject Analyst probe
- Files identified: <list>
- Reasoning: <text>
- Dispatch verdict: PARALLEL_DISPATCH_CONFIRMED | SEQUENTIAL_DISPATCH_LEAKED

### P3 Implementer probe
- Dependency task IDs: <list from Coordinator>
- File written: E:/tmp/wf-audit-<TS>/audit-report.md
- Size: <bytes>

### P4 Verifier probe
| Claim or URL | Method | Result | HTTP | Verdict |
|---|---|---|---|---|
| ... | Read/open/HTTP | ... | 200/308/etc | PASS/FAIL |

### P5 Coordinator self-report
- Dispatch order: <list>
- Dependencies declared: <list>
- Coordinator tool calls: 0
- Task IDs: <list>
- Audit verdict: PASS | FAIL
```

**Pass criteria (all 10 must hold):**

1. File exists at the reported path with size between 3KB and 30KB.
2. The doc names all 5 roles verbatim (Coordinator, Implementer, Researcher, Subject Analyst, Verifier).
3. Section 1 cites at least 5 file:line references from `E:/Eigent/resources/backend/app/` that you can verify by opening each cited line and confirming the content matches.
4. P1 Researcher section contains a verbatim tool output that matches what that tool actually returns (e.g., "Example Domain" for example.com, a real Context7 URL, or a real SearXNG result URL).
5. P2 Subject Analyst section identifies at least 3 real files from `E:/Eigent/` (open each one and confirm it exists at the cited path).
6. P2 Subject Analyst section ends with exactly one of the two marker sentences. If it says `PARALLEL_DISPATCH_CONFIRMED`, the files it lists should not overlap with the Researcher's external findings. If it says `SEQUENTIAL_DISPATCH_LEAKED`, parallel dispatch is broken — investigate.
7. P3 Implementer section cites dependency task IDs that match the task IDs in P5 Coordinator's self-report.
8. P4 Verifier table has at least 5 rows with HTTP codes. Any 308-to-200 redirect MUST be marked PASS. If the Verifier marked a redirect as FAIL, the Verifier's URL rule prompt is not loaded or the prompt above was not honored.
9. P5 Coordinator self-report shows zero tool calls from Coordinator (this proves the empty-tools patch at chat_service.py:2540-2548 is intact) and lists a non-empty dispatch order.
10. The final audit verdict (PASS or FAIL) matches your independent read of the report.

**Fail hints per criterion:**

- (1) fails: Coordinator didn't dispatch, or Implementer couldn't write. Check `chat_service.py:2633-2643` asyncio.gather is intact (PATCHES.md P2). Check that `E:/tmp/` is writable.
- (2) fails: a role's sys_prompt is being dropped. Check prompt.py imports in chat_service.py and the four factory files (developer.py, browser.py, document.py, multi_modal.py).
- (3) fails: Researcher or Subject Analyst didn't read source files. Check MCP tools loaded (`healthtest.md` T17, T23). Check that BROWSER_SYS_PROMPT and DOCUMENT_SYS_PROMPT actually contain the new Researcher / Subject Analyst instructions, not the old "search the web" / "document processing" defaults.
- (4) fails: Researcher fabricated output (claimed tool result without calling the tool). Same anti-fabrication gap as `healthtest.md` T31. Known model-behavior ceiling on GLM-5.2.
- (5) fails: Subject Analyst didn't use Read/Glob on `E:/Eigent/`. Check that DOCUMENT_SYS_PROMPT (the Subject Analyst prompt) instructs source-file reading.
- (6) fails with `SEQUENTIAL_DISPATCH_LEAKED`: dependency routing is leaking across parallel stages. This is a CAMEL workforce.py concern. Check whether Coordinator declared dependencies it shouldn't have, or whether camel's worker dependency-injection is over-eager.
- (7) fails: Coordinator didn't pass dependency task IDs to Implementer. Check `COORDINATOR_SYS_PROMPT` dispatch_contract section is present and the Coordinator is following it.
- (8) fails: Verifier's URL rule is too strict. The prompt above explicitly says 308-to-200 = PASS. If Verifier still marked it FAIL, the VERIFIER_SYS_PROMPT (or legacy MULTI_MODAL_SYS_PROMPT) is not loaded, or the model ignored the explicit rule.
- (9) fails with non-zero Coordinator tool calls: the empty-tools patch at `chat_service.py:2540-2548` was reverted, or Coordinator is being created via a different code path that gives it tools. Re-apply PATCHES.md P2.
- (10) fails: workforce output contradicts itself. Cross-reference P4 Verifier table against P5 Coordinator verdict and identify which agent produced the inconsistent claim.

**Notes:**
- The "4 agents running" indicator in the Eigent UI is correct, not a bug. It counts dispatched workers (`workforce._children`), and Coordinator is the orchestrator, not a counted worker. 4 workers + 1 Coordinator = 5 total.
- Cosmetic known issue: the Researcher slot's internal `role_name` is still the literal string `"Browser Agent"` (browser.py:399) for legacy reasons. This is a label only; routing is driven by the worker description string in chat_service.py (`add_single_agent_worker("Researcher Agent: ...")`), not by role_name. Do not treat "Browser Agent" in any worker self-identification as a bug.

---

## Final checklist

- [ ] W1 smoke test passes (workforce can be triggered at all).
- [ ] W2 giga audit passes all 10 criteria.
- [ ] If you intend to use workforce mode in production, re-run W2 after every Eigent update or prompt.py edit.
