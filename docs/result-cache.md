# The result cache for summary queries (spec §11, M4)

Status: implemented, apart from step 8 (section 5), which the author writes. Nothing here
measures what the cache saves: that is the experiment E3 (M5), which has not been run.

Authorship: contributed by both the project author and Claude Code.
- **Claude Code** proposed the designs and wrote the Redis service and its client, the resolver
  and the registry tool, `summary.py`'s request flow, the scaffold of `cache.py`, the tests, the
  mutation checks and this document, with the derivations in it.
- **The project author** wrote the cache logic in `cache.py` (steps 1–6) and moved their SQL
  into `summary.py` (step 7), with tutoring. They made every decision recorded here: the run to
  register, the ticker-set parameter, each step's rules, the configuration, the policy for
  non-finite results, and the three revisions in sections 3, 4 and 6.

## 1. What a request does

`python -m etf_risk.summary query` (a new process per request) and `serve` (one warm process,
JSON lines) answer requests such as `{"query": "overview", "run": "<folder>", "params":
{"tickers": ["QQQ"]}}`:

1. **Resolve** the run (`etf_risk.runs`). It is servable only as an accepted job run (the job
   succeeded, and its accepted attempt recorded the run digest) or as a historical run in the
   reviewed registry `docs/accepted-runs.json`. Anything else is refused, with no fallback to
   another run. Resolving only reads the job table.
2. **Check the folder** against that digest (section 3).
3. **Build the result's identity** (`etf_risk.cache`, section 4) from the run digest, the query
   name, the SHA-256 of its SQL, the normalized parameters and the PySpark version.
4. **Get or compute** (section 5). A hit returns the stored result. A miss runs the query in
   Spark, checks the folder again, and only then returns the result and writes it back. If the
   folder changed while Spark read it, the request is refused and nothing is cached.
5. **Answer** with the result and this request's own provenance (section 4).

Queries: `overview`, `comparison` and `sensitivity`, whose SQL comes from `analysis/sql_*.py`
(those scripts stay unchanged) with one filter added, `array_contains(:tickers, ticker)`. Each
takes `tickers`, a subset of AAPL, MSFT, NVDA, TSLA and QQQ, which defaults to all five.

## 2. The registered run

`run-20261013T043848Z-4` (`data/outputs/windows/full-2026-10-12/rolling-252-s21-r2/`) was
registered on 2026-10-25, after `python -m etf_risk.runs register` checked it:
- `run.json` status ok;
- 0 check violations;
- `verify.json` with 0 mismatches and the same breached windows, written for this run;
- all four tables complete.

Its digest is `dab5188eed8be1533843b7a42e73c27920677c4ae5ce14a1324cca92b6148b95` (101 files,
45 MB). Recomputing the digest gave the same value and left every file's size and modification
time unchanged.

The documented run of record is `-2`. `plots.py` states that the protocol's four runs have
identical tables, and `-4` is the only one of the four with a `verify.json`. On `-4`, the three
queries reproduce the spec §8 values (`tests/test_summary_spark.py`, compared with
`plots.DOCUMENTED`).

## 3. The folder check and what it does not detect

**A full hash** reads every file and recomputes the run digest. Each file is stat-ed before
and after it is hashed, and a file whose size or modification time changed in between is
refused. A full hash happens:
- on the first request for a folder in a process, so on every one-shot request;
- on request (`"verify_full": true`);
- whenever the cheaper check below finds a difference.

**The warm check**, in a warm process before and after each query, walks the folder with
`lstat` only. It compares the set of relative file paths, and each file's size and
`st_mtime_ns`, with the snapshot from the last full hash.

- **Detected:** a file added, removed or renamed; a symbolic link anywhere; a change in any
  file's size; a change in any file's `st_mtime_ns`. Each of these triggers a full hash. The
  folder is refused unless the digest is unchanged; if it is, the snapshot is renewed.
- **Not detected:** a change of content that leaves every path, size and `st_mtime_ns` equal
  to the snapshot. For example:
  - a same-length overwrite whose modification time is set back afterwards (`touch -r`,
    `os.utime`, or `cp -p` / `rsync -t` from a same-length file);
  - a same-length overwrite that lands on the same timestamp, because the file system records
    time coarsely (APFS keeps nanoseconds; HFS+ one second, FAT two) or because the clock was
    set back.

  Only a full hash finds such a change. `ctime` and inode numbers are not compared.
- **The second check after a query** has the same limits. A change that this check does not
  see can reach a result computed during that query, and that result is then cached under the
  accepted digest. The window is one query's duration, and in a one-shot process that window
  starts right after a full hash.

`tests/test_runs_resolver.py` pins both lists, including a same-length overwrite with its
modification time set back, which passes the warm check and fails `verify_full()`.

## 4. Identity and provenance

The cached result's identity is what the result is a function of:
- the format version;
- the PySpark version;
- the run digest;
- the query name and the SHA-256 of its SQL;
- the normalized parameters: every declared parameter, the default filled in, upper-cased
  tickers as a sorted list without duplicates (step 1), deep-copied into the identity (step 2).

It contains nothing about the request that asked: no store id, job id, attempt, run id,
registry entry or path. The key is `etf-risk:result:v<format>:<query>:<SHA-256 of the identity
as canonical JSON>`. The stored value is `{"identity": …, "result": …}` as standard JSON.

The store id is not in the key, and the cache is still correct, for these reasons:
- **The result depends only on the content.** It is a function of the files' content, which
  the digest identifies, together with the SQL, the parameters and the engine. Two runs with
  the same digest give the same result whichever store accepted them.
- **The cache does not decide acceptance.** That is decided for every request by the resolver,
  before any lookup, including on a hit.
- **Adding the store id would only add duplicates.** It would create duplicate entries for the
  same content, and its presence in the key could be mistaken for an acceptance check.

What must not be shared is provenance, and it is not. A response's `run` field comes from this
request's own resolution:
- for a job run: the basis, store id, job id, attempt number and run id;
- for a historical run: the registry entry's path and approval;
- in both cases, the digest.

So when store B's job is answered from an entry computed for store A's byte-identical run, the
response names store B. `tests/test_summary.py` pins this with two job tables, both with a stub
cache and with the real one. With the real one, the stored bytes contain neither store A's id
nor any local path.

## 5. What the cache does (the author's decisions)

- **A hit** returns the stored result, equal to the computed one including value types.
- **A miss** computes, writes back and returns. A stored value that `decode` turns down counts
  as a miss and is replaced. `decode` turns down:
  - bytes that are not UTF-8 JSON;
  - an object without `identity` and `result`, or with another identity;
  - a result whose `columns` and `rows` are not lists, whose columns are not lists of two
    strings, or whose rows are not lists as long as `columns`;
  - a row holding NaN or infinity (also written as a number too large for a float, like
    `1e999`) or a value that is not a JSON scalar.
- **Redis failing never fails a query.** A GET or SET that raises a Redis error falls back to
  Spark, writes nothing more in that request, and is reported to the breaker. Any other
  exception propagates, and so does anything the query raises.
- **The breaker** opens after `failure_threshold` consecutive failures. While open it calls no
  Redis until `cooldown` has passed (inclusive), then lets one probe through. The probe's
  success closes it; its failure reopens it for a full cooldown. Outside a probe, a failure
  reported while open restarts the cooldown and a success closes it.
- **Configuration** (`CacheConfig`; the author kept Claude Code's proposals on 2026-10-26):
  connect and read timeouts of 0.1 s each, a threshold of 3 failures and a cooldown of 5.0 s.
- **Counters:** every request lands in exactly one of hits, misses, decode misses, GET errors
  and skipped (breaker open); every computed result in exactly one of writes, SET errors and
  write skips.
- **Non-finite results (step 8, the author's decision of 2026-10-26).** Standard JSON cannot
  hold NaN or infinity, so `encode` refuses such a result. The policy: the result is returned
  exactly as the query gave it, as without the cache, and is not written. It counts as a write
  skip and is not a Redis failure, so caching never turns a query that would succeed uncached
  into a failure. Without the cache, a response may then hold NaN or infinity, which Python's
  `json` writes as `NaN` and `Infinity`; a cached request answers the same way.
  - **Status:** `get_or_compute` does not follow this policy yet. Until step 8 is written,
    `encode`'s `ValueError` escapes and the request fails. Five tests pin the policy as strict
    xfails expecting that `ValueError` (`tests/test_cache_contract.py`, `tests/test_summary.py`).
    For the three queries here, Spark gives `null`, not NaN, for an empty median.

## 6. Redis waiting time per request: a conditional calculation

This section calculates how long one request can wait on Redis. The result holds only under
the conditions below. It is not a hard end-to-end bound on a request's latency, and it says
nothing about the time a request spends elsewhere.

**Conditions:**
1. **The client.** It is `etf_risk.services.redis_client` on redis-py 8.1.0, the cache group's
   exact pin, with the settings listed below. Another version or other settings void the
   calculation. `tests/test_redis_client.py` checks the locked version.
2. **The host is an IP address.** `redis_client` refuses anything else.
3. **The socket timeouts hold.** Python applies them per blocking call: in total for
   `sendall`, per call for `recv`. The operating system must honour them.
4. **The calls per request.** `get_or_compute` makes at most one GET and at most one SET, no
   SET after a failed GET, and no call while the breaker is open. The author's code (steps 5
   and 6) passes the tests that pin this, and the mutations that break it are caught.
5. **The simple form needs small values and one-piece replies.** Each packed command must fit
   redis-py's 6000-byte buffer cutoff, and each reply must arrive in one piece. Otherwise the
   general form applies. A reply that arrives in many delayed pieces has no bound at all.
6. **Only waits inside the client's socket calls are counted.** Left out:
   - CPU time: the key's hash, encoding, decoding;
   - resolution and the folder checks;
   - Spark and process start-up;
   - time the process is descheduled or the machine sleeps.

Notation: `t_c` is the connect timeout and `t_r` the read timeout, 0.1 s each (section 5).

**One command** (GET or SET) makes only these blocking socket calls:
- **Connection:** at most 2 attempts, each at most `t_c`. `ConnectionPool.get_connection`
  connects a connection without a socket, and connects once more when the socket then has data
  or is closed, as after a Redis restart. A reused healthy connection makes none. The host must
  be an IP address, so there is no DNS lookup and exactly one address to try.
- **Handshake:** none.
  - The client speaks RESP2, so there is no `HELLO` and no maintenance-notifications
    handshake. redis-py 8.1.0 defaults to RESP3.
  - `driver_info=None` removes `CLIENT SETINFO LIB-NAME` and `LIB-VER`, which are otherwise
    sent on every new connection.
  - There is no `AUTH`, `SELECT` or `CLIENT SETNAME`: the URL may not name a user, password or
    database other than 0.
  - `health_check_interval=0` means no health-check `PING`.
- **Send:** `s` `sendall` calls, each at most `t_r` in total. `s` = 1 when the packed command
  fits redis-py's 6000-byte buffer cutoff; a SET with a longer value takes 3.
- **Receive:** `k` `recv` calls, each at most `t_r`, where `k` is the number of pieces the
  reply arrives in (1 when it arrives at once).
- **Retries:** none, at the command or at the connection (`Retry(NoBackoff(), 0)`). redis-py
  8.1.0's default is 10 retries with exponential backoff (10 ms base, 1 s cap).

So under conditions 1–3, one command waits at most `T_cmd ≤ 2·t_c + (s + k)·t_r`.

**One request.** Under conditions 1–4 and 6:

- `T_request ≤ T_GET + T_SET ≤ 4·t_c + (s_GET + k_GET + s_SET + k_SET)·t_r`.
- With condition 5 as well, `T_request ≤ 4·t_c + 4·t_r`, which is 0.8 s with the timeouts of
  section 5.
- A request whose GET fails: `T_request ≤ 2·t_c + 2·t_r`, 0.4 s.
- A request while the breaker is open: 0.
- During an outage of length `W`, with threshold `F` and cooldown `T`, at most `F + ⌈W/T⌉`
  requests call Redis: `F` failures open the breaker, then one probe per cooldown.

`t_r` limits each blocking call, not a whole command. When condition 5 fails, the general form
above still holds, but `k` is whatever the server makes it. When any of conditions 1–4 fails,
the calculation says nothing.

**Where each part is pinned:**
- **The per-command parts against the locked client:** `tests/test_redis_client.py`. A fake
  RESP server records that a GET and a SET each send only their own command on one connection.
  A silent server times out once, after `t_r`. A closed port fails at once. A command makes
  one or two connection attempts. A reply in three delayed pieces succeeds after more than
  `t_r`. A SET longer than the cutoff is packed in three pieces.
- **The calls per request (condition 4):** `tests/test_cache_contract.py`, steps 5 and 6.

## 7. Checks and dry runs

**Tests and mutations** (2026-10-26; full counts in the milestone report):
- the contract (`tests/test_cache_contract.py`): 97 passed and 4 strict xfails (step 8);
- the request flow (`tests/test_summary.py`): 23 passed and 1 strict xfail (step 8);
- the spec §8 values on `-4` (`tests/test_summary_spark.py`);
- the client against the locked redis-py (`tests/test_redis_client.py`);
- the Compose Redis (`tests/test_redis_live.py`, with `ETF_RISK_REDIS_URL`).

24 focused mutations of the resolver, the registry, the request flow, the cache logic and the
client's settings were all caught, each by its own test file (`tests/mutation_check.py`; run
`data/outputs-mutations/20261026T083916Z-m4`).

**The client against Redis's states** (2026-10-25, one run of each case, `t_c = t_r` = 0.1 s):

| Redis | One GET | Outcome |
|---|---|---|
| running, pooled connection | median 0.38 ms, max 5.7 ms (50 GETs) | ok |
| running, new client each time | median 1.19 ms (20) | ok |
| paused (`docker compose pause redis`) | median 102 ms (5) | TimeoutError, no retry |
| stopped | under 1 ms (5) | ConnectionError |
| started again | the same pooled client works | ok |

**The cache in one warm `serve` process** (2026-10-26, no other container in Docker's VM;
records in `data/outputs-cache-dryrun/20261026T084131Z/`). 17 requests on the registered run:
- **Redis up.** Each query and a ticker subset written in two spellings (`["qqq", "TSLA"]`,
  then `["TSLA", "QQQ", "QQQ"]`) missed once and then hit.
- **Redis stopped.** 4 requests were all answered from Spark: 3 GET errors, then 1 request
  skipped with the breaker open.
- **Redis restarted, after the cooldown.** The probe missed (persistence is off, so the
  restarted Redis was empty) and was written back; the repeat hit.
- **Redis paused.** The request was answered from Spark after one read timeout. The cache's
  share of that request was 0.109 s.
- **Unpaused.** A miss, then a hit.

Every one of the 17 answers was compared, with value types, against a separate `--no-cache`
process's answer, and all 17 were equal: 8 hits and 9 Spark answers. Some of the hits were
served from entries an earlier dry run had written, so they came from another process.

An earlier run of the same driver (`20261026T084053Z`) behaved the same. One equality flag in
it was a driver error: it compared the subset's two spellings under different keys.

**Redis's memory:** the container's cgroup `memory.peak` was 19 MiB of 128 MiB after the dry
run, counted from its last restart, which resets the counter. Redis's `used_memory_peak` was
1.46 MB with 2 keys. Right after a start, idle, the peak was 50 MiB. These are light loads, not
a check of the budget under the E3 workload. The timings in the records are not E3
measurements and are not compared here.

## 8. Not claimed

- Any latency saving from the cache (E3, M5).
- Detection of content changes that keep every path, size and modification time (section 3).
- A hard end-to-end bound on a request's latency. Section 6 is a conditional calculation of
  Redis waiting time only, and gives no bound when a reply arrives in many delayed pieces.
- The non-finite policy, until step 8 is written (section 5).
- Results for runs other than accepted job runs and registered historical runs.
- Memory figures for the warm query service. The native processes' memory remains
  unvalidated (spec §11).
