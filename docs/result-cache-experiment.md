# Result-cache experiment (E3): Part A, draft for approval

Author: contributed by both the project author and Claude Code. Claude Code proposed this design,
drafted this document and wrote the tooling (`src/etf_risk/cache_experiment.py`,
`analysis/collect_result_cache_measurements.py`, `docs/result-cache-session.zsh` and their tests).
The author makes every decision and approval: the decisions taken so far are in section 1, and
the ones this draft asks for are in section 9. On 2026-10-26 the author approved section 6, the
protocol, with its swap-out rule, and the formal seed and rerun policy (section 4). The rest
awaits approval. The protocol is not frozen, and no formal batch has run.

> **Correction, 2026-10-26.** Until this date E3's tooling and this draft called psutil's `sin`
> and `sout` "swap-in" and "swap-out". On macOS they are page-ins and page-outs. This draft now
> uses the correct names, and the batches recorded before the correction are unchanged. See
> [host-counters-correction.md](host-counters-correction.md).

> **Protocol correction, 2026-10-26, before any formal measurement.** The page-in and page-out
> validity limits are withdrawn, and the counters are kept as diagnostics (section 6). It does
> not relabel past batches: each keeps the verdict it was collected with.

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
- **The paired functional check** (section 10, editor open): page-ins fell from 792 MiB in the
  first block to 28 MiB by the sixth, and the first pair compared at 0.35 where about 1 was
  expected.
- **The prepared full-length dry run**, with a single lead-in block L, in which the first blocks
  paged little (page-ins 21 MiB in L, 1 MiB in W0, 94 MiB in R0): round 0's R0/W0 ratio was
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
- **Repeats.** Each warm block starts its own process, with its warm-ups, and ends it.

**The formal batch.**
- **Seed 5309,** fixed on 2026-10-26, before the batch. No dry run or functional check used it:
  they used 1, 2, 3, 7, 2610 and 2611. So the formal workload's sequences were not seen while the
  protocol was developed. With the default settings it plans the 56 blocks above.
- **One formal batch,** in a new folder under `data/outputs-result-cache/formal/`, on the frozen
  commit with a clean worktree (`run --formal` refuses otherwise).

**Rerun policy.**
- **The decision to rerun rests on `validity.json` alone,** made before the paired results are
  read.
- **A host, cleanup or drift failure allows one rerun.** Host and cleanup cover power, sleep,
  thermal, memory pressure, competing containers, cleanup and an aborted batch. The rerun uses the
  same seed and the same frozen commit, in a new folder.
- **A correctness failure stops formal batches.** Correctness covers complete, statuses, sources,
  pairs, breaker, answers, keys and Redis. Such a failure points to a fault: no formal batch runs
  until it is diagnosed. A fix needs a new commit, the author's approval and a new freeze.
- **At most two formal batches run on one frozen commit.** Each is kept and reported with its
  verdict. An invalid batch's paired results are reported as invalid observations, never pooled
  with a valid batch's. If the rerun is invalid too, E3 has no valid formal result, and the
  author decides what follows.
- **Swap-out flags never cause a rerun.** They only decide what the sensitivity analysis leaves
  out (section 6).

## 5. Host conditions and contemporaneous controls on this Mac (proposals)

**Why not the 4.0 GiB gate.** That gate was approved in M2 to decide whether *memory figures*
are representative: resident sizes shrink under compression and swap. E3's main results are
*latencies compared within one batch*, where every configuration runs interleaved under the same
host state. What can distort a latency happens during the block: a sleep, thermal throttling,
critical memory pressure, competing containers or other work, paging or swapping. Section 6
checks those it can detect reliably and records the rest as diagnostics, with their limits.
Available memory is recorded but not gated:
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
- **The host sampler, every 1 s:**
  - macOS's memory-pressure level;
  - `vm_stat`'s Pageins, Pageouts, Swapins and Swapouts, each by its own name;
  - the 1-minute load average, and the CPUs' busy and idle time (all CPUs summed);
  - `pmset -g therm`'s thermal and performance warnings.

  Every sample is kept (`host_samples.jsonl`). The block readings before and after leave out
  psutil's `sin` and `sout` (the correction above).
- **The experiment's own CPU time, every 0.5 s and at every block boundary**
  (`own_cpu_samples.jsonl`):
  - the CPU seconds of the driver and every process descended from it, each followed by pid and
    creation time, also after it is re-parented (the Spark JVM outlives its summary process);
  - the CPUs' busy and idle seconds, read at the same instant.
- **Both clocks,** monotonic and wall, at every block boundary and at the batch's start and end,
  for the sleep check. `e3_run` keeps the Mac awake (`caffeinate -i`); the check verifies it.
- **The process tree of each warm process (or each N process), every 0.5 s.** Then one scan,
  after the block, for processes still carrying the block's marker. A full marker scan reads
  every process's environment, which costs too much to repeat during timing.

**Contemporaneous controls.**
- **Every R block has its own W control:** the identical requests and warm-ups without the cache,
  run right before or right after it (section 4).
- **Every comparison is paired** (section 7).
- **The drift rule** (section 6) compares the W controls' medians in the last round with the
  first.

## 6. The protocol: host-specific paired latency observations (approved by the author, 2026-10-26)

**What a valid batch yields.** Paired end-to-end latency differences, observed on this Mac in one
batch, under its recorded host state: each R request against the identical request of its W
control, and each N request against the same request in its round's W0. They are host-specific
observations, not performance claims (section 12).

A valid batch shows that none of the checks below failed. It does not show that every source of
host interference was controlled. Running each pair's two blocks next to each other is the main
control.

**Checks.** The collector checks each of these. Any failure makes the batch invalid, and
`validity.json` lists why.

| Check | Holds when |
|---|---|
| Correctness | every planned request is recorded once, warm-ups included; every answer is `ok` and equals the reference answer, value types included; sources are as designed (W and N from Spark, R's hit rate exact, every warm-up from Spark); each R and F block starts with none of its keys in Redis; F's breaker counts 3 GET errors, then skips, and misses after the restart; each R block and its W control ran identical requests and warm-ups |
| Power | AC power and the lid open at every block's readings |
| Sleep | over every block and over the whole batch, the wall clock advances as the monotonic clock does, within 1.0 s (M3's tolerance). macOS's monotonic clock stops while the Mac sleeps |
| Thermal | no thermal or performance warning in any sample |
| Memory pressure | never critical (level 4) |
| Competing containers | none running at any block reading; no other project's container event at any time of the batch, the gaps between blocks included; the container monitor ran |
| Cleanup | every block's marked processes are gone within the 15 s settle, which runs outside request timing. A survivor fails its block and is ended only when its ownership is verified; the batch aborts if that cannot be confirmed. Every process exits 0, and Redis's peak stays within its 128 MiB limit |
| Drift | for each query, the pooled W median of the last round is within ±20% of the first round's |

**The lead-in round** is checked like any block for correctness, Redis and sleep, and is covered
by the batch-wide container check. Its other per-block host readings are reported, not gated, and
it is left out of every comparison.

**Diagnostics,** recorded and reported but never gated (`host.csv`, `host_samples.jsonl`,
`own_cpu_samples.jsonl`):
- page-ins and page-outs, and swap-ins and swap-outs (vm_stat);
- the 1-minute load average and the CPUs' busy share;
- the experiment's own CPU time by kind, beside the CPUs' busy time read at the same instants, and
  the remainder, which is left unaccounted for;
- available memory, swap in use, the pressure level, and the gap between the two clocks;
- the timing diagnostics of section 7.

**The page limits are withdrawn** (protocol correction, 2026-10-26, decided by the author before
any formal measurement).
- Until then, page-outs were limited to 64 MiB per block and page-ins to 256 MiB per W or R block.
- Those limits were introduced as swap limits, under the misreading of psutil's counters
  ([host-counters-correction.md](host-counters-correction.md)), and no relation between page
  counts and timing validity was established.
- The counters stay as diagnostics. Past batches are not relabelled: each keeps the verdict it
  was collected with, and none is collected again.

**Limitations.**
- **Paging.** A page-in is any request for a page from a pager, file reads included. The counters
  do not say which process caused the paging, or whether any request waited on it. Episodes of
  hundreds of MiB came and went in both prepared dry runs while the configuration stayed the same;
  their source is not recorded.
- **CPU attribution.** The experiment's own CPU is a lower bound. It is sampled every 0.5 s and at
  block boundaries, so it misses the CPU a process uses after its last sample, and processes
  shorter than the interval. Two things fall in the unaccounted remainder:
  - the Docker VM, which runs Redis and cannot be attributed by process;
  - the kernel's work for the experiment, which is not a process.

  So unaccounted CPU is not evidence of external interference, and total CPU use alone never is.
- **The checks are a minimum.** A condition they do not cover (paging, CPU or disk contention) can
  differ between blocks. The design controls only for what affects both members of a pair.
- **Drift.** In the last prepared dry run, single rounds' W medians ranged from −18% to +11%
  around round 0's. So the ±20% rule can fail a formal batch on round-to-round variation alone.
  It is kept unchanged.
- **Swap.** Only one prepared batch has recorded swap counters.
- **Monitoring overhead.** Every timing includes the monitoring configuration:
  - the host sampler, which every second starts `sysctl`, `vm_stat` and `pmset`;
  - the own-CPU sampler and each warm process's tree sampler, every 0.5 s;
  - `docker events`, for the whole batch.

  Every configuration runs under the same monitoring, so both members of a pair carry it. But the
  samplers' overhead on the latencies has not been separately quantified, so absolute latencies
  are the latencies of this monitored setup.

**The swap-out rule** (approved by the author, 2026-10-26; implemented in the collector).
- **Why swap matters.** A swap-out means the memory compressor ran out of room and wrote memory to
  disk. A later swap-in makes whatever needs those pages wait for the disk. Unlike page-ins, swap
  traffic indicates a memory shortage directly, and it is what the withdrawn limits were meant to
  catch.
- **The rule:**
  - **Flagging.** A pair is flagged when either member's block swapped out (vm_stat's Swapouts
    rose during the block): an R block or its W control, an N block or its W0. N pairs were
    first flagged by W0 alone; the author extended the rule to both members on 2026-10-26.
    `paired.csv` gives each pair's `swap_flag`.
  - **The primary analysis** keeps every valid pair, flagged or not, and the flagged data are
    kept.
  - **The sensitivity analysis,** labelled "sensitivity: excluding swap-out pairs" in
    `paired_summary.csv`, leaves out every pair not known to be free of swap-outs: flagged, or
    with either member's swap counter not recorded, the same rule on both sides. Every group
    reports `n` and `n_excluded`, including a group left
    empty. `swap_flags.json` gives the counts of block pairs and request pairs, and names the
    flagged ones.
  - **Effect on validity:** none. Swap-ins are reported only.
- **Why no size threshold.** The one prepared batch with these counters swapped nothing out in all
  56 blocks, and swapped in at most 8.4 MiB in a W or R block. The editor-open functional check
  swapped out up to 556 MiB in a block. One run supports neither a size above zero nor a swap-in
  limit. The rule's zero is not fitted to that run: it is where the host starts writing memory to
  disk.
- **The stricter alternative,** where any swap-out in a W or R block invalidates the batch, was
  not adopted.

## 7. Measures and reporting

**The attribution rule.** A difference is attributed to the cache only when it is a **paired
end-to-end difference**: the client latency of an R request against that of the identical request
at the same position of its W control. Differences between blocks with different ticker subsets,
other repeat patterns or another round are never attributed to caching. The same holds for N:
each N request is compared with the same request in its round's W0. The lead-in round is never
compared. **These paired end-to-end differences are the primary result.** The primary analysis
uses every valid pair. The swap-out sensitivity analysis (section 6) is reported beside it,
labelled, with its sample counts, and never replaces it.

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
- **The host per block** (`host.csv`; descriptive, and nothing in it gates):
  - page-ins, page-outs, swap-ins and swap-outs in MiB, and which counters they came from;
  - the 1-minute load average (mean and maximum over the block's samples), and `cpu_busy_share`;
  - the experiment's own CPU seconds by kind (`own_e3_driver_s`, `own_summary_s`,
    `own_spark_jvm_s`, `own_python_worker_s`, `own_other_s`; total `own_cpu_s`), beside the
    CPUs' busy seconds read at the same instants (`busy_cpu_s`, out of `cpu_capacity_s`);
  - `unaccounted_cpu_s`, busy less own, which is not external interference (section 6,
    limitations);
  - `clock_gap_s`, the pressure level, and available memory and swap in use before and after.

  None of these says by itself why a block's latencies differ.
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
6. **The protocol** (section 6): approved on 2026-10-26, with the swap-out rule.
7. **Reporting** (section 7): paired end-to-end differences as the primary result; the
   diagnostics as descriptive and the hit imbalance as an estimate; F as correctness and Redis's
   share, not a latency comparison; memory figures as not representative.
8. **The formal batch and the rerun policy** (section 4): approved on 2026-10-26. Seed 5309; at
   most two formal batches on one frozen commit; a rerun only after a host, cleanup or drift
   failure; none after a correctness failure until it is diagnosed.

Decided by the author on 2026-10-26, for the next dry run: the lead-in round (section 4), the
settle and the batch-wide container check (section 6), the descriptive diagnostics (section 7),
and keeping the six measured rounds and the current limits. After the lead-in-round dry run, on
the same day:
- the correction of the counters' names;
- page and swap traffic recorded separately, with no old limit carried over to swap;
- the load diagnostics;
- the drift rule unchanged.

After the vm-counters dry run, later the same day, before any formal measurement:
- **The page-in and page-out limits are withdrawn**, and the counters kept as diagnostics. This is a
  documented protocol correction, not a relabelling of past batches (section 6).
- **The experiment's own CPU time,** child processes included, is recorded as a diagnostic.
  External CPU interference is never inferred from total CPU use alone.
- **One compact protocol** (section 6) keeps the power, sleep, thermal, critical-pressure,
  competing-container, correctness, cleanup and drift checks. E3 had no sleep check until then:
  it relied on `caffeinate` and the lid. The wall-against-monotonic check, with M3's 1.0 s
  tolerance, was added to meet this decision.

Approved by the author on 2026-10-26:
- **Section 6,** the protocol.
- **The swap-out flagging rule:**
  - a pair is flagged when either its W or its R block swapped out;
  - all valid pairs stay in the primary analysis, and the flagged data are kept;
  - the analysis without flagged pairs is reported as a labelled sensitivity analysis, with
    sample counts.
- **N pairs** are flagged when either member swapped out, N included. A missing counter on
  either side leaves the pair out of the sensitivity analysis.
- **The formal seed, 5309, and the rerun policy** (section 4).

## 10. Dry runs so far (not formal)

| Batch | Purpose | Outcome |
|---|---|---|
| `sizing/20261026T113443Z` | sizing, 1 round, 3 warm-ups | every check the collector had then held except host: memory pressure was critical during R0. (It would also fail the warm-up check added afterwards.) The run found two driver bugs, both fixed: the host sampler's stop event shadowed `Thread._stop`, so finishing failed after all 6 blocks; and warm-ups ran before the block's keys were deleted, so 2 of them hit Redis and warmed nothing. The collector now checks that every warm-up reached Spark. |
| `sizing/20261026T121817Z` | functional check of the paired design, 1 round, editor open, no lead-in | the W controls ran and paired: **pairs**, sources, breaker, answers, keys, Redis and drift held. Host failed: page-ins (recorded as swap-in) of 792 MiB in W0 and 285 MiB in R0, over the provisional 256 MiB. That start-of-batch transient is the reason for the lead-in (section 4). Not evidence for thresholds: the editor was open. |
| `dry-run/20261026T160445Z` | **the prepared full-length dry run** (run by the author, editor closed): a single lead-in block L and six measured rounds | NOT valid, on host only (43 problems); every other check held. **42:** "1 marked process alive after the block" in every gated warm block (L's is not gated), none in N. The driver kept only a count, so the processes were not identified. Available memory stayed at 2.8–3.3 GiB and swap in use fell from 1.09 to 1.00 GiB, so they did not accumulate: most likely a shutdown still in progress, which led to the settle (section 6). **1:** `b18-R0` paged in 271 MiB (recorded as swap-in), over 256; its latencies matched its control's (median 0.137 vs 0.138 s). Page-outs at most 5.8 MiB; memory pressure normal throughout; 0 other-project container events, gaps included. Drift: last against first +8.5%, +11.6%, −0.5%. Round 0's R0/W0 ratio was 1.25 (section 4). Kept unchanged (62 files). |
| `dry-run/20261026T155212Z` | a start of the full-length dry run, before 160445Z | stopped during its third block (`b02-R0`) after 46 s, with 2 of 49 blocks recorded; the driver recorded no abort, and the records do not say why it stopped. Its collector output: NOT valid, with complete 47, pairs 1 and host 1 (the host problem: "1 marked process alive after the block" in `b01-W0`). Kept unchanged (16 files). |
| `dry-run/20261026T193201Z-lead-in-round` | **the prepared full-length dry run with the lead-in round** (run by the author, editor closed), seed 2611, 56 blocks, 18.0 min | NOT valid: host 7 and drift 1; every other check held. **Host 7:** page-ins (recorded as swap-in) over 256 MiB in the W and R blocks `b22`–`b28`, 267–2,306 MiB, one episode from about t+4.8 to t+11 min that N and F blocks shared (`b30-N` 1,206 MiB, not gated). Page-outs at most 4.9 MiB, swap in use flat at 0.47–0.48 GiB, pressure level 1 throughout, no thermal warning. Swap traffic was not recorded. The settle was clean in all 56 blocks (the warm blocks' JVMs gone after 0.52–0.54 s); 0 other-project container events out of 1,780. **Drift 1:** comparison's pooled W median 0.132 s in round 0 and 0.169 s in round 5 (+28.7%, limit 20%); overview +17.2%, sensitivity +4.9%. Round 0's W controls were the fastest for overview and comparison, as in 160445Z; the records do not show why. Round 0's R0/W0 total ratio was 1.062, inside rounds 1–5's 0.90–1.13. Kept unchanged (69 files). |
| `dry-run/20261026T225409Z-vm-counters` | **the prepared full-length dry run with vm_stat's counters** (run by the author, editor closed), seed 2611, 56 blocks, 15.4 min, commit `4abec0a` (clean) | **NOT valid, as collected at `4abec0a`: host 4;** every other check held. The four: page-ins over the then-current 256 MiB limit in `b19-W90` (271 MiB), `b20-R50` (273), `b35-W90` (879) and `b37-W50` (279); those blocks swapped in 0.1–0.8 MiB. The limit was withdrawn afterwards (section 6); this verdict stands as recorded, and the batch is not collected again. **Swap:** 0.0 MiB swapped out in all 56 blocks; swap-ins at most 48.3 MiB per block (`b14-N`), at most 8.4 MiB in a W or R block; swap in use 0.60 → 0.37 GiB. **Paging:** two page-in episodes, about t+4.6–6.6 and t+9.5–10.9 min; page-outs at most 4.0 MiB. **Load:** the warm blocks of rounds 1–2 (`b18`–`b29`, about t+5.3–7.8 min) kept 60–81% of all CPU time busy, against 28–56% in rounds 0, 3 and 5 (each block's first 5 s, its JVM start, left out); load average up to 10.2. The experiment's own CPU was not recorded then, so the excess is not attributed. **Drift** held: last round against round 0, −4.7%, −4.4% and −9.9%; single rounds ranged from −17.9% to +11.3%; round 1 had the fastest W medians, round 0 did not. **Pairs:** R0/W0 total ratio 0.998–1.117 across rounds (round 0: 1.072), R50 0.480–0.644, R90 0.117–0.175; hits 5.2–5.6 ms by round median. Settle clean in all 56 blocks; 0 other-project container events out of 1,553; pressure level 1; no thermal warning. Kept unchanged (71 files). |
| `functional/20261026T172508Z` | functional check of the settle, 1 round, editor open | in every warm block the marked process was the Spark JVM, gone 0.27–0.54 s after the driver exited; no survivor, every block confirmed clean. The batch-wide check counted 3 short-lived containers of another project (15 events, 3 of them between block windows). Paging with the editor open is not threshold evidence. |
| `functional/20261026T212648Z-vm-counters` | functional check of the corrected counters and the load diagnostics: 1 round, no lead-in round, seed 7, editor open, on the uncommitted change (its source hashes recorded), 5.9 min | **valid** on every check. The records carry vm_stat's four counters under their own names, and no psutil `sin` or `sout`. All 340 samples have every counter, taken 1.02–1.45 s apart, and each block's window equals the difference of its first and last samples. **Swap traffic, recorded and not gated:** swap-outs 0–556 MiB per block, while page-outs stayed at 1.4–6.7 MiB (`b03-R50`: 556 MiB swapped out, 1.8 MiB paged out); swap-ins 25–339 MiB. **The load:** 1-minute load average 9.3–11.9 on 8 logical CPUs, and 76–82% of all CPU time busy in every block. Pressure level 2 throughout, with 1.3–2.0 GiB available. Not evidence for any limit or for timing: the editor was open and the host loaded. |
| `functional/20261026T233512Z-own-cpu` | functional check of the protocol correction (no page limits, the sleep check, the experiment's own CPU): 1 round, no lead-in round, seed 7, editor open, on the uncommitted change (its source hashes recorded), 2.6 min | **valid** on every check, sleep included. Clock gaps within 1 ms per block, −3 ms over the batch. 319 own-CPU samples followed 47 processes of 4 kinds (e3_driver, summary, spark_jvm, other). Per warm block, own CPU was 21.9–34.4 s, 19.3–31.5 s of it the Spark JVM's, against 32–54 s busy, leaving 9.6–19.5 s unaccounted. N: 75.0 s own, 60.2 s unaccounted. F: 25.9 s own, 48.3 s unaccounted while Docker stopped and started Redis, whose VM is not attributable by process. Swap-outs up to 208 MiB per block. Not evidence about interference or for any limit: the editor was open. |
| `dry-run/20261026T114515Z` | dry run, 1 round, 12 warm-ups, before the pairs | **valid** on every check then defined (drift trivially: one round). 0 other containers, 0 container events, no critical pressure, no thermal warning. |

**Tests.** On the commit that adds the lead-in round and the diagnostics, the E3 suites
(`tests/test_cache_experiment.py`, `tests/test_result_cache_collector.py`,
`tests/test_result_cache_session.py`) passed: **84 tests**. The new collector, run on a copy of
`dry-run/20261026T160445Z`, gives the same 43 host problems; the original was not touched.

With the correction of the counters and the load diagnostics, the same suites pass: **97
tests**. They include a check, on macOS, that psutil's `sin` and `sout` lie between two vm_stat
readings of Pageins and Pageouts. Five deliberate faults were each caught by a failing test:
- reading the old fields as swap;
- gating swap-ins;
- passing a block whose page-ins are missing;
- putting psutil's `sin` back into the samples;
- keeping psutil's counters in the block readings.

No earlier batch was collected again: the collector writes into the batch folder.

With the protocol correction, the same suites pass: **108 tests**. The correction withdraws the
page limits and adds the sleep check and the experiment's own CPU time; one test follows a
process re-parented after its parent exits. Five deliberate faults were each caught by a failing
test:
- forgetting a gone process's CPU;
- not following a re-parented process;
- counting all busy CPU as unaccounted;
- disabling the sleep check;
- gating page-ins again.

With the swap-out rule, N pairs flagged by either member, the same suites pass: **114 tests**.
Five deliberate faults were each caught by a failing test:
- ignoring the W control's swap-out;
- keeping unrecorded pairs in the sensitivity analysis;
- dropping flagged pairs from the primary analysis;
- flagging N pairs by W0 alone;
- reading a missing N counter as free of swap-outs.

The collector was also run on a copy of `functional/20261026T233512Z-own-cpu` (the original
untouched). It flagged 3 of the 4 block pairs:
- R0, whose R block swapped out 75 MiB;
- R50, whose W control swapped out 50 MiB;
- the N pair, whose N block swapped out 6 MiB while its W0 swapped out nothing.

R90 was left unflagged. The sensitivity analysis kept 30 of 96 request pairs.

**The next prepared dry run (proposed; not started).** The same design and seed (2611), under the
protocol of section 6, so that each block can be set beside the same block of the two earlier
prepared runs. It adds the experiment's own CPU time, the sleep check, and a second batch of swap
counters. The author decides when it runs, from Terminal under the preparation of section 5,
with the editor closed. Its records are kept whatever its outcome. Claude Code cannot run it: the
preparation means quitting the editor, which Claude Code runs in.

**Freezing the protocol.** Section 6 and the swap-out rule are approved. The freeze needs the
author's approval of the rest of Part A (section 9), the formal seed and the rerun policy
included, and the required checks passing on the final code. The frozen commit is then recorded
here, in a documentation-only commit that leaves the code unchanged; the formal batch's recorded
source hashes must match the frozen commit's. The formal batch
runs on that commit only. `run --formal` refuses a dirty worktree, and the batch records its code
identity.

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
with AC power, the lid open, and Docker running with nothing else (`<repository>` is the main
checkout):

```zsh
cd <repository>/.claude/worktrees/result-cache-experiment
deactivate 2>/dev/null
export E3_PURPOSE=dry-run
export E3_SEED=2611
export E3_BATCH=$(date -u +%Y%m%dT%H%M%SZ)-protocol
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
- Latencies free of the monitoring's overhead, which has not been separately quantified
  (section 6).
- Behaviour under a paused or partially responsive Redis. The design stops Redis, which refuses
  connections at once.
- Any change to the analysis results in spec §8.
