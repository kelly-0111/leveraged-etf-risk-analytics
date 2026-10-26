"""The result-cache experiment E3 (docs/result-cache-experiment.md): the workload, the keys the
experiment owns, the host and container monitors, and the driver of the blocks N, W, R and F.

    uv run --group cache --group jobs python -m etf_risk.cache_experiment plan --seed <S> --out <batch>
    uv run --group cache --group jobs python -m etf_risk.cache_experiment preflight [--formal]
    uv run --group cache --group jobs python -m etf_risk.cache_experiment run <batch> [--formal]

`plan` writes plan.json: every block in its order, with its requests and warm-ups, and the cache
keys of every request (the experiment's keys). `run` executes it against the registered run and
writes the records the collector (analysis/collect_result_cache_measurements.py) reads:
requests.jsonl (one line per request, warm-ups included), blocks.jsonl (one per block: host
readings before and after, the pressure sampler's extremes, container events, memory peaks),
reference.json (each request's answer from a no-cache process, computed first), containers.jsonl
(every container event of the batch, never a name), and batch.json.

Configurations (Part A, section 2):
- N: one new process per request (`summary --no-cache query`): process start, imports, a full
  hash of the run folder, a new SparkSession and the query;
- W: one warm process per block (`summary --no-cache serve`); a full hash on its first request,
  the warm stat check after that. Each W block is the control of one R block: the same request
  sequence and the same warm-ups, without the cache;
- R: like W with Redis (`summary serve`); a block's hit rate is set by repeats, its keys deleted
  before its warm-ups and again before its measured requests;
- F: like R; Redis is stopped after the first phase and started again before the third;
- the lead-in round (round -1, blocks flagged lead_in): a full round before round 0, recorded and
  excluded from the comparisons. Batches from before 20261026T17 had a single lead-in block L.

Keys. The driver deletes only the experiment's keys, by name (DEL), never FLUSHDB or a pattern.
F's restart empties Redis (persistence off), so a batch refuses to start while Redis holds any
key that is not the experiment's.

Monitoring, never shown by name: `docker events` for the whole batch (other projects' container
events counted, including any between readings), the number of other running containers at every
block boundary, and a sampler (every --pressure-interval s) of macOS's memory-pressure level,
swap activity and `pmset -g therm` warnings.

The settle. After a block's last process exits, and after its requests are timed, settle() waits
up to settle_grace seconds (15) for every process carrying the block's marker to exit, and
records each one's identity and when it disappeared. A survivor fails the block; it is ended
only when its ownership is verified (same marker, same creation time), and the batch stops
(batch.json "aborted") when that cannot be confirmed.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_cache_experiment.py.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from etf_risk import cache, runs, summary

QUERIES = ("overview", "comparison", "sensitivity")
SUBSETS = [list(c) for n in range(1, len(summary.TICKERS) + 1)
           for c in itertools.combinations(sorted(summary.TICKERS), n)]          # 31 non-empty subsets
KEY_SPACE = [(q, tuple(s)) for q in QUERIES for s in SUBSETS]                    # 93 requests
COMPOSE = ["docker", "compose", "-f", str(runs.REPO_ROOT / "docker" / "compose.yaml")]
PURPOSES = ("formal", "dry-run", "sizing", "functional")   # functional: checks the tooling only


@dataclass(frozen=True)
class Settings:
    """The proposals of Part A, section 3; each is a command-line option."""
    rounds: int = 6
    block_size: int = 30              # W, R0, R50 and R90 requests per block
    hit_rates: tuple[float, ...] = (0.0, 0.5, 0.9)
    n_size: int = 6                   # N requests per round (two per query)
    f_phase: int = 6                  # F requests per phase: up, down, after the restart
    warmups: int = 12                 # unmeasured requests at the start of each warm process
    cooldown_wait: float = 5.5        # s after Redis is ready again: past the breaker's 5 s
    lead_in: bool = True              # a recorded lead-in round before round 0 (Part A, section 4)
    settle_grace: float = 15.0        # s a block's marked processes may take to exit (as M2's memory check)
    sample_interval: float = 0.5      # the process-tree sampler
    pressure_interval: float = 1.0    # the host sampler


# The workload

def request(query: str, tickers: Iterable[str]) -> dict:
    return {"query": query, "tickers": sorted(tickers)}


def balanced_keys(rng: random.Random, n: int) -> list[tuple[str, tuple[str, ...]]]:
    """n distinct requests, the same number for each query (n a multiple of 3)."""
    if n % len(QUERIES) or n // len(QUERIES) > len(SUBSETS):
        raise ValueError(f"{n} distinct requests cannot be balanced over {len(QUERIES)} queries")
    per = n // len(QUERIES)
    return [(q, tuple(s)) for q in QUERIES for s in rng.sample(SUBSETS, per)]


def hit_rate_requests(rng: random.Random, n: int, hit_rate: float) -> list[dict]:
    """n requests whose designed hit rate on an empty cache is hit_rate: d = n(1 - hit_rate)
    distinct requests, balanced over the queries, each made n/d times, in a shuffled order. The
    first request of each key misses and the rest hit, so hits = n - d exactly."""
    distinct = round(n * (1 - hit_rate))
    if distinct < len(QUERIES) or n % distinct or abs(1 - distinct / n - hit_rate) > 1e-9:
        raise ValueError(f"hit rate {hit_rate} is not exact with {n} requests")
    keys = balanced_keys(rng, distinct) * (n // distinct)
    rng.shuffle(keys)
    return [request(q, s) for q, s in keys]


def designed_sources(requests: list[dict]) -> list[str]:
    """'spark' for the first request of each key, 'cache' after it (an empty cache, no failure)."""
    seen, out = set(), []
    for r in requests:
        k = (r["query"], tuple(r["tickers"]))
        out.append("cache" if k in seen else "spark")
        seen.add(k)
    return out


def warmup_requests(rng: random.Random, n: int) -> list[dict]:
    """n unmeasured requests (a multiple of 3), the same number for each query: each query's full
    ticker set first, then subsets. They run on an empty cache, so each one reaches Spark."""
    per = n // len(QUERIES)
    if n % len(QUERIES) or per < 1:
        raise ValueError(f"{n} warm-ups cannot be balanced over {len(QUERIES)} queries")
    full = sorted(summary.TICKERS)
    rest = [s for s in SUBSETS if s != full]
    return [request(q, s) for q in QUERIES for s in [full] + rng.sample(rest, per - 1)]


def block_label(block: dict) -> str:
    """W0, R0, W50, R50, W90, R90, N or F: a W control is named after the R block it pairs with."""
    pair = block.get("pair")
    return block["config"] + (f"{int(round(pair * 100))}" if pair is not None else "")


def forward_order(settings: Settings) -> list[str]:
    """One round's blocks in the forward order: each hit rate's pair (its W control, then its R
    block), then N, then F."""
    return [f"{c}{int(round(h * 100))}" for h in settings.hit_rates for c in ("W", "R")] + ["N", "F"]


def _round_units(rng: random.Random, settings: Settings) -> list[dict]:
    """One round's blocks in the forward order: each hit rate's pair (its W control, then its R
    block, the identical requests and warm-ups), N, F."""
    units = []
    for h in settings.hit_rates:
        sequence = hit_rate_requests(rng, settings.block_size, h)
        warmups = warmup_requests(rng, settings.warmups)
        units.append({"config": "W", "pair": h, "requests": list(sequence), "warmups": list(warmups)})
        units.append({"config": "R", "pair": h, "hit_rate": h, "requests": list(sequence), "warmups": list(warmups)})
        if h == 0.0:
            cold = sequence
    per_query = settings.n_size // len(QUERIES)
    n_requests = [r for q in QUERIES for r in [x for x in cold if x["query"] == q][:per_query]]
    f_keys = [request(q, s) for q, s in balanced_keys(rng, len(QUERIES))]
    phase = [f_keys[i % len(f_keys)] for i in range(settings.f_phase)]
    units.append({"config": "N", "requests": n_requests, "warmups": []})
    units.append({"config": "F", "phases": [phase, phase, phase], "requests": phase * 3,
                  "warmups": warmup_requests(rng, settings.warmups)})
    return units


def plan_blocks(seed: int, settings: Settings) -> list[dict]:
    """Every block in its order. Each round draws one request sequence per hit rate and runs it
    twice, as a pair: once without the cache (the W control) and once with it (R), the two
    identical request for request, warm-ups included. N runs the first n_size // 3 requests of
    each query in the 0% sequence; F has its own 3 requests.

    With settings.lead_in, a lead-in round runs first as round -1: a full round in the forward
    order, with requests of its own, every block flagged lead_in. It is recorded and checked like
    any block, but excluded by design from every comparison and from the host gates (its host
    readings are reported): every kind of process runs once before measurement starts.

    Order of the measured rounds: even-numbered rounds (0, 2, 4) run forward_order(); odd-numbered
    rounds (1, 3, 5) run its exact reverse. Every block's position is therefore mirrored between
    consecutive rounds, and within each pair the W control runs first in the forward rounds and
    second in the reverse ones."""
    if 0.0 not in settings.hit_rates:
        raise ValueError("N draws its requests from the 0% sequence")
    rng = random.Random(seed)
    blocks = []
    if settings.lead_in:
        for b in _round_units(rng, settings):
            blocks.append({**b, "round": -1, "lead_in": True})
    for k in range(settings.rounds):
        units = _round_units(rng, settings)
        if k % 2:
            units.reverse()
        blocks += [{**b, "round": k} for b in units]
    for i, b in enumerate(blocks):
        b["id"] = f"b{i:02d}-{'lead-' if b.get('lead_in') else ''}{block_label(b)}"
    return blocks


# The keys the experiment owns

def key_of(query: str, tickers: Iterable[str], *, digest: str, engine: str) -> str:
    q = summary.QUERIES[query]
    params = cache.normalize_params(q.params, {"tickers": list(tickers)})
    return cache.cache_key(cache.identity(run_digest=digest, query=query, sql=q.sql, params=params, engine=engine))


def experiment_keys(blocks: list[dict], *, digest: str, engine: str) -> list[str]:
    reqs = [r for b in blocks for r in b["requests"] + b["warmups"]]
    return sorted({key_of(r["query"], r["tickers"], digest=digest, engine=engine) for r in reqs})


def foreign_keys(client: Any, ours: list[str]) -> int:
    """How many keys Redis holds that are not the experiment's."""
    present = client.exists(*ours) if ours else 0
    return client.dbsize() - present


def delete_keys(client: Any, keys: list[str]) -> int:
    """Delete exactly these keys, by name; the number deleted."""
    return client.delete(*keys) if keys else 0


# Monitors

class ContainerEvents(threading.Thread):
    """`docker events` for container events, from start() until stop(). Each event keeps its
    time, its action and whether it belongs to this project; never a name or an id."""

    def __init__(self, project: str, command: list[str] | None = None):
        super().__init__(daemon=True)
        self.project = project
        self.command = command or ["docker", "events", "--filter", "type=container", "--format", "{{json .}}"]
        self.events: list[dict] = []
        self.error: str | None = None
        self._proc: subprocess.Popen | None = None

    def run(self) -> None:
        try:
            self._proc = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        except OSError as error:
            self.error = f"{type(error).__name__}: {error}"
            return
        for line in self._proc.stdout:
            event = parse_container_event(line, self.project)
            if event is not None:
                event["mono"] = time.monotonic()
                self.events.append(event)

    def stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            self._proc.wait(timeout=10)
        self.join(timeout=10)

    def count(self, start: float, end: float, *, ours: bool) -> int:
        return sum(1 for e in self.events if start <= e["mono"] <= end and e["ours"] == ours)


def parse_container_event(line: str, project: str) -> dict | None:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    attributes = (data.get("Actor") or {}).get("Attributes") or {}
    return {"action": data.get("Action") or data.get("status"),
            "ours": attributes.get("com.docker.compose.project") == project,
            "time": data.get("time")}


def parse_therm(text: str) -> dict:
    """`pmset -g therm`: the thermal and performance warning levels and the CPU power status,
    None while macOS has recorded none."""
    def level(name: str) -> int | None:
        match = re.search(rf"{name}\s*(?:level)?\s*[:=]\s*(\d+)", text, re.IGNORECASE)
        return int(match.group(1)) if match else None
    return {"thermal_warning": level("thermal warning"), "performance_warning": level("performance warning"),
            "cpu_speed_limit": level("CPU_Speed_Limit")}


class HostSampler(threading.Thread):
    """Every interval: macOS's memory-pressure level, swap in and out, and pmset's warnings.
    window() gives the extremes and the swap traffic between two monotonic times."""

    def __init__(self, interval: float, read: Callable[[], dict] | None = None):
        super().__init__(daemon=True)
        self.interval, self.read = interval, read or read_host_sample
        self.samples: list[dict] = []
        self._halt = threading.Event()

    def run(self) -> None:
        while not self._halt.is_set():
            sample = self.read()
            sample["mono"] = time.monotonic()
            self.samples.append(sample)
            self._halt.wait(self.interval)

    def stop(self) -> None:
        self._halt.set()
        self.join(timeout=10)

    def window(self, start: float, end: float) -> dict:
        inside = [s for s in self.samples if start <= s["mono"] <= end]
        if not inside:
            return {"samples": 0}
        def most(name):
            values = [s[name] for s in inside if s.get(name) is not None]
            return max(values) if values else None
        return {"samples": len(inside), "max_pressure_level": most("pressure_level"),
                "thermal_warning": most("thermal_warning"), "performance_warning": most("performance_warning"),
                "swap_out_bytes": inside[-1]["swap_out_bytes"] - inside[0]["swap_out_bytes"],
                "swap_in_bytes": inside[-1]["swap_in_bytes"] - inside[0]["swap_in_bytes"]}


def read_host_sample() -> dict:
    import psutil
    pressure = _run("sysctl", "-n", "kern.memorystatus_vm_pressure_level").strip()
    swap = psutil.swap_memory()
    return {"pressure_level": int(pressure) if pressure.isdigit() else None,
            "swap_out_bytes": swap.sout, "swap_in_bytes": swap.sin, **parse_therm(_run("pmset", "-g", "therm"))}


def _run(*argv: str) -> str:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


# The driver

class ServeProcess:
    """One warm `summary serve` process, its tree sampled; ask() times one request on the client."""

    def __init__(self, argv: list[str], env: dict, stderr, sample_interval: float):
        from etf_risk.measure import TreeSampler
        self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                     text=True, bufsize=1, env=env)
        self.sampler = TreeSampler(self.proc.pid, interval=sample_interval)
        self.sampler.start()

    def ask(self, request: dict) -> tuple[dict, float]:
        line = json.dumps(request) + "\n"
        start = time.monotonic()
        self.proc.stdin.write(line)
        self.proc.stdin.flush()
        answer = self.proc.stdout.readline()
        elapsed = time.monotonic() - start
        if not answer:
            raise RuntimeError(f"the serve process ended (exit {self.proc.poll()})")
        return json.loads(answer), elapsed

    def close(self) -> dict:
        self.proc.stdin.close()
        self.proc.wait(timeout=120)
        exited = time.monotonic()
        self.sampler.stop()
        self.sampler.join(timeout=10)
        return {"exit": self.proc.returncode, "pid": self.proc.pid, "exited_mono": exited,
                "peak_total_bytes": self.sampler.peak_total, "peak_by_kind": self.sampler.peak_by_kind,
                "samples": self.sampler.samples}


@dataclass
class Batch:
    folder: Path
    plan: dict
    settings: Settings
    redis_url: str
    python: str = sys.executable
    containers: ContainerEvents | None = None
    host: HostSampler | None = None
    client: Any = None
    marker_prefix: str = field(default="")

    def record(self, name: str, row: dict) -> None:
        with (self.folder / name).open("a") as f:
            f.write(json.dumps(row, default=str) + "\n")

    def summary_argv(self, *args: str) -> list[str]:
        return [self.python, "-m", "etf_risk.summary", "--redis-url", self.redis_url, *args]

    def wire(self, r: dict) -> dict:
        return {"query": r["query"], "run": self.plan["run"], "params": {"tickers": r["tickers"]}}


def _row(block: dict, i: int, phase: int | None, req: dict, answer: dict, client_s: float, warmup: bool) -> dict:
    return {"block": block["id"], "config": block["config"], "round": block["round"],
            "hit_rate": block.get("hit_rate"), "pair": block.get("pair"), "lead_in": block.get("lead_in", False),
            "index": i, "phase": phase, "warmup": warmup,
            "query": req["query"], "tickers": req["tickers"], "status": answer.get("status"),
            "source": answer.get("source"), "client_seconds": client_s, "server_seconds": answer.get("seconds"),
            "full_hashes": answer.get("full_hashes"), "counters": answer.get("counters"),
            "reason": answer.get("reason") or answer.get("error"), "result": answer.get("result")}


def run_block(batch: Batch, block: dict) -> dict:
    """One block, with its host readings, its container events and its memory peaks."""
    from etf_risk.jobs.harness import host_state
    from etf_risk.jobs.processes import MARKER_ENV
    from etf_risk.services import memory_peak, other_containers
    ours = batch.plan["keys_by_request"]
    before = {"host": host_state(), "other_containers": other_containers(), "mono": time.monotonic()}
    marker = f"e3:{batch.folder.name}:{block['id']}"
    env = {**os.environ, MARKER_ENV: marker}
    env.pop("VIRTUAL_ENV", None)
    info: dict = {"block": block["id"], "config": block["config"], "round": block["round"],
                  "hit_rate": block.get("hit_rate"), "pair": block.get("pair"), "lead_in": block.get("lead_in", False),
                  "marker": marker}
    stderr = (batch.folder / "logs" / f"{block['id']}.log").open("w")
    try:
        if block["config"] == "N":
            info["processes"] = []
            for i, req in enumerate(block["requests"]):
                info["processes"].append(_one_shot(batch, block, i, req, env, stderr))
        else:
            serve = ServeProcess(batch.summary_argv(*(["--no-cache"] if block["config"] in ("W", "L") else []), "serve"),
                                 env, stderr, batch.settings.sample_interval)
            try:
                keys = sorted({ours[_rk(r)] for r in block["requests"] + block["warmups"]})
                if block["config"] in ("R", "F"):          # warm-ups must miss, or they warm nothing in Spark
                    info["keys_deleted_before_warmups"] = delete_keys(batch.client, keys)
                for i, req in enumerate(block["warmups"]):
                    answer, s = serve.ask(batch.wire(req))
                    batch.record("requests.jsonl", _row(block, i, None, req, answer, s, warmup=True))
                if block["config"] in ("R", "F"):
                    info["keys_deleted"] = delete_keys(batch.client, keys)
                    info["keys_present_after_delete"] = batch.client.exists(*keys)
                if block["config"] == "F":
                    _run_f(batch, block, serve, info)
                else:
                    for i, req in enumerate(block["requests"]):
                        answer, s = serve.ask(batch.wire(req))
                        batch.record("requests.jsonl", _row(block, i, None, req, answer, s, warmup=False))
            finally:
                info["serve"] = serve.close()
    finally:
        stderr.close()
    last = info["processes"][-1] if block["config"] == "N" else info["serve"]
    info["settle"] = settle(marker, exited_mono=last["exited_mono"], root_pid=last["pid"],
                            grace=batch.settings.settle_grace)            # after timing: no request is affected
    after = {"host": host_state(), "other_containers": other_containers(), "mono": time.monotonic()}
    info["redis_peak"] = asdict(memory_peak("redis"))
    info["redis_used_memory_peak"] = batch.client.info("memory").get("used_memory_peak")
    info.update(before=before, after=after, seconds=after["mono"] - before["mono"],
                host_window=batch.host.window(before["mono"], after["mono"]),
                other_container_events=batch.containers.count(before["mono"], after["mono"], ours=False),
                own_container_events=batch.containers.count(before["mono"], after["mono"], ours=True))
    batch.record("blocks.jsonl", info)
    if not info["settle"]["confirmed_clean"]:
        raise CleanupFailed(f"{block['id']}: a surviving marked process could not be confirmed ended; "
                            f"see its settle record")
    return info


def _rk(r: dict) -> str:
    return json.dumps([r["query"], sorted(r["tickers"])])


def _one_shot(batch: Batch, block: dict, i: int, req: dict, env: dict, stderr) -> dict:
    from etf_risk.measure import TreeSampler
    argv = batch.summary_argv("--no-cache", "query", req["query"], "--run", batch.plan["run"], "--tickers", *req["tickers"])
    start = time.monotonic()
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=stderr, text=True, env=env)
    sampler = TreeSampler(proc.pid, interval=batch.settings.sample_interval)
    sampler.start()
    out, _ = proc.communicate(timeout=600)
    exited = time.monotonic()
    elapsed = exited - start
    sampler.stop()
    sampler.join(timeout=10)
    try:
        answer = json.loads(out)
    except json.JSONDecodeError:
        answer = {"status": "error", "error": f"exit {proc.returncode}, no JSON answer"}
    batch.record("requests.jsonl", _row(block, i, None, req, answer, elapsed, warmup=False))
    return {"exit": proc.returncode, "pid": proc.pid, "exited_mono": exited, "peak_total_bytes": sampler.peak_total}


def _run_f(batch: Batch, block: dict, serve: ServeProcess, info: dict) -> None:
    """Phase 0 with Redis up, phase 1 with it stopped, phase 2 after it is started again and the
    breaker's cooldown has passed. Redis's peak is read before the stop, which resets it."""
    from etf_risk.services import memory_peak, redis_ready, wait_until_ready
    info["phase_marks"] = []
    for phase, requests in enumerate(block["phases"]):
        if phase == 1:
            info["redis_peak_before_stop"] = asdict(memory_peak("redis"))
            info["redis_used_memory_peak_before_stop"] = batch.client.info("memory").get("used_memory_peak")
            subprocess.run(COMPOSE + ["stop", "redis"], check=True, capture_output=True)
        if phase == 2:
            subprocess.run(COMPOSE + ["start", "redis"], check=True, capture_output=True)
            info["redis_ready_seconds"] = wait_until_ready("redis", lambda: redis_ready(batch.redis_url), timeout=60)
            time.sleep(batch.settings.cooldown_wait)
        info["phase_marks"].append(time.monotonic())
        for i, req in enumerate(requests):
            answer, s = serve.ask(batch.wire(req))
            batch.record("requests.jsonl", _row(block, i, phase, req, answer, s, warmup=False))


class CleanupFailed(RuntimeError):
    """A marked process outlived its block and could not be confirmed ended: the batch stops."""


def _identity(process: Any, root_pid: int) -> dict | None:
    from etf_risk.measure import process_kind
    try:
        return {"pid": process.pid, "name": process.name(), "kind": process_kind(process, root_pid),
                "create_time": process.create_time()}
    except Exception:                           # gone, or unreadable, between the scan and now
        return None


def settle(marker: str, *, exited_mono: float, root_pid: int, grace: float = 15.0, poll: float = 0.25,
           scan: Callable[[], list] | None = None, owned: Callable[[Any, float], bool] | None = None,
           end: Callable[[list, Callable[[], list]], dict] | None = None,
           clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep) -> dict:
    """Wait, after a block's last process has exited, until no process carries the block's marker,
    for at most `grace` seconds, polling every `poll`. Every process seen is recorded: pid, name,
    kind, creation time, and when it was first and last seen and found gone, in seconds after the
    exit. A process still alive after the grace is a survivor and fails the block (collector).
    Survivors are then ended (TERM, then KILL), but only those whose ownership is verified: they
    still carry the marker and have the creation time first seen, so a reused pid is never
    signalled. confirmed_clean is False when a survivor could not be verified or remains."""
    from etf_risk.jobs.processes import alive, marked_processes, marker_of, terminate
    scan = scan or (lambda: alive(marked_processes().get(marker, [])))
    owned = owned or (lambda p, created: marker_of(p) == marker and p.create_time() == created)
    end = end or (lambda procs, rescan: terminate(procs, term_grace=5.0, kill_confirm=5.0, rescan=rescan))
    start, seen, live = clock(), {}, []
    settled_after = None
    while True:
        now, live = clock(), scan()
        current = set()
        for process in live:
            ident = _identity(process, root_pid)
            if ident is None:
                continue
            key = (ident["pid"], ident["create_time"])
            current.add(key)
            entry = seen.setdefault(key, {**ident, "first_seen_s": now - exited_mono, "gone_by_s": None})
            entry["last_seen_s"] = now - exited_mono
        for key, entry in seen.items():
            if key not in current and entry["gone_by_s"] is None:
                entry["gone_by_s"] = now - exited_mono
        if not current:
            settled_after = now - exited_mono
            break
        if now - start >= grace:
            break
        sleep(poll)
    record = {"grace_s": grace, "poll_s": poll, "scan_started_s": start - exited_mono,
              "settled_after_s": settled_after, "seen": list(seen.values()), "survivors": [],
              "unverified": [], "cleanup": None, "confirmed_clean": True}
    if settled_after is None:
        verified, unverified = [], []
        for process in live:
            ident = _identity(process, root_pid)
            if ident is None:
                continue
            try:
                ok = owned(process, ident["create_time"])
            except Exception:
                ok = False
            (verified if ok else unverified).append((process, ident))
        record["survivors"] = [ident for _, ident in verified + unverified]
        record["unverified"] = [ident for _, ident in unverified]
        rescan = lambda: [p for p in scan() if (i := _identity(p, root_pid)) is not None and owned(p, i["create_time"])]
        record["cleanup"] = end([p for p, _ in verified], rescan) if verified else {"terminated": [], "killed": [],
                                                                                    "remaining": []}
        record["confirmed_clean"] = not unverified and not record["cleanup"]["remaining"]
    return record


def reference_answers(batch: Batch, requests: list[dict]) -> dict:
    """Each distinct request's answer from one no-cache serve process: the reference every
    measured answer is compared with."""
    distinct = {_rk(r): r for r in requests}
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    with (batch.folder / "logs" / "reference.log").open("w") as stderr:
        serve = ServeProcess(batch.summary_argv("--no-cache", "serve"), env, stderr, batch.settings.sample_interval)
        try:
            answers = {}
            for key, r in distinct.items():
                answer, _ = serve.ask(batch.wire(r))
                if answer.get("status") != "ok":
                    raise RuntimeError(f"no reference answer for {key}: {answer}")
                answers[key] = answer["result"]
        finally:
            serve.close()
    return answers


def make_plan(seed: int, settings: Settings, *, registry: Path = runs.REGISTRY) -> dict:
    entries = runs.load_registry(registry)
    if len(entries) != 1:
        raise SystemExit(f"E3 uses the one registered run; the registry lists {len(entries)}")
    entry, engine = entries[0], summary.engine()
    blocks = plan_blocks(seed, settings)
    reqs = [r for b in blocks for r in b["requests"] + b["warmups"]]
    keys_by_request = {_rk(r): key_of(r["query"], r["tickers"], digest=entry["digest"], engine=engine) for r in reqs}
    return {"format": 1, "seed": seed, "settings": asdict(settings), "run": entry["path"], "digest": entry["digest"],
            "engine": engine, "blocks": blocks, "keys_by_request": keys_by_request,
            "keys": sorted(set(keys_by_request.values()))}


def run_batch(folder: Path, *, formal: bool, redis_url: str) -> int:
    from etf_risk.provenance import code_state
    from etf_risk.services import PROJECT, other_containers, redis_client
    plan = json.loads((folder / "plan.json").read_text())
    settings = Settings(**{**plan["settings"], "hit_rates": tuple(plan["settings"]["hit_rates"])})
    code = code_state()
    if formal and (code["git_worktree_clean"] is not True or folder.parent.name != "formal"):
        raise SystemExit("a formal batch needs a clean worktree and a folder under data/outputs-result-cache/formal/")
    (folder / "logs").mkdir(exist_ok=True)
    client = redis_client(redis_url, connect_timeout=1.0, read_timeout=1.0)
    foreign = foreign_keys(client, plan["keys"])
    if foreign:
        raise SystemExit(f"Redis holds {foreign} key(s) the experiment does not own; F's restart would erase them")
    batch = Batch(folder, plan, settings, redis_url, client=client, containers=ContainerEvents(PROJECT),
                  host=HostSampler(settings.pressure_interval))
    batch.containers.start()
    batch.host.start()
    status = 0
    started = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "code": code, "formal": formal,
               "python": sys.version.split()[0], "redis_info": {k: client.info("server").get(k) for k in ("redis_version",)},
               "other_containers_at_start": other_containers(), "keys_deleted_at_start": delete_keys(client, plan["keys"])}
    try:
        reference = reference_answers(batch, [r for b in plan["blocks"] for r in b["requests"] + b["warmups"]])
        (folder / "reference.json").write_text(json.dumps(reference, indent=1) + "\n")
        for block in plan["blocks"]:
            run_block(batch, block)
    except CleanupFailed as error:
        started["aborted"] = str(error)
        status = 1
    finally:
        batch.host.stop()
        batch.containers.stop()
        started["keys_deleted_at_end"] = delete_keys(client, plan["keys"])
        started["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        started["container_monitor_error"] = batch.containers.error
        (folder / "containers.jsonl").write_text("".join(json.dumps(e) + "\n" for e in batch.containers.events))
        (folder / "batch.json").write_text(json.dumps(started, indent=2, default=str) + "\n")
        client.close()
    return status


def all_keys(*, digest: str, engine: str) -> set[str]:
    """The cache keys of every request the experiment can make on the registered run."""
    return {key_of(q, s, digest=digest, engine=engine) for q, s in KEY_SPACE}


def preflight_problems(*, formal: bool, host: dict, other_containers: int | None, our_services: list[str],
                       redis_ok: bool, foreign: int | None, therm: dict, clean: bool | None) -> list[str]:
    """Why a batch may not start now (Part A, section 5); empty when it may."""
    problems = []
    if host.get("power_source") != "AC Power":
        problems.append(f"power: {host.get('power_source')}, not AC Power")
    if host.get("lid_closed") is not False:
        problems.append("the lid is closed, or its state is unknown")
    if other_containers != 0:
        problems.append(f"{other_containers} running container(s) of other projects")
    if [s for s in our_services if s != "redis"]:
        problems.append(f"other services of this project are running: {sorted(set(our_services) - {'redis'})}")
    if not redis_ok:
        problems.append("Redis does not answer PING")
    if foreign:
        problems.append(f"Redis holds {foreign} key(s) the experiment does not own")
    if (host.get("memory_pressure") or 0) >= 4:
        problems.append("memory pressure is critical")
    if therm.get("thermal_warning") is not None or therm.get("performance_warning") is not None:
        problems.append(f"a thermal or performance warning is recorded: {therm}")
    if formal and clean is not True:
        problems.append("a formal batch needs a clean worktree")
    return problems


def preflight(*, formal: bool, redis_url: str) -> int:
    from etf_risk.jobs.harness import host_state
    from etf_risk.provenance import code_state
    from etf_risk.services import other_containers, redis_client, redis_ready
    entry = runs.load_registry()[0]
    host = host_state()
    running = subprocess.run(COMPOSE + ["ps", "--status", "running", "--format", "{{.Service}}"],
                             capture_output=True, text=True).stdout.split()
    try:
        redis_ready(redis_url)
        client = redis_client(redis_url, connect_timeout=1.0, read_timeout=1.0)
        ours = all_keys(digest=entry["digest"], engine=summary.engine())
        foreign, redis_ok = client.dbsize() - sum(1 for k in client.scan_iter(count=1000) if k.decode() in ours), True
    except Exception as error:                     # reported, never raised: preflight only reads
        foreign, redis_ok = None, False
        print(f"Redis: {type(error).__name__}: {error}", file=sys.stderr)
    problems = preflight_problems(formal=formal, host=host, other_containers=other_containers(), our_services=running,
                                  redis_ok=redis_ok, foreign=foreign, therm=parse_therm(_run("pmset", "-g", "therm")),
                                  clean=code_state()["git_worktree_clean"])
    gib = 2**30
    print(f"host: {host['available_bytes'] / gib:.2f} GiB available, swap {host['swap_used_bytes'] / gib:.2f} GiB used, "
          f"pressure level {host['memory_pressure']}, {host['power_source']}, lid closed {host['lid_closed']}")
    for p in problems:
        print(f"NOT READY: {p}")
    print("ready" if not problems else "not ready")
    return 0 if not problems else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etf_risk.cache_experiment", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("plan", help="write plan.json for a batch")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--out", type=Path, required=True, help="data/outputs-result-cache/<purpose>/<batch>")
    for name, value in asdict(Settings()).items():
        if name == "hit_rates":
            p.add_argument("--hit-rates", type=float, nargs="+", default=list(value))
        elif isinstance(value, bool):
            p.add_argument(f"--{name.replace('_', '-')}", action=argparse.BooleanOptionalAction, default=value)
        else:
            p.add_argument(f"--{name.replace('_', '-')}", type=type(value), default=value)
    r = commands.add_parser("run", help="run a planned batch")
    r.add_argument("folder", type=Path)
    r.add_argument("--formal", action="store_true")
    r.add_argument("--redis-url", default=os.environ.get("ETF_RISK_REDIS_URL", summary.DEFAULT_REDIS_URL))
    f = commands.add_parser("preflight", help="check that a batch may start now; reads only")
    f.add_argument("--formal", action="store_true")
    f.add_argument("--redis-url", default=os.environ.get("ETF_RISK_REDIS_URL", summary.DEFAULT_REDIS_URL))
    args = parser.parse_args(argv)
    if args.command == "preflight":
        return preflight(formal=args.formal, redis_url=args.redis_url)
    if args.command == "plan":
        if args.out.resolve().parent.name not in PURPOSES:
            parser.error(f"the batch folder's parent must be one of {PURPOSES}")
        if args.out.exists():
            parser.error(f"{args.out} exists: a batch is never overwritten")
        values = {name: getattr(args, name) for name in asdict(Settings())}
        values["hit_rates"] = tuple(values["hit_rates"])
        plan = make_plan(args.seed, Settings(**values))
        args.out.mkdir(parents=True)
        (args.out / "plan.json").write_text(json.dumps(plan, indent=1) + "\n")
        print(f"{len(plan['blocks'])} blocks, {len(plan['keys'])} keys -> {args.out / 'plan.json'}")
        return 0
    return run_batch(args.folder, formal=args.formal, redis_url=args.redis_url)


if __name__ == "__main__":
    sys.exit(main())
