"""analysis/collect_result_cache_measurements.py on a synthetic E3 batch that follows its plan
exactly (valid), and on copies of it with one problem planted each (each must fail its check).

AI contribution: written with Claude Code (Opus 5.5).
"""
import importlib.util
import json
from pathlib import Path

import pytest

from etf_risk import cache_experiment as e3

SPEC = importlib.util.spec_from_file_location(
    "collect_result_cache_measurements",
    Path(__file__).resolve().parents[1] / "analysis" / "collect_result_cache_measurements.py")
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)

SETTINGS = e3.Settings(rounds=2, block_size=30, n_size=6, f_phase=6, warmups=3)
GOOD_HOST = {"power_source": "AC Power", "lid_closed": False, "available_bytes": 2**31}
GOOD_WINDOW = {"samples": 20, "max_pressure_level": 2, "thermal_warning": None, "performance_warning": None,
               "swap_out_bytes": 2**20, "swap_in_bytes": 2**24}


def answer_for(r):
    return {"columns": [["ticker", "string"], ["n", "bigint"]], "rows": [[t, len(r["query"])] for t in r["tickers"]]}


def build(folder: Path) -> Path:
    blocks = e3.plan_blocks(11, SETTINGS)
    plan = {"format": 1, "settings": {**SETTINGS.__dict__, "hit_rates": list(SETTINGS.hit_rates)},
            "run": "data/run", "blocks": blocks}
    folder.mkdir()
    (folder / "plan.json").write_text(json.dumps(plan))
    every = [r for b in blocks for r in b["requests"] + b["warmups"]]
    (folder / "reference.json").write_text(json.dumps({e3._rk(r): answer_for(r) for r in every}))
    rows, infos = [], []
    for b in blocks:
        def row(i, r, source, warmup, phase=None, counters=None):
            return {"block": b["id"], "config": b["config"], "round": b["round"], "hit_rate": b.get("hit_rate"),
                    "pair": b.get("pair"), "index": i, "phase": phase, "warmup": warmup, "query": r["query"], "tickers": r["tickers"],
                    "status": "ok", "source": source, "client_seconds": 0.2 if source == "spark" else 0.01,
                    "server_seconds": {"resolve": 0.007, "total": 0.19}, "full_hashes": 1, "counters": counters,
                    "reason": None, "result": answer_for(r)}
        rows += [row(i, r, "spark", True) for i, r in enumerate(b["warmups"])]
        counters = {"get_errors": 0, "skipped": 0}
        for i, (r, (phase, source)) in enumerate(zip(b["requests"], collector.designed(b))):
            if phase == 1:
                down = sum(1 for x in rows if x["block"] == b["id"] and x["phase"] == 1)
                counters = {**counters, ("get_errors" if down < collector.THRESHOLD else "skipped"):
                            counters["get_errors" if down < collector.THRESHOLD else "skipped"] + 1}
            rows.append(row(i, r, source, False, phase, dict(counters)))
        start = 100.0 * len(infos)
        info = {"block": b["id"], "config": b["config"], "round": b["round"], "keys_present_after_delete": 0,
                "before": {"host": GOOD_HOST, "other_containers": 0, "mono": start},
                "after": {"host": GOOD_HOST, "other_containers": 0, "mono": start + 90.0},
                "host_window": GOOD_WINDOW, "other_container_events": 0,
                "settle": {"grace_s": 15.0, "settled_after_s": 0.6, "survivors": [], "unverified": [], "cleanup": None,
                           "confirmed_clean": True, "seen": [{"pid": 9, "kind": "spark_jvm", "gone_by_s": 0.6}]},
                "redis_peak": {"peak_bytes": 50 * 2**20}}
        if b["config"] == "N":
            info["processes"] = [{"exit": 0}] * len(b["requests"])
        else:
            info["serve"] = {"exit": 0}
        infos.append(info)
    (folder / "requests.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (folder / "blocks.jsonl").write_text("".join(json.dumps(i) + "\n" for i in infos))
    (folder / "batch.json").write_text(json.dumps({"container_monitor_error": None}))
    (folder / "containers.jsonl").write_text(json.dumps({"action": "exec_start", "ours": True, "time": 1, "mono": 95.0}) + "\n")
    return folder


def edit(folder, name, change):
    path = folder / name
    if name.endswith(".jsonl"):
        items = [json.loads(line) for line in path.read_text().splitlines()]
        change(items)
        path.write_text("".join(json.dumps(i) + "\n" for i in items))
    else:
        item = json.loads(path.read_text())
        change(item)
        path.write_text(json.dumps(item))


def first(items, **where):
    return next(i for i in items if all(i.get(k) == v for k, v in where.items()))


def run(folder):
    code = collector.main([str(folder)])
    return code, json.loads((folder / "validity.json").read_text())


def test_a_batch_that_follows_its_plan_is_valid(tmp_path):
    code, validity = run(build(tmp_path / "batch"))
    assert code == 0 and validity["valid"] and not any(validity["problems"].values())
    assert (tmp_path / "batch" / "summary.csv").read_text().startswith("group,query,n,")
    pairs = (tmp_path / "batch" / "paired.csv").read_text().splitlines()
    assert len(pairs) - 1 == 2 * (30 * 3 + 6)        # every R request and every N request, both rounds
    summary = (tmp_path / "batch" / "paired_summary.csv").read_text()
    assert ",block," not in summary.splitlines()[0] and "block,R,0.9,all,all,1," in summary


def _set(item, **values):
    item.update(values)


PLANTS = {
    "a missing request": ("requests.jsonl", lambda rs: rs.remove(first(rs, config="W", warmup=False)), "complete"),
    "a refused answer": ("requests.jsonl", lambda rs: _set(first(rs, config="N"), status="refused"), "statuses"),
    "a hit served from Spark": ("requests.jsonl", lambda rs: _set(first(rs, hit_rate=0.5, source="cache"), source="spark"),
                                "sources"),
    "a warm-up served from the cache": ("requests.jsonl", lambda rs: _set(first(rs, config="R", warmup=True), source="cache"),
                                        "sources"),
    "a GET error not counted": ("requests.jsonl", lambda rs: _set(first(rs, config="F", phase=1),
                                                                  counters={"get_errors": 0, "skipped": 0}), "breaker"),
    "a wrong answer": ("requests.jsonl", lambda rs: first(rs, config="W", warmup=False)["result"]["rows"].append(["X", 0]),
                       "answers"),
    "keys left before a block": ("blocks.jsonl", lambda bs: _set(first(bs, config="R"), keys_present_after_delete=2), "keys"),
    "battery power": ("blocks.jsonl", lambda bs: first(bs, config="W")["before"].update(
        host={**GOOD_HOST, "power_source": "Battery Power"}), "host"),
    "a closed lid": ("blocks.jsonl", lambda bs: first(bs, config="N")["after"].update(host={**GOOD_HOST, "lid_closed": True}),
                     "host"),
    "another container running": ("blocks.jsonl", lambda bs: first(bs, config="F")["after"].update(other_containers=1),
                                  "host"),
    "a container started between readings": ("blocks.jsonl", lambda bs: _set(first(bs, config="W"), other_container_events=1),
                                             "host"),
    "critical memory pressure": ("blocks.jsonl", lambda bs: _set(first(bs, config="R"),
                                                                 host_window={**GOOD_WINDOW, "max_pressure_level": 4}),
                                 "host"),
    "a thermal warning": ("blocks.jsonl", lambda bs: _set(first(bs, config="N"),
                                                          host_window={**GOOD_WINDOW, "thermal_warning": 2}), "host"),
    "too much swapped out": ("blocks.jsonl", lambda bs: _set(first(bs, config="W"),
                                                             host_window={**GOOD_WINDOW, "swap_out_bytes": 2**30}), "host"),
    "W or R swapping in": ("blocks.jsonl", lambda bs: _set(first(bs, config="R"),
                                                           host_window={**GOOD_WINDOW, "swap_in_bytes": 2**30}), "host"),
    "a W control that ran other requests": ("requests.jsonl", lambda rs: _set(
        first(rs, config="W", pair=0.5, warmup=False), tickers=["NOT-PLANNED"]), "pairs"),
    "a survivor after the settle": ("blocks.jsonl", lambda bs: first(bs, config="F")["settle"].update(
        settled_after_s=None, survivors=[{"pid": 9, "kind": "spark_jvm"}]), "host"),
    "a cleanup that was not confirmed": ("blocks.jsonl", lambda bs: first(bs, config="W")["settle"].update(
        confirmed_clean=False), "host"),
    "a block without a settle record": ("blocks.jsonl", lambda bs: first(bs, config="R").pop("settle"), "host"),
    "a count kept without a settle (before 20261026)": ("blocks.jsonl", lambda bs: (
        first(bs, config="N").pop("settle"), first(bs, config="N").update(stragglers=1)), "host"),
    "an aborted batch": ("batch.json", lambda m: _set(m, aborted="b03-W50: could not be confirmed ended"), "host"),
    "another project's container between blocks": ("containers.jsonl", lambda es: es.append(
        {"action": "start", "ours": False, "time": 2, "mono": 95.0}), "host"),
    "a serve process that failed": ("blocks.jsonl", lambda bs: _set(first(bs, config="R"), serve={"exit": 1}), "host"),
    "a container monitor that failed": ("batch.json", lambda m: _set(m, container_monitor_error="OSError: docker"), "host"),
    "Redis over its limit": ("blocks.jsonl", lambda bs: _set(first(bs, config="W"), redis_peak={"peak_bytes": 200 * 2**20}),
                             "redis"),
    "W drifting": ("requests.jsonl", lambda rs: [_set(r, client_seconds=0.3) for r in rs
                                                 if r["config"] == "W" and r["round"] == 1], "drift"),
}


@pytest.mark.parametrize("plant", list(PLANTS))
def test_each_planted_problem_fails_its_check(tmp_path, plant):
    name, change, check = PLANTS[plant]
    folder = build(tmp_path / "batch")
    edit(folder, name, change)
    code, validity = run(folder)
    assert code == 1 and not validity["valid"] and validity["problems"][check], validity["problems"]
