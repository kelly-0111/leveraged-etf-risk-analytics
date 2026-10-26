"""Collect one E3 batch (docs/result-cache-experiment.md): check it against Part A's validity
rules, then summarize the latencies by configuration.

    uv run --group cache --group jobs python analysis/collect_result_cache_measurements.py <batch>

Writes measurements.csv (one row per measured request), summary.csv (by configuration and query,
and per round) and validity.json (every check with its outcome) into the batch folder. Prints the
verdict and exits 0 only when every check holds; 1 otherwise.

Checks (Part A, section 6):
- complete: every planned request has exactly one record, warm-ups included;
- statuses: every answer is ok;
- sources: each answer came from where the design says (W and N from Spark; R and F as
  designed_sources gives, F's second phase from Spark); every warm-up from Spark (an empty
  cache); R's realized hit rate equals its design;
- breaker: in F, the first `threshold` requests with Redis stopped count GET errors and the rest
  are skipped; after the restart the first request misses;
- answers: every answer equals the no-cache reference answer, value types included;
- keys: an R or F block starts with none of its keys in Redis;
- host, per block: AC power and lid open before and after; no other running container at either
  reading and no other project's container event in between; the container monitor ran; memory
  pressure never critical (4); no thermal or performance warning; swap-out traffic within its
  limit, and for W and R swap-in traffic too (N's new JVMs and F's restarts page by design); no marked process left after the block; the serve process exited 0;
- Redis: its peak within the container's limit;
- drift: for each query, W's median client latency in the last round within the drift limit of
  the first round's.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_result_cache_collector.py.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from etf_risk.cache_experiment import QUERIES, _rk, designed_sources  # noqa: E402

REDIS_LIMIT = 128 * 2**20
THRESHOLD = 3                    # CacheConfig.failure_threshold


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


def typed(v):
    if isinstance(v, dict):
        return {k: typed(x) for k, x in v.items()}
    if isinstance(v, list):
        return [typed(x) for x in v]
    return (type(v).__name__, repr(v))


def designed(block: dict) -> list[tuple[int | None, str]]:
    """(phase, source) for each measured request, in order."""
    if block["config"] in ("W", "N"):
        return [(None, "spark")] * len(block["requests"])
    if block["config"] == "R":
        return [(None, s) for s in designed_sources(block["requests"])]
    p0, p1, p2 = block["phases"]
    return ([(0, s) for s in designed_sources(p0)] + [(1, "spark")] * len(p1)
            + [(2, s) for s in designed_sources(p2)])


def check(batch: Path, *, swap_out_limit: int, swap_in_limit: int, drift_limit: float) -> tuple[dict, list[dict]]:
    plan = json.loads((batch / "plan.json").read_text())
    rows = read_jsonl(batch / "requests.jsonl")
    blocks = {b["block"]: b for b in read_jsonl(batch / "blocks.jsonl")}
    reference = json.loads((batch / "reference.json").read_text()) if (batch / "reference.json").is_file() else {}
    meta = json.loads((batch / "batch.json").read_text()) if (batch / "batch.json").is_file() else {}
    problems: dict[str, list[str]] = {name: [] for name in (
        "complete", "statuses", "sources", "breaker", "answers", "keys", "host", "redis", "drift")}

    for block in plan["blocks"]:
        bid, mine = block["id"], [r for r in rows if r["block"] == block["id"]]
        measured, warm = [r for r in mine if not r["warmup"]], [r for r in mine if r["warmup"]]
        want = designed(block)
        if len(measured) != len(want) or len(warm) != len(block["warmups"]) or bid not in blocks:
            problems["complete"].append(f"{bid}: {len(measured)} of {len(want)} requests, {len(warm)} of "
                                        f"{len(block['warmups'])} warm-ups, block record {'present' if bid in blocks else 'missing'}")
            continue
        for r in mine:
            if r["status"] != "ok":
                problems["statuses"].append(f"{bid} #{r['index']}: {r['status']}: {r['reason']}")
            elif typed(r["result"]) != typed(reference.get(_rk(r))):
                problems["answers"].append(f"{bid} #{r['index']}: differs from the reference answer")
        for r in warm:
            if r["status"] == "ok" and r["source"] != "spark":
                problems["sources"].append(f"{bid} warm-up #{r['index']}: {r['source']}, not spark: it warmed nothing")
        for r, (phase, source) in zip(measured, want):
            if r["source"] != source or r["phase"] != phase:
                problems["sources"].append(f"{bid} #{r['index']}: {r['source']} in phase {r['phase']}, designed "
                                           f"{source} in phase {phase}")
        if block["config"] == "R":
            hits = sum(r["source"] == "cache" for r in measured) / len(measured)
            if abs(hits - block["hit_rate"]) > 1e-9:
                problems["sources"].append(f"{bid}: realized hit rate {hits:.3f}, designed {block['hit_rate']}")
        if block["config"] == "F":
            problems["breaker"] += check_breaker(bid, measured)
        info = blocks[bid]
        if block["config"] in ("R", "F") and info.get("keys_present_after_delete"):
            problems["keys"].append(f"{bid}: {info['keys_present_after_delete']} of its keys in Redis at its start")
        problems["host"] += check_host(bid, info, swap_out_limit, swap_in_limit if block["config"] in ("W", "R") else None)
        peak = (info.get("redis_peak_before_stop") or info.get("redis_peak") or {}).get("peak_bytes")
        if peak is not None and peak > REDIS_LIMIT:
            problems["redis"].append(f"{bid}: Redis memory.peak {peak / 2**20:.0f} MiB over 128 MiB")
    if meta.get("container_monitor_error"):
        problems["host"].append(f"the container monitor failed: {meta['container_monitor_error']}")
    problems["drift"] = check_drift(plan, rows, drift_limit)
    return problems, rows


def check_breaker(bid: str, measured: list[dict]) -> list[str]:
    down = [r for r in measured if r["phase"] == 1]
    out, previous = [], next((r["counters"] for r in reversed(measured) if r["phase"] == 0), None)
    for i, r in enumerate(down):
        c = r["counters"] or {}
        kind = "get_errors" if i < THRESHOLD else "skipped"
        if previous is None or c.get(kind, 0) - previous.get(kind, 0) != 1:
            out.append(f"{bid}: request {i} with Redis stopped did not count one {kind}")
        previous = c
    after = [r for r in measured if r["phase"] == 2]
    if after and after[0]["source"] != "spark":
        out.append(f"{bid}: the first request after the restart was not a miss")
    return out


def check_host(bid: str, info: dict, swap_out_limit: int, swap_in_limit: int | None) -> list[str]:
    out = []
    for when in ("before", "after"):
        reading = info.get(when) or {}
        host = reading.get("host") or {}
        if host.get("power_source") != "AC Power":
            out.append(f"{bid} {when}: power {host.get('power_source')}")
        if host.get("lid_closed") is not False:
            out.append(f"{bid} {when}: lid closed or unknown")
        if reading.get("other_containers") != 0:
            out.append(f"{bid} {when}: {reading.get('other_containers')} other running container(s)")
    if info.get("other_container_events"):
        out.append(f"{bid}: {info['other_container_events']} other project container event(s) during the block")
    window = info.get("host_window") or {}
    if not window.get("samples"):
        out.append(f"{bid}: no host samples")
    else:
        if (window.get("max_pressure_level") or 0) >= 4:
            out.append(f"{bid}: memory pressure critical")
        if window.get("thermal_warning") is not None or window.get("performance_warning") is not None:
            out.append(f"{bid}: thermal or performance warning recorded")
        if window.get("swap_out_bytes", 0) > swap_out_limit:
            out.append(f"{bid}: {window['swap_out_bytes'] / 2**20:.0f} MiB swapped out, over the limit")
        if swap_in_limit is not None and window.get("swap_in_bytes", 0) > swap_in_limit:
            out.append(f"{bid}: {window['swap_in_bytes'] / 2**20:.0f} MiB swapped in, over the limit for W and R")
    if info.get("stragglers"):
        out.append(f"{bid}: {info['stragglers']} marked process(es) alive after the block")
    if (info.get("serve") or {}).get("exit") not in (0, None):
        out.append(f"{bid}: the serve process exited {info['serve']['exit']}")
    if any(p.get("exit") != 0 for p in info.get("processes", [])):
        out.append(f"{bid}: a one-shot process exited non-zero")
    return out


def w_medians(plan: dict, rows: list[dict], round_: int) -> dict[str, float]:
    w = [r for r in rows if r["config"] == "W" and r["round"] == round_ and not r["warmup"]]
    return {q: statistics.median(r["client_seconds"] for r in w if r["query"] == q)
            for q in QUERIES if any(r["query"] == q for r in w)}


def check_drift(plan: dict, rows: list[dict], limit: float) -> list[str]:
    rounds = sorted({b["round"] for b in plan["blocks"]})
    first, last = w_medians(plan, rows, rounds[0]), w_medians(plan, rows, rounds[-1])
    out = []
    for q in QUERIES:
        if q in first and q in last and abs(last[q] / first[q] - 1) > limit:
            out.append(f"{q}: W median {first[q]:.3f} s in round {rounds[0]}, {last[q]:.3f} s in round "
                       f"{rounds[-1]} ({last[q] / first[q] - 1:+.0%}, limit {limit:.0%})")
    return out


def label(r: dict) -> str:
    if r["config"] == "R":
        return f"R{int(r['hit_rate'] * 100)}-{'hit' if r['source'] == 'cache' else 'miss'}"
    if r["config"] == "F":
        return {0: "F-up", 1: "F-down", 2: "F-restarted"}[r["phase"]] + f"-{r['source']}"
    return r["config"]


def summarize(rows: list[dict]) -> list[dict]:
    measured = [r for r in rows if not r["warmup"] and r["status"] == "ok"]
    out = []
    for key in sorted({(label(r), r["query"]) for r in measured}):
        group = [r for r in measured if (label(r), r["query"]) == key]
        client = [r["client_seconds"] for r in group]
        resolve = [(r["server_seconds"] or {}).get("resolve") for r in group]
        resolve = [x for x in resolve if x is not None]
        out.append({"group": key[0], "query": key[1], "n": len(group), "client_median_s": statistics.median(client),
                    "client_min_s": min(client), "client_max_s": max(client),
                    "resolve_median_s": statistics.median(resolve) if resolve else None})
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("batch", type=Path)
    parser.add_argument("--swap-out-limit-mib", type=float, default=64.0, help="per block (Part A, a proposal)")
    parser.add_argument("--swap-in-limit-mib", type=float, default=256.0, help="per W or R block (Part A, a proposal)")
    parser.add_argument("--drift-limit", type=float, default=0.20, help="W's last round against its first (Part A)")
    args = parser.parse_args(argv)
    problems, rows = check(args.batch, swap_out_limit=int(args.swap_out_limit_mib * 2**20),
                           swap_in_limit=int(args.swap_in_limit_mib * 2**20), drift_limit=args.drift_limit)
    write_csv(args.batch / "measurements.csv",
              [{k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items() if k != "result"}
               for r in rows if not r["warmup"]])
    write_csv(args.batch / "summary.csv", summarize(rows))
    valid = not any(problems.values())
    (args.batch / "validity.json").write_text(json.dumps({"valid": valid, "problems": problems}, indent=2) + "\n")
    for name, found in problems.items():
        print(f"{'ok  ' if not found else 'FAIL'} {name}" + ("" if not found else f": {len(found)} problem(s); first: {found[0]}"))
    print("valid" if valid else "NOT valid")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
