# The result cache for summary queries (spec §11, M4)

Status: in progress. The infrastructure, the resolver, the registry, `summary.py` and the
contract tests exist. The cache logic (`src/etf_risk/cache.py`, steps 1–6) and the queries' SQL
(step 7) are the project author's, written with tutoring, and are not written yet. Nothing here
measures what the cache saves: that is the experiment E3 (M5).

Authorship: contributed by both the project author and Claude Code. Claude Code drafted this
document, the derivations in it, the infrastructure, the resolver, `summary.py` and the tests.
The author decided which historical run to register and that the queries take a ticker set,
and asked for the three revisions recorded in sections 3–5. The cache logic and the SQL are
the author's.

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
4. **Get or compute.** A hit returns the stored result. A miss runs the query in Spark, checks
   the folder again, and only then returns the result and writes it back. If the folder
   changed while Spark read it, the request is refused and nothing is cached.
5. **Answer** with the result and this request's own provenance (section 4).

Queries: `overview`, `comparison` and `sensitivity`, from `analysis/sql_*.py` (those scripts
stay unchanged). Each takes `tickers`, a subset of AAPL, MSFT, NVDA, TSLA and QQQ, which
defaults to all five.

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
identical tables, and `-4` is the only one of the four with a `verify.json`. Whether the
queries reproduce the spec §8 values on `-4` is tested once the SQL is in place (step 7,
`tests/test_summary_spark.py`).

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
- the normalized parameters.

It contains nothing about the request that asked: no store id, job id, attempt, run id,
registry entry or path. The stored value holds the identity and the result only.

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
response names store B. `tests/test_summary.py` pins this with two job tables. Its end-to-end
form with the real cache waits for step 6. That form checks that the stored bytes contain
neither store A's id nor any local path.

## 5. Redis waiting time per request: a conditional calculation

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
   SET after a failed GET, and no call while the breaker is open. This is the author's code
   (steps 5 and 6). Until those steps are written and their tests pass, this condition is a
   contract, not a checked fact.
5. **The simple form needs small values and one-piece replies.** Each packed command must fit
   redis-py's 6000-byte buffer cutoff, and each reply must arrive in one piece. Otherwise the
   general form applies. A reply that arrives in many delayed pieces has no bound at all.
6. **Only waits inside the client's socket calls are counted.** Left out:
   - CPU time: the key's hash, encoding, decoding;
   - resolution and the folder checks;
   - Spark and process start-up;
   - time the process is descheduled or the machine sleeps.

Notation: `t_c` is the connect timeout and `t_r` the read timeout (`CacheConfig`). The
proposals are 0.1 s each; the author decides them in step 6.

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

**One request.** Under condition 4, `ResultCache.get_or_compute` makes at most one GET and at
most one SET, no SET after a failed GET, and no call while the breaker is open. Under
conditions 1–4 and 6:

- `T_request ≤ T_GET + T_SET ≤ 4·t_c + (s_GET + k_GET + s_SET + k_SET)·t_r`.
- With condition 5 as well, `T_request ≤ 4·t_c + 4·t_r`, which is 0.8 s at the proposed
  values.
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
- **The calls per request (condition 4):** `tests/test_cache_contract.py`, steps 5 and 6. They
  are not yet passing, because those steps are not written.

**Dry run, 2026-10-25,** on the Compose service on this machine (Docker Desktop), one run of
each case, with `t_c = t_r` = 0.1 s:

| Redis | One GET | Outcome |
|---|---|---|
| running, pooled connection | median 0.38 ms, max 5.7 ms (50 GETs) | ok |
| running, new client each time | median 1.19 ms (20) | ok |
| paused (`docker compose pause redis`) | median 102 ms (5) | TimeoutError, no retry |
| stopped | under 1 ms (5) | ConnectionError |
| started again | the same pooled client works | ok |

These are observations from one run, not a benchmark. Right after starting, the container's
cgroup `memory.peak` was 50 MiB of its 128 MiB limit, page cache included. That was idle, and
is not a check of the budget.

## 6. Not claimed

- Any latency saving from the cache (E3, M5).
- Detection of content changes that keep every path, size and modification time (section 3).
- A hard end-to-end bound on a request's latency. Section 5 is a conditional calculation of
  Redis waiting time only, and gives no bound when a reply arrives in many delayed pieces.
- Results for runs other than accepted job runs and registered historical runs.
- Memory figures for the warm query service. The native processes' memory remains
  unvalidated (spec §11).
