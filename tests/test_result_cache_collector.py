"""analysis/collect_result_cache_measurements.py on a synthetic E3 batch that follows its plan
exactly (valid), and on copies of it with one problem planted each (each must fail its check).

AI contribution: written with Claude Code (Opus 5.5).
"""
import csv
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
PAGE = 16384
GOOD_WINDOW = {"samples": 20, "max_pressure_level": 2, "thermal_warning": None, "performance_warning": None,
               "page_size": PAGE, "pageins": 2**24 // PAGE, "pageouts": 2**20 // PAGE, "swapins": 0, "swapouts": 0,
               "load_1m_mean": 2.0, "load_1m_max": 2.5, "cpu_busy_share": 0.3}
# what batches up to dry-run/20261026T193201Z-lead-in-round recorded: psutil's sin and sout, page-ins and page-outs
LEGACY_WINDOW = {"samples": 20, "max_pressure_level": 2, "thermal_warning": None, "performance_warning": None,
                 "swap_out_bytes": 2**20, "swap_in_bytes": 2**24}
OWN_CPU = {"seconds": 90.0, "capacity_s": 720.0, "busy_s": 300.0, "own_s": 200.0,
           "own_by_kind": {"e3_driver": 5.0, "summary": 45.0, "spark_jvm": 150.0}, "unaccounted_s": 100.0}
WALL = 1.8e9         # the wall clock at the batch's monotonic 0


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
                    "server_seconds": {"resolve": 0.007, "spark": 0.18 if source == "spark" else 0.0, "total": 0.19},
                    "lead_in": b.get("lead_in", False), "full_hashes": 1, "counters": counters,
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
                "before": {"host": GOOD_HOST, "other_containers": 0, "mono": start, "wall": WALL + start},
                "after": {"host": GOOD_HOST, "other_containers": 0, "mono": start + 90.0, "wall": WALL + start + 90.2},
                "host_window": GOOD_WINDOW, "own_cpu": OWN_CPU, "other_container_events": 0,
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
    (folder / "batch.json").write_text(json.dumps({"container_monitor_error": None,
                                                   "clock_start": {"mono": -5.0, "wall": WALL - 5.0},
                                                   "clock_end": {"mono": start + 95.0, "wall": WALL + start + 95.5}}))
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
    """The first measured item matching where: the lead-in round (round -1) is not gated by design."""
    return next(i for i in items if i.get("round", 0) != -1 and all(i.get(k) == v for k, v in where.items()))


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
    "a sleep during a block": ("blocks.jsonl", lambda bs: first(bs, config="R")["after"].update(
        wall=first(bs, config="R")["after"]["wall"] + 60.0), "sleep"),
    "a sleep during the lead-in round": ("blocks.jsonl", lambda bs: bs[0]["after"].update(
        wall=bs[0]["after"]["wall"] + 60.0), "sleep"),
    "a sleep between blocks": ("batch.json", lambda m: m["clock_end"].update(wall=m["clock_end"]["wall"] + 60.0),
                               "sleep"),
    "a block without wall-clock readings": ("blocks.jsonl", lambda bs: first(bs, config="W")["before"].pop("wall"),
                                            "sleep"),
    "a batch without clock readings": ("batch.json", lambda m: m.pop("clock_start"), "sleep"),
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


def test_the_lead_in_rounds_host_readings_are_reported_not_gated(tmp_path):
    folder = build(tmp_path / "batch")
    edit(folder, "blocks.jsonl", lambda bs: [_set(b, host_window={**GOOD_WINDOW, "max_pressure_level": 4,
                                                                 "pageins": 2**31 // PAGE})
                                             for b in bs if b["round"] == -1])
    code, validity = run(folder)
    assert code == 0 and validity["valid"]


def test_the_lead_in_round_is_left_out_of_every_comparison(tmp_path):
    folder = build(tmp_path / "batch")
    edit(folder, "requests.jsonl", lambda rs: [_set(r, client_seconds=9.0) for r in rs if r["lead_in"]])
    code, validity = run(folder)
    assert code == 0 and not validity["problems"]["drift"]
    pairs = list(csv.DictReader((folder / "paired.csv").open()))
    assert {p["round"] for p in pairs} == {"0", "1"} and len(pairs) == 2 * (30 * 3 + 6)
    assert "9.0" not in (folder / "summary.csv").read_text()


def test_the_diagnostics_are_descriptive_columns_beside_the_end_to_end_result(tmp_path):
    folder = build(tmp_path / "batch")
    run(folder)
    pairs = list(csv.DictReader((folder / "paired.csv").open()))
    hit = next(p for p in pairs if p["kind"] == "hit")
    miss = next(p for p in pairs if p["kind"] == "miss")
    assert hit["diag_spark_difference_s"] == "" and float(miss["diag_spark_difference_s"]) == 0.0
    assert float(hit["difference_s"]) == pytest.approx(0.01 - 0.2)          # end to end, unadjusted
    blocks = [r for r in csv.DictReader((folder / "paired_summary.csv").open())
              if r["scope"] == "block" and r["analysis"] == "primary"]
    by_rate = {r["pair"]: r for r in blocks if r["round"] == "0"}
    assert by_rate["0.0"]["estimate_hit_imbalance_s"] == ""                 # no hits, no estimate
    assert by_rate["0.5"]["estimate_hit_imbalance_s"] != "" and by_rate["0.9"]["estimate_hit_imbalance_s"] != ""
    assert by_rate["0.5"]["median_difference_s"] == "" and by_rate["0.5"]["total_difference_s"] != ""


def test_swap_traffic_is_recorded_and_never_gated(tmp_path, capsys):
    folder = build(tmp_path / "batch")
    edit(folder, "blocks.jsonl", lambda bs: [_set(b, host_window={**GOOD_WINDOW, "swapins": 2**31 // PAGE,
                                                                 "swapouts": 2**30 // PAGE}) for b in bs])
    code, validity = run(folder)
    assert code == 0 and validity["valid"]
    hosts = list(csv.DictReader((folder / "host.csv").open()))
    assert {h["counters"] for h in hosts} == {"vm_stat"} and float(hosts[0]["swapins_mib"]) == 2048.0
    assert "swap-ins up to 2048.0 MiB; swap-outs up to 1024.0 MiB (per block)" in capsys.readouterr().out


def test_page_traffic_is_reported_and_never_gated(tmp_path, capsys):
    """The page-in and page-out limits were withdrawn on 2026-10-26 (Part A, section 6): the
    counters are diagnostics, in any amount and when missing."""
    folder = build(tmp_path / "batch")
    edit(folder, "blocks.jsonl", lambda bs: [_set(b, host_window={**GOOD_WINDOW, "pageins": 2**32 // PAGE,
                                                                 "pageouts": 2**31 // PAGE}) for b in bs])
    edit(folder, "blocks.jsonl", lambda bs: _set(first(bs, config="W"), host_window={**GOOD_WINDOW, "pageins": None}))
    code, validity = run(folder)
    assert code == 0 and validity["valid"]
    out = capsys.readouterr().out
    assert "page-ins up to 4096.0 MiB (not recorded in 1 block(s)); page-outs up to 2048.0 MiB (per block)" in out
    assert not hasattr(collector, "PAGE_LIMITS") and "--page-in-limit-mib" not in Path(collector.__file__).read_text()


def test_a_legacy_batchs_psutil_counters_are_page_counts_never_swap(tmp_path, capsys):
    """psutil's sin and sout, recorded as swap_in_bytes and swap_out_bytes, are page-ins and page-outs:
    reported as such, gating nothing, with swap traffic not recorded."""
    folder = build(tmp_path / "batch")
    edit(folder, "blocks.jsonl", lambda bs: [_set(b, host_window={**LEGACY_WINDOW, "swap_in_bytes": 2**31})
                                             for b in bs])
    code, validity = run(folder)
    assert code == 0 and validity["valid"]
    hosts = list(csv.DictReader((folder / "host.csv").open()))
    assert {h["counters"] for h in hosts} == {"psutil sin/sout"}
    assert {(h["pageins_mib"], h["swapins_mib"], h["swapouts_mib"]) for h in hosts} == {("2048.0", "", "")}
    assert "swap-ins not recorded; swap-outs not recorded (per block)" in capsys.readouterr().out


def test_host_csv_has_one_row_per_block_with_the_load_diagnostics(tmp_path):
    folder = build(tmp_path / "batch")
    run(folder)
    hosts = list(csv.DictReader((folder / "host.csv").open()))
    plan = json.loads((folder / "plan.json").read_text())
    assert [h["block"] for h in hosts] == [b["id"] for b in plan["blocks"]]
    assert {(h["load_1m_mean"], h["load_1m_max"], h["cpu_busy_share"]) for h in hosts} == {("2.0", "2.5", "0.3")}
    assert {h["lead_in"] for h in hosts if h["round"] == "-1"} == {"True"} and float(hosts[0]["available_gib_before"]) == 2.0
    assert {round(float(h["clock_gap_s"]), 6) for h in hosts} == {0.2}


def test_own_cpu_is_reported_beside_the_busy_cpu_and_never_called_external(tmp_path, capsys):
    folder = build(tmp_path / "batch")
    code, validity = run(folder)
    assert code == 0 and validity["valid"]
    h = next(csv.DictReader((folder / "host.csv").open()))
    assert (float(h["busy_cpu_s"]), float(h["own_cpu_s"]), float(h["unaccounted_cpu_s"])) == (300.0, 200.0, 100.0)
    assert (float(h["own_spark_jvm_s"]), float(h["own_summary_s"]), float(h["own_other_s"])) == (150.0, 45.0, 0.0)
    out = capsys.readouterr().out
    assert "own CPU up to 200.0 s (per block); unaccounted CPU up to 14% of capacity (not attributed)" in out
    assert "external" not in out and "interference" not in out


def test_a_batch_without_own_cpu_records_leaves_the_columns_empty(tmp_path, capsys):
    folder = build(tmp_path / "batch")
    edit(folder, "blocks.jsonl", lambda bs: [b.pop("own_cpu") for b in bs])
    code, validity = run(folder)
    assert code == 0 and validity["valid"]
    h = next(csv.DictReader((folder / "host.csv").open()))
    assert (h["own_cpu_s"], h["own_spark_jvm_s"], h["unaccounted_cpu_s"]) == ("", "", "")
    assert "own CPU not recorded (per block); unaccounted CPU not recorded (not attributed)" in capsys.readouterr().out


def block_id(folder, config, round_, pair=None):
    plan = json.loads((folder / "plan.json").read_text())
    return next(b["id"] for b in plan["blocks"] if (b["config"], b["round"], b.get("pair")) == (config, round_, pair))


def swap_out(folder, *ids):
    edit(folder, "blocks.jsonl", lambda bs: [_set(b, host_window={**GOOD_WINDOW, "swapouts": 10})
                                             for b in bs if b["block"] in ids])


def summaries(folder):
    return list(csv.DictReader((folder / "paired_summary.csv").open()))


def test_a_pair_is_flagged_when_its_w_or_r_block_swapped_out_and_kept_in_the_primary_analysis(tmp_path, capsys):
    folder = build(tmp_path / "batch")
    r50, w90 = block_id(folder, "R", 0, 0.5), block_id(folder, "W", 1, 0.9)
    swap_out(folder, r50, w90)                              # an R block in round 0, a W control in round 1
    code, validity = run(folder)
    assert code == 0 and validity["valid"]                  # flags never invalidate
    pairs = list(csv.DictReader((folder / "paired.csv").open()))
    flagged = {(p["round"], p["pair"]) for p in pairs if p["swap_flag"] == "True"}
    assert flagged == {("0", "0.5"), ("1", "0.9")} and {p["swap_flag"] for p in pairs} == {"True", "False"}
    flags = json.loads((folder / "swap_flags.json").read_text())
    assert flags["block_pairs"] == {"total": 8, "flagged": 2, "not_recorded": 0, "free": 6}
    assert flags["request_pairs"] == {"total": 192, "flagged": 60, "not_recorded": 0, "free": 132}
    rows = summaries(folder)
    primary = [r for r in rows if r["analysis"] == "primary"]
    sensitivity = [r for r in rows if r["analysis"] == "sensitivity: excluding swap-out pairs"]
    assert len(primary) == len(sensitivity) and sum(int(r["n"]) for r in primary if r["scope"] == "requests") == 192
    assert sum(int(r["n"]) for r in sensitivity if r["scope"] == "requests") == 132
    assert sum(int(r["n_excluded"]) for r in sensitivity if r["scope"] == "requests") == 60
    gone = next(r for r in sensitivity if r["scope"] == "block" and (r["round"], r["pair"]) == ("0", "0.5"))
    assert (gone["n"], gone["n_excluded"], gone["total_ratio"]) == ("0", "30", "")
    assert "2 of 8 block pairs flagged, 0 not recorded (60 and 0 of 192 request pairs)" in capsys.readouterr().out


@pytest.mark.parametrize("member", ["N", "W0"])
def test_an_n_pair_is_flagged_when_either_member_swapped_out(tmp_path, member):
    folder = build(tmp_path / "batch")
    swap_out(folder, block_id(folder, "N", 0) if member == "N" else block_id(folder, "W", 0, 0.0))
    run(folder)
    flags = json.loads((folder / "swap_flags.json").read_text())
    n_pair = f"{block_id(folder, 'N', 0)}/{block_id(folder, 'W', 0, 0.0)}"
    assert n_pair in flags["flagged"]
    assert flags["block_pairs"]["flagged"] == (1 if member == "N" else 2)     # W0 is also R0's control


@pytest.mark.parametrize("missing", ["N", "W0"])
def test_an_n_pair_with_either_counter_missing_is_not_recorded(tmp_path, missing):
    folder = build(tmp_path / "batch")
    target = block_id(folder, "N", 0) if missing == "N" else block_id(folder, "W", 0, 0.0)
    edit(folder, "blocks.jsonl", lambda bs: [_set(b, host_window={**GOOD_WINDOW, "swapouts": None})
                                             for b in bs if b["block"] == target])
    code, validity = run(folder)
    assert code == 0 and validity["valid"]
    flags = json.loads((folder / "swap_flags.json").read_text())
    assert f"{block_id(folder, 'N', 0)}/{block_id(folder, 'W', 0, 0.0)}" in flags["not_recorded"]
    assert flags["block_pairs"]["flagged"] == 0
    pairs = list(csv.DictReader((folder / "paired.csv").open()))
    assert {p["swap_flag"] for p in pairs if p["config"] == "N" and p["round"] == "0"} == {""}


def test_pairs_without_swap_counters_stay_in_the_primary_analysis_and_leave_the_sensitivity_one(tmp_path, capsys):
    folder = build(tmp_path / "batch")
    edit(folder, "blocks.jsonl", lambda bs: [_set(b, host_window=LEGACY_WINDOW) for b in bs])
    code, validity = run(folder)
    assert code == 0 and validity["valid"]
    flags = json.loads((folder / "swap_flags.json").read_text())
    assert flags["block_pairs"] == {"total": 8, "flagged": 0, "not_recorded": 8, "free": 0}
    rows = summaries(folder)
    assert sum(int(r["n"]) for r in rows if r["analysis"] == "primary" and r["scope"] == "requests") == 192
    assert {r["n"] for r in rows if r["analysis"] != "primary"} == {"0"}
    assert "keeps 0" in capsys.readouterr().out
