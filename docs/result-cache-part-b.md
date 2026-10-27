# Result-cache experiment (E3): Part B, the formal batch

_Drafted with Claude Code (Opus 5.5) on 2026-10-27 at the author's request; contributed by both.
- **The cache's logic and the SQL** are the project author's (M4,
  [result-cache.md](result-cache.md)).
- **The E3 design, its tooling and this draft** are Claude Code's, decided and approved by the
  author.
- **Sources:** the records of `data/outputs-result-cache/formal/20261027T062927Z-formal-1`, with
  every number read by script, and Part A, [result-cache-experiment.md](result-cache-experiment.md),
  approved on 2026-10-26. The executable code was frozen at `5b916a5`.
- **The records** stay outside Git, unchanged since the collector wrote them (73 files,
  fingerprint `d44f81c2cc80e8f0`).
- **What is approved:** sections 1–6 give facts. The answer in section 7 was drafted with
  Claude Code and approved by the author on 2026-10-27, with one wording adjustment (the
  Redis-down overhead).
- **Predictions** are compared, never revised (Part A, section 8).
- **Times** are UTC on 2026-10-27._

## 1. The batch

| | |
|---|---|
| Folder | `data/outputs-result-cache/formal/20261027T062927Z-formal-1` |
| Run by | the author, from Terminal, editor closed, under the preparation of Part A section 5 |
| Time | 06:29:53–06:45:11 (15.3 min); 56 blocks: the lead-in round and six measured rounds |
| Seed | 5309 (Part A, section 4) |
| Code | HEAD `51d5453`, a documentation commit on the frozen `5b916a5`; clean worktree. After the batch, the recorded hashes of all 39 source files and `uv.lock` matched `5b916a5` |
| Redis | 8.10.2, this project's only service; the experiment's keys deleted by name (40 at the end) |
| Verdict | **valid** on every check: correctness, power, sleep, thermal, memory pressure, competing containers, cleanup, Redis, drift |
| Rerun | none needed (rerun policy, Part A section 4) |

Every request was recorded:
- **2,016 requests** in all, 588 of them warm-ups;
- **1,428 measured,** of which 204 belong to the lead-in round, which is excluded by design;
- **1,224 measured requests in the six rounds:**
  - W 540;
  - R 540: 288 misses and 252 hits, exactly as designed;
  - N 36;
  - F 108.

**Paired comparisons:** 576 request pairs (540 R against their W controls, 36 N against W0),
grouped in 24 block pairs (18 R, 6 N).

## 2. Paired results (the primary analysis)

These are end-to-end client latencies: each R request against the identical request at the same
position of its W control; each N request against the same request in its round's W0.

**The swap-out sensitivity analysis equals the primary analysis.** No block pair was flagged: no
W, R or N block swapped out (0 of 24 block pairs; 0 of 576 request pairs excluded).
`paired_summary.csv` holds both analyses, and every one of their 36 rows is identical apart from
its label.

### 2.1 Each R block's total against its W control (30 requests each)

| Round | R0 (0% hits) | R50 (50%) | R90 (90%) |
|---:|---|---|---|
| 0 | 4.17 / 4.30 s = **0.969** | 2.14 / 4.39 s = **0.488** | 0.57 / 3.88 s = **0.147** |
| 1 | 3.77 / 4.27 s = **0.884** | 2.66 / 3.91 s = **0.679** | 0.64 / 4.59 s = **0.139** |
| 2 | 4.53 / 4.04 s = **1.119** | 2.05 / 4.57 s = **0.448** | 0.62 / 4.00 s = **0.156** |
| 3 | 4.11 / 4.35 s = **0.946** | 2.57 / 4.07 s = **0.632** | 0.63 / 4.79 s = **0.132** |
| 4 | 4.47 / 3.75 s = **1.192** | 2.08 / 3.90 s = **0.532** | 0.60 / 3.62 s = **0.167** |
| 5 | 4.42 / 3.33 s = **1.326** | 2.02 / 4.39 s = **0.461** | 0.62 / 4.90 s = **0.127** |
| Median | 1.044 | 0.510 | 0.143 |
| Time saved per block, median | −0.17 s (no saving) | 2.04 s | 3.66 s |

At 0% hits the cache saved nothing. Across rounds, R0's total fell on both sides of its control's.

### 2.2 By request (medians of the paired differences)

| Group | Query | n | Median difference | Median ratio [range] |
|---|---|---:|---:|---|
| R0 misses | overview | 60 | +6.4 ms | 1.053 [0.553–1.845] |
| | comparison | 60 | +7.5 ms | 1.075 [0.528–1.932] |
| | sensitivity | 60 | +6.3 ms | 1.047 [0.473–1.763] |
| R50 hits | overview | 30 | −116.2 ms | 0.047 [0.029–0.063] |
| | comparison | 30 | −121.0 ms | 0.043 [0.027–0.068] |
| | sensitivity | 30 | −122.4 ms | 0.045 [0.028–0.062] |
| R50 misses | overview | 30 | −1.9 ms | 0.987 [0.530–1.654] |
| | comparison | 30 | +7.6 ms | 1.056 [0.658–1.653] |
| | sensitivity | 30 | −15.8 ms | 0.883 [0.492–1.830] |
| R90 hits | overview | 54 | −127.4 ms | 0.041 [0.026–0.083] |
| | comparison | 54 | −130.0 ms | 0.040 [0.022–0.066] |
| | sensitivity | 54 | −124.0 ms | 0.041 [0.025–0.061] |
| R90 misses | overview | 6 | −6.9 ms | 0.962 [0.681–1.179] |
| | comparison | 6 | −16.5 ms | 0.899 [0.645–1.079] |
| | sensitivity | 6 | +19.4 ms | 1.148 [0.896–1.395] |
| N against W0 | overview | 12 | +5,788 ms | 46.1 [30.3–57.1] |
| | comparison | 12 | +5,813 ms | 42.9 [29.1–57.5] |
| | sensitivity | 12 | +5,775 ms | 40.3 [29.5–64.9] |

- **Hits.** About 120–130 ms faster than the identical no-cache request, at about 4% of its
  latency, consistently across queries and rounds: the round medians were 5.2–6.1 ms.
- **Misses.** Single requests ranged widely: ratios 0.47–1.93 at R0. The medians at R0 put the
  cache's misses 6–8 ms behind their controls. The R50 and R90 misses are fewer (30 and 6 per
  query) and fall on both sides.
- **N.** A new process per request took 40–46 times as long as the same request in a warm
  session.

### 2.3 Latencies and their parts

Medians over the six rounds.

| Configuration | Client latency | Resolution (`seconds.resolve`) |
|---|---|---|
| W | 0.132 s (W0 0.128, W50 0.132, W90 0.135); Spark 0.121 s | the warm stat check, 4.8 ms (W and R) |
| R miss | 0.139 s | the warm stat check |
| R hit | 5.4 ms (5th–95th percentile 5.0–6.5 ms; maximum 10.8 ms) | the warm stat check, 4.6 ms; the rest, Redis's GET and decoding, about 0.9 ms |
| N | 5.92 s (5.84–6.49 s; round medians 5.89–5.96 s) | the full hash, 30 ms |

These are descriptive diagnostics, not causes. Outside Spark and resolution, R misses took 6.97
ms against W's 4.99 ms. The difference is the miss's GET and SET, among anything else the request
waited on.

### 2.4 Redis down (F)

All six F blocks met the breaker check, and every answer equalled the reference.

| Phase | Requests | Sources | Median (range) |
|---|---:|---|---|
| 0, Redis up | 36 | 18 Spark, 18 cache | 55.6 ms (5.1–209.2) |
| 1, Redis stopped | 36 | 36 Spark | 151.0 ms (93.5–211.2) |
| 2, restarted | 36 | 18 Spark, 18 cache | 62.5 ms (5.2–223.2) |

- **With Redis stopped,** each block counted 3 GET errors, then skipped Redis for 3 requests.
  After the restart, the first request missed.
- **The time outside Spark and resolution** with Redis stopped had a median of 4.86 ms, against
  W's 4.99 ms. The observed medians were similar (4.86 ms versus 4.99 ms); this does not
  establish zero overhead.
- **F's Spark-served latencies are not compared with W's.** Docker stopped and started the
  container on the same machine (Part A, section 7).

## 3. Drift

The rule held: for each query, the pooled W median of round 5 against round 0's.

| Query | Round 0 | 1 | 2 | 3 | 4 | 5 | Last against first | Range against round 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| overview | 0.123 | 0.134 | 0.132 | 0.143 | 0.125 | 0.139 | +12.9% | +0.0% to +16.5% |
| comparison | 0.136 | 0.145 | 0.138 | 0.127 | 0.124 | 0.127 | −6.6% | −9.2% to +6.3% |
| sensitivity | 0.136 | 0.135 | 0.129 | 0.147 | 0.116 | 0.126 | −7.9% | −14.9% to +7.8% |

Single rounds moved by up to 16.5% against round 0. The pairs, run next to each other, are the
control for that.

## 4. Host conditions and diagnostics

### 4.1 Checked (all held)

- **Power and lid:** AC power and the lid open at every reading.
- **Sleep:** the wall clock against the monotonic clock was within 18.6 ms per block, and within
  38 ms over the batch.
- **Thermal and pressure:** no thermal or performance warning; memory pressure at level 1
  (normal) throughout.
- **Containers:** 0 other running containers at every reading, and 0 of the batch's 1,547
  container events from another project.
- **Cleanup:**
  - every block settled clean, with the warm blocks' Spark JVMs gone 0.52–0.55 s after their
    driver;
  - no survivor, every process exited 0;
  - Redis's cgroup peak was 19–50 MiB against its 128 MiB limit.

### 4.2 Recorded, never gated (measured blocks)

- **Swap:** 0.0 MiB swapped out in every block; swap-ins at most 7.7 MiB. Swap in use stayed at
  1.12–1.14 GiB.
- **Paging:** page-ins at most 226 MiB in a W or R block, 141 MiB in N and 17 MiB in F. Page-outs
  at most 4.4 MiB.
- **Memory:** 2.63–3.30 GiB available before the blocks.
- **Load:** the 1-minute load average's block means were 3.3–8.8.
- **CPU:**

  | Block | Own CPU | Busy CPU | Unaccounted |
  |---|---|---|---|
  | W | 0.26–0.36 | 0.35–0.78 | 0.04–0.52 |
  | R | 0.27–0.36 | 0.35–0.71 | 0.05–0.42 |
  | N | 0.28–0.30 | 0.36–0.65 | 0.06–0.35 |
  | F | 0.17–0.22 | 0.23–0.50 | 0.06–0.33 |

  Shares of capacity. Own CPU is the experiment's own, a lower bound.

- **An unaccounted-CPU episode.** From about t+5.4 to t+10.7 min (`b19`–`b40`, rounds 1–4), the
  unaccounted share was 0.30–0.52, while the experiment's own share stayed at 0.26–0.35.
  - **Not attributed.** The extra CPU was not in the experiment's sampled processes. The protocol
    does not attribute it: the Docker VM, which runs Redis, and the kernel's work for the
    experiment are in the remainder too.
  - **The pairs during the episode.** Three of the block ratios of rounds 1–3 are the extremes of
    their columns: round 1's R0 (0.884, the lowest) and R50 (0.679, the highest), and round 2's
    R50 (0.448, the lowest). The other six fall within the other rounds' ranges, and all of R90
    does. The records do not show whether the episode caused those extremes.
  - **A similar onset** appeared about 5 minutes into the dry run `20261026T225409Z-vm-counters`.
- **Round 5's R0 pair, the most extreme at 1.326,** fell outside the episode: the unaccounted
  share was 0.05–0.07 in both of its blocks.
- **Memory peaks** (not representative, Part A section 5):
  - each warm process tree: 0.67–1.06 GiB;
  - each N process: 0.55–0.59 GiB;
  - Redis's `used_memory_peak`: 1.6 MiB.

## 5. Predictions against the results

Neither set of predictions is revised (Part A, section 8).

| | Original (editor-open dry runs) | Revised, dry-run-informed (2026-10-26) | Formal batch | Missed |
|---|---|---|---|---|
| W | 0.20–0.26 s | 0.13–0.16 s | 0.132 s | original |
| R misses | 0.20–0.36 s | 0.137–0.164 s | 0.139 s | original |
| R hits | 8.5–17 ms | 5.5–6.9 ms | 5.4 ms | both (below) |
| Warm stat check | about 7.5 ms | 4.6–6.4 ms | 4.6 ms in hits, 4.8 ms overall | original |
| R0 total, per round | — | 0.90–1.13 | 0.884–1.326 | revised: rounds 1, 4, 5 |
| R50 total, per round | — | 0.46–0.64 | 0.448–0.679 | revised: rounds 1, 2 |
| R90 total, per round | — | 0.12–0.18 | 0.127–0.167 | — |
| N | 9.4–15 s | 6.0–7.4 s | 5.92 s | both (below) |
| N's full hash | 75–170 ms | 30–38 ms | 30 ms | original |
| Redis down | under 1 ms added | within 0.4 ms of W | −0.13 ms against W | — |
| Breaker sequence | exact | exact | exact | — |

The revised ranges came from three dry runs. The formal batch's per-round totals at 0% and 50%
spread wider than those dry runs' did.

## 6. Limitations: what these observations are and are not

**Host-specific observations.**
- **One valid formal batch,** on one 8 GiB Mac, in one recorded host state.
- **One workload:** the three summary queries on the registered run
  `run-20261013T043848Z-4`, with hit rates set exactly by repeats.
- **A Redis on the same machine,** in Docker.

These are paired latency observations under those conditions.

**Not general performance claims.** Nothing here states the cache's savings on another host,
another workload or run, real query mixes, a shared or remote Redis, or under load. Part A,
section 12, lists what is not claimed.

**Further limits:**
- **The monitoring.** Every timing includes the monitoring configuration (Part A, section 6), and
  its overhead has not been separately quantified. Both members of each pair carry it.
- **CPU attribution.** The experiment's own CPU is a lower bound. Unaccounted CPU is not evidence
  of external interference, and the episode of section 4.2 is not attributed.
- **Paging.** Page-ins include file reads, and their source is not recorded. They gate nothing.
- **No prepared dry run under the final protocol** (the author's decision). The sleep check and
  the own-CPU sampler had run in functional checks only before this batch.
- **Variation.** Single requests vary widely: miss ratios 0.47–1.93. Per-round block totals at
  0% hits fell on both sides of their controls, and the W medians moved by up to 16.5% between
  rounds. The medians are of one batch, with no confidence intervals.
- **The comparisons are end to end on the client:** the pipe, the JSON and the process's own
  work included.
- **Memory figures** are not representative (Part A, section 5).

## 7. The answer to E3 (approved by the author, 2026-10-27)

> How much latency does a result cache save for repeated summary queries, compared with a new
> Spark process and with a warm Spark session, at which hit rates, and what happens when Redis
> is down?

**Answer (drafted with Claude Code; approved by the author on 2026-10-27).** On this Mac, in one valid
formal batch of six measured rounds, these are paired observations under the recorded host state.
They are not a general performance claim.
- **A cache hit** answered in a median 5.4 ms. The identical request without the cache, in a warm
  Spark session, took a median 0.132 s. Per query, the median paired difference was 116–130 ms,
  and a hit took about 4% of the warm request's time. Most of a hit was the warm check of the run
  folder, 4.6 ms. Redis's GET and the decoding took about 0.9 ms.
- **A miss** cost a median 6–8 ms more than its control at a 0% hit rate, within a wide spread of
  single requests.
- **Per block of 30 requests**, the cache's total against its no-cache control was:

  | Hit rate | Range across six rounds | Median | Saved per block, median |
  |---|---|---|---|
  | 0% | 0.88–1.33 | 1.04 | nothing |
  | 50% | 0.45–0.68 | 0.51 | about 2.0 s |
  | 90% | 0.13–0.17 | 0.14 | about 3.7 s |

- **A new Spark process per request** took a median 5.9 s, 40–46 times the warm request. The warm
  session, not the cache, makes the largest difference against a new process.
- **With Redis stopped:**
  - every answer was correct, served by Spark;
  - the circuit breaker opened after 3 failed GETs, and later requests skipped Redis;
  - outside Spark and resolution, the observed medians were similar (4.86 ms versus 4.99 ms);
    this does not establish zero overhead;
  - after Redis was restarted, the first request missed and caching resumed.
- **No pair swapped out,** so the sensitivity analysis without swap-out pairs equals the primary
  analysis.
- **Every timing includes the experiment's monitoring,** whose overhead was not separately
  measured.

## 8. Records

`data/outputs-result-cache/formal/20261027T062927Z-formal-1`, outside Git, unchanged since the
collector wrote it (73 files, fingerprint `d44f81c2cc80e8f0`):

| Group | Files |
|---|---|
| Plan and requests | `plan.json`, `requests.jsonl`, `reference.json` |
| Blocks and samples | `blocks.jsonl`, `host_samples.jsonl`, `own_cpu_samples.jsonl` |
| Batch-level | `containers.jsonl`, `batch.json` |
| Collector outputs | `validity.json`, `measurements.csv`, `summary.csv`, `paired.csv`, `paired_summary.csv`, `swap_flags.json`, `host.csv` |
| Logs | `session.log`, `logs/` |

After the batch:
- the Redis service was removed;
- no container ran;
- no process carried an E3 marker;
- no Spark or JVM scratch was left in the temporary folders.
