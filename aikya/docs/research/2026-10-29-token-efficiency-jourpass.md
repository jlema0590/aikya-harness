# Token-efficiency investigation: jourpass_app

Date: 2026-10-29. Source revision: `512dea2`.
Scope: read-only investigation of the user-identified local project, its main
Claude transcript from 2026-10-28 and the two subagent transcripts belonging to
that session. No project source, settings, runtime or private memory was changed.
This report contains usage metadata, not transcript text or application code.

## Conclusion

There is a verified gap between maintaining local Memory and using it to reduce
model context. In this Flutter project, the current index stores 153 Dart files
as `file_only`, with no Dart class/method symbols. The normal analyze/mobile
workflows do not require an indexed lookup before reading source. The selected
session also carried a large growing history and used additional agents.

The user reports about 50% of account usage consumed after analyze and mobile
work. That percentage cannot be independently verified or assigned to those two
commands from transcript tokens: no provider quota samples from before/after
the work were supplied. The observed session contains three analyze invocations,
two mobile-feature invocations, Memory, architecture review and intervening
conversation/plugin activity. Counts below separate chronological intervals;
they are not a per-command bill or a causal quota allocation.

## Observed session usage

The main session spans 14:42:32–18:05:57 UTC on 2026-10-28. Streaming/replayed
assistant records are deduplicated by message identity using the existing
aggregator, keeping the largest cumulative usage in each category. Tool calls
are separately deduplicated by tool-use ID; counting raw transcript blocks
would overstate activity.

| Recorded category, main plus two subagents | Tokens |
|---|---:|
| Uncached input | 455 |
| Cache creation | 800,904 |
| Cache reads | 36,622,945 |
| Output | 191,016 |
| Sum of recorded categories | 37,615,320 |

**97.36% of this sum is cache reads.** This is cumulative processing across
requests, not 37.6 million unique tokens or a single context window. Cache reads
are meaningful usage; they should neither be treated as newly read code nor
discarded as free. Anthropic documents the separate input fields and their
[sum](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).
No API price estimate or conversion into subscription quota is made here.

| Actor | Distinct usage-bearing messages | Observed model |
|---|---:|---|
| Main conversation | 168 | `claude-opus-4-7` |
| Subagent A | 56 | `claude-opus-4-7` |
| Subagent B | 20 | `claude-sonnet-5-5` |
| Total | 244 | Recorded, not inferred from configuration |

The main conversation's first recorded input is 77,242 tokens, its mean input
per distinct message is 192,734 and its maximum is 336,173. Input here includes
uncached input, cache creation and cache reads. This measures recorded request
input, not a claim about the model's advertised window capacity.

Chronological intervals between Aikya slash-command markers:

| Interval | Main messages | Subagent messages | Recorded tokens, including cache |
|---|---:|---:|---:|
| Three analyze markers, before Memory | 64 | 76 | 13,389,086 |
| Memory marker to first mobile marker | 89 | 0 | 19,570,855 |
| Two mobile markers, before architecture review | 9 | 0 | 2,704,540 |
| Architecture-review marker to session end | 6 | 0 | 1,950,839 |

Follow-up requests and plugin activity share these windows. In particular,
**the 89 messages in the Memory window are not 89 model calls made by the local
Memory exporter**. That interval includes 60 distinct Bash calls, 14 Reads,
9 Writes, 20 Edits, task tracking and other conversational activity. Three
`hook_blocking_error` attachments identify `stop_docs.py` at 15:40:46, 16:08:35
and 16:24:17 UTC. They document additional blocked completions; the exact tokens
caused by each block are not isolated.

## Verified implementation and configuration findings

### 1. Dart is inventoried, without symbol-level retrieval

Current read-only index inspection returns generation 7, status `complete`,
209 files and eight symbols. All eight symbols belong to Python. File statuses
include 153 Dart, seven TypeScript, 41 SQL and native mobile files as `file_only`.
Code-index policy enables observation and automatic export.

`complete` currently means the bounded index operation completed; it does not
mean every language has semantic coverage. The parser registry supports Python
and optional Java/JavaScript/TypeScript/C#/Go adapters. Dart has no adapter.
The fallback query constructs file entries from lines 1–20 and matches file
paths, rather than class/method names. Even a fresh HTML graph therefore does
not provide the Dart symbol memory expected for this project.

Evidence: [parser registry](../../../src/aikya/code_index/parsers/registry.py),
[optional adapters](../../../src/aikya/code_index/parsers/treesitter.py),
[query behavior](../../../src/aikya/code_index/query.py).

### 2. Automatic maintenance does not imply automatic retrieval

The observer's Memory hook maintains leases, dirty hints and the local watcher.
It does not inject task-scoped indexed code into the normal command context.
Both installed project/global analyze and mobile-feature instructions lack an
indexed lookup or reference-recall step. No recognizable code-index query or
reference-recall command was found in the selected tool activity; one explicit
Memory-file Read is present. This search is not proof that no alternative
retrieval mechanism could have been used.

Automatic code-context retrieval exists in the optional loop, which only allows
feature, bugfix and implement. It does not cover mobile-feature directly.
Reference-note recall in that loop defaults to a zero-character budget. Its
code query is bounded to 6,000 characters and uses an empty query within the
approved file allowlist; this can favor early sorted symbols over task relevance.

Evidence: [Memory hooks](../../../src/aikya/code_index/hooks.py),
[observer](../../../src/aikya/middleware/observer.py),
[loop](../../../src/aikya/core/loop.py).

### 3. History and delegation multiply processed context

The first analyze interval contains two Agent invocations and all 76 subagent
messages. Main-session and subagent reads/searches add separate context. The
deduplicated activity includes 125 main Bash calls and 23 main Reads, plus 55
subagent Bash calls and 29 subagent Reads. Bash text classification finds many
file-reading commands; these are not counted as proof of any specific file's
contents or of unnecessary work. Only four main paths were read twice through
Read, so repeated Read calls alone do not explain millions of tokens.

Current global settings select Opus. Current Flutter agent metadata has high
effort and a 60-turn allowance; current planner/orchestrator defaults select
Opus with high effort. Historical model use is established by the transcript,
not by today's settings. The recorded Flutter subagent actually used Sonnet.
No claim is made that all installed agents ran or all skill bodies were loaded.

Anthropic explains that [long history, tool turns and subagents](https://code.claude.com/docs/en/costs)
contribute additional usage, including repeated cached context.

### 4. Efficiency instructions are mostly advisory

The context rule recommends bounded reads and avoiding unnecessary delegation.
The static context estimator has an optional ceiling and explicitly does not
measure the provider tokenizer or bills. Normal interactive commands have no
enforced cumulative task token budget.

The opt-in SDK loop has real cost/time/iteration controls, but `max_turns` is
passed to each implementation/review query. It is not a cumulative turn allowance
for the whole task. Review uses a separate context, and resumed implementation
queries append workflow instructions and context again. These observations do
not establish that the optional SDK loop ran in this session.

Shared workflow instructions are another, smaller source of overhead. At a
rough 3.5-character proxy, the shipped template's visible instructions/metadata
estimate 3,356 tokens; analyze adds about 1,667 when invoked. Such estimates
exclude provider prompts, tools, actual installed selection and conversation
history. They cannot alone explain the measured request sizes.

### 5. The displayed quantities need distinct labels

`metrics.cache_usage()` sums input, output and both cache categories into
`session_tokens`; it preserves category totals but a single displayed total
obscures the difference. Account 5h/7d percentages are taken separately from
the runtime, not derived from this sum. The mod's exact displayed two-million
value was not captured, so its aggregation scope is unverified.

Anthropic defines the [5-hour and 7-day status-line percentages](https://code.claude.com/docs/en/statusline)
as consumed rate-limit percentages. Neither hiding Usage nor removing a status
line reduces the model requests already being made.

## Recommended order of corrective work

1. **Add trustworthy Dart symbol support and surface language coverage.** Verify
   class/method ranges, source hashes and invalidation. Show file-only coverage
   explicitly; never manufacture symbols or hide incomplete semantic coverage.
2. **Make task-scoped retrieval the normal entry point.** Integrate it into
   mobile/feature/bugfix workflows; use relevant symbols, paths and changed-file
   evidence first, with direct bounded reads when freshness or missing coverage
   requires them. Do not preload the full graph, HTML or documentation library.
3. **Separate adoption from optional deep audits.** Keep deterministic analyze
   discovery local, save full plans as reviewable artifacts and return a concise
   summary. Invoke architecture/security specialists only for the requested
   scope and risk. Preserve authorization and required security checks.
4. **Automate bookkeeping and prevent avoidable retries.** Move execution-phase
   recording and repetitive status handling into local code where the underlying
   action provides evidence. Check documentation obligations before completion;
   keep truthful REQ audits and security gates rather than disabling them.
5. **Apply configurable task budgets and deliberate model routing.** Keep the
   user's model choice explicit. Distinguish cumulative limits from per-query
   limits in the SDK loop. In an interactive external Claude session, start with
   measured warnings and bounded context; Aikya cannot promise global enforcement
   of provider account quota or control of every model request.
6. **Measure the same accepted task before and after.** Record uncached input,
   cache creation/read, output, distinct requests, agent share and retrieval
   coverage. Capture account percentages with timestamps/reset boundaries if
   quota attribution is desired. Do not promise a saving percentage before this
   comparison; preserve test, review and acceptance quality.

## Verification and limits

Nineteen existing tests passed: token-efficiency 11, runtime metrics five and
context classification/proxy three. A synthetic 25-request fixture produced
2,012,500 cumulative tokens, including 2,000,000 cache reads, confirming that a
large total alone does not establish unique context or a quota percentage.

The investigation made no model/API calls to reproduce the application work.
No raw transcript, application source, secrets or provider billing data was copied
into this repository. Only this report, its sanitized metadata receipt and the
documentation index were added/updated. No runtime fix, release, commit or push
is part of this investigation.

[Sanitized usage and coverage receipt](2026-10-29-token-efficiency-jourpass.json)
contains the exact interval boundaries, category totals and test counts.

GENERATED BY AIKYA HARNESS
