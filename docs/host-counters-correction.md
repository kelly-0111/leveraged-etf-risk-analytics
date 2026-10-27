# Correction (2026-10-26): page-ins and page-outs recorded as swap traffic

Contributed by both the project author and Claude Code. Claude Code found the mislabel in the
E3 dry run `dry-run/20261026T193201Z-lead-in-round`, verified it and drafted this note. The
author decided how it is handled: correct the names, record page and swap traffic separately,
keep the historical records unchanged, infer nothing about swap from the old values, and carry
no old threshold over to the new counters.

## 1. What was wrong

M3's `harness.host_state()` and E3's host sampler recorded psutil's `swap_memory().sin` and
`.sout` as the bytes "swapped in" and "swapped out" (`swap_in_bytes`, `swap_out_bytes`). On
macOS these are **page-ins and page-outs**: vm_stat's `Pageins` and `Pageouts` times the page
size. Swap traffic is counted separately, as `Swapins` and `Swapouts`, which neither milestone
read.

A page-in is a request for a page from a pager. vm_stat(1)'s example is the inode pager, so
reads of files count: executables, libraries, memory-mapped and data files. A page-in count is
not a measure of swap, and these counters cannot split it into file reads and swap.

**Correct as recorded:** swap in use (`swap_used_bytes`, psutil's `used`, from `sysctl
vm.swapusage`), available memory, and macOS's memory-pressure level.

## 2. Evidence

- **The installed psutil (7.2.2).** `psutil/_psosx.py` returns the last two values of the C
  function `swap_mem()` as `sin` and `sout`. At the tag `release-7.2.2`,
  `psutil/arch/osx/mem.c` computes them as `vmstat.pageins * pagesize` and
  `vmstat.pageouts * pagesize`. It fills `vmstat` with `host_statistics64(HOST_VM_INFO64)`; the
  installed extension imports `host_statistics64`.
- **psutil's documentation** (`docs/index.rst`, same tag) describes `sin` and `sout` as "the
  number of bytes the system has swapped in/out from disk (cumulative)". Its only platform note
  is for Windows.
- **The macOS SDK** (`mach/vm_statistics.h`, `struct vm_statistics64`) gives four separate
  fields. `pageins` is "# of pageins" and `pageouts` "# of pageouts". `swapins` is "# of pages
  swapped in (via compression segments)" and `swapouts` "# of pages swapped out".
  vm_stat(1)'s descriptions of Swapins and Swapouts read as transposed against the header
  ("Swapins: … swapped out to disk"); this note follows the header.
- **This Mac (2026-10-26, page size 16,384 bytes):**
  - psutil's `sin` divided by the page size was within 1–3 pages of `Pageins`, which advanced
    between the reads, and `sout` equalled `Pageouts`;
  - `Swapins` and `Swapouts` were other counters: 80.2 and 84.1 million pages since boot,
    against `Pageins` 49.3 million and `Pageouts` 1.56 million.

  `tests/test_cache_experiment.py` now checks the mapping on every run on macOS: psutil's value
  must lie between two vm_stat readings taken around it.

## 3. Where the mislabelled counters were described

### E3 (`feature/result-cache-experiment`, not merged)

- **Part A** (`docs/result-cache-experiment.md`) said "swap-in" and "swap-out" for these
  counters, in:
  - section 4 (the lead-in's reasons);
  - section 5 (the list of what distorts a latency; the host sampler);
  - section 6 (rule 7 and its limits paragraph);
  - section 9 (decision 6);
  - section 10 (the dry-run rows).

  This change rewords them. The earlier wording stays in Git, up to `f867303`.
- **Tooling**, renamed in this change:
  - the driver's block windows (`host_window.swap_in_bytes`, `.swap_out_bytes`) and block
    readings (`before`/`after.host`, through `host_state()`);
  - the collector's messages ("MiB swapped in", "MiB swapped out") and its options
    `--swap-in-limit-mib` and `--swap-out-limit-mib`;
  - the session helpers' `E3_SWAP_IN_MIB` and `E3_SWAP_OUT_MIB`.
- **Records** (`data/outputs-result-cache/`, outside Git), kept unchanged. Every batch before
  this correction carries the old names in `blocks.jsonl`:
  - `sizing/20261026T113443Z` and `sizing/20261026T121817Z`;
  - `dry-run/20261026T114515Z`, `dry-run/20261026T155212Z`, `dry-run/20261026T160445Z` and
    `dry-run/20261026T193201Z-lead-in-round`;
  - `functional/20261026T172508Z`.

  The `validity.json` and `session.log` of four of them report "MiB swapped in": 121817Z (2
  problems), 160445Z (1), 172508Z (3) and 193201Z-lead-in-round (7). Each is a page-in figure.
  The collector reads these fields as page-ins and page-outs and reports their swap traffic as
  not recorded. These batches are not re-collected, because the collector writes into the batch
  folder.

### M3 (merged as PR #14)

- **Code**, unchanged here because it lies outside this milestone. The tests and mutation checks
  of both use the same names.
  - `src/etf_risk/jobs/harness.py`: `host_state()`, with its docstring ("the bytes swapped in
    and out so far (psutil)") and its keys `swap_in_bytes` and `swap_out_bytes`;
  - `analysis/collect_recovery_measurements.py`: its docstring and the columns
    `swap_out_during_bytes`, `swap_out_batch_bytes` and `swap_in_batch_bytes`.
- **`docs/recovery-part-a.md`:**
  - section 11 (preflight-4): the column "Swapped out during it", and "4.4 GiB was swapped in
    and 67 MiB swapped out";
  - section 12: condition 5 ("the bytes swapped in and out", "swap activity"), the example
    "26.5 MiB swapped out during the job", and "`injections.csv` gives each job its … swap
    activity".
- **`docs/recovery-part-b.md`:**
  - section 5.2: the column "Swapped out during (MiB)", and the two late jobs' "83 MiB" and
    "132 MiB swapped out during it";
  - section 6: "1.35 GiB swapped out, 47.9 GiB swapped in".

  All of these are page-outs and page-ins.
- **Two statements characterized swap traffic** that the recorded counters do not measure:
  "heavy swapping" (Part B, section 5.2) and "swapping heavily" (section 7.3, an approved
  answer).
- **No M3 verdict depended on the counters:** M3 recorded them and never gated on them (Part A,
  section 12, condition 5).

**Reworded on 2026-10-26, at the author's instruction.** Every passage listed above for the two
M3 documents now says "paged in" and "paged out", with its figures unchanged. The two statements
about heavy swapping give the swap in use from the records instead:
- 3.86–8.25 GiB at the 17 readings of batch-2's positions 1–17;
- 3.16–8.25 GiB at all readings of both formal batches: batch-1 4.64–5.33 GiB, batch-2
  3.16–8.25 GiB, ending 2.67 GiB above its start.

Swap-in-use figures are kept as they were. Each M3 document opens with a dated note, and M3 Part A
lists the changes in its section 13. M3's code keeps its names, to match its records. A code
correction, if the author wants one, is kept separate from E3.

## 4. What this correction does not do

- **It infers no swap traffic.** The old values are page-ins and page-outs. They give neither a
  value nor a bound for swap in those batches.
- **It carries no threshold over.** E3's limits were set from page-in and page-out values, so
  this correction kept them on those counters, correctly named: page-outs ≤ 64 MiB per block,
  and page-ins ≤ 256 MiB per W or R block. Swap-ins and swap-outs got no limit. Section 6 records
  that the page limits were later withdrawn.
- **It changes no record.** The approved M3 text changes only as section 3 lists: the names of
  the page figures, and the two statements about heavy swapping.

## 5. From now on (E3)

- **The host sampler** reads `vm_stat` every second, recording `pageins`, `pageouts`, `swapins`
  and `swapouts` in pages, with `page_size`. Every sample is saved to `host_samples.jsonl`.
- **The block readings** leave out psutil's two counters.
- **The collector** records page and swap traffic per block. In `host.csv`, a `counters` column
  says which counters each block's figures came from: `vm_stat`, or `psutil sin/sout` for
  batches recorded before this correction. Since the protocol correction of section 6, it gates
  neither.

## 6. Later the same day: the page limits withdrawn

After the prepared dry run `dry-run/20261026T225409Z-vm-counters`, the author withdrew the
page-in and page-out validity limits, before any formal measurement. They had been introduced as
swap limits, under the misreading this note corrects, and no relation between page counts and
timing validity was established.
- The counters are kept as diagnostics.
- This is a documented protocol correction ([result-cache-experiment.md](result-cache-experiment.md),
  section 6), not a relabelling of past batches: each keeps the verdict it was collected with,
  that dry run's "NOT valid: host 4" included.
- Real swap traffic got its own rule, approved the same day. A pair is flagged when its W or R
  block swapped out, and the analysis without flagged pairs is reported as a labelled
  sensitivity analysis. Validity is unaffected, and no size threshold is set.
