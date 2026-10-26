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
  requests the exact balanced rates are **0, 50, 80 and 90%**. Proposed: **0, 50 and 90%**
  (blocks R0, R50, R90).
  - R0: 30 distinct requests, 10 per query; every request misses.
  - R50: 15 distinct requests, each twice: 15 misses, then 15 hits.
  - R90: 3 distinct requests, one per query, each 10 times: 3 misses, then 27 hits.
- **W** runs the round's R0 requests (the same 30), so W and R0 are matched request for request.
- **N** runs the first 2 of them for each query: 6 requests, each its own process.
- **F**: 3 distinct requests (one per query), each twice per phase. The phases are:
  1. Redis up: 3 misses, then 3 hits.
  2. Redis stopped: 3 GET errors open the breaker, then 3 requests skip Redis.
  3. Redis started again, after its PING answers and the breaker's 5 s cooldown has passed
     (the driver waits 5.5 s): a probe that misses (the restarted Redis is empty), 2 more misses
     on the other requests, then 3 hits.
- **Warm-ups.** 12 unmeasured requests at the start of every warm process (W, R, F): 4 per
  query, each query's full ticker set first.
  - **Why 12.** In the sizing run, after 3 warm-ups the first measured Spark requests took
    0.3–0.7 s against a steady 0.22 s. After 12 they took 0.19–0.33 s, near the block's median.
  - **They always reach Spark.** A block's keys are deleted before its warm-ups and again
    before its measured requests, so neither can hit.
- **Rounds.** 6, each with W, R0, R50, R90, N and F once.

Measured requests per batch:

| Configuration | Per round | 6 rounds | Per query |
|---|---|---|---|
| W | 30 | 180 | 60 |
| R0 (misses) | 30 | 180 | 60 |
| R50 | 15 misses, 15 hits | 90, 90 | 30, 30 |
| R90 | 3 misses, 27 hits | 18, 162 | 6, 54 |
| N | 6 | 36 | 12 |
| F | 18 (3 phases of 6) | 108 | 36 |

**Runtime.** The one-round dry run took 183 s of blocks (W 23, R0 20, R50 17, R90 14, N 71 and
F 38 s), plus about 25 s for the reference answers. Six rounds come to about 20 minutes.

## 4. Order and repeats (proposals)

- **ABBA rounds.** Within a round the blocks run W, R0, R50, R90, N, F; odd rounds run them in
  reverse, so a slow drift does not fall on one configuration.
- **A fresh process for every block.** Each warm block starts its own process (with its
  warm-ups) and ends it. Each block's memory peak is its own, and no block inherits another's
  JIT or cache state, apart from the operating system's file cache, which all configurations
  share.
- **A seed per batch.** The workload is drawn from a seed: the same seed gives the same plan.
  The formal seed is chosen before the batch and recorded (section 9).
- **One formal batch.** If it is invalid, the author decides what happens next, for example a
  new batch with the same seed.

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
- **W in every round** runs the same requests as that round's R0.
- **The drift rule** (section 6) compares W's medians in the last round with the first.
- **Within-round ratios** (R hits / W, R misses / W, N / W) are reported for each round, with
  their spread over the rounds. The batch's comparisons rest on these, not on absolute times
  alone.

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
   - swap-out traffic at most **64 MiB**, and for W and R blocks swap-in traffic at most
     **256 MiB**;
   - no marked process left after the block; every process exited 0.
8. **Redis:** its peak within the 128 MiB container limit.
9. **Drift:** for each query, W's median client latency in the last round within **±20%** of the
   first round's.

**Swap limits.** N and F are not limited on swap-in: every N request starts a new JVM, and F
stops and starts a container, so their paging is part of what they are.
- **Swap-in in the dry runs:** W and R blocks 21–49 MiB (the second dry run), 26–379 MiB (the
  sizing run, on a more loaded host); N 984–2,147 MiB; F 490–569 MiB.
- **Swap-out:** at most 20 MiB in any block.

## 7. Measures and reporting

- **Per request:** the client's monotonic latency (from writing the request to reading its
  answer; for N, from starting the process to its exit), and the server's resolve, Spark and
  total seconds. Also the source, the counters and the full-hash count.
- **Per configuration, query and round:** the median, minimum and maximum, and the per-round
  ratios of section 5.
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
2. **Workload** (section 3): block size 30; hit rates 0, 50 and 90%; W matched to R0; N with 6
   requests per round; F with 3 phases of 6; 12 warm-ups.
3. **Order and repeats** (section 4): 6 ABBA rounds; one formal batch; the seed (proposed: draw
   one now and record it).
4. **Host conditions and controls** (section 5): the preparation, the preflight, the monitoring,
   and the reason the 4.0 GiB gate is not a timing rule.
5. **Validity rules and limits** (section 6): swap-out at most 64 MiB per block, swap-in at most
   256 MiB per W or R block, drift ±20%, and critical pressure or any thermal warning
   invalidating its block and so the batch.
6. **Reporting** (section 7): F as correctness and Redis's share, not a latency comparison; memory
   figures as not representative.

## 10. Dry runs so far (not formal)

| Batch | Purpose | Outcome |
|---|---|---|
| `sizing/20261026T113443Z` | sizing, 1 round, 3 warm-ups | every check the collector had then held except host: memory pressure was critical during R0. (It would also fail the warm-up check added afterwards.) The run found two driver bugs, both fixed: the host sampler's stop event shadowed `Thread._stop`, so finishing failed after all 6 blocks; and warm-ups ran before the block's keys were deleted, so 2 of them hit Redis and warmed nothing. The collector now checks that every warm-up reached Spark. |
| `dry-run/20261026T114515Z` | dry run, 1 round, 12 warm-ups | **valid** on every check (drift trivially: one round). 0 other containers, 0 container events, no critical pressure, no thermal warning. |

## 11. Commands

```zsh
source docs/result-cache-session.zsh     # E3_PURPOSE=formal E3_SEED=<seed> before it, for the formal batch
e3_steps        # the checklist
e3_redis        # start the redis service alone and wait for PING
e3_preflight    # exits 1 with the reasons unless a batch may start
e3_plan         # write the plan
e3_run          # run it, the Mac kept awake
e3_collect      # validity and the summary; exits 1 unless valid
e3_cleanup      # stop and remove the redis service only
```

## 12. Not claimed

- Latency savings for other workloads, other runs, other hosts, or a shared or remote Redis.
- A hard end-to-end bound on any request ([result-cache.md](result-cache.md), section 6).
- Representative memory figures (section 5).
- Behaviour under a paused or partially responsive Redis. The design stops Redis, which refuses
  connections at once.
- Any change to the analysis results in spec §8.
