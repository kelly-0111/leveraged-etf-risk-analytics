"""The figures (src/etf_risk/plots.py) on a small run and small experiment records: their numbers, their
files, their manifest, and what happens when an input is missing, cannot be parsed, or lacks a column or
field that the figures read.

The fixture runs the Spark pipeline in the tests' shared session on two tickers. BBB has a −60% day on
an unverified date, so its 2x path is breached in every window that holds that day. Each figure's
checked numbers are compared with a direct computation from the same tables. The four experiments'
measurements CSVs are written here with known summaries: every group has three measured runs, and a
warm-up, a failed run and, where the CSV marks used protocols, a run of an unused one, each of which
would change the summaries if it were counted. One test reads the committed copies of the real CSVs
(docs/measurements) and needs nothing under data/. Without the "plots" dependency group this module
fails to import rather than being skipped.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import math
import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk import plots, spark_pipeline
from etf_risk.windows import build_definitions, write_definitions

pytestmark = pytest.mark.spark
ANCHOR = "2024-01-02"
# Each group's base time b: its measured runs take b, b + 1 and b + 2 s in wall_excl_capture_s, 0.5 s more in wall_s
STRIDES = {"p1": (21, "baseline", 100, 20.0), "p2": (14, "planned", 150, 19.0), "p3": (7, "planned", 300, 24.0),
           "p4": (3, "exploratory", 700, 40.0), "p5": (21, "drift_check", 100, 17.0)}
STRIDE_BASES = {"stride 21, first": 20.0, "stride 14": 19.0, "stride 7": 24.0, "stride 3, exploratory": 40.0,
                "stride 21, repeated": 17.0}
PARTITION_BASES = {"A": 26.0, "B": 44.0, "C": 25.0}
BASELINE_BASES = {"S": 25.0, "P": 14.0}
CACHING_BASES = {"A": 26.0, "B": 27.0, "C": 28.0}


def measurement_rows(key: str, bases: dict[str, float], marks_used: bool = True) -> pd.DataFrame:
    """Per group: three measured runs (b, b + 1 and b + 2 s; 1, 2 and 3 GiB; each phase a tenth of the
    time), then the runs a summary leaves out, each at b + 50 s and 9 GiB."""
    left_out = [{"warmup": True, "status": "ok", "used": True}, {"warmup": False, "status": "failed", "used": True}]
    left_out += [{"warmup": False, "status": "ok", "used": False}] if marks_used else []
    rows = []
    for group, base in bases.items():
        runs = [({"warmup": False, "status": "ok", "used": True}, base + i, i + 1) for i in range(3)]
        for n, (flags, t, gib) in enumerate(runs + [(flags, base + 50, 9) for flags in left_out]):
            rows.append({key: group, "run_id": f"{group}-run-{n}", **flags, "wall_excl_capture_s": t, "wall_s": t + 0.5,
                         **{f"{p}_s": t / 10 for p in plots.PHASES}, "peak_rss_total_bytes": gib * 2**30})
    rows = pd.DataFrame(rows)
    return rows if marks_used else rows.drop(columns="used")


def write_measurements(root):
    stride = measurement_rows("protocol_id", {p: v[3] for p, v in STRIDES.items()}, marks_used=False)
    for i, column in enumerate(("stride", "role", "windows")):
        stride[column] = stride["protocol_id"].map({p: v[i] for p, v in STRIDES.items()})
    baseline = measurement_rows("engine", BASELINE_BASES)
    baseline.loc[baseline["engine"] == "P", "session_start_s"] = np.nan        # P starts no Spark session
    tables = {"stride_csv": stride, "partitions_csv": measurement_rows("config", PARTITION_BASES),
              "baseline_csv": baseline, "caching_csv": measurement_rows("config", CACHING_BASES)}
    root.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        rows.to_csv(root / plots.MEASUREMENT_CSVS[name][0], index=False)
    return root


@pytest.fixture(scope="module")
def inputs(spark, tmp_path_factory):
    root = tmp_path_factory.mktemp("plots")
    rng = np.random.default_rng(23)
    dates = nyse_sessions(ANCHOR, 81)
    b = rng.normal(0, 0.02, 80)
    b[39] = -0.60                                                 # 1 + 2r < 0: a 2x breach on dates[40]
    snap = write_snapshot(root, "snap", {"AAA": (dates, rng.normal(0.001, 0.02, 80)), "BBB": (dates, b)},
                          unverified=[{"ticker": "BBB", "date": str(dates[40])}])
    windows = write_definitions(*build_definitions(snap, "rolling", window_days=10, stride=3, anchor=ANCHOR), root / "w")
    out = root / "out"
    assert spark_pipeline.main(["--windows", str(windows), "--out-root", str(out), "--run-id", "r"]) == 0
    run = out / "snap" / windows.name / "r"
    return {"run": run, "snapshot": snap, "windows": windows, "measurements": write_measurements(root / "measurements"),
            "dates": dates, "paired": plots.read_table(run / "paired")}


def arguments(inputs, out=None, *extra):
    args = ["--run", str(inputs["run"]), "--snapshot", str(inputs["snapshot"]), "--windows", str(inputs["windows"]),
            "--measurements", str(inputs["measurements"])]
    return args + (["--out", str(out)] if out is not None else []) + list(extra)


def input_paths(inputs):
    return plots.default_inputs(inputs["run"], inputs["snapshot"], inputs["windows"], inputs["measurements"])


def test_tickers_follow_the_spec_order_then_the_rest():
    assert plots.tickers_in(["QQQ", "ZZZ", "AAPL", "TSLA", "AAPL"]) == ["AAPL", "TSLA", "QQQ", "ZZZ"]


def test_m1_counts_the_windows_above_twice_the_1x_return(inputs):
    paired = inputs["paired"]
    data, checks = plots.m1_returns(paired)
    assert data[["return_1x", "return_2x"]].notna().all().all()
    for t in ("AAA", "BBB"):
        w = paired[paired["ticker"] == t].dropna(subset=["return_1x", "return_2x"])
        assert checks[t]["windows_with_both_returns"] == len(w)
        assert checks[t]["above_twice_1x"] == int((w["return_2x"] > 2 * w["return_1x"]).sum())
    assert checks["AAA"]["breached_2x"] == 0 and checks["BBB"]["breached_2x"] == int(paired["breached_2x"].sum()) > 0


def test_m2_and_m3_show_the_identity_and_the_bound_holding(inputs):
    paired = inputs["paired"]
    _, gap = plots.m2_gap(paired)
    assert gap["windows_without_breach"] == int((paired["breached_2x"] == False).sum())  # noqa: E712
    assert gap["largest_exact_gap"] < 0 and gap["largest_identity_difference"] <= 1e-9
    _, bound = plots.m3_drawdown(paired)
    assert all(c["below_bound"] == 0 for c in bound.values()) and sum(c["windows"] for c in bound.values()) > 0


def test_m5_shows_every_breached_window_ending_on_its_breach_day(inputs):
    paired = inputs["paired"]
    data, checks = plots.m5_breaches(paired, inputs["run"])
    breach_day = inputs["dates"][40]
    assert checks["breached_windows"] == int(paired["breached_2x"].sum()) > 0
    assert checks["tickers"] == ["BBB"] and checks["breach_dates"] == [str(breach_day)]
    assert checks["breach_day_returns"] == pytest.approx([-0.60]) and checks["all_use_an_unverified_day"]
    on_breach_day = data["date"] == breach_day
    assert data.loc[on_breach_day, "nav"].isna().all() and data.loc[~on_breach_day, "nav"].notna().all()
    assert data.groupby(plots.KEY).ngroups == checks["breached_windows"]


def test_s1_splits_the_medians_by_the_unverified_flag(inputs):
    paired = inputs["paired"]
    _, checks = plots.s1_sensitivity(paired)
    for t in ("AAA", "BBB"):
        w = paired[paired["ticker"] == t]
        plain = w[~w["contains_unverified_day"]]
        for leverage, column in (("1x", "return_1x"), ("2x", "return_2x")):
            c = checks[f"{t} {leverage}"]
            assert (c["all_windows"], c["unflagged_windows"]) == (w[column].count(), plain[column].count())
            assert c["all_median"] == pytest.approx(w[column].median())
            assert c["unflagged_median"] == pytest.approx(plain[column].median(), nan_ok=True)


def test_d1_and_d2_count_the_returns_the_unverified_days_and_the_windows(inputs):
    (returns, flagged), d1 = plots.d1_returns(inputs["snapshot"])
    assert d1["unverified_extreme_days"] == 1 and d1["unverified_days_without_a_return"] == 0
    assert d1["BBB"]["unverified_extreme_days"] == 1 and d1["AAA"]["unverified_extreme_days"] == 0
    assert d1["AAA"]["returns"] == 80 and d1["AAA"]["first_date"] == str(inputs["dates"][1])
    assert flagged["daily_return"].tolist() == pytest.approx([-0.60])
    _, d2 = plots.d2_windows(inputs["windows"])
    defs = pd.read_parquet(inputs["windows"] / "windows.parquet")
    for t in ("AAA", "BBB"):
        assert d2[t] == {"windows": int((defs["ticker"] == t).sum()),
                         "use_an_unverified_day": int(defs.loc[defs["ticker"] == t, "contains_unverified_day"].sum())}
    assert d2["BBB"]["use_an_unverified_day"] > 0 == d2["AAA"]["use_an_unverified_day"]


def test_x_figures_summarize_only_the_measured_runs_with_each_experiment_time_metric(inputs):
    paths = input_paths(inputs)
    _, x1 = plots.x1_stride(paths["stride_csv"])
    cases = ((x1["protocols"], STRIDE_BASES, "wall_s"),
             (plots.x2_partitions(paths["partitions_csv"])[1], PARTITION_BASES, "wall_excl_capture_s"),
             (plots.x3_baseline(paths["baseline_csv"])[1], BASELINE_BASES, "wall_s"),
             (plots.x4_caching(paths["caching_csv"])[1], CACHING_BASES, "wall_excl_capture_s"))
    for checks, bases, metric in cases:
        assert list(checks) == list(bases)                       # in the order the groups first appear
        for group, base in bases.items():
            c, t = checks[group], base + (0.5 if metric == "wall_s" else 0.0)
            assert (c["metric"], c["runs"]) == (metric, 3)
            assert (c["min_s"], c["median_s"], c["max_s"]) == pytest.approx((t, t + 1, t + 2))
            assert (c["peak_min_gib"], c["peak_median_gib"], c["peak_max_gib"]) == (1, 2, 3)
            assert c["phases_s"]["checks"] == pytest.approx((base + 1) / 10)
    assert math.isnan(cases[2][0]["P"]["phases_s"]["session_start"])
    exploratory = x1["protocols"]["stride 3, exploratory"]
    assert (exploratory["protocol"], exploratory["stride"], exploratory["windows"]) == ("p4", 3, 700)
    assert x1["drift_of_the_repeated_protocol"] == pytest.approx((18.5 - 21.5) / 21.5)


def test_x1_without_a_repeated_protocol_has_no_drift_and_still_draws(inputs, tmp_path):
    rows = pd.read_csv(inputs["measurements"] / plots.MEASUREMENT_CSVS["stride_csv"][0])
    rows[rows["role"] != "drift_check"].to_csv(tmp_path / "stride.csv", index=False)
    data, checks = plots.x1_stride(tmp_path / "stride.csv")
    assert checks["drift_of_the_repeated_protocol"] is None and "stride 21, repeated" not in checks["protocols"]
    plt.close(plots.draw_x1(data, checks))


def test_panels_have_one_axes_per_ticker_in_the_spec_order(inputs):
    fig = plots.draw_m1(*plots.m1_returns(inputs["paired"]))
    titles = [ax.get_title() for ax in fig.axes if ax.get_title()]
    plt.close(fig)
    assert [title.split(":")[0] for title in titles] == ["AAA", "BBB"]


def test_every_figure_and_the_manifest_are_written(inputs, tmp_path, capsys):
    assert plots.main(arguments(inputs, tmp_path / "check", "--check")) == 3     # other inputs: not compared
    printed = capsys.readouterr().out
    assert "documented values: not compared for M1, M2, M3, M4, M5, S1, D1, D2, X1, X2, X3, X4," in printed
    assert not (tmp_path / "check").exists()                                       # --check draws nothing
    assert plots.main(arguments(inputs, tmp_path / "f")) == 0
    manifest = json.loads((tmp_path / "f" / "figures.json").read_text())
    assert [f["id"] for f in manifest["figures"]] == list(plots.FIGURES) and len(manifest["figures"]) == 12
    for figure_id, (name, reads, _) in plots.FIGURES.items():
        assert (tmp_path / "f" / name).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        entry = next(f for f in manifest["figures"] if f["id"] == figure_id)
        assert entry["file"] == name and entry["inputs"] == list(reads) and entry["checks"]
    assert set(manifest["inputs"]) == {"run", "snapshot", "windows", *plots.MEASUREMENT_CSVS}
    assert all(len(i["sha256"]) == 64 and i["files"] > 0 for i in manifest["inputs"].values())
    assert manifest["matplotlib"] == plots.matplotlib.__version__ and len(manifest["plots_py_sha256"]) == 64


def test_regenerating_in_the_same_environment_gives_byte_identical_files(inputs, tmp_path):
    for out in ("first", "second"):
        assert plots.main(arguments(inputs, tmp_path / out)) == 0
    names = sorted(p.name for p in (tmp_path / "first").iterdir())
    assert names == sorted(p.name for p in (tmp_path / "second").iterdir()) and len(names) == len(plots.FIGURES) + 1
    for name in names:
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes(), name


def test_differences_from_the_documented_values_are_reported(inputs):
    problems = plots.compare_documented(plots.compute(input_paths(inputs)))   # the test data is not the run of record
    assert "D2 AAPL windows: None, documented 529" in problems
    assert any(p.startswith("D1 unverified extreme days: 1,") for p in problems)
    assert any(p.startswith("X2 A: ('27.000 (26.000–28.000)', '2.000 (1.000–3.000)', '2.700, ") for p in problems)
    assert any(p.startswith("X3 P: ('15.500 (14.500–16.500)', '2.000 (1.000–3.000)', '—, 1.500, ") for p in problems)


def test_missing_or_unusable_inputs_are_named_and_nothing_is_computed(inputs, tmp_path, capsys):
    run = tmp_path / "run"                         # an unfinished run: no _SUCCESS in path_days, checks failed
    for part in ("paired", "path_days"):
        (run / part).mkdir(parents=True)
    (run / "paired" / "_SUCCESS").touch()
    (run / "run.json").write_text(json.dumps({"status": "checks_failed"}))
    problems = plots.input_problems("run", run)
    assert any(p.endswith("path_days/_SUCCESS does not exist") for p in problems)
    assert any(p.endswith("records status 'checks_failed', not 'ok'") for p in problems)
    assert plots.input_problems("run", inputs["run"]) == [] == plots.input_problems("snapshot", inputs["snapshot"])
    args = arguments(inputs, tmp_path / "out", "--figures", "M1", "X2")
    args[args.index("--run") + 1] = str(tmp_path / "no-run")
    assert plots.main(args) == 2 and not (tmp_path / "out").exists()
    printed = capsys.readouterr().out
    assert "  run, for M1:" in printed and "no-run does not exist" in printed and "nothing computed" in printed


def test_a_csv_without_a_column_its_figure_reads_is_named_and_nothing_is_written(inputs, tmp_path, capsys):
    out, broken = tmp_path / "out", tmp_path / "measurements"
    assert plots.main(arguments(inputs, out, "--figures", "X2")) == 0                 # an earlier result in out
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    shutil.copytree(inputs["measurements"], broken)
    csv = broken / plots.MEASUREMENT_CSVS["partitions_csv"][0]
    pd.read_csv(csv).drop(columns="config").to_csv(csv, index=False)
    args = arguments(inputs, out, "--figures", "X2")
    args[args.index("--measurements") + 1] = str(broken)
    assert plots.main(args) == 2
    printed = capsys.readouterr().out
    assert "  partitions_csv, for X2:" in printed and f"{csv} lacks columns: config" in printed
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_csv_files_that_cannot_be_parsed_or_lack_columns_are_named(tmp_path):
    empty, ragged, header = (tmp_path / name for name in ("empty.csv", "ragged.csv", "header.csv"))
    empty.write_text("")
    ragged.write_text("engine,used\nS,True\nS,True,1,2\n")
    header.write_text("engine,used,wall_s\n")
    assert plots.input_problems("baseline_csv", empty)[0].startswith(f"{empty} cannot be parsed as CSV: EmptyDataError")
    assert plots.input_problems("baseline_csv", ragged)[0].startswith(f"{ragged} cannot be parsed as CSV: ParserError")
    assert plots.input_problems("baseline_csv", header) == [f"{header} lacks columns: {', '.join(plots.RUN_COLUMNS)}"]


def test_json_records_that_cannot_be_parsed_or_lack_fields_are_named(inputs, tmp_path):
    run, snap, windows = tmp_path / "run", tmp_path / "snap", tmp_path / "windows"
    for source, copy in ((inputs["run"], run), (inputs["snapshot"], snap), (inputs["windows"], windows)):
        shutil.copytree(source, copy)
    (run / "run.json").write_text('{"status": ')
    assert plots.input_problems("run", run)[0].startswith(f"{run / 'run.json'} cannot be parsed as JSON:")
    report = json.loads((snap / "quality_report.json").read_text())
    del report["unverified_extreme_days"]
    (snap / "quality_report.json").write_text(json.dumps(report))
    assert plots.input_problems("snapshot", snap) == [f"{snap / 'quality_report.json'} lacks fields: "
                                                      "unverified_extreme_days, a list of entries with ticker and date"]
    (windows / "config.json").write_text("[]")
    assert plots.input_problems("windows", windows) == [f"{windows / 'config.json'} does not hold a JSON object"]
    (windows / "config.json").write_text("{}")
    assert plots.input_problems("windows", windows) == [f"{windows / 'config.json'} lacks fields: windows_file"]


def test_parquet_tables_that_cannot_be_read_or_lack_columns_are_named(inputs, tmp_path):
    run, windows = tmp_path / "run", tmp_path / "windows"
    shutil.copytree(inputs["run"], run)
    shutil.copytree(inputs["windows"], windows)
    paired = pq.read_table(run / "paired").drop_columns(["mdd_bound", "log_gap"])
    for part in (run / "paired").glob("*.parquet"):
        part.unlink()
    pq.write_table(paired, run / "paired" / "part-0.parquet")
    assert plots.input_problems("run", run) == [f"{run / 'paired'} lacks columns: log_gap, mdd_bound"]
    (windows / "windows.parquet").write_bytes(b"not a Parquet file")
    assert plots.input_problems("windows", windows)[0].startswith(f"{windows / 'windows.parquet'} cannot be read as "
                                                                  "Parquet")


def test_an_unexpected_value_ends_in_an_error_and_leaves_the_output_folder_as_it_was(inputs, tmp_path):
    out, odd = tmp_path / "out", tmp_path / "measurements"
    assert plots.main(arguments(inputs, out, "--figures", "X1", "X2")) == 0
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    shutil.copytree(inputs["measurements"], odd)
    for name, column, change in (("stride_csv", "wall_s", lambda s: s * 2),       # X1 would differ if written
                                 ("partitions_csv", "config", lambda s: s.replace({"C": "D"}))):  # X2 has no "D"
        csv = odd / plots.MEASUREMENT_CSVS[name][0]
        rows = pd.read_csv(csv)
        rows[column] = change(rows[column])
        rows.to_csv(csv, index=False)
    args = arguments(inputs, out, "--figures", "X1", "X2")
    args[args.index("--measurements") + 1] = str(odd)
    with pytest.raises(KeyError, match="D"):                 # a value, not a missing input: not caught
        plots.main(args)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_a_selection_is_drawn_only_into_another_folder(inputs, tmp_path):
    assert plots.main(arguments(inputs, tmp_path / "sel", "--figures", "X3", "X1")) == 0
    manifest = json.loads((tmp_path / "sel" / "figures.json").read_text())
    assert [f["id"] for f in manifest["figures"]] == ["X1", "X3"]
    assert set(manifest["inputs"]) == {"stride_csv", "baseline_csv"}
    assert sorted(p.name for p in (tmp_path / "sel").iterdir()) == ["figures.json", "x1-stride-experiment.png",
                                                                     "x3-pandas-baseline.png"]
    assert plots.main(["--figures", "X1"]) == 2            # into docs/figures: refused before anything is read


def test_the_committed_measurement_csvs_give_the_documented_values(capsys):
    results = plots.compute(plots.default_inputs(), ("X1", "X2", "X3", "X4"))
    assert list(results) == ["X1", "X2", "X3", "X4"] and plots.compare_documented(results) == []
    assert plots.main(["--check", "--figures", "X1", "X2", "X3", "X4"]) == 0
    assert "documented values: compared for X1, X2, X3, X4: all match" in capsys.readouterr().out
