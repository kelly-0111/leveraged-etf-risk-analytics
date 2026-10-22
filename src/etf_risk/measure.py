"""Run a pipeline in fresh processes and record runtime and peak memory.

Usage:
    uv run --group measure python -m etf_risk.measure --repeats 4 -- \\
        --windows data/windows/full-2026-10-12/rolling-252-s21

Each run is a new `python -m etf_risk.spark_pipeline` process with its own run id;
`--pipeline pandas` starts `etf_risk.pandas_pipeline`, the single-process baseline,
instead, and the protocol then records the pipeline, as it does for an explicit
`--pipeline spark`. The arguments after `--` go to the pipeline. From outside that
process tree, a sampler adds up the resident memory (RSS) of the process and all
its descendants (Spark JVM, Python workers) every 0.25 s and keeps the peak, in
total and per process type. The first run is marked as a warm-up and left out of
the summary.

Stop rule: threshold T = 0.60 x total physical RAM (psutil.virtual_memory().total
when the protocol starts). After each run, no further run is started if (a) any
sample of that run exceeded T, (b) the run exited with a non-zero status (failed,
crashed or killed), or (c) any of its checks failed. The run in progress is never
killed; it is recorded with status memory_threshold_exceeded, checks_failed or
failed. Every run is recorded, including the one that stopped the protocol.

Measurement limits: sampling every 0.25 s can miss shorter peaks, so the true peak
may be higher than recorded; summed RSS counts shared pages once per process, so the
sum can also overstate real use; 60% is an experimental safety limit chosen for this
machine, not a measured or guaranteed safe bound.

Output: each run's run.json gains a "measurement" section; protocol-<UTC time>.json
and one <run id>.log per run are written next to the run folders.

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_measure.py (sampler, status rules, and a protocol that must stop) and,
for --pipeline, tests/test_pandas_pipeline.py.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path

import psutil

from etf_risk.provenance import code_state

DEFAULT_INTERVAL = 0.25
DEFAULT_THRESHOLD_FRACTION = 0.60
LIMITS = [
    "RSS is sampled every interval; peaks shorter than the interval can be missed, so the true peak may be higher.",
    "Summed RSS counts pages shared between processes once per process, so the sum can also overstate real use.",
    "The threshold (default 60% of physical RAM) is an experimental safety limit for this machine, "
    "not a measured or guaranteed safe bound.",
    "Peaks per process type are each the maximum over the run, taken at different moments; they do not add up "
    "to the total peak.",
]


def process_kind(proc: psutil.Process, root_pid: int) -> str:
    if proc.pid == root_pid:
        return "driver"
    name = proc.name().lower()
    if "java" in name:
        return "spark_jvm"
    cmdline = " ".join(proc.cmdline()).lower()
    if "pyspark.daemon" in cmdline or "pyspark/daemon" in cmdline or "pyspark.worker" in cmdline:
        return "python_worker"
    return "other"


class TreeSampler(threading.Thread):
    """Sample summed RSS of a process and all its descendants until stopped."""

    def __init__(self, pid: int, interval: float = DEFAULT_INTERVAL, threshold_bytes: float = float("inf")):
        super().__init__(daemon=True)
        self.pid, self.interval, self.threshold = pid, interval, threshold_bytes
        self.peak_total = 0
        self.peak_by_kind: dict[str, int] = {}
        self.samples = 0
        self.max_processes = 0
        self.first_exceeded_at: float | None = None
        self._stop_event = threading.Event()
        self._t0 = time.perf_counter()

    def run(self) -> None:
        try:
            root = psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            return
        while not self._stop_event.is_set():
            try:
                procs = [root, *root.children(recursive=True)]
            except psutil.NoSuchProcess:
                break
            total, by_kind, counted = 0, {}, 0
            for p in procs:
                try:
                    rss, kind = p.memory_info().rss, process_kind(p, self.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                total += rss
                by_kind[kind] = by_kind.get(kind, 0) + rss
                counted += 1
            self.samples += 1
            self.max_processes = max(self.max_processes, counted)
            self.peak_total = max(self.peak_total, total)
            for kind, value in by_kind.items():
                self.peak_by_kind[kind] = max(self.peak_by_kind.get(kind, 0), value)
            if total > self.threshold and self.first_exceeded_at is None:
                self.first_exceeded_at = time.perf_counter() - self._t0
            self._stop_event.wait(self.interval)

    def stop(self) -> None:
        self._stop_event.set()
        self.join()

    @property
    def exceeded(self) -> bool:
        return self.first_exceeded_at is not None


def run_status(exit_code: int, exceeded: bool) -> tuple[str, list[str]]:
    """Primary status and every reason to stop. Pipeline exit codes: 0 ok, 1 checks failed, other = failed."""
    reasons = []
    if exit_code not in (0, 1):
        reasons.append(f"failed (exit code {exit_code})")
    if exit_code == 1:
        reasons.append("checks_failed")
    if exceeded:
        reasons.append("memory_threshold_exceeded")
    if exit_code not in (0, 1):
        return "failed", reasons
    if exit_code == 1:
        return "checks_failed", reasons
    return ("memory_threshold_exceeded" if exceeded else "ok"), reasons


def run_protocol(make_command: Callable[[str], Sequence[str]], run_dir_of: Callable[[str], Path], log_dir: Path,
                 repeats: int, interval: float = DEFAULT_INTERVAL,
                 threshold_fraction: float = DEFAULT_THRESHOLD_FRACTION) -> dict:
    total_ram = psutil.virtual_memory().total
    threshold = threshold_fraction * total_ram
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir.mkdir(parents=True, exist_ok=True)
    runs, stop_reason = [], None
    for i in range(repeats):
        run_id = f"run-{stamp}-{i + 1}"
        free_before = psutil.virtual_memory().available
        started_at = datetime.now(timezone.utc).isoformat()
        log_path = log_dir / f"{run_id}.log"
        t0 = time.perf_counter()
        with log_path.open("w") as log:
            proc = subprocess.Popen(list(make_command(run_id)), stdout=log, stderr=subprocess.STDOUT)
            sampler = TreeSampler(proc.pid, interval, threshold)
            sampler.start()
            exit_code = proc.wait()
            sampler.stop()
        wall = time.perf_counter() - t0
        status, reasons = run_status(exit_code, sampler.exceeded)
        measurement = {
            "warmup": i == 0, "exit_code": exit_code, "protocol_status": status, "stop_reasons": reasons,
            "wall_seconds": round(wall, 3), "started_at_utc": started_at, "log": str(log_path),
            "free_memory_before_bytes": free_before, "peak_rss_total_bytes": sampler.peak_total,
            "peak_rss_by_kind_bytes": sampler.peak_by_kind, "samples": sampler.samples,
            "sample_interval_seconds": interval, "max_processes_seen": sampler.max_processes,
            "threshold_bytes": int(threshold), "threshold_first_exceeded_after_seconds": sampler.first_exceeded_at,
            "limits": LIMITS,
        }
        run_json = run_dir_of(run_id) / "run.json"
        record = json.loads(run_json.read_text()) if run_json.exists() else {"run_id": run_id, "status": "no run.json written"}
        record["measurement"] = measurement
        if run_json.parent.exists():
            run_json.write_text(json.dumps(record, indent=2, default=str) + "\n")
        runs.append({
            "run_id": run_id, "warmup": i == 0, "status": status, "exit_code": exit_code, "wall_seconds": round(wall, 3),
            "in_process_seconds": record.get("timings_seconds", {}), "peak_rss_total_bytes": sampler.peak_total,
            "peak_rss_by_kind_bytes": sampler.peak_by_kind, "samples": sampler.samples,
        })
        if reasons:
            stop_reason = f"{run_id}: {', '.join(reasons)}"
            break
    measured = [r for r in runs if not r["warmup"] and r["status"] == "ok"]

    def spread(values):
        return {"median": statistics.median(values), "min": min(values), "max": max(values)} if values else None

    return {
        "protocol_started": stamp, "code": code_state(), "repeats_requested": repeats, "runs_started": len(runs),
        "stopped_early": stop_reason is not None, "stop_reason": stop_reason,
        "total_ram_bytes": total_ram, "threshold_fraction": threshold_fraction, "threshold_bytes": int(threshold),
        "sample_interval_seconds": interval, "limits": LIMITS, "runs": runs,
        "summary_over_measured_runs": {
            "runs": [r["run_id"] for r in measured],
            "wall_seconds": spread([r["wall_seconds"] for r in measured]),
            "peak_rss_total_bytes": spread([r["peak_rss_total_bytes"] for r in measured]),
        },
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" not in argv:
        print("usage: python -m etf_risk.measure [--repeats N] [--pipeline spark|pandas] -- <pipeline arguments>",
              file=sys.stderr)
        return 2
    split = argv.index("--")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument("--threshold-fraction", type=float, default=DEFAULT_THRESHOLD_FRACTION)
    parser.add_argument("--pipeline", choices=["spark", "pandas"], default=None,
                        help="the pipeline each run starts (default spark); pandas is the single-process baseline")
    args = parser.parse_args(argv[:split])
    pipeline_args = argv[split + 1:]

    name = args.pipeline or "spark"
    if name == "pandas":
        from etf_risk import pandas_pipeline as pipeline
    else:
        from etf_risk import spark_pipeline as pipeline      # imports pyspark only after argument checks
    pargs = pipeline.build_parser().parse_args(pipeline_args)
    base = pipeline.run_dir_for(pargs.windows, pargs.out_root, "x").parent

    result = run_protocol(
        make_command=lambda run_id: [sys.executable, "-m", f"etf_risk.{name}_pipeline", *pipeline_args, "--run-id", run_id],
        run_dir_of=lambda run_id: base / run_id, log_dir=base, repeats=args.repeats,
        interval=args.interval, threshold_fraction=args.threshold_fraction,
    )
    if args.pipeline is not None:                            # without the flag, the protocol is as before
        result["pipeline"] = args.pipeline
    path = base / f"protocol-{result['protocol_started']}.json"
    path.write_text(json.dumps(result, indent=2, default=str) + "\n")
    gib = 1024 ** 3
    print(f"threshold {result['threshold_bytes'] / gib:.2f} GiB ({args.threshold_fraction:.0%} of "
          f"{result['total_ram_bytes'] / gib:.1f} GiB); runs started {result['runs_started']} of {args.repeats}")
    for r in result["runs"]:
        print(f"  {r['run_id']}{' (warm-up)' if r['warmup'] else ''}: {r['status']}, {r['wall_seconds']:.1f} s, "
              f"peak RSS {r['peak_rss_total_bytes'] / gib:.2f} GiB, {r['samples']} samples")
    if result["stopped_early"]:
        print("  stopped:", result["stop_reason"])
    print(f"protocol: {path}")
    return 0 if not result["stopped_early"] else 1


if __name__ == "__main__":
    sys.exit(main())
