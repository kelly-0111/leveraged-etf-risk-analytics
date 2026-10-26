"""Collect one E3 batch (docs/result-cache-experiment.md): check it against Part A's validity
rules, then summarize the latencies by configuration.

    uv run --group cache --group jobs python analysis/collect_result_cache_measurements.py <batch>

Writes measurements.csv (one row per measured request), summary.csv (by configuration and query),
paired.csv (each R request beside the identical request of its W control, and each N request
beside the same request in its round's W0), paired_summary.csv (the paired end-to-end differences
and ratios by hit rate, hit or miss and query, the primary result; each R block's total against
its control's; and descriptive diagnostics, which attribute nothing: see paired()), host.csv
(one row per block: paging, swap and load, descriptive; see host_rows()) and validity.json
(every check with its outcome) into the batch folder. Prints the verdict and exits 0 only when
every check holds; 1 otherwise.

Checks (Part A, section 6):
- complete: every planned request has exactly one record, warm-ups included;
- statuses: every answer is ok;
- sources: each answer came from where the design says (W and N from Spark; R and F as
  designed_sources gives, F's second phase from Spark); every warm-up from Spark (an empty
  cache); R's realized hit rate equals its design;
- pairs: each R block and its W control ran the same requests in the same order, warm-ups
  included, so what differs between them is the cache alone;
- breaker: in F, the first `threshold` requests with Redis stopped count GET errors and the rest
  are skipped; after the restart the first request misses;
- answers: every answer equals the no-cache reference answer, value types included;
- keys: an R or F block starts with none of its keys in Redis;
- host, per block: AC power and lid open before and after; no other running container at either
  reading and no other project's container event in between; the container monitor ran; memory
  pressure never critical (4); no thermal or performance warning; page-outs within their limit,
  and for W and R page-ins too (N's new JVMs and F's restarts page by design); swap-ins and
  swap-outs recorded, never gated (see paging());
  no marked process alive once the settle's grace has passed, and any survivor confirmed ended;
  the serve process exited 0;
- the batch: not aborted, and no other project's container event at any time of the batch, between
  block windows included;
- Redis: its peak within the container's limit;
- the lead-in round (blocks flagged lead_in; a single block L in batches before 20261026T17) is
  checked like any block, but its host readings are reported, not gated, and it is left out of
  every comparison: pairs' outputs, summaries and drift;
- drift: for each query, the median client latency of the W controls (all three, pooled) in the
  last round within the drift limit of the first round's.

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
from etf_risk.cache_experiment import QUERIES, VM_COUNTERS, _rk, designed_sources  # noqa: E402

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
    if block["config"] in ("W", "N", "L"):
        return [(None, "spark")] * len(block["requests"])
    if block["config"] == "R":
        return [(None, s) for s in designed_sources(block["requests"])]
    p0, p1, p2 = block["phases"]
    return ([(0, s) for s in designed_sources(p0)] + [(1, "spark")] * len(p1)
            + [(2, s) for s in designed_sources(p2)])


def check(batch: Path, *, page_out_limit: int, page_in_limit: int, drift_limit: float) -> tuple[dict, list[dict]]:
    plan = json.loads((batch / "plan.json").read_text())
    rows = read_jsonl(batch / "requests.jsonl")
    blocks = {b["block"]: b for b in read_jsonl(batch / "blocks.jsonl")}
    reference = json.loads((batch / "reference.json").read_text()) if (batch / "reference.json").is_file() else {}
    meta = json.loads((batch / "batch.json").read_text()) if (batch / "batch.json").is_file() else {}
    problems: dict[str, list[str]] = {name: [] for name in (
        "complete", "statuses", "sources", "pairs", "breaker", "answers", "keys", "host", "redis", "drift")}

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
        if block["config"] != "L" and not block.get("lead_in"):     # the lead-in's host readings are reported, not gated
            problems["host"] += check_host(bid, info, page_out_limit,
                                           page_in_limit if block["config"] in ("W", "R") else None)
        peak = (info.get("redis_peak_before_stop") or info.get("redis_peak") or {}).get("peak_bytes")
        if peak is not None and peak > REDIS_LIMIT:
            problems["redis"].append(f"{bid}: Redis memory.peak {peak / 2**20:.0f} MiB over 128 MiB")
    problems["pairs"] = check_pairs(plan, rows)
    if meta.get("aborted"):
        problems["host"].append(f"the batch was aborted: {meta['aborted']}")
    events = read_jsonl(batch / "containers.jsonl")
    others = [e for e in events if not e.get("ours")]
    if others:
        windows = [(b["before"]["mono"], b["after"]["mono"]) for b in blocks.values() if "mono" in b.get("before", {})]
        between = sum(1 for e in others if not any(a <= e["mono"] <= z for a, z in windows))
        problems["host"].append(f"{len(others)} other-project container event(s) during the batch, {between} of "
                                f"them between block windows")
    if meta.get("container_monitor_error"):
        problems["host"].append(f"the container monitor failed: {meta['container_monitor_error']}")
    problems["drift"] = check_drift(plan, rows, drift_limit)
    return problems, rows


def sequence(rows: list[dict], block_id: str) -> list[tuple[str, tuple[str, ...]]]:
    return [(r["query"], tuple(r["tickers"])) for r in rows if r["block"] == block_id and not r["warmup"]]


def partner(plan: dict, block: dict) -> dict | None:
    """The W control of an R block: the same round and pair."""
    return next((b for b in plan["blocks"] if b["config"] == "W" and b["round"] == block["round"]
                 and b.get("pair") == block.get("pair")), None)


def check_pairs(plan: dict, rows: list[dict]) -> list[str]:
    """Each R block and its W control ran the same requests in the same order, warm-ups
    included: what differs between them is the cache alone."""
    out = []
    for b in plan["blocks"]:
        if b["config"] != "R":
            continue
        w = partner(plan, b)
        if w is None:
            out.append(f"{b['id']}: no W control")
        elif w["requests"] != b["requests"] or w["warmups"] != b["warmups"]:
            out.append(f"{b['id']}: its W control {w['id']} was planned with other requests")
        elif sequence(rows, w["id"]) != sequence(rows, b["id"]):
            out.append(f"{b['id']}: its W control {w['id']} ran other requests")
    return out


def _spark(r: dict) -> float:
    return (r["server_seconds"] or {}).get("spark") or 0.0


def _rest(r: dict) -> float:
    """Client time less the server's Spark and resolve seconds: the pipe, JSON, the cache's calls,
    encoding and decoding, and whatever else the request waited on. Descriptive only."""
    server = r["server_seconds"] or {}
    return r["client_seconds"] - (server.get("spark") or 0.0) - (server.get("resolve") or 0.0)


def paired(plan: dict, rows: list[dict]) -> list[dict]:
    """One row per pair of a measured round: an R request and the identical request at the same
    position of its W control, or an N request and the same request's first run in its round's
    W0. The lead-in round is left out by design.

    seconds, w_seconds, difference_s and ratio are end-to-end client latencies: the primary
    result. The diag_ columns are descriptive diagnostics, not causal attributions:
    diag_spark_difference_s is the Spark time of the R (or N) request less its control's (empty
    for a hit, which runs no Spark); diag_rest_difference_s is the same difference for the time
    outside Spark and resolution. Neither says why a difference arose."""
    out = []
    measured = [r for r in rows if not r["warmup"] and r["status"] == "ok"]
    for b in plan["blocks"]:
        if b["config"] not in ("R", "N") or b.get("lead_in"):
            continue
        w = partner(plan, b) if b["config"] == "R" else next(
            (x for x in plan["blocks"] if x["config"] == "W" and x["round"] == b["round"] and x.get("pair") == 0.0), None)
        if w is None:
            continue
        ws = [r for r in measured if r["block"] == w["id"]]
        for r in [x for x in measured if x["block"] == b["id"]]:
            if b["config"] == "R":
                c = next((x for x in ws if x["index"] == r["index"]), None)
                kind = "hit" if r["source"] == "cache" else "miss"
            else:
                c = next((x for x in ws if (x["query"], x["tickers"]) == (r["query"], r["tickers"])), None)
                kind = "new process"
            if c is None or (c["query"], c["tickers"]) != (r["query"], r["tickers"]):
                continue
            out.append({"round": b["round"], "pair": b.get("pair"), "config": b["config"], "block": b["id"],
                        "kind": kind, "index": r["index"], "query": r["query"], "tickers": " ".join(r["tickers"]),
                        "seconds": r["client_seconds"], "w_seconds": c["client_seconds"],
                        "difference_s": r["client_seconds"] - c["client_seconds"],
                        "ratio": r["client_seconds"] / c["client_seconds"],
                        "diag_spark_difference_s": None if kind == "hit" else _spark(r) - _spark(c),
                        "diag_rest_difference_s": _rest(r) - _rest(c)})
    return out


def _median(values) -> float | None:
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


SUMMARY_FIELDS = ("scope", "config", "pair", "kind", "query", "round", "n", "median_difference_s", "median_ratio",
                  "min_ratio", "max_ratio", "total_difference_s", "total_ratio", "diag_median_spark_difference_s",
                  "diag_median_rest_difference_s", "estimate_hit_imbalance_s")


def paired_summary(pairs: list[dict]) -> list[dict]:
    """By configuration, hit rate, kind and query: the medians of the paired end-to-end
    differences and ratios (the primary result), with the diagnostics' medians beside them.
    Then, per R block and round: the block's total time against its control's (end to end), and
    for blocks with hits, estimate_hit_imbalance_s: the median Spark-time difference of the
    block's own misses against their controls. It is an estimate of how unequal the pair's
    conditions were, offered beside the hits' end-to-end difference, never subtracted from it."""
    out = []
    keys = sorted({(p["config"], p["pair"] if p["pair"] is not None else -1, p["kind"], p["query"]) for p in pairs})
    for config, pair, kind, query in keys:
        g = [p for p in pairs if (p["config"], p["pair"] if p["pair"] is not None else -1, p["kind"], p["query"])
             == (config, pair, kind, query)]
        out.append(dict.fromkeys(SUMMARY_FIELDS) | {
            "scope": "requests", "config": config, "pair": None if pair == -1 else pair, "kind": kind, "query": query,
            "n": len(g), "median_difference_s": statistics.median(p["difference_s"] for p in g),
            "median_ratio": statistics.median(p["ratio"] for p in g),
            "min_ratio": min(p["ratio"] for p in g), "max_ratio": max(p["ratio"] for p in g),
            "diag_median_spark_difference_s": _median(p["diag_spark_difference_s"] for p in g),
            "diag_median_rest_difference_s": _median(p["diag_rest_difference_s"] for p in g)})
    for (round_, pair) in sorted({(p["round"], p["pair"]) for p in pairs if p["config"] == "R"}):
        g = [p for p in pairs if p["config"] == "R" and p["round"] == round_ and p["pair"] == pair]
        total, control = sum(p["seconds"] for p in g), sum(p["w_seconds"] for p in g)
        misses = [p["diag_spark_difference_s"] for p in g if p["kind"] == "miss"]
        has_hits = any(p["kind"] == "hit" for p in g)
        out.append(dict.fromkeys(SUMMARY_FIELDS) | {
            "scope": "block", "config": "R", "pair": pair, "kind": "all", "query": "all", "round": round_, "n": len(g),
            "total_difference_s": total - control, "total_ratio": total / control,
            "diag_median_spark_difference_s": _median(misses),
            "estimate_hit_imbalance_s": _median(misses) if has_hits else None})
    return out


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


def paging(window: dict) -> dict:
    """A block's page and swap traffic in bytes, and the counters they came from: vm_stat's
    Pageins, Pageouts, Swapins and Swapouts. Batches up to dry-run/20261026T193201Z-lead-in-round
    recorded psutil's sin and sout as swap_in_bytes and swap_out_bytes; on macOS those are
    Pageins and Pageouts (docs/host-counters-correction.md), so they are read as page-ins and
    page-outs, and those batches' swap traffic is not recorded: it is never inferred from them."""
    if any(name in window for name in VM_COUNTERS):
        size = window.get("page_size")
        return {"counters": "vm_stat", **{f"{name}_bytes": None if size is None or window.get(name) is None
                                          else window[name] * size for name in VM_COUNTERS}}
    return {"counters": "psutil sin/sout", "pageins_bytes": window.get("swap_in_bytes"),
            "pageouts_bytes": window.get("swap_out_bytes"), "swapins_bytes": None, "swapouts_bytes": None}


def check_host(bid: str, info: dict, page_out_limit: int, page_in_limit: int | None) -> list[str]:
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
        p = paging(window)
        if p["pageouts_bytes"] is None:
            out.append(f"{bid}: page-outs not recorded")
        elif p["pageouts_bytes"] > page_out_limit:
            out.append(f"{bid}: {p['pageouts_bytes'] / 2**20:.0f} MiB paged out, over the limit")
        if page_in_limit is not None and p["pageins_bytes"] is None:
            out.append(f"{bid}: page-ins not recorded")
        elif page_in_limit is not None and p["pageins_bytes"] > page_in_limit:
            out.append(f"{bid}: {p['pageins_bytes'] / 2**20:.0f} MiB paged in, over the limit for W and R")
    settle = info.get("settle")
    if settle is None:                          # batches before the settle (20261026) kept only a count
        if "stragglers" not in info:
            out.append(f"{bid}: no settle record")
        elif info["stragglers"]:
            out.append(f"{bid}: {info['stragglers']} marked process(es) alive after the block (counted without a settle)")
    else:
        if settle["survivors"]:
            who = ", ".join(f"{x['kind']} pid {x['pid']}" for x in settle["survivors"])
            out.append(f"{bid}: {len(settle['survivors'])} marked process(es) alive {settle['grace_s']:g} s after the "
                       f"block: {who}")
        if not settle["confirmed_clean"]:
            out.append(f"{bid}: the survivors could not be confirmed ended")
    if (info.get("serve") or {}).get("exit") not in (0, None):
        out.append(f"{bid}: the serve process exited {info['serve']['exit']}")
    if any(p.get("exit") != 0 for p in info.get("processes", [])):
        out.append(f"{bid}: a one-shot process exited non-zero")
    return out


def w_medians(plan: dict, rows: list[dict], round_: int) -> dict[str, float]:
    w = [r for r in rows if r["config"] == "W" and r["round"] == round_ and not r["warmup"] and not r.get("lead_in")]
    return {q: statistics.median(r["client_seconds"] for r in w if r["query"] == q)
            for q in QUERIES if any(r["query"] == q for r in w)}


def check_drift(plan: dict, rows: list[dict], limit: float) -> list[str]:
    rounds = sorted({b["round"] for b in plan["blocks"] if b["config"] == "W" and not b.get("lead_in")})
    first, last = w_medians(plan, rows, rounds[0]), w_medians(plan, rows, rounds[-1])
    out = []
    for q in QUERIES:
        if q in first and q in last and abs(last[q] / first[q] - 1) > limit:
            out.append(f"{q}: W median {first[q]:.3f} s in round {rounds[0]}, {last[q]:.3f} s in round "
                       f"{rounds[-1]} ({last[q] / first[q] - 1:+.0%}, limit {limit:.0%})")
    return out


def label(r: dict) -> str:
    if r["config"] == "W":
        return f"W{int(round(r['pair'] * 100))}"
    if r["config"] == "R":
        return f"R{int(r['hit_rate'] * 100)}-{'hit' if r['source'] == 'cache' else 'miss'}"
    if r["config"] == "F":
        return {0: "F-up", 1: "F-down", 2: "F-restarted"}[r["phase"]] + f"-{r['source']}"
    return r["config"]


def summarize(rows: list[dict]) -> list[dict]:
    measured = [r for r in rows if not r["warmup"] and r["status"] == "ok" and r["config"] != "L" and not r.get("lead_in")]
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


def host_rows(plan: dict, blocks: dict) -> list[dict]:
    """One row per recorded block: its page and swap traffic in MiB and the counters they came
    from (swap empty where not recorded), the load diagnostics, pressure and memory. Descriptive:
    only check_host's rules gate. The load includes the experiment's own processes, so no column
    says by itself why a block's latencies differ."""
    def mib(value):
        return None if value is None else value / 2**20
    def gib(reading, name):
        value = ((reading or {}).get("host") or {}).get(name)
        return None if value is None else value / 2**30
    out = []
    for block in plan["blocks"]:
        info = blocks.get(block["id"])
        if info is None:
            continue
        window = info.get("host_window") or {}
        p = paging(window)
        out.append({"block": block["id"], "config": block["config"], "round": block["round"], "pair": block.get("pair"),
                    "lead_in": bool(block.get("lead_in")) or block["config"] == "L", "seconds": info.get("seconds"),
                    "samples": window.get("samples"), "counters": p["counters"],
                    **{f"{name}_mib": mib(p[f"{name}_bytes"]) for name in VM_COUNTERS},
                    "max_pressure_level": window.get("max_pressure_level"), "load_1m_mean": window.get("load_1m_mean"),
                    "load_1m_max": window.get("load_1m_max"), "cpu_busy_share": window.get("cpu_busy_share"),
                    "available_gib_before": gib(info.get("before"), "available_bytes"),
                    "available_gib_after": gib(info.get("after"), "available_bytes"),
                    "swap_used_gib_before": gib(info.get("before"), "swap_used_bytes"),
                    "swap_used_gib_after": gib(info.get("after"), "swap_used_bytes")})
    return out


def swap_line(hosts: list[dict]) -> str:
    """The measured blocks' swap traffic in one line, recorded and not gated."""
    measured = [h for h in hosts if not h["lead_in"]]
    recorded = [h for h in measured if h["swapins_mib"] is not None and h["swapouts_mib"] is not None]
    if not recorded:
        return "not recorded"
    line = (f"up to {max(h['swapins_mib'] for h in recorded):.1f} MiB swapped in and "
            f"{max(h['swapouts_mib'] for h in recorded):.1f} MiB swapped out in a measured block (vm_stat; not gated)")
    return line + (f"; not recorded in {len(measured) - len(recorded)} block(s)" if len(recorded) < len(measured) else "")


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
    parser.add_argument("--page-out-limit-mib", type=float, default=64.0, help="per block (Part A, a proposal)")
    parser.add_argument("--page-in-limit-mib", type=float, default=256.0, help="per W or R block (Part A, a proposal)")
    parser.add_argument("--drift-limit", type=float, default=0.20, help="W's last round against its first (Part A)")
    args = parser.parse_args(argv)
    problems, rows = check(args.batch, page_out_limit=int(args.page_out_limit_mib * 2**20),
                           page_in_limit=int(args.page_in_limit_mib * 2**20), drift_limit=args.drift_limit)
    write_csv(args.batch / "measurements.csv",
              [{k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items() if k != "result"}
               for r in rows if not r["warmup"]])
    write_csv(args.batch / "summary.csv", summarize(rows))
    plan = json.loads((args.batch / "plan.json").read_text())
    pairs = paired(plan, rows)
    write_csv(args.batch / "paired.csv", pairs)
    write_csv(args.batch / "paired_summary.csv", paired_summary(pairs))
    hosts = host_rows(plan, {b["block"]: b for b in read_jsonl(args.batch / "blocks.jsonl")})
    write_csv(args.batch / "host.csv", hosts)
    valid = not any(problems.values())
    (args.batch / "validity.json").write_text(json.dumps({"valid": valid, "problems": problems}, indent=2) + "\n")
    for name, found in problems.items():
        print(f"{'ok  ' if not found else 'FAIL'} {name}" + ("" if not found else f": {len(found)} problem(s); first: {found[0]}"))
    print(f"swap: {swap_line(hosts)}")
    print("valid" if valid else "NOT valid")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
