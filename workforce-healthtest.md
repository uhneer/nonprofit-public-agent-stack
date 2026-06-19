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

## Audit output location & naming convention (mandatory)

All workforce audit artifacts go to **`E:/Logseq/audits/`** (create the dir if missing). Two artifact types:

1. **Workforce-produced audit doc** (the W2 deliverable): `E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/audit-report.md`. Same dir also gets `audit-report.json` (machine-readable Verifier table).
2. **Audit run record** (the human/agent's summary of running the audit, written separately from the workforce output): `E:/Logseq/audits/audit-YYYY-MM-DD-NN.md`.

Naming rules:
- `YYYY-MM-DD` is today's date.
- `NN` is a zero-padded sequence number starting at `01`. Bump NN for every new run on the same day, regardless of which artifact type.
- Before creating, `ls E:/Logseq/audits/` to find the highest existing NN for today, then use NN+1.
- Example: first run on 2026-06-19 → workforce writes `wf-audit-2026-06-19-01/audit-report.md`, run record is `audit-2026-06-19-01.md`. Second run same day → `02` for both.

**Agents running audits MUST be told this in the prompt.** The W1 and W2 prompts below already include the `E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/` path. If you write a new audit prompt, hard-code the same path scheme.

**Front-facing chat output is mandatory.** After every workforce audit, the dispatching agent (or the human running it) MUST report a PASS/FAIL verdict in the chat, not just "the doc is at X". Users don't open .md files. The doc is for the AI to fix issues; the chat is for the human to see status. See W1 and W2 output-format sections below.

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

**Required chat output (after dispatch completes):**
```
W1 SMOKE TEST
Verdict: PASS | FAIL
Worker fired: <name>
Page title returned: <text>
Dispatch log excerpt: <1-2 lines>
One-sentence evidence: <why this passes or fails>
```

**Fail hint:** if dispatch fails or only the Single Agent responds, multi-agent routing isn't configured. Check Settings → Agents to verify all 5 roles are enabled, and re-verify `healthtest.md` T13b (chat_service.py patches).

**Note on UI count:** Eigent UI shows "4 agents running" during workforce dispatch. This is correct, not a bug. It counts dispatched workers (`workforce._children`). Coordinator is the orchestrator, passed separately to the `Workforce(...)` constructor, and is not counted as a child. 4 workers + 1 Coordinator = 5 total.

---

## W2 — Workforce architecture audit (giga) `[AI]`

**Proves:** the 5-agent workforce is firing exactly as architected. Specifically:
- 4 dispatched workers + 1 Coordinator orchestrator run.
- Each worker exhibits behavior UNIQUE to its sys_prompt role.
- Workers run in parallel when Coordinator declares no dependency; sequential when it does.
- Parallel-stage workers do NOT see each other's first-pass output.
- Coordinator has zero tools and never produces tool output itself (chat_service.py:2540-2548 — `agent_model(key, BaseMessage, options, [])` where `[]` is the empty tools list as the 4th positional arg).
- Verifier runs last with explicit dependency on Implementer's output.
- URL verification uses sensible redirect rules (HTTP 301/302/307/308 followed by 2xx = PASS, not FAIL). The rule lives in two places: (a) the user-prompt below, and (b) the `<url_verification>` block inside `MULTI_MODAL_SYS_PROMPT` at `app/agent/prompt.py` so it applies even if the user-prompt is forgotten.
- Every claim in the final doc traces to a tool call or verifiable artifact (anti-fabrication).

**Naming scheme for audit artifacts (mandatory):**
- Workspace dir: `E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/` where `YYYY-MM-DD` is today's date and `NN` is a zero-padded sequence number starting at `01`. Bump NN if you re-run on the same day.
- Final report: `audit-report.md` inside that dir.
- Verifier table also exported as `audit-report.json` for machine parsing.
- Example: first run on 2026-06-19 → `E:/Logseq/audits/wf-audit-2026-06-19-01/audit-report.md`. Second run same day → `wf-audit-2026-06-19-02/`.
- Run record (separate from the workforce output, written by whoever ran the audit): `E:/Logseq/audits/audit-YYYY-MM-DD-NN.md`.

**Preflight (must pass before dispatch):**
- Eigent backend alive on port **5001** (NOT 8000). Quick check: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/health` should return `200` within 2s. If it returns `000` (timeout), the backend event loop is hung — see "Backend hang recovery" below.
- `.mcp.json` at workspace root (`E:/Logseq/.mcp.json`), not at `E:/Eigent/`. T17 in `healthtest.md` covers this.
- `E:/Logseq/audits/` writable (create if missing).

**Backend hang recovery:** if the preflight curl returns `000` repeatedly, the asyncio event loop is blocked (likely a stuck prior chat dispatch). Close and restart Eigent.exe, OR `taskkill /PID <pid> /F` the uvicorn process holding port 5001, then relaunch Eigent. Restart loses in-UI session state. This is the only known recovery. See PATCHES.md P12 for diagnosis status.

**Prompt (paste into Eigent multi-agent dispatch — replace `YYYY-MM-DD` with today's date and `NN` with the next sequence number from `ls E:/Logseq/audits/`):**

```
You are running a Workforce Architecture Audit. Final deliverable: a structured results sheet at E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/audit-report.md written by the Implementer, verified by the Verifier, with parallel contributions from the Researcher and Subject Analyst. The doc's primary purpose is to PROVE the 5-agent architecture is firing. Every claim must trace back to a tool call or a verifiable artifact on disk.

# MANDATORY front-facing chat output

After the workforce finishes and the Verifier signs off, the Coordinator MUST emit a single chat message to the user with this exact shape (in addition to the doc on disk). Users do not open .md files. The chat IS the deliverable for them; the doc is for follow-up AI work.

```
W2 WORKFORCE AUDIT — YYYY-MM-DD-NN
Verdict: PASS | FAIL
Criteria (10):
  1. File exists, 3-30KB                 PASS | FAIL | NA
  2. All 5 roles named                   PASS | FAIL | NA
  3. 5+ file:line citations              PASS | FAIL | NA
  4. P1 Researcher verbatim tool output  PASS | FAIL | NA
  5. P2 Subject Analyst 3+ files         PASS | FAIL | NA
  6. P2 parallel-dispatch marker         PASS | FAIL | NA
  7. P3 Implementer dep task IDs match   PASS | FAIL | NA
  8. P4 Verifier redirect rule honored   PASS | FAIL | NA
  9. P5 Coordinator 0 tool calls         PASS | FAIL | NA
  10. Final verdict matches reality      PASS | FAIL | NA
Doc: E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/audit-report.md
JSON: E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/audit-report.json
One-sentence summary: <what happened>
Top failure (if any): <criterion N — one-sentence root cause>
```

If the workforce cannot produce the doc (e.g., backend hung, dispatch failed), the Coordinator still emits the chat block with all criteria marked FAIL or NA and a one-sentence reason. Silence is not acceptable.

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
Write the final doc to E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/audit-report.md.
  - Cite the dependency task IDs from P1 and P2 (Coordinator provides these in the dispatch payload).
  - Use the Write tool to create the file.
  - After writing, run a Read on the file to confirm it exists and report its size in bytes.

## P4 — Verifier probe (depends on P3, runs LAST)
Open E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/audit-report.md and verify:
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

# Output structure of E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/audit-report.md

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
- File written: E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/audit-report.md
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
- (8) fails: Verifier's URL rule is too strict. The rule is encoded in TWO places: (a) the user-prompt above, and (b) the `<url_verification>` block in `MULTI_MODAL_SYS_PROMPT` at `app/agent/prompt.py:273-283`. If Verifier still marked a 308-to-200 as FAIL, either both prompt locations were not loaded, or the model ignored the explicit rule (deeper model-behavior issue).
- (9) fails with non-zero Coordinator tool calls: the empty-tools patch at `chat_service.py:2540-2548` (`agent_model(..., options, [])` where `[]` is the 4th positional arg) was reverted. The patch is positional, not keyword — a grep for `tools=[]` will return no matches even when the patch is present. To verify, read lines 2540-2548 directly and confirm the `[]` arg is there. Re-apply PATCHES.md P2 if missing.
- (10) fails: workforce output contradicts itself. Cross-reference P4 Verifier table against P5 Coordinator verdict and identify which agent produced the inconsistent claim.

**Notes:**
- The "4 agents running" indicator in the Eigent UI is correct, not a bug. It counts dispatched workers (`workforce._children`), and Coordinator is the orchestrator, not a counted worker. 4 workers + 1 Coordinator = 5 total.
- Cosmetic known issue: the Researcher slot's internal `role_name` is still the literal string `"Browser Agent"` (browser.py:399) for legacy reasons. This is a label only; routing is driven by the worker description string in chat_service.py (`add_single_agent_worker("Researcher Agent: ...")`), not by role_name. Do not treat "Browser Agent" in any worker self-identification as a bug.

---

## W3 — Production workload simulator `[AI]`

**Proves:** the workforce can one-shot a real production-style research task from scratch. This is the test that validates workforce mode for actual use, not just architectural correctness. W1 and W2 prove the wiring works; W3 proves the workforce can do useful work with that wiring.

**Scope:** the workforce researches a niche technical subject, evaluates candidates against requirements, and writes a verbose 1500-2500 word deliverable doc with real verifiable claims (URLs, versions, licenses, stars). This mirrors how a user would one-shot a research project by asking the workforce "find the best open-source X for Y and write up the recommendation."

**Naming scheme for artifacts (mandatory):**
- Workspace dir: `E:/Logseq/audits/wf-proj-YYYY-MM-DD-NN/` (note: `wf-proj-`, not `wf-audit-`).
- Final deliverable: `deliverable.md` inside that dir.
- Run record: `E:/Logseq/audits/audit-YYYY-MM-DD-NN.md` (same scheme as W2).
- Use the next NN from `ls E:/Logseq/audits/`.

**Prompt (paste into Eigent multi-agent dispatch — replace `YYYY-MM-DD` with today's date, `NN` with next sequence number, and `[SUBJECT]` with one of the subjects listed below or your own):**

```
You are running a Production Workload Simulation. Final deliverable: a verbose 1500-2500 word technical doc at E:/Logseq/audits/wf-proj-YYYY-MM-DD-NN/deliverable.md. This simulates a user one-shotting a large research project from scratch. Every claim must trace to a real tool call (Scrapling fetch, SearXNG search, GitHub MCP, Context7). Fabricated URLs, versions, or licenses are a hard fail.

# MANDATORY front-facing chat output

After the workforce finishes and the Verifier signs off, the Coordinator MUST emit a single chat message with this exact shape. Users do not open .md files. The chat IS the deliverable for them.

```
WF-PROJ YYYY-MM-DD-NN
Subject: <one-line>
Verdict: PASS | FAIL
Top recommendation: <name + one-line reason>
Doc: E:/Logseq/audits/wf-proj-YYYY-MM-DD-NN/deliverable.md
Verifier stats: <URLs checked> URLs / <PASS> pass / <FAIL> fail | <claims checked> claims / <verified> verified
Confidence: HIGH | MEDIUM | LOW — <one-sentence reason>
Next steps for the operator: <2-3 concrete actions or open questions>
```

If the workforce cannot produce the doc, the Coordinator still emits this block with Verdict: FAIL and a one-sentence reason. Silence is not acceptable.

# Subject

[SUBJECT]

Example subjects (pick one or substitute your own of similar scope):
- Find the best open-source finite-state-machine library for Python with async transition support, under active maintenance (commits in last 90 days), and write a getting-started example.
- Identify the top 3 self-hostable web analytics tools with no cookies, no GDPR consent requirement, and sub-1MB client script size. Include a deployment sketch for the top pick.
- Research SOTA for running LLMs locally on Windows with an AMD GPU (not NVIDIA). Cover Vulkan vs ROCm vs DirectML paths, and recommend the best stack as of today.
- Find a minimalist open-source CRDT library that supports rich-text collaboration and has Python bindings. Compare against Yjs and Automerge for ease of integration.
- Identify the best open-source headless CMS with a SQLite backend and a REST/GraphQL API. Must not require Node at runtime.

# Pipeline

## Stage 1 (PARALLEL — Researcher and Subject Analyst MUST NOT see each other)

Researcher: real tool calls only (Scrapling fetch, SearXNG search, GitHub MCP, Context7). Identify 4-6 candidate projects that fit the subject. For each, collect: name, repo URL, star count, latest version, release date, license, primary language, last-commit date, and a one-sentence description. GitHub MCP for star count and license (NOT hallucinated); Scrapling for README content; Context7 for docs.

Subject Analyst (parallel to Researcher, MUST NOT see Researcher's output): decompose the subject into 6-10 evaluation criteria without looking at external sources. Rank criteria by importance. Example criteria: activity (last commit < 90 days), license permissiveness, docs quality, API ergonomics, test coverage, binary size, dependency count, community size, platform compatibility, performance. End section with one marker:
  "PARALLEL_DISPATCH_CONFIRMED: I did not have access to the Researcher's output."
  "SEQUENTIAL_DISPATCH_LEAKED: I was given the Researcher's output as a dependency."

## Stage 2 (depends on Stage 1 — Implementer)

Write deliverable.md. 1500-2500 words. Sections in this order:
  1. Executive Summary (150-200 words) — top pick + 2-sentence rationale.
  2. Requirements Decomposition — Subject Analyst's criteria, presented as a ranked list.
  3. Per-Candidate Deep Dive — one subsection per candidate, 150-250 words each. For each: what it is, what it does well, where it falls short, real star count, real license, real last-commit date.
  4. Comparison Matrix — markdown table with all candidates × all criteria. Cells must be concrete (e.g., "12,345 stars" not "popular"; "MIT" not "permissive"; "2026-05-14" not "recent").
  5. Recommendation + Rationale — top pick, second pick, why, what would change the recommendation.
  6. Risks and Trade-offs — maintenance risk, license risk, vendor lock-in, migration cost if the pick fails.
  7. Getting-Started Code Sample — copy-pasteable snippet for the top pick (10-30 lines).

## Stage 3 (depends on Stage 2 — Verifier, runs LAST)

Open E:/Logseq/audits/wf-proj-YYYY-MM-DD-NN/deliverable.md and verify:
  - Word count is 1500-2500.
  - Every GitHub URL: fetch via Scrapling or GitHub MCP, confirm star count, license, last-commit date all match what the doc claims (±5% on stars, exact on license and date).
  - Every external URL: reachable per the <url_verification> rule (HTTP 308 → 2xx = PASS; HTTP 4xx/5xx = FAIL).
  - Comparison matrix has no empty cells.
  - Getting-Started code sample is syntactically valid for the stated language.
Build a verification table in a new file `E:/Logseq/audits/wf-proj-YYYY-MM-DD-NN/verifier-report.md`:
  | Claim in deliverable | Verification method | Expected | Actual | Verdict |

## Stage 4 (Coordinator wrap)

Emit the front-facing chat block (see above). Include: dispatch order (Stage 1 parallel → Stage 2 → Stage 3 → Stage 4), task IDs assigned to each worker, confirmation "Coordinator made 0 tool calls during this workload."

# Output structure

deliverable.md follows the 7-section structure above. No sections skipped. No "TODO" placeholders. No "the workforce could not..." cop-outs — if a candidate doesn't have a piece of data, say "not available" and explain the gap, do not fabricate.
```

**Pass criteria (all 8 must hold):**

1. Doc exists at the reported path, size 8-40KB, word count 1500-2500.
2. All 7 sections present in order, none empty.
3. At least 4 candidates evaluated in Section 3 with real verifiable GitHub URLs.
4. Section 4 comparison matrix has zero empty cells and zero "TBD" / "unknown" values (unknowns go in Section 6 Risks).
5. Every star count, license, and last-commit date in the doc matches what GitHub MCP or a Scrapling fetch of the repo returns (±5% on stars; exact on license and date).
6. Every URL in the doc is reachable per the 308-to-2xx rule. A 308 that resolves to 200 MUST be marked PASS.
7. Subject Analyst's section ends with PARALLEL_DISPATCH_CONFIRMED (not SEQUENTIAL_DISPATCH_LEAKED).
8. Coordinator's front-facing chat block is emitted with Verdict matching the Verifier's report.

**Fail hints per criterion:**

- (1) fails: Implementer didn't write, or wrote too short/long. Check word count in the doc; if short, Implementer may be summarizing instead of decomposing (prompt compliance issue, not architecture issue).
- (2) fails: a section was skipped. Implementer prompt compliance issue.
- (3) fails: Researcher didn't do real tool calls, or only surfaced 1-2 candidates. Check `healthtest.md` T17 (MCP loading) and T23 (Scrapling).
- (4) fails with empty cells: Implementer took shortcuts. Prompt compliance.
- (5) fails: Researcher fabricated data (the big risk). Same anti-fabrication ceiling as W2 criterion 4. Cross-check against GitHub MCP — if MCP returns a different number, the doc is wrong.
- (6) fails: Verifier's URL rule didn't load, or Verifier didn't run. Check that MULTI_MODAL_SYS_PROMPT still contains the `<url_verification>` block (PATCHES.md P11).
- (7) fails with SEQUENTIAL_DISPATCH_LEAKED: same parallel-dispatch bug as W2 criterion 6. CAMEL workforce.py dependency injection is leaking.
- (8) fails: Coordinator didn't emit chat output, or emitted a Verdict that contradicts Verifier. Re-run W2 to isolate.

**Notes:**
- W3 is the test to re-run when you change anything about how the workforce does real work: prompt.py edits, MCP config changes, asyncio.to_thread patches. W2 catches architectural regressions; W3 catches "the workforce can still produce useful output."
- If W3 fails on (5) fabrication, that is a model-behavior issue (GLM-5.2 ceiling), not an architecture bug. The fix is parent-side verification (Verifier catches the fabrication), which W3's Stage 3 does test.

---

## W4 — URL rule isolation test (Verifier-only) `[AI]`

**Proves:** the `<url_verification>` block in MULTI_MODAL_SYS_PROMPT (PATCHES.md P11) is loaded and honored. This is the cheap regression test for the 308-to-200 false-fail rule — no full workforce dispatch, no Implementer, no doc. Just the Verifier answering 3 URLs.

**Why this exists:** W2 and W3 both require a full workforce dispatch, which at GLM-5.2 token costs is expensive to re-run every time you tweak prompt.py. W4 isolates the one rule most likely to silently break (because it was added late and lives in a specific block of MULTI_MODAL_SYS_PROMPT).

**Naming scheme for artifacts:**
- No file artifacts required. The chat output IS the deliverable.
- Optional: if you want a record, save the Verifier's raw output to `E:/Logseq/audits/wf-url-YYYY-MM-DD-NN.md` (use `wf-url-` prefix to distinguish from `wf-audit-` and `wf-proj-`).

**Prompt (paste into Eigent — this routes to Verifier only, no full workforce dispatch needed):**

```
Verifier-only micro-test. Do NOT invoke Researcher, Subject Analyst, or Implementer. You are the Verifier; answer directly.

Verify these 3 URLs and emit the standard Verifier output schema (VERDICT / EVIDENCE / FIX / ESCALATION) for each:

1. https://openhands.dev  (known 308 redirect to www.openhands.dev)
2. https://docs.openhands.dev  (known 308 redirect)
3. https://github.com/OpenHands/OpenHands  (straight 200, no redirect)

Fetch each with redirects enabled. Report the final HTTP code and final URL after redirects, then verdict.

Per the <url_verification> block in your sys_prompt (MULTI_MODAL_SYS_PROMPT at app/agent/prompt.py), the rule is strict:
  - HTTP 200, 201, 204 = PASS.
  - HTTP 301, 302, 307, 308 that resolves to a 2xx final response = PASS. Do NOT mark these FAIL.
  - HTTP 4xx, 5xx = FAIL.
  - Connection error, timeout, DNS failure = FAIL.

A 308-to-200 marked as FAIL is a regression. The rule is not loaded or not honored.

# MANDATORY front-facing chat output

```
W4 URL RULE TEST — YYYY-MM-DD-NN
URL | final HTTP | verdict
1. https://openhands.dev            | <code> | PASS | FAIL
2. https://docs.openhands.dev       | <code> | PASS | FAIL
3. https://github.com/OpenHands/... | <code> | PASS | FAIL
Rule loaded: YES | NO
Regression: YES | NO
```

All 3 rows should be PASS. If row 1 or 2 is FAIL, the URL rule is broken.
```

**Pass criteria (all 3 must hold):**

1. Row 1 (openhands.dev) returns PASS with a 2xx final HTTP code (typically 200 after 308 → www.openhands.dev).
2. Row 2 (docs.openhands.dev) returns PASS with a 2xx final HTTP code.
3. Row 3 (github.com/OpenHands/OpenHands) returns PASS with HTTP 200.

**Fail hints:**

- (1) or (2) fails with FAIL: the Verifier is marking 308 redirects as fails. Either the `<url_verification>` block in MULTI_MODAL_SYS_PROMPT was removed/reverted, or the model is ignoring it. Check `E:/Eigent/resources/backend/app/agent/prompt.py` for the `<url_verification>` block (around line 273-283). If missing, re-apply PATCHES.md P11.
- (3) fails: unrelated to P11. The GitHub URL is genuinely down, or Scrapling is broken. Check `healthtest.md` T23.
- Verifier invokes other workers: the routing is wrong, or the prompt wasn't pasted as a Verifier-only message. Re-paste the prompt.

**Notes:**
- W4 should take under 30 seconds and cost under 5K tokens. Run it every time you edit prompt.py.
- If you change the URL rule text in MULTI_MODAL_SYS_PROMPT, update this test's "known 308 redirect" URLs to match — or keep them stable as a regression baseline.

---

## Final checklist

- [ ] W1 smoke test passes (workforce can be triggered at all).
- [ ] W2 architecture audit passes all 10 criteria.
- [ ] W3 production workload simulator passes all 8 criteria with a real subject. This is the test that validates workforce mode for actual use, not just architectural correctness.
- [ ] W4 URL rule isolation test passes all 3 rows. Run this after every prompt.py edit.
- [ ] After any Eigent update, prompt.py edit, or chat_service.py patch: re-run W4 (cheap, ~5K tokens), then W2 (medium, ~200-500K tokens), then W3 (expensive, ~500K-2M tokens) only if W2 caught nothing but you need to confirm real-work output still works.
- [ ] Audit artifacts stored at the correct path scheme: `E:/Logseq/audits/wf-audit-YYYY-MM-DD-NN/` (W2), `E:/Logseq/audits/wf-proj-YYYY-MM-DD-NN/` (W3), optional `E:/Logseq/audits/wf-url-YYYY-MM-DD-NN.md` (W4).
- [ ] Run record at `E:/Logseq/audits/audit-YYYY-MM-DD-NN.md` covers what was run, what passed/failed, and any anomalies.
- [ ] Front-facing chat output emitted for every workforce run. Users saw the verdict without opening the doc.
