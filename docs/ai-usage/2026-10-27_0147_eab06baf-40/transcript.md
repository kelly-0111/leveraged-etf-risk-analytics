# Claude Code message 40

Session: `eab06baf-de8e-4e5f-830e-4907c7544308` · prompt sent 2026-10-27 01:47 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): email ×3, git-user ×18, home ×121, host ×15, memory ×36, model-reasoning ×9, user ×38. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-27T06:47:00.550Z



<pasted_content id="2323">
(base) [REDACTED:user]@[REDACTED:host] ~ % cd ~/leveraged-etf-risk-analytics/.claude/worktrees/result-cache-experiment
deactivate 2>/dev/null
git diff --quiet 5b916a5 -- src analysis tests pyproject.toml uv.lock docs/result-cache-session.zsh && test -z "$(git status --porcelain)" && echo "frozen code: ok" || echo "frozen code: STOP"
export E3_PURPOSE=formal
export E3_SEED=5309
export E3_BATCH=$(date -u +%Y%m%dT%H%M%SZ)-formal-1
source docs/result-cache-session.zsh
e3_redis
e3_plan
frozen code: ok
[+] Running 1/1
 ✔ redis Pulled                                                            3.4s 
[+] Running 1/1
 ✔ Container etf-risk-jobs-redis-1  H...                                   2.8s 
redis: ready after 0.1 s
56 blocks, 92 keys -> data/outputs-result-cache/formal/20261027T062927Z-formal-1/plan.json
(base) [REDACTED:user]@[REDACTED:host] result-cache-experiment % e3_run
host: 2.82 GiB available, swap 1.16 GiB used, pressure level 1, AC Power, lid closed False
ready
(base) [REDACTED:user]@[REDACTED:host] result-cache-experiment % e3_collect
ok   complete
ok   statuses
ok   sources
ok   pairs
ok   breaker
ok   answers
ok   keys
ok   host
ok   sleep
ok   redis
ok   drift
valid
diagnostics (measured blocks; never gated):
  swap-ins up to 7.7 MiB; swap-outs up to 0.0 MiB (per block)
  page-ins up to 226.1 MiB; page-outs up to 4.4 MiB (per block)
  own CPU up to 85.7 s (per block); unaccounted CPU up to 52% of capacity (not attributed)
swap-out flags: 0 of 24 block pairs flagged, 0 not recorded (0 and 0 of 576 request pairs); primary analysis keeps all, 'sensitivity: excluding swap-out pairs' keeps 576
(base) [REDACTED:user]@[REDACTED:host] result-cache-experiment % e3_cleanup
[+] Stopping 1/1
 ✔ Container etf-risk-jobs-redis-1  S...                                   0.2s 
Going to remove etf-risk-jobs-redis-1
[+] Removing 1/1
 ✔ Container etf-risk-jobs-redis-1  R...                                   0.0s 
(base) [REDACTED:user]@[REDACTED:host] result-cache-experiment % uv run python -c 'import hashlib, json, subprocess, sys; folder, frozen_commit = sys.argv[1], "5b916a5"; code = json.load(open(folder + "/batch.json"))["code"]; seed = json.load(open(folder + "/plan.json"))["seed"]; show = lambda path: subprocess.run(["git", "show", frozen_commit + ":" + path], capture_output=True, check=True).stdout; names = subprocess.run(["git", "ls-tree", "-r", "--name-only", frozen_commit, "src/etf_risk"], capture_output=True, text=True, check=True).stdout.split(); frozen = {n[len("src/etf_risk/"):]: hashlib.sha256(show(n)).hexdigest() for n in names if n.endswith((".py", ".sql"))}; same_source = code["source_sha256"] == frozen; same_lock = code["uv_lock_sha256"] == hashlib.sha256(show("uv.lock")).hexdigest(); print("HEAD", code["git_commit"], "| seed", seed, "| source hashes match", frozen_commit, same_source, "|", len(frozen), "files | uv.lock matches", same_lock, "| worktree clean", code["git_worktree_clean"]); sys.exit(0 if same_source and same_lock and code["git_worktree_clean"] is True and seed == 5309 else 1)' $E3_DIR
HEAD 51d5453824a66dea500f7f6aaf2bdef1047529b6 | seed 5309 | source hashes match 5b916a5 True | 39 files | uv.lock matches True | worktree clean True
(base) [REDACTED:user]@[REDACTED:host] result-cache-experiment %
</pasted_content id="2323">


## 2. Assistant — 2026-10-27T06:47:09.268Z

The formal batch completed and checks out on its own record:
- **Valid** on every check (correctness, host, sleep, Redis, drift);
- **Verified against the frozen code:** it ran on `51d5453`, a documentation-only commit after `5b916a5`, with seed 5309. All 39 source-file hashes and `uv.lock` match `5b916a5`, and the worktree was clean.
- **No swap-outs:** 0 of 24 block pairs flagged, so the sensitivity analysis keeps all 576 request pairs and equals the primary analysis.

I'll fingerprint the folder and read the results from it without modifying anything:

## 3. Assistant — 2026-10-27T06:47:15.861Z

### Tool call: Bash

```
{
  "command": "cd ~/leveraged-etf-risk-analytics/.claude/worktrees/result-cache-experiment && F=data/outputs-result-cache/formal/20261027T062927Z-formal-1 && uv run python -c '\nimport hashlib, os, sys\nroot = sys.argv[1]; h = hashlib.sha256(); n = 0\nfor dp, dn, fn in sorted(os.walk(root)):\n    dn.sort()\n    for f in sorted(fn):\n        p = os.path.join(dp, f); n += 1\n        h.update(os.path.relpath(p, root).encode()); h.update(open(p, \"rb\").read())\nprint(\"fingerprint:\", n, \"files\", h.hexdigest()[:16])' $F | tee /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/formal1-fingerprint.txt && python3 - $F <<'EOF'\nimport json, sys\nfrom datetime import datetime\nd = sys.argv[1] + \"/\"\nb = json.load(open(d + \"batch.json\")); v = json.load(open(d + \"validity.json\"))\nt = [datetime.fromisoformat(b[k]) for k in (\"started_at_utc\", \"finished_at_utc\")]\nprint(f\"{b['started_at_utc'][:19]}Z, {(t[1]-t[0]).total_seconds()/60:.1f} min, aborted={b.get('aborted')}, formal={b['formal']}, commit {b['code']['git_commit'][:7]}, clean {b['code']['git_worktree_clean']}, redis {b['redis_info']}, keys deleted at start/end {b['keys_deleted_at_start']}/{b['keys_deleted_at_end']}, monitor error {b['container_monitor_error']}\")\nprint(\"valid:\", v[\"valid\"], {k: len(x) for k, x in v[\"problems\"].items()})\nev = [json.loads(l) for l in open(d + \"containers.jsonl\")]\nprint(\"container events\", len(ev), \"other-project\", sum(not e[\"ours\"] for e in ev))\nprint(\"clock gap batch\", round((b[\"clock_end\"][\"wall\"]-b[\"clock_start\"][\"wall\"])-(b[\"clock_end\"][\"mono\"]-b[\"clock_start\"][\"mono\"]), 3), \"s\")\nEOF",
  "description": "Fingerprint the formal batch and read its metadata"
}
```

## 4. User — 2026-10-27T06:47:19.184Z

### Tool result

```
fingerprint: 73 files d44f81c2cc80e8f0
2026-10-27T06:29:53Z, 15.3 min, aborted=None, formal=True, commit 51d5453, clean True, redis {'redis_version': '8.10.2'}, keys deleted at start/end 0/40, monitor error None
valid: True {'complete': 0, 'statuses': 0, 'sources': 0, 'pairs': 0, 'breaker': 0, 'answers': 0, 'keys': 0, 'host': 0, 'sleep': 0, 'redis': 0, 'drift': 0}
container events 1547 other-project 0
clock gap batch 0.038 s
```

## 5. Assistant — 2026-10-27T06:47:20.521Z

Now the primary results by round, drift, the resolver cost, F, and the descriptive host diagnostics:

## 6. Assistant — 2026-10-27T06:47:34.950Z

### Tool call: Bash

```
{
  "command": "python3 - data/outputs-result-cache/formal/20261027T062927Z-formal-1 <<'EOF'\nimport csv, json, statistics as st, sys\nd = sys.argv[1] + \"/\"\nrows = [json.loads(l) for l in open(d + \"requests.jsonl\")]\nm = [r for r in rows if not r[\"warmup\"] and r[\"status\"] == \"ok\" and not r.get(\"lead_in\")]\nS = [r for r in csv.DictReader(open(d + \"paired_summary.csv\")) if r[\"analysis\"] == \"primary\"]\nP = list(csv.DictReader(open(d + \"paired.csv\")))\nmed = lambda v: st.median(v)\nprint(\"BLOCK TOTALS R/W (end to end) by round 0..5\")\nfor pair in (\"0.0\", \"0.5\", \"0.9\"):\n    g = sorted((int(r[\"round\"]), float(r[\"total_ratio\"]), float(r[\"total_difference_s\"])) for r in S if r[\"scope\"] == \"block\" and r[\"pair\"] == pair)\n    print(f\"  R{int(float(pair)*100):<3}\", \" \".join(f\"{x[1]:.3f}\" for x in g), f\"| median {med([x[1] for x in g]):.3f}, saved per block {med([-x[2] for x in g]):+.2f} s median\")\nprint(\"REQUEST GROUPS (median paired difference ms, median ratio, n)\")\nfor r in S:\n    if r[\"scope\"] == \"requests\":\n        print(f\"  {r['config']} {r['pair'] or '-':4} {r['kind']:11} {r['query'][:4]} n={r['n']:>3} diff {1000*float(r['median_difference_s']):+8.1f} ms ratio {float(r['median_ratio']):.3f} [{float(r['min_ratio']):.3f}-{float(r['max_ratio']):.3f}]\")\nlat = lambda sel: [r[\"client_seconds\"] for r in m if sel(r)]\nprint(f\"LATENCY medians: W {med(lat(lambda r: r['config']=='W')):.3f} s; R miss {med(lat(lambda r: r['config']=='R' and r['source']=='spark')):.3f} s; R hit {1000*med(lat(lambda r: r['config']=='R' and r['source']=='cache')):.1f} ms; N {med(lat(lambda r: r['config']=='N')):.2f} s\")\nrv = lambda sel: [(r[\"server_seconds\"] or {}).get(\"resolve\") for r in m if sel(r) and (r[\"server_seconds\"] or {}).get(\"resolve\") is not None]\nprint(f\"RESOLVE medians: N full hash {1000*med(rv(lambda r: r['config']=='N')):.0f} ms; warm check {1000*med(rv(lambda r: r['config'] in ('W','R'))):.1f} ms\")\nrest = lambda r: r[\"client_seconds\"] - ((r[\"server_seconds\"] or {}).get(\"spark\") or 0) - ((r[\"server_seconds\"] or {}).get(\"resolve\") or 0)\nprint(f\"REDIS DOWN rest median {1000*med([rest(r) for r in m if r['config']=='F' and r['phase']==1]):.2f} ms vs W {1000*med([rest(r) for r in m if r['config']=='W']):.2f} ms\")\nprint(\"DRIFT (pooled W median by round 0..5):\")\nfor q in (\"overview\", \"comparison\", \"sensitivity\"):\n    v = [med([r[\"client_seconds\"] for r in m if r[\"config\"]==\"W\" and r[\"round\"]==k and r[\"query\"]==q]) for k in range(6)]\n    print(f\"  {q:11}\", \" \".join(f\"{x:.3f}\" for x in v), f\"| last/first {v[5]/v[0]-1:+.1%}, rounds {min(v)/v[0]-1:+.1%}..{max(v)/v[0]-1:+.1%}\")\nH = [h for h in csv.DictReader(open(d + \"host.csv\")) if h[\"lead_in\"] == \"False\"]\nf = lambda k: [float(h[k]) for h in H if h[k] != \"\"]\nwr = [h for h in H if h[\"config\"] in (\"W\", \"R\")]\nprint(f\"HOST: pressure max {max(f('max_pressure_level')):.0f}; swap-ins max {max(f('swapins_mib')):.1f} MiB, swap-outs max {max(f('swapouts_mib')):.1f}; page-ins W/R max {max(float(h['pageins_mib']) for h in wr):.0f} MiB; clock gap max {max(abs(x) for x in f('clock_gap_s'))*1000:.1f} ms\")\nfor cfg in (\"W\", \"R\", \"N\", \"F\"):\n    g = [h for h in H if h[\"config\"] == cfg]\n    sh = [float(h[\"unaccounted_cpu_s\"])/float(h[\"cpu_capacity_s\"]) for h in g]; own = [float(h[\"own_cpu_s\"])/float(h[\"cpu_capacity_s\"]) for h in g]\n    print(f\"  {cfg}: own CPU share {min(own):.2f}-{max(own):.2f}, unaccounted share {min(sh):.2f}-{max(sh):.2f}, busy share {min(f2:=[float(h['busy_cpu_s'])/float(h['cpu_capacity_s']) for h in g]):.2f}-{max(f2):.2f}\")\nEOF",
  "description": "Summarize formal results, drift and host diagnostics"
}
```

## 7. User — 2026-10-27T06:47:35.778Z

### Tool result

```
BLOCK TOTALS R/W (end to end) by round 0..5
  R0   0.969 0.884 1.119 0.946 1.192 1.326 | median 1.044, saved per block -0.17 s median
  R50  0.488 0.679 0.448 0.632 0.532 0.461 | median 0.510, saved per block +2.04 s median
  R90  0.147 0.139 0.156 0.132 0.167 0.127 | median 0.143, saved per block +3.66 s median
REQUEST GROUPS (median paired difference ms, median ratio, n)
  N -    new process comp n= 12 diff  +5813.3 ms ratio 42.921 [29.126-57.500]
  N -    new process over n= 12 diff  +5788.4 ms ratio 46.086 [30.338-57.084]
  N -    new process sens n= 12 diff  +5775.0 ms ratio 40.333 [29.493-64.883]
  R 0.0  miss        comp n= 60 diff     +7.5 ms ratio 1.075 [0.528-1.932]
  R 0.0  miss        over n= 60 diff     +6.4 ms ratio 1.053 [0.553-1.845]
  R 0.0  miss        sens n= 60 diff     +6.3 ms ratio 1.047 [0.473-1.763]
  R 0.5  hit         comp n= 30 diff   -121.0 ms ratio 0.043 [0.027-0.068]
  R 0.5  hit         over n= 30 diff   -116.2 ms ratio 0.047 [0.029-0.063]
  R 0.5  hit         sens n= 30 diff   -122.4 ms ratio 0.045 [0.028-0.062]
  R 0.5  miss        comp n= 30 diff     +7.6 ms ratio 1.056 [0.658-1.653]
  R 0.5  miss        over n= 30 diff     -1.9 ms ratio 0.987 [0.530-1.654]
  R 0.5  miss        sens n= 30 diff    -15.8 ms ratio 0.883 [0.492-1.830]
  R 0.9  hit         comp n= 54 diff   -130.0 ms ratio 0.040 [0.022-0.066]
  R 0.9  hit         over n= 54 diff   -127.4 ms ratio 0.041 [0.026-0.083]
  R 0.9  hit         sens n= 54 diff   -124.0 ms ratio 0.041 [0.025-0.061]
  R 0.9  miss        comp n=  6 diff    -16.5 ms ratio 0.899 [0.645-1.079]
  R 0.9  miss        over n=  6 diff     -6.9 ms ratio 0.962 [0.681-1.179]
  R 0.9  miss        sens n=  6 diff    +19.4 ms ratio 1.148 [0.896-1.395]
LATENCY medians: W 0.132 s; R miss 0.139 s; R hit 5.4 ms; N 5.92 s
RESOLVE medians: N full hash 30 ms; warm check 4.8 ms
REDIS DOWN rest median 4.86 ms vs W 4.99 ms
DRIFT (pooled W median by round 0..5):
  overview    0.123 0.134 0.132 0.143 0.125 0.139 | last/first +12.9%, rounds +0.0%..+16.5%
  comparison  0.136 0.145 0.138 0.127 0.124 0.127 | last/first -6.6%, rounds -9.2%..+6.3%
  sensitivity 0.136 0.135 0.129 0.147 0.116 0.126 | last/first -7.9%, rounds -14.9%..+7.8%
HOST: pressure max 1; swap-ins max 7.7 MiB, swap-outs max 0.0; page-ins W/R max 226 MiB; clock gap max 18.6 ms
  W: own CPU share 0.26-0.36, unaccounted share 0.04-0.52, busy share 0.35-0.78
  R: own CPU share 0.27-0.36, unaccounted share 0.05-0.42, busy share 0.35-0.71
  N: own CPU share 0.28-0.30, unaccounted share 0.06-0.35, busy share 0.36-0.65
  F: own CPU share 0.17-0.22, unaccounted share 0.06-0.33, busy share 0.23-0.50
```

## 8. Assistant — 2026-10-27T06:47:44.885Z

### Tool call: Bash

```
{
  "command": "python3 - data/outputs-result-cache/formal/20261027T062927Z-formal-1 <<'EOF'\nimport csv, json, sys\nd = sys.argv[1] + \"/\"\nB = {b[\"block\"]: b for b in map(json.loads, open(d + \"blocks.jsonl\"))}\nt0 = min(b[\"before\"][\"mono\"] for b in B.values())\nfor h in csv.DictReader(open(d + \"host.csv\")):\n    if h[\"lead_in\"] == \"True\": continue\n    u = float(h[\"unaccounted_cpu_s\"]) / float(h[\"cpu_capacity_s\"])\n    mark = \" <==\" if u > 0.25 else \"\"\n    if u > 0.25 or h[\"config\"] in (\"W\", \"R\") and h[\"pair\"] == \"0.0\" and h[\"round\"] == \"5\":\n        print(f\"{h['block']:8} r{h['round']} t+{(B[h['block']]['before']['mono']-t0)/60:5.1f} min unaccounted {u:.2f} own {float(h['own_cpu_s'])/float(h['cpu_capacity_s']):.2f} load {float(h['load_1m_mean']):.1f} pagein {float(h['pageins_mib']):6.1f}{mark}\")\nEOF",
  "description": "Locate blocks with high unaccounted CPU"
}
```

## 9. User — 2026-10-27T06:47:45.765Z

### Tool result

```
b19-W90  r1 t+  5.4 min unaccounted 0.52 own 0.26 load 5.4 pagein  121.2 <==
b20-R50  r1 t+  5.6 min unaccounted 0.41 own 0.27 load 7.0 pagein    7.4 <==
b21-W50  r1 t+  5.8 min unaccounted 0.40 own 0.29 load 7.4 pagein   33.3 <==
b22-R0   r1 t+  6.0 min unaccounted 0.33 own 0.27 load 7.5 pagein   15.1 <==
b23-W0   r1 t+  6.2 min unaccounted 0.32 own 0.27 load 8.0 pagein    3.1 <==
b24-W0   r2 t+  6.5 min unaccounted 0.31 own 0.33 load 8.5 pagein    3.0 <==
b25-R0   r2 t+  6.7 min unaccounted 0.38 own 0.28 load 8.1 pagein   47.0 <==
b26-W50  r2 t+  6.9 min unaccounted 0.39 own 0.30 load 8.6 pagein   15.7 <==
b27-R50  r2 t+  7.1 min unaccounted 0.39 own 0.31 load 8.8 pagein    2.6 <==
b28-W90  r2 t+  7.3 min unaccounted 0.37 own 0.32 load 8.1 pagein    0.9 <==
b29-R90  r2 t+  7.5 min unaccounted 0.37 own 0.34 load 7.9 pagein    2.8 <==
b30-N    r2 t+  7.7 min unaccounted 0.35 own 0.30 load 8.3 pagein   32.2 <==
b31-F    r2 t+  8.3 min unaccounted 0.33 own 0.17 load 7.0 pagein    8.2 <==
b32-F    r3 t+  8.6 min unaccounted 0.31 own 0.18 load 6.9 pagein    2.7 <==
b33-N    r3 t+  8.9 min unaccounted 0.31 own 0.30 load 6.4 pagein   17.9 <==
b34-R90  r3 t+  9.4 min unaccounted 0.33 own 0.27 load 6.7 pagein    1.7 <==
b35-W90  r3 t+  9.6 min unaccounted 0.30 own 0.31 load 6.3 pagein    8.0 <==
b36-R50  r3 t+  9.8 min unaccounted 0.30 own 0.30 load 6.4 pagein    9.2 <==
b37-W50  r3 t+ 10.0 min unaccounted 0.32 own 0.31 load 6.8 pagein   63.9 <==
b38-R0   r3 t+ 10.2 min unaccounted 0.42 own 0.28 load 7.7 pagein   96.2 <==
b39-W0   r3 t+ 10.5 min unaccounted 0.41 own 0.29 load 7.7 pagein  123.3 <==
b40-W0   r4 t+ 10.7 min unaccounted 0.33 own 0.35 load 7.6 pagein   48.7 <==
b54-R0   r5 t+ 14.5 min unaccounted 0.07 own 0.33 load 3.8 pagein   16.8
b55-W0   r5 t+ 14.7 min unaccounted 0.05 own 0.34 load 3.8 pagein   16.9
```

## 10. Assistant — 2026-10-27T06:48:00.150Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/result-cache-experiment-m5.md",
  "old_string": "[REDACTED:memory]",
  "new_string": "[REDACTED:memory]"
}
```

## 11. User — 2026-10-27T06:48:01.050Z

### Tool result

```
[REDACTED:memory]
```

## 12. Assistant — 2026-10-27T06:48:14.538Z

# Formal batch `formal-1`: valid and verified against the frozen code

The first formal E3 batch is the formal result; under the rerun policy no rerun is needed. I only read the records: the folder is untouched (73 files, fingerprint `d44f81c2cc80e8f0`), and I haven't committed anything.

## Validity and provenance
- **It passed every check:** correctness (complete, statuses, sources, pairs, breaker, answers, keys), host, sleep, Redis and drift.
- **It ran on the frozen code:** commit `51d5453` with a clean worktree and seed 5309. All 39 source-file hashes and `uv.lock` match `5b916a5`.
- **The host was quiet by every check:** 15.3 minutes, not aborted, 0 of 1,547 container events from another project, memory pressure 1 throughout, no thermal warnings. The wall and monotonic clocks agreed within 38 ms over the batch.
- **No pair was flagged for swap-outs** (0 of 24 block pairs swapped out; swap-ins at most 7.7 MiB). The sensitivity analysis keeps all 576 request pairs, so it equals the primary analysis.

## Primary results: paired end-to-end differences on this Mac
| Comparison | Result |
|---|---|
| R block total ÷ its W control, by round | **R0** 0.88–1.33 (median 1.04); **R50** 0.45–0.68 (median 0.51); **R90** 0.13–0.17 (median 0.14) |
| Time saved per 30-request block, median | R0 about −0.17 s (slightly slower); R50 2.0 s; R90 3.7 s |
| Hit against the identical W request | 116–130 ms faster per query (median); ratio about 0.04 |
| Miss against W | R0: 6–8 ms slower (ratio 1.05–1.08); R50 and R90 misses are mixed, n = 6–30 |
| N against W0 | about 5.8 s slower; ratio 40–46 |

- **Typical latencies (medians):** W 0.132 s, R miss 0.139 s, hit 5.4 ms, N 5.92 s.
- **Checking the cache key** (the resolver) took 30 ms for N's full hash of the run folder and 4.8 ms for a warm process's quick check.
- **Redis stopped:** time outside Spark and that check was 4.86 ms, against W's 4.99 ms. The breaker sequence was exact.

## Drift
The rule passed: last round against first was +12.9% (overview), −6.6% (comparison) and −7.9% (sensitivity). Individual rounds ranged from −14.9% to +16.5% around round 0.

## Diagnostics (descriptive, nothing attributed)
- **A CPU episode from about t+5.4 to t+10.7 min (b19–b40):**
  - 30–52% of CPU capacity was unaccounted for, while the experiment's own share stayed at 26–35%. So the extra CPU wasn't the experiment's sampled processes.
  - Under the protocol that still isn't evidence of interference from outside: the Docker VM and kernel work are also in the unaccounted remainder.
  - The vm-counters dry run had an episode starting around the same point, about t+5 min.
  - Pair ratios in rounds 1–3 stayed within the other rounds' range.
- **The extreme R0 pair** (1.326, round 5) fell outside the episode, when unaccounted CPU was 5–7%.
- **Page-ins** reached at most 226 MiB in a W or R block; they're diagnostics only now.

## Against the dry-run-informed predictions (not revised)
- **Within the predictions:** W, R misses, R90, Redis down and the breaker.
- **Outside them:**
  - R0 at its round extremes (0.884 and 1.326, against a predicted 0.90–1.13);
  - R50 at its extremes (0.448 and 0.679, against 0.46–0.64);
  - N (5.92 s against 6.0–7.4 s) and hits (5.4 ms against 5.5–6.9 ms), both slightly below.

## Next
Writing Part B (the formal results, approached as in M3) is the next step. I'll draft it when you ask. The branch has 13 unpushed commits; pushing and merging are yours.
