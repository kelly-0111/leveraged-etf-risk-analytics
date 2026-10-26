# Result-cache experiment (E3): Part A, draft for approval

Author: contributed by both the project author and Claude Code. Claude Code proposed this design,
drafted this document and wrote the tooling (`src/etf_risk/cache_experiment.py`,
`analysis/collect_result_cache_measurements.py`, `docs/result-cache-session.zsh` and their tests).
The author makes every decision and approval: the decisions taken so far are in section 1, and
the ones this draft asks for are in section 9. Nothing here is approved yet, and no formal batch
has run.

## 1. Question and scope

**E3 (spec §11):** how much latency does the result cache save for repeated summary queries,
compared with a new Spark process and with a warm Spark session, at which hit rates, and what
happens when Redis is down?

Decided by the author (2026-10-26):
- Claude Code drafts the proposals and the answers; the author decides, reviews and approves,
  with joint credit (the M3 arrangement).
- Formal batches use only the registered historical run, `run-20261013T043848Z-4`
  ([result-cache.md](result-cache.md), section 2). The job-run path through a MySQL job table is
  covered separately by a functional check outside any formal batch:
  `tests/test_resolver_mysql_live.py` passed 4 of 4 on 2026-10-26. That covers an accepted job
  resolving and only reading, refusals, and a job whose accepted folder is a copy of the
  registered run answered from the registered run's cache entry. It is not a measurement.
- Clearing the cache deletes only the experiment's own keys, by name. `FLUSHDB` and pattern
  deletes are never used.
- Competing containers are monitored for the whole session, including starts between readings.
- The 4.0 GiB idle-memory gate of M2 is not reused as a timing rule without justification
  (section 5).

## 2. Configurations, and what each one measures

| | Process | Resolution per request | Cache |
|---|---|---|---|
| **N** | a new process per request (`summary --no-cache query`) | a **full hash** of the run folder (101 files, 45 MB) | none |
| **W** | one warm process per block (`summary --no-cache serve`) | the **warm stat check**; a full hash only on the process's first request, which is a warm-up | none |
| **R** | like W (`summary serve`) | the warm stat check | Redis; the block's hit rate is set by repeats |
| **F** | like R | the warm stat check | Redis stopped after phase 1, started again before phase 3 |

**Reading N, W and R apart.** The resolution differs by configuration, so its cost is reported on
its own: the server's `seconds.resolve`, next to the client's latency. In the dry runs:
- **N's full hash** took 75–170 ms of a 9.4–15 s request. Process start-up, imports and a new
  SparkSession are the rest.
- **The warm stat check** took about 7.5 ms. That is most of a warm hit (8.5–17 ms): Redis's
  GET and the decoding are about 1 ms.

So the reports compare:
- **R's hits with W:** what the cache saves over a warm session;
- **R's misses with W:** what the cache costs when it misses;
- **N with W:** what a warm process saves.

A one-shot process with Redis is not a configuration here. Its hits would still pay the
process start-up and the full hash.

## 3. Workload (proposals)

- **Key space.** The 3 queries × the 31 non-empty ticker subsets give 93 distinct requests on
  the registered run.
- **Block size.** 30 requests. A hit rate is exact only when 30 × (1 − rate) distinct requests,
  a multiple of 3 so the queries stay balanced, each repeat 30 / distinct times. With 30
  requests the exact balanced rates are **0, 50, 80 and 90%**. Proposed: **0, 50 and 90%**.
  - **The 0% sequence:** 30 distinct requests, 10 per query; every request misses.
  - **The 50% sequence:** 15 distinct requests, each twice: 15 misses, then 15 hits.
  - **The 90% sequence:** 3 distinct requests, one per query, each 10 times: 3 misses, then 27
    hits.
- **Pairs.** Each round draws one sequence per hit rate and runs it twice, in two blocks of
  their own:
  - with the cache, the R block (R0, R50, R90);
  - without it, the R block's **W control** (W0, W50, W90): a `--no-cache` warm process.

  The two blocks of a pair run **the identical request sequence**, in the same order with the
  same repeats, **and the identical warm-ups**. The only difference between them is the cache.
- **N** runs the first 2 requests of each query in the round's 0% sequence: 6 requests, each its
  own process. Each is paired with the same request in that round's W0.
- **F**: 3 distinct requests (one per query), each twice per phase. The phases are:
  1. Redis up: 3 misses, then 3 hits.
  2. Redis stopped: 3 GET errors open the breaker, then 3 requests skip Redis.
  3. Redis started again, after its PING answers and the breaker's 5 s cooldown has passed
     (the driver waits 5.5 s): a probe that misses (the restarted Redis is empty), 2 more misses,
     then 3 hits.
- **Warm-ups.** 12 unmeasured requests at the start of every warm process (W, R, F): 4 per
  query, each query's full ticker set first.
  - **Why 12.** In the sizing run, after 3 warm-ups the first measured Spark requests took
    0.3–0.7 s against a steady 0.22 s. After 12 they took 0.19–0.33 s, near the block's median.
  - **They always reach Spark.** An R or F block's keys are deleted before its warm-ups and again
    before its measured requests.
- **Rounds.** 6, each with every block once: W0, R0, W50, R50, W90, R90, N and F.

Measured requests per batch:

| Block | Per round | 6 rounds | Per query |
|---|---|---|---|
| W0, R0 (each) | 30 | 180 | 60 |
| W50 | 30 | 180 | 60 |
| R50 | 15 misses, 15 hits | 90, 90 | 30, 30 |
| W90 | 30 | 180 | 60 |
| R90 | 3 misses, 27 hits | 18, 162 | 6, 54 |
| N | 6 | 36 | 12 |
| F | 18 (3 phases of 6) | 108 | 36 |

**Runtime.** In the prepared full-length dry run (`dry-run/20261026T160445Z`, section 10) a
measured round took 122–130 s (median 124 s), and the whole batch, with a single lead-in block
and the reference answers, 13.2 minutes. With the lead-in round (section 4) and the settle after
each block (about 0.5 s; section 6), the next batch should take about 15–16 minutes. The
editor-open estimate of about 24 minutes overstated it.

## 4. Order (proposals)

**The lead-in round (approved by the author, 2026-10-26, for the next dry run).** A full round,
numbered −1, runs before round 0. It has the 8 blocks in the forward order, with requests and
warm-ups of its own, and every block is flagged `lead_in`. It is recorded, and checked for
completeness, statuses, sources, the breaker, answers and keys like any block. By design it is
excluded from every comparison (`paired.csv`, the summaries, drift), and its host readings are
reported, not gated. The six measured rounds are unchanged. Every kind of process (no-cache,
cached, one-shot, F's restart) thus runs once before measurement starts.

Why:
- **The paired functional check** (section 10, editor open): swap-in fell from 792 MiB in the
  first block to 28 MiB by the sixth, and the first pair compared at 0.35 where about 1 was
  expected.
- **The prepared full-length dry run**, with a single lead-in block L, in which the first blocks
  paged little (swap-in 21 MiB in L, 1 MiB in W0, 94 MiB in R0): round 0's R0/W0 ratio was
  1.25, against 0.96–1.07 in rounds 1–5. Its difference sat in the requests' Spark time (R0 0.141 s, W0 0.101 s, by median), while the time outside Spark and
  resolution differed as in every round. Why the first pair's processes differed is not known.
- **What the next dry run reports to judge the lead-in round:** round 0's ratio beside rounds
  1–5, with the descriptive diagnostics of section 7. Round 0 is not excluded, and no spread
  limit is added.

Rounds are numbered 0 to 5. The **forward order** is W0, R0, W50, R50, W90, R90, N, F. Rounds 0,
2 and 4 run it; rounds 1, 3 and 5 run its exact reverse. The full order of the batch's 56 blocks:

| Round | 1st | 2nd | 3rd | 4th | 5th | 6th | 7th | 8th |
|---|---|---|---|---|---|---|---|---|
| −1 (lead-in) | W0 | R0 | W50 | R50 | W90 | R90 | N | F |
| 0 | W0 | R0 | W50 | R50 | W90 | R90 | N | F |
| 1 | F | N | R90 | W90 | R50 | W50 | R0 | W0 |
| 2 | W0 | R0 | W50 | R50 | W90 | R90 | N | F |
| 3 | F | N | R90 | W90 | R50 | W50 | R0 | W0 |
| 4 | W0 | R0 | W50 | R50 | W90 | R90 | N | F |
| 5 | F | N | R90 | W90 | R50 | W50 | R0 | W0 |

What this order does and does not do:
- **Positions are mirrored.** Every block takes position *p* in the forward rounds and position
  9 − *p* in the reverse rounds, so over the six measured rounds its mean position is the same,
  4.5, for all eight blocks.
- **Within each pair,** the W control runs right before its R block in rounds 0, 2 and 4, and
  right after it in rounds 1, 3 and 5. Neither member of a pair always runs first.
- **What it does not do.** It does not randomize the order, and it does not balance carry-over
  effects: R50, for example, always follows W50 in forward rounds and precedes it in reverse
  ones. Because the two members of a pair are adjacent, slow drift affects both almost equally.
  The drift rule (section 6) watches for faster changes.
- **Repeats.** Each warm block starts its own process, with its warm-ups, and ends it. One
  formal batch, with a seed chosen before the batch and recorded. If the batch is invalid, the
  author decides what follows.

## 5. Host conditions and contemporaneous controls on this Mac (proposals)

**Why not the 4.0 GiB gate.** That gate was approved in M2 to decide whether *memory figures*
are representative: resident sizes shrink under compression and swap. E3's main results are
*latencies compared within one batch*, where every configuration runs interleaved under the same
host state. What distorts a latency is something happening during the block:
- paging (swap traffic);
- critical memory pressure;
- thermal throttling;
- competing work.

Each of these can be measured directly, per block. Available memory is recorded but not gated:
this 8 GiB machine showed 1.2–1.5 GiB available throughout both dry runs, with the editor open
and 7.7–8.4 GiB of swap in use. Memory figures from E3 (section 7) are reported as not
representative, like M2's.

**Preparation (proposal).**
- Quit other applications, the editor included, and run from Terminal.
- AC power, lid open.
- Nothing else in Docker; this project's Redis is the only service.

`e3_preflight` refuses to start unless:
- power is AC and the lid is open;
- no other project's container runs, and no other service of this project;
- Redis answers PING and holds no key the experiment does not own;
- memory pressure is not critical, and no thermal or performance warning is recorded;
- for a formal batch, the worktree is clean.

**Monitoring during the batch** (`src/etf_risk/cache_experiment.py`). Nothing is ever recorded by
name.
- **Containers.** `docker events` runs for the whole batch, so another project's container that
  starts or stops between two readings is counted. The number of other running containers is
  read at every block boundary.
- **The host sampler, every 1 s:** macOS's memory-pressure level, swap traffic in and out, and
  `pmset -g therm`'s thermal and performance warnings.
- **The process tree of each warm process (or each N process), every 0.5 s.** Then one scan,
  after the block, for processes still carrying the block's marker. A full marker scan reads
  every process's environment, which costs too much to repeat during timing.

**Contemporaneous controls.**
- **Every R block has its own W control:** the identical requests and warm-ups without the cache,
  run right before or right after it (section 4).
- **Every comparison is paired** (section 7).
- **The drift rule** (section 6) compares the W controls' medians in the last round with the
  first.

## 6. Validity rules (proposals; checked by the collector)

A batch is valid when every one of these holds; otherwise the collector exits 1 and lists the
problems (`validity.json`):
1. **Complete:** every planned request has exactly one record, warm-ups included.
2. **Statuses:** every answer is `ok`.
3. **Sources as designed:** W and N from Spark; R and F as designed; every warm-up from Spark.
   R's realized hit rate equals its designed rate exactly.
4. **Breaker (F):** with Redis stopped, the first 3 requests count GET errors and the next 3
   are skipped; after the restart the first request misses.
5. **Answers:** every answer equals the reference answer (computed first, by a separate no-cache
   process), value types included.
6. **Keys:** each R and F block starts with none of its keys in Redis.
7. **Host, per block:**
   - AC power and lid open before and after;
   - no other running container at either reading, and no other project's container event in
     between; the container monitor ran;
   - memory pressure never critical;
   - no thermal or performance warning;
   - swap-out traffic within its limit, and for W and R blocks swap-in traffic within its limit.
     The limits are set from the full-length dry run (section 10); the tooling's provisional
     defaults are 64 MiB and 256 MiB;
   - **the settle:** after a block's last process exits, and outside every request's timing, the
     driver waits up to **15 s** (the settle M2's memory check uses) for the block's marked
     processes to exit, and records each one's pid, name, kind, creation time, and when it was
     first and last seen and found gone. A process alive after the 15 s fails the block. It is
     ended (TERM, then KILL) only when its ownership is verified (the same marker and creation
     time). If the cleanup cannot be confirmed, the batch stops and `batch.json` records
     `aborted`;
   - every process exited 0.
8. **Redis:** its peak within the 128 MiB container limit.
   **The batch:** not aborted, and no other project's container event at any time of the batch,
   between block windows included (`containers.jsonl`).
9. **Pairs:** each R block and its W control ran the identical requests and warm-ups.
10. **Drift:** for each query, the median client latency of the W controls (all three, pooled) in
    the last round within **±20%** of the first round's.

**Swap limits.** N and F are not limited on swap-in: every N request starts a new JVM, and F
stops and starts a container, so their paging is part of what they are.
- **Swap-in in the dry runs:** W and R blocks 21–49 MiB (the second dry run), 26–379 MiB (the
  sizing run, on a more loaded host); N 984–2,147 MiB; F 490–569 MiB.
- **Swap-out:** at most 20 MiB in any block.

## 7. Measures and reporting

**The attribution rule.** A difference is attributed to the cache only when it is a **paired
end-to-end difference**: the client latency of an R request against that of the identical request
at the same position of its W control. Differences between blocks with different ticker subsets,
other repeat patterns or another round are never attributed to caching. The same holds for N:
each N request is compared with the same request in its round's W0. The lead-in round is never
compared. **These paired end-to-end differences are the primary result.**

- **Per request:** the client's monotonic latency (from writing the request to reading its
  answer; for N, from starting the process to its exit), and the server's resolve, Spark and
  total seconds. Also the source, the counters and the full-hash count.
- **Paired** (`paired.csv`): each R request beside its control. Kept apart:
  - the difference and ratio for hits (what a hit saves against Spark in the same warm process
    state);
  - the difference and ratio for misses (what the cache costs when it misses);
  - N against W0 (what a warm process saves).

  Summaries (`paired_summary.csv`):
  - **per request group** (hit rate, hit or miss, query): `median_difference_s`,
    `median_ratio`, `min_ratio` and `max_ratio` of the paired end-to-end values;
  - **per R block and round:** `total_difference_s` and `total_ratio`, the block's total client
    time against its control's. That is what a hit rate of 0, 50 or 90% saves end to end.
- **Descriptive diagnostics** (columns named `diag_…`). They describe the time; they do not say
  why a difference arose:
  - `diag_spark_difference_s`: the Spark time of an R (or N) request less its control's. Empty
    for a hit, which runs no Spark. A Spark-time difference is not assumed to be a host effect;
  - `diag_rest_difference_s`: the same difference for the time outside Spark and resolution
    (the pipe, JSON, the cache's calls, encoding and decoding, and anything else the request
    waited on). It is not a causal cost of the cache;
  - their medians per group (`diag_median_spark_difference_s`, `diag_median_rest_difference_s`).
- **An estimate for hits** (`estimate_hit_imbalance_s`, per R block that has hits): the median
  Spark-time difference of the block's own misses against their controls. It is an estimate of
  how unequal the pair's conditions were, reported beside the hits' end-to-end difference and
  never subtracted from it.
- **The resolver's cost:** N's full hash against the warm check, from `seconds.resolve`.
- **Hit rates:** realized against designed (they must be equal; section 6).
- **F:** whether every answer is right, the breaker's sequence, and Redis's share of each
  request (client latency less Spark and resolve). F's Spark-served latencies are not compared
  with W's: in the dry run they ranged 0.25–3.9 s while Docker stopped and started the
  container on the same machine.
- **Memory, reported and not representative (section 5):** each warm process tree's peak (0.45–0.78
  GiB in the dry runs), each N process's peak (about 0.42 GiB), and Redis's cgroup peak (read
  before every stop, since a restart resets it) and `used_memory_peak`.

## 8. Predictions (from the two dry runs; not results)

- **W:** a median of 0.20–0.26 s per request.
- **R misses:** about W, at 0.20–0.36 s.
- **R hits:** 8.5–17 ms, about 7.5–13 ms of it the warm stat check.
- **N:** 9.4–15 s per request.
- **Redis down:** with Redis stopped, a refused connection adds under 1 ms. A paused Redis,
  which this design does not include, adds one read timeout (0.1 s; [result-cache.md](result-cache.md),
  section 7).
- **The breaker's sequence** is exact: 3 errors, then skips.

## 9. Decisions this draft asks for

1. **Configurations and interpretation** (section 2), including that N has no Redis variant.
2. **Workload** (section 3): block size 30; hit rates 0, 50 and 90%; a W control for each R
   block with the identical requests and warm-ups; N with 6 requests per round; F with 3 phases
   of 6; 12 warm-ups.
3. **Order and repeats** (section 4): the lead-in; the six-round order in the table, the
   forward order in rounds 0, 2 and 4 and its exact reverse in 1, 3 and 5; one formal batch;
   the seed.
4. **The attribution rule** (section 7): only paired differences are attributed to the cache.
5. **Host conditions and controls** (section 5): the preparation, the preflight, the monitoring,
   and the reason the 4.0 GiB gate is not a timing rule.
6. **Validity rules and limits** (section 6): the swap-out, swap-in and drift limits, kept at
   64 MiB, 256 MiB and ±20% for the next dry run (the author, 2026-10-26); the 15 s settle; the
   batch-wide container check; and that critical pressure or any thermal warning invalidates its
   block and so the batch.
7. **Reporting** (section 7): paired end-to-end differences as the primary result; the
   diagnostics as descriptive and the hit imbalance as an estimate; F as correctness and Redis's
   share, not a latency comparison; memory figures as not representative.

Decided by the author on 2026-10-26, for the next dry run: the lead-in round (section 4), the
settle and the batch-wide container check (section 6), the descriptive diagnostics (section 7),
and keeping the six measured rounds and the current limits.

## 10. Dry runs so far (not formal)

| Batch | Purpose | Outcome |
|---|---|---|
| `sizing/20261026T113443Z` | sizing, 1 round, 3 warm-ups | every check the collector had then held except host: memory pressure was critical during R0. (It would also fail the warm-up check added afterwards.) The run found two driver bugs, both fixed: the host sampler's stop event shadowed `Thread._stop`, so finishing failed after all 6 blocks; and warm-ups ran before the block's keys were deleted, so 2 of them hit Redis and warmed nothing. The collector now checks that every warm-up reached Spark. |
| `sizing/20261026T121817Z` | functional check of the paired design, 1 round, editor open, no lead-in | the W controls ran and paired: **pairs**, sources, breaker, answers, keys, Redis and drift held. Host failed: swap-in of 792 MiB in W0 and 285 MiB in R0, over the provisional 256 MiB. That start-of-batch transient is the reason for the lead-in (section 4). Not evidence for thresholds: the editor was open. |
| `dry-run/20261026T160445Z` | **the prepared full-length dry run** (run by the author, editor closed): a single lead-in block L and six measured rounds | NOT valid, on host only (43 problems); every other check held. **42:** "1 marked process alive after the block" in every gated warm block (L's is not gated), none in N. The driver kept only a count, so the processes were not identified. Available memory stayed at 2.8–3.3 GiB and swap in use fell from 1.09 to 1.00 GiB, so they did not accumulate: most likely a shutdown still in progress, which led to the settle (section 6). **1:** `b18-R0` swapped in 271 MiB, over 256; its latencies matched its control's (median 0.137 vs 0.138 s). Swap-out at most 5.8 MiB; memory pressure normal throughout; 0 other-project container events, gaps included. Drift: last against first +8.5%, +11.6%, −0.5%. Round 0's R0/W0 ratio was 1.25 (section 4). Kept unchanged (62 files). |
| `functional/20261026T172508Z` | functional check of the settle, 1 round, editor open | in every warm block the marked process was the Spark JVM, gone 0.27–0.54 s after the driver exited; no survivor, every block confirmed clean. The batch-wide check counted 3 short-lived containers of another project (15 events, 3 of them between block windows). Paging with the editor open is not threshold evidence. |
| `dry-run/20261026T114515Z` | dry run, 1 round, 12 warm-ups, before the pairs | **valid** on every check then defined (drift trivially: one round). 0 other containers, 0 container events, no critical pressure, no thermal warning. |

**Tests.** On the commit that adds the lead-in round and the diagnostics, the E3 suites
(`tests/test_cache_experiment.py`, `tests/test_result_cache_collector.py`,
`tests/test_result_cache_session.py`) passed: **84 tests**. The new collector, run on a copy of
`dry-run/20261026T160445Z`, gives the same 43 host problems; the original was not touched.

**The next prepared dry run.** The lead-in round and six measured rounds (56 blocks), run by the
author from Terminal under the preparation of section 5, with the editor closed. Its records are
kept whatever its outcome. Claude Code cannot run it: the preparation means quitting the editor,
which Claude Code runs in.

**Freezing the protocol.** After that dry run, the limits are written into this document, the
author approves it, and the protocol is frozen: the approved commit is recorded here. The
formal batch runs on that commit only. `run --formal` refuses a dirty worktree, and the batch
records its code identity.

## 11. Commands

The session helpers, in order:

| Command | What it does |
|---|---|
| `source docs/result-cache-session.zsh` | loads the helpers; set `E3_PURPOSE`, `E3_SEED` and `E3_BATCH` before it |
| `e3_steps` | prints the checklist |
| `e3_redis` | starts the redis service alone and waits for PING |
| `e3_preflight` | exits 1 with the reasons unless a batch may start |
| `e3_plan` | writes the plan into a new batch folder |
| `e3_run` | runs the preflight, then the batch, the Mac kept awake; appends its output to `session.log` |
| `e3_collect` | checks validity and writes the summaries; exits 1 unless valid; appends to `session.log` |
| `e3_cleanup` | stops and removes the redis service only |

For the next prepared dry run, after quitting every other application (the editor included),
with AC power, the lid open, and Docker running with nothing else:

```zsh
cd ~/leveraged-etf-risk-analytics/.claude/worktrees/result-cache-experiment
deactivate 2>/dev/null
export E3_PURPOSE=dry-run
export E3_SEED=2611
export E3_BATCH=$(date -u +%Y%m%dT%H%M%SZ)-lead-in-round
source docs/result-cache-session.zsh
e3_redis
e3_plan
e3_run
e3_collect
e3_cleanup
```

## 12. Not claimed

- Latency savings for other workloads, other runs, other hosts, or a shared or remote Redis.
- A hard end-to-end bound on any request ([result-cache.md](result-cache.md), section 6).
- Representative memory figures (section 5).
- Behaviour under a paused or partially responsive Redis. The design stops Redis, which refuses
  connections at once.
- Any change to the analysis results in spec §8.
